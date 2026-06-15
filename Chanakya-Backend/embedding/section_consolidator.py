"""
Section-level consolidation: merge page JSONs (5-10 pages) into one section summary via Gemini text-only.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

GEMINI_RETRY_BACKOFFS = (10, 30, 60, 120)


def _is_rate_limit_error(e: Exception) -> bool:
    try:
        from google.genai.errors import ClientError
        if isinstance(e, ClientError):
            return getattr(e, "code", None) in (429, 503)
    except ImportError:
        pass
    return "429" in str(e) or "503" in str(e) or "RESOURCE_EXHAUSTED" in str(e)


SECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "section_title": {"type": "string", "description": "Title of the section"},
        "content": {"type": "string", "description": "Merged content, headers/footers removed"},
        "tables": {"type": "array", "items": {"type": "string"}, "description": "Merged tables (markdown)"},
    },
    "required": ["section_title", "content", "tables"],
}

DEFAULT_SECTION_PAGES = 7  # 5-10 per plan


def _pages_to_input(pages: List[Dict[str, Any]]) -> str:
    """Turn list of page results (with 'result' key) into a single text block for the prompt."""
    parts = []
    for i, p in enumerate(pages, 1):
        r = p.get("result") or {}
        page_num = r.get("page") or p.get("page_number") or i
        parts.append(f"--- Page {page_num} ---")
        for key in ("headings", "content", "paragraphs", "tables"):
            val = r.get(key)
            if isinstance(val, list):
                parts.extend(str(x) for x in val)
            elif isinstance(val, str):
                parts.append(val)
    return "\n\n".join(parts)


def consolidate_section(
    page_results: List[Dict[str, Any]],
    page_start: int,
    page_end: int,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Merge a range of page JSONs into one section summary (Gemini text-only).

    Args:
        page_results: List of items with at least {"result": {...}} per page.
        page_start: 1-based start page index (for labeling).
        page_end: 1-based end page index.
        api_key: Gemini API key (default: GEMINI_API_KEY).
        model: Gemini model (default: GEMINI_PDF_MODEL or gemini-2.5-flash).

    Returns:
        {"section_title": str, "content": str, "tables": list}.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for section consolidation")
    model = model or os.getenv("GEMINI_PDF_MODEL", "gemini-2.5-flash")
    if not model.startswith("models/"):
        model = f"models/{model}"

    input_text = _pages_to_input(page_results)
    if not input_text.strip():
        return {"section_title": f"Pages {page_start}-{page_end}", "content": "", "tables": []}

    prompt = f"""You are given structured outputs from pages {page_start} to {page_end} of a document.

Tasks:
- Merge related headings.
- Remove headers and footers.
- Merge tables across pages.
- Produce a clean section summary.

Output valid JSON only with keys: section_title (string), content (string), tables (array of strings)."""

    full_prompt = f"{prompt}\n\n---\n{input_text}"

    client = genai.Client(api_key=api_key)
    last_error = None
    for attempt, backoff in enumerate(GEMINI_RETRY_BACKOFFS):
        try:
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=SECTION_SCHEMA,
                ),
            )
            raw = (response.text or "").strip()
            if not raw:
                return {"section_title": f"Pages {page_start}-{page_end}", "content": input_text[:5000], "tables": []}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"section_title": f"Pages {page_start}-{page_end}", "content": raw[:5000], "tables": []}
        except Exception as e:
            last_error = e
            if _is_rate_limit_error(e) and attempt < len(GEMINI_RETRY_BACKOFFS) - 1:
                logger.warning("Section consolidation rate limit (attempt %s), retrying in %s s: %s", attempt + 1, backoff, e)
                time.sleep(backoff)
            else:
                raise
    if last_error:
        raise last_error
    return {"section_title": f"Pages {page_start}-{page_end}", "content": input_text[:5000], "tables": []}


def run_section_consolidation(
    page_results: List[Dict[str, Any]],
    section_size: int = DEFAULT_SECTION_PAGES,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    delay_sec: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Run consolidation for every section_size pages. Returns list of
    {section_index, page_start, page_end, result: {section_title, content, tables}}.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    model = model or os.getenv("GEMINI_PDF_MODEL", "gemini-2.5-flash")
    delay = int(os.getenv("PDF_COMPILER_DELAY_SEC", "8")) if delay_sec is None else delay_sec
    sections_out = []
    i = 0
    section_index = 0
    while i < len(page_results):
        if section_index > 0:
            time.sleep(delay)
        chunk = page_results[i : i + section_size]
        if not chunk:
            break
        page_start = chunk[0].get("page_number") or (i + 1)
        page_end = chunk[-1].get("page_number") or (i + len(chunk))
        result = consolidate_section(chunk, page_start, page_end, api_key=api_key, model=model)
        sections_out.append({
            "section_index": section_index,
            "page_start": page_start,
            "page_end": page_end,
            "result": result,
        })
        section_index += 1
        i += len(chunk)
    return sections_out
