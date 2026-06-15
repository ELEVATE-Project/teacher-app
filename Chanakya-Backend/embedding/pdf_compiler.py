"""
PDF compiler orchestrator: LlamaParse-only parsing, page/section persistence, section consolidation.
"""

import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .database import Database
from .pdf_llamaparse_pipeline import run_llamaparse_text_pipeline
from .section_consolidator import run_section_consolidation

logger = logging.getLogger(__name__)

SECTION_PAGE_SIZE = 7
# Max chars for document-ready summary (show more content in chat card)
SUMMARY_MAX_CHARS = 50000


def _get_delay_sec() -> int:
    """Seconds between Gemini calls (default 8; set to 2 for fast mode / higher quota)."""
    return int(os.getenv("PDF_COMPILER_DELAY_SEC", "8"))


def _get_skip_section_pages() -> int:
    """Skip section consolidation for PDFs with this many pages or fewer (default 5)."""
    return int(os.getenv("PDF_COMPILER_SKIP_SECTION_PAGES", "5"))


def _ensure_pdf_path(pdf_path_or_bytes: str | bytes) -> Tuple[str, Optional[tempfile._TemporaryFileWrapper]]:
    """If bytes, write to temp file and return (path, temp_file); else (path, None). Caller should close temp_file."""
    if isinstance(pdf_path_or_bytes, bytes):
        f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        f.write(pdf_path_or_bytes)
        f.flush()
        return f.name, f
    path = Path(pdf_path_or_bytes)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    return str(path), None


def compile_pdf(
    pdf_path_or_bytes: str | bytes,
    document_id: Optional[str] = None,
    db_path: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    section_page_size: int = SECTION_PAGE_SIZE,
) -> Tuple[str, str]:
    """
    Run the full PDF compiler: parse with LlamaParse only, persist page results,
    run section consolidation, produce summary.

    Args:
        pdf_path_or_bytes: Path to PDF file or raw bytes.
        document_id: If provided, use this; otherwise generate a UUID.
        db_path: SQLite path for page/section storage (default: embedding/ncert_books.db).
        api_key: Gemini API key for section consolidation (default: GEMINI_API_KEY).
        model: Gemini model for section consolidation (default: GEMINI_PDF_MODEL or gemini-2.5-flash).
        section_page_size: Number of pages per section for consolidation (default 7).

    Returns:
        (document_id, summary_text).
    """
    if not os.getenv("LLAMA_CLOUD_API_KEY") or not os.getenv("LLAMA_CLOUD_API_KEY").strip():
        raise ValueError(
            "LLAMA_CLOUD_API_KEY is required for PDF compilation. Set it in .env. "
            "Get your key from: https://cloud.llamaindex.ai/"
        )
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for PDF compiler (section consolidation)")
    document_id = document_id or str(uuid.uuid4())
    db_path = db_path or os.getenv("PDF_COMPILER_DB_PATH", "embedding/ncert_books.db")

    pdf_path, temp_file = _ensure_pdf_path(pdf_path_or_bytes)
    try:
        db = Database(db_path=db_path)
        try:
            db.delete_pdf_document_results(document_id)
        except Exception:
            pass

        logger.info("Using LlamaParse for PDF parsing")
        page_results = run_llamaparse_text_pipeline(pdf_path)

        delay_sec = _get_delay_sec()
        for pr in page_results:
            db.insert_pdf_page_result(
                document_id=document_id,
                page_number=pr["page_number"],
                result_json=pr["result"],
                pipeline_type=pr.get("pipeline_type", "text"),
                confidence_flags=pr.get("confidence_flags"),
                image_ref=None,
            )

        num_pages = len(page_results)
        skip_section_threshold = _get_skip_section_pages()
        if num_pages <= skip_section_threshold:
            logger.info("Skipping section consolidation for small PDF (%s pages <= %s)", num_pages, skip_section_threshold)
            sections = []
        else:
            sections = run_section_consolidation(
                page_results,
                section_size=section_page_size,
                api_key=api_key,
                model=model,
                delay_sec=delay_sec,
            )
        for s in sections:
            db.insert_pdf_section_result(
                document_id=document_id,
                section_index=s["section_index"],
                page_start=s["page_start"],
                page_end=s["page_end"],
                result_json=s["result"],
            )

        summary = db.get_pdf_document_text_for_rag(document_id, max_chars=SUMMARY_MAX_CHARS)
        if not summary.strip():
            summary = "Document processed. No extractable content summary available."
        db.close()
        return document_id, summary
    finally:
        if temp_file:
            try:
                temp_file.close()
                os.unlink(pdf_path)
            except Exception:
                pass


def main():
    """CLI entrypoint: python -m embedding.pdf_compiler /path/to/file.pdf [--db-path ...]"""
    import argparse
    parser = argparse.ArgumentParser(description="Compile PDF: LlamaParse parsing, section consolidation")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--db-path", default="embedding/ncert_books.db", help="SQLite database path")
    parser.add_argument("--document-id", default=None, help="Document ID (default: generate UUID)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    doc_id, summary = compile_pdf(args.pdf_path, document_id=args.document_id, db_path=args.db_path)
    print(f"document_id: {doc_id}")
    print(f"summary (first 500 chars): {summary[:500]}...")


if __name__ == "__main__":
    main()
