"""
PDF Compiler Service: wraps the embedding PDF compiler for chat uploads.
Runs type detection, text/vision pipeline, section consolidation; returns document_id and summary.
"""

import asyncio
import os
import structlog
from pathlib import Path
from typing import Optional, Tuple

logger = structlog.get_logger(__name__)

# Ensure repo root (Chanakya/) is on path so "embedding" package can be imported
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_REPO_ROOT))

from embedding.pdf_compiler import compile_pdf  # noqa: E402


def _compile_sync(pdf_bytes: bytes, document_id: Optional[str], db_path: Optional[str]) -> Tuple[str, str]:
    """Sync wrapper for compile_pdf (run in executor)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for PDF compiler")
    return compile_pdf(
        pdf_bytes,
        document_id=document_id,
        db_path=db_path,
        api_key=api_key,
    )


async def compile_pdf_async(
    pdf_bytes: bytes,
    document_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Run the PDF compiler in a thread pool so the event loop is not blocked.
    Returns (document_id, summary).
    """
    loop = asyncio.get_event_loop()
    db_path = db_path or os.getenv("PDF_COMPILER_DB_PATH")
    if not db_path:
        # Default: embedding DB at repo root
        db_path = str(_REPO_ROOT / "embedding" / "ncert_books.db")
    return await loop.run_in_executor(
        None,
        _compile_sync,
        pdf_bytes,
        document_id,
        db_path,
    )
