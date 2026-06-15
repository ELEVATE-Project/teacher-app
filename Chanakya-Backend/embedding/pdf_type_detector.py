"""
PDF type detection: text-based vs image-based.
Uses pdfplumber on the first 3 pages; > 300 chars => text, else image.
"""

import logging
from pathlib import Path
from typing import Literal, Union

import pdfplumber

logger = logging.getLogger(__name__)

# Threshold: if extracted text from first 3 pages exceeds this, treat as text-based PDF
TEXT_DENSITY_THRESHOLD = 300


def pdf_type(path: Union[str, Path]) -> Literal["text", "image"]:
    """
    Detect whether a PDF is text-based or image-based (scanned/hybrid).

    Uses the first 3 pages only. If concatenated text length > 300 chars,
    the PDF is considered text-based; otherwise image-based (vision required).

    Args:
        path: Path to the PDF file (or path-like).

    Returns:
        "text" if the PDF has sufficient extractable text; "image" otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a PDF or cannot be opened.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {path}")

    try:
        with pdfplumber.open(path) as pdf:
            pages_to_check = pdf.pages[:3]
            if not pages_to_check:
                logger.warning("PDF has no pages, treating as image")
                return "image"
            text_parts = []
            for page in pages_to_check:
                try:
                    t = page.extract_text()
                    text_parts.append(t or "")
                except Exception as e:
                    logger.debug("Page text extraction failed: %s", e)
                    text_parts.append("")
            text = "".join(text_parts)
            total_chars = len(text.strip())
            result = "text" if total_chars > TEXT_DENSITY_THRESHOLD else "image"
            logger.info("PDF type detection: %s (%d chars in first 3 pages) -> %s", path.name, total_chars, result)
            return result
    except pdfplumber.PDFSyntaxError as e:
        raise ValueError(f"Invalid or corrupted PDF: {path}") from e
    except Exception as e:
        raise ValueError(f"Could not open PDF {path}: {e}") from e
