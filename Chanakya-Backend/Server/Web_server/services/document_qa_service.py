"""
Document Q&A: answer questions using only the content of an uploaded PDF (by document_id).
Retrieves compiled PDF text from the embedding DB and uses Gemini to generate an answer.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
import structlog

logger = structlog.get_logger(__name__)

DOCUMENT_QA_RETRY_BACKOFFS = (5, 15, 45)


def _is_rate_limit(e: Exception) -> bool:
    try:
        from google.genai.errors import ClientError
        if isinstance(e, ClientError):
            return getattr(e, "code", None) in (429, 503)
    except ImportError:
        pass
    return "429" in str(e) or "503" in str(e) or "RESOURCE_EXHAUSTED" in str(e)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from embedding.database import Database  # noqa: E402

# Max context chars to send to Gemini (leave room for query + response)
DOCUMENT_QA_MAX_CONTEXT_CHARS = 28000


def get_document_answer(
    document_id: str,
    query: str,
    api_key: Optional[str] = None,
    db_path: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Retrieve PDF document content by document_id and generate an answer to the query using Gemini.
    Returns the answer text.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for document Q&A")
    model = model or os.getenv("GEMINI_PDF_MODEL", "gemini-2.5-flash")
    if not model.startswith("models/"):
        model = f"models/{model}"
    db_path = db_path or os.getenv("PDF_COMPILER_DB_PATH")
    if not db_path:
        db_path = str(_REPO_ROOT / "embedding" / "ncert_books.db")

    db = Database(db_path=db_path)
    try:
        context = db.get_pdf_document_text_for_rag(document_id, max_chars=DOCUMENT_QA_MAX_CONTEXT_CHARS)
    finally:
        db.close()

    if not context or not context.strip():
        return "I couldn't find any content for this document. It may not have been processed yet or the document might be empty."

    prompt = f"""You are answering a question about an uploaded document. Use ONLY the following document content. Do not use external knowledge. If the answer is not in the document, say so clearly.

Document content:
---
{context}
---

Question: {query}

Answer (concise, based only on the document):"""

    client = genai.Client(api_key=api_key)
    last_error = None
    for attempt, backoff in enumerate(DOCUMENT_QA_RETRY_BACKOFFS):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )
            return (response.text or "").strip() or "I couldn't generate an answer."
        except Exception as e:
            last_error = e
            if _is_rate_limit(e) and attempt < len(DOCUMENT_QA_RETRY_BACKOFFS) - 1:
                logger.warning("Document Q&A rate limit (attempt %s), retrying in %s s", attempt + 1, backoff)
                time.sleep(backoff)
            else:
                raise
    if last_error:
        raise last_error
    return "I couldn't generate an answer."
