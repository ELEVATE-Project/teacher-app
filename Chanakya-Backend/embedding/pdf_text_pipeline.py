"""
Text-based PDF pipeline: extract text with pdfplumber, chunk, then structure with Gemini (text-only).
"""

import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Rate limit: retry 429/503 with exponential backoff (seconds)
GEMINI_RETRY_BACKOFFS = (10, 30, 60, 120)

# Approximate chars per token for chunking (target 800-1200 tokens)
CHARS_PER_TOKEN = 4
CHUNK_MIN_CHARS = 800 * CHARS_PER_TOKEN   # 3200
CHUNK_MAX_CHARS = 1200 * CHARS_PER_TOKEN  # 4800

TEXT_STRUCTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "headings": {"type": "array", "items": {"type": "string"}, "description": "Section headings"},
        "content": {"type": "array", "items": {"type": "string"}, "description": "Paragraphs or content blocks"},
        "tables": {"type": "array", "items": {"type": "string"}, "description": "Tables as markdown or text"},
    },
    "required": ["headings", "content", "tables"],
}


def _extract_text_per_page(pdf_path: str) -> List[Tuple[int, str]]:
    """Extract text from each page. Returns list of (page_number_1based, text)."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    result = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            try:
                t = page.extract_text()
                result.append((i, (t or "").strip()))
            except Exception as e:
                logger.warning("Page %s extract failed: %s", i, e)
                result.append((i, ""))
    return result


def _chunk_text(
    pages: List[Tuple[int, str]],
    min_chars: int = CHUNK_MIN_CHARS,
    max_chars: int = CHUNK_MAX_CHARS,
) -> List[Dict[str, Any]]:
    """
    Chunk pages into segments of ~800-1200 tokens (by char count).
    Prefer splitting on double newlines or lines that look like headings.
    Returns list of {"page_start": 1-based, "page_end": 1-based, "text": str}.
    """
    if not pages:
        return []
    chunks = []
    current_text: List[str] = []
    current_pages: List[int] = []
    current_len = 0

    def flush():
        if current_text and current_pages:
            chunks.append({
                "page_start": min(current_pages),
                "page_end": max(current_pages),
                "text": "\n\n".join(current_text),
            })

    for page_num, text in pages:
        if not text.strip():
            if current_text:
                flush()
            current_text = []
            current_pages = []
            current_len = 0
            continue
        # Prefer split by paragraph (double newline) or single newline
        parts = re.split(r"\n\s*\n", text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if current_len + len(part) + 2 > max_chars and current_text:
                flush()
                current_text = []
                current_pages = []
                current_len = 0
            current_text.append(part)
            current_pages.append(page_num)
            current_len += len(part) + 2
            if current_len >= min_chars:
                flush()
                current_text = []
                current_pages = []
                current_len = 0
    flush()
    return chunks


def _is_rate_limit_error(e: Exception) -> bool:
    """True if exception is 429 or 503 (rate limit / resource exhausted)."""
    try:
        from google.genai.errors import ClientError
        if isinstance(e, ClientError):
            return getattr(e, "code", None) in (429, 503)
    except ImportError:
        pass
    return "429" in str(e) or "503" in str(e) or "RESOURCE_EXHAUSTED" in str(e)


def _call_gemini_structure(
    client: genai.Client,
    model: str,
    chunk_text: str,
) -> Dict[str, Any]:
    """Call Gemini to structure a text chunk into headings, content, tables. Returns JSON dict."""
    prompt = """You are analyzing extracted document text.

Tasks:
- Preserve structure.
- Identify headings and tables.
- Do not hallucinate missing content.

Output valid JSON only with keys: headings (array of strings), content (array of strings), tables (array of strings)."""

    full_prompt = f"{prompt}\n\n---\nDocument text:\n{chunk_text}"

    last_error = None
    for attempt, backoff in enumerate(GEMINI_RETRY_BACKOFFS):
        try:
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=TEXT_STRUCTURE_SCHEMA,
                ),
            )
            raw = (response.text or "").strip()
            if not raw:
                return {"headings": [], "content": [], "tables": []}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"headings": [], "content": [chunk_text], "tables": []}
        except Exception as e:
            last_error = e
            if _is_rate_limit_error(e) and attempt < len(GEMINI_RETRY_BACKOFFS) - 1:
                logger.warning("Gemini rate limit (attempt %s), retrying in %s s: %s", attempt + 1, backoff, e)
                time.sleep(backoff)
            else:
                raise
    if last_error:
        raise last_error
    return {"headings": [], "content": [], "tables": []}


def _process_chunk(
    client: genai.Client,
    model: str,
    idx: int,
    ch: Dict[str, Any],
) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
    """Process one chunk; returns (chunk_index, chunk, structured)."""
    page_start = ch["page_start"]
    page_end = ch["page_end"]
    text = ch["text"]
    if not text.strip():
        return idx, ch, {"headings": [], "content": [], "tables": []}
    try:
        structured = _call_gemini_structure(client, model, text)
    except Exception as e:
        logger.warning("Gemini structure failed for pages %s-%s: %s", page_start, page_end, e)
        structured = {"headings": [], "content": [text], "tables": []}
    return idx, ch, structured


def run_text_pipeline(
    pdf_path: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    delay_sec: Optional[int] = None,
    max_concurrent: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Run the full text-based PDF pipeline: extract text, chunk, structure with Gemini.
    Uses limited parallelism (max_concurrent workers) and configurable delay between batches.

    Args:
        pdf_path: Path to the PDF file.
        api_key: Gemini API key (default: GEMINI_API_KEY env).
        model: Gemini model name (default: GEMINI_PDF_MODEL or gemini-2.5-flash).
        delay_sec: Seconds between batches of Gemini calls (default: PDF_COMPILER_DELAY_SEC or 8).
        max_concurrent: Max concurrent Gemini calls (default: PDF_COMPILER_MAX_CONCURRENT or 2).

    Returns:
        List of page-level structured results.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for text pipeline")
    model = model or os.getenv("GEMINI_PDF_MODEL", "gemini-2.5-flash")
    if not model.startswith("models/"):
        model = f"models/{model}"
    delay = int(os.getenv("PDF_COMPILER_DELAY_SEC", "8")) if delay_sec is None else delay_sec
    max_workers = max(1, int(os.getenv("PDF_COMPILER_MAX_CONCURRENT", "2")) if max_concurrent is None else max_concurrent)

    client = genai.Client(api_key=api_key)
    pages = _extract_text_per_page(pdf_path)
    if not pages:
        logger.warning("No text extracted from %s", pdf_path)
        return []

    chunks = _chunk_text(pages)
    work = [(i, ch) for i, ch in enumerate(chunks) if ch["text"].strip()]
    if not work:
        return []

    chunk_results: List[Tuple[int, Dict[str, Any], Dict[str, Any]]] = []
    completed_per_batch = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_chunk, client, model, idx, ch): idx for idx, ch in work}
        for fut in as_completed(futures):
            idx, ch, structured = fut.result()
            chunk_results.append((idx, ch, structured))
            completed_per_batch += 1
            if completed_per_batch >= max_workers:
                time.sleep(delay)
                completed_per_batch = 0

    chunk_results.sort(key=lambda x: x[0])
    results = []
    for _idx, ch, structured in chunk_results:
        page_start = ch["page_start"]
        page_end = ch["page_end"]
        for p in range(page_start, page_end + 1):
            results.append({
                "page_number": p,
                "result": structured,
                "pipeline_type": "text",
                "confidence_flags": None,
            })
    return results