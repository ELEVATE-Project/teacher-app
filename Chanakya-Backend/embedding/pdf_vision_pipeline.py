"""
Image-based PDF pipeline: render each page at 300 DPI, one Gemini vision call per page.
"""

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# 300 DPI for vision path (plan spec)
PAGE_DPI = 300
# Zoom factor for PyMuPDF: 300/72 ≈ 4.17
PAGE_ZOOM = PAGE_DPI / 72.0

VISION_PAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "page": {"type": "integer", "description": "Page number (1-based)"},
        "headings": {"type": "array", "items": {"type": "string"}},
        "paragraphs": {"type": "array", "items": {"type": "string"}},
        "tables": {"type": "array", "items": {"type": "string"}, "description": "Tables as markdown"},
        "uncertain": {"type": "array", "items": {"type": "string"}, "description": "Text that was unclear"},
    },
    "required": ["page", "headings", "paragraphs", "tables", "uncertain"],
}

MAX_RETRIES = 5
# Exponential backoff for 429/503 (seconds)
RETRY_BACKOFFS = (10, 30, 60, 120, 180)


def _render_page_to_bytes(doc: fitz.Document, page_index: int) -> bytes:
    """Render a single page (0-based index) to PNG bytes at 300 DPI."""
    page = doc[page_index]
    mat = fitz.Matrix(PAGE_ZOOM, PAGE_ZOOM)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")


def _call_gemini_vision_page(
    client: genai.Client,
    model: str,
    page_number: int,
    image_bytes: bytes,
) -> Dict[str, Any]:
    """One page per request. Returns JSON dict with page, headings, paragraphs, tables, uncertain."""
    prompt = f"""You are analyzing page {page_number} of a document.

Extract:
- Headings
- Paragraphs
- Tables as markdown
- Notes if text is unclear (put in "uncertain")

Rules:
- Do not infer missing text.
- Keep output compact and factual.

Output valid JSON only with keys: page (integer), headings (array), paragraphs (array), tables (array), uncertain (array)."""

    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
    response = client.models.generate_content(
        model=model,
        contents=[image_part, types.Part.from_text(text=prompt)],
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=VISION_PAGE_SCHEMA,
        ),
    )
    raw = (response.text or "").strip()
    if not raw:
        return {
            "page": page_number,
            "headings": [],
            "paragraphs": [],
            "tables": [],
            "uncertain": [],
        }
    try:
        out = json.loads(raw)
        out["page"] = page_number
        return out
    except json.JSONDecodeError:
        return {
            "page": page_number,
            "headings": [],
            "paragraphs": [],
            "tables": [],
            "uncertain": [raw[:500]],
        }


def _is_rate_limit(e: Exception) -> bool:
    try:
        from google.genai.errors import ClientError
        if isinstance(e, ClientError):
            return getattr(e, "code", None) in (429, 503)
    except ImportError:
        pass
    return "429" in str(e) or "503" in str(e) or "RESOURCE_EXHAUSTED" in str(e)


def _process_vision_page(
    client: genai.Client,
    model: str,
    page_number: int,
    image_bytes: bytes,
) -> Tuple[int, Dict[str, Any]]:
    """Process one page; returns (page_number, structured)."""
    structured = None
    for attempt in range(MAX_RETRIES):
        try:
            structured = _call_gemini_vision_page(client, model, page_number, image_bytes)
            break
        except Exception as e:
            backoff = RETRY_BACKOFFS[attempt] if attempt < len(RETRY_BACKOFFS) else RETRY_BACKOFFS[-1]
            if _is_rate_limit(e) and attempt < MAX_RETRIES - 1:
                logger.warning("Vision rate limit for page %s (attempt %s), retrying in %s s: %s", page_number, attempt + 1, backoff, e)
                time.sleep(backoff)
            else:
                logger.warning("Vision failed for page %s after %s attempts: %s", page_number, attempt + 1, e)
                structured = {
                    "page": page_number,
                    "headings": [],
                    "paragraphs": [],
                    "tables": [],
                    "uncertain": [str(e)],
                }
                break
    if structured is None:
        structured = {
            "page": page_number,
            "headings": [],
            "paragraphs": [],
            "tables": [],
            "uncertain": ["Vision failed after retries"],
        }
    return page_number, structured


def run_vision_pipeline(
    pdf_path: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    delay_sec: Optional[int] = None,
    max_concurrent: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Run the vision pipeline: render each page at 300 DPI, one Gemini vision call per page.
    Uses limited parallelism (max_concurrent workers) and configurable delay between batches.

    Args:
        pdf_path: Path to the PDF file.
        api_key: Gemini API key (default: GEMINI_API_KEY env).
        model: Gemini model name (default: GEMINI_PDF_MODEL or gemini-2.5-flash).
        delay_sec: Seconds between batches of Gemini calls (default: PDF_COMPILER_DELAY_SEC or 8).
        max_concurrent: Max concurrent Gemini calls (default: PDF_COMPILER_MAX_CONCURRENT or 2).

    Returns:
        List of items: {page_number, result, pipeline_type: "vision", confidence_flags}.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for vision pipeline")
    model = model or os.getenv("GEMINI_PDF_MODEL", "gemini-2.0-flash-001")
    if not model.startswith("models/"):
        model = f"models/{model}"
    delay = int(os.getenv("PDF_COMPILER_DELAY_SEC", "8")) if delay_sec is None else delay_sec
    max_workers = max(1, int(os.getenv("PDF_COMPILER_MAX_CONCURRENT", "2")) if max_concurrent is None else max_concurrent)

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(str(path))
    try:
        num_pages = len(doc)
        page_images: List[Tuple[int, bytes]] = []
        for page_index in range(num_pages):
            image_bytes = _render_page_to_bytes(doc, page_index)
            page_images.append((page_index + 1, image_bytes))
    finally:
        doc.close()

    if not page_images:
        return []

    client = genai.Client(api_key=api_key)
    page_results: List[Tuple[int, Dict[str, Any]]] = []
    completed_per_batch = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process_vision_page, client, model, pnum, img): pnum
            for pnum, img in page_images
        }
        for fut in as_completed(futures):
            pnum, structured = fut.result()
            page_results.append((pnum, structured))
            completed_per_batch += 1
            if completed_per_batch >= max_workers:
                time.sleep(delay)
                completed_per_batch = 0

    page_results.sort(key=lambda x: x[0])
    results = []
    for page_number, structured in page_results:
        confidence = {"uncertain": len(structured.get("uncertain", [])) > 0}
        results.append({
            "page_number": page_number,
            "result": structured,
            "pipeline_type": "vision",
            "confidence_flags": confidence,
        })
    return results


def run_vision_single_page(
    pdf_path: str,
    page_number: int,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run vision for one page only (for hybrid: sparse page fallback).
    Returns one item: {page_number, result, pipeline_type, confidence_flags}.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    model = model or os.getenv("GEMINI_PDF_MODEL", "gemini-2.5-flash")
    if not model.startswith("models/"):
        model = f"models/{model}"
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
    doc = fitz.open(str(path))
    try:
        if page_number < 1 or page_number > len(doc):
            raise ValueError(f"Page {page_number} out of range (1..{len(doc)})")
        image_bytes = _render_page_to_bytes(doc, page_number - 1)
        structured = _call_gemini_vision_page(client, model, page_number, image_bytes)
        return {
            "page_number": page_number,
            "result": structured,
            "pipeline_type": "vision",
            "confidence_flags": {"uncertain": len(structured.get("uncertain", [])) > 0},
        }
    finally:
        doc.close()
