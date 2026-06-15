"""
LlamaParse-based PDF text pipeline for the compiler.
Uses LlamaParse API for extraction (no Gemini calls); output matches compiler page-result schema.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)


def run_llamaparse_text_pipeline(
    pdf_path: str,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract text from a PDF using LlamaParse and return page results in the compiler schema.

    Requires LLAMA_CLOUD_API_KEY (env or api_key). No Gemini calls.

    Args:
        pdf_path: Path to the PDF file.
        api_key: LlamaParse API key (default: LLAMA_CLOUD_API_KEY env).

    Returns:
        List of page-result dicts: {"page_number", "result": {"headings", "content", "tables"}, "pipeline_type": "llamaparse", "confidence_flags": None}.
    """
    key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "LLAMA_CLOUD_API_KEY is required for LlamaParse pipeline. "
            "Set it in .env or pass api_key. Get your key from: https://cloud.llamaindex.ai/"
        )
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    extractor = PDFExtractor(api_key=key)
    pages = extractor.extract_text(str(pdf_path))

    page_results: List[Dict[str, Any]] = []
    for p in pages:
        page_number = p.get("page_number")
        text = (p.get("text") or "").strip()
        if page_number is None:
            continue
        result = {
            "headings": [],
            "content": [text] if text else [],
            "tables": [],
        }
        page_results.append({
            "page_number": page_number,
            "result": result,
            "pipeline_type": "llamaparse",
            "confidence_flags": None,
        })

    logger.info("LlamaParse extracted %s pages from %s", len(page_results), path.name)
    return page_results
