"""
RAGFlow Integration Service (Improved)

Replaces the basic orchestrator's RAG with RAGFlow backend.
Uses synchronous requests with connection pooling for reliability.
Handles dataset routing, session management, and chunk retrieval.
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import settings
from module.models.schemas import TextbookContent

logger = logging.getLogger(__name__)


class RAGFlowClientV2:
    """
    Improved RAGFlow client with:
    - Bearer token authentication
    - Connection pooling & retries
    - Session management
    - Dataset routing
    - Better error handling
    """

    def __init__(self):
        """Initialize RAGFlow client with connection pooling."""
        self.base_url = settings.RAGFLOW_BASE_URL.rstrip("/")
        # Prioritize RAGFLOW_API_KEY over RAGFLOW_CLIENT_ID for API Key bearer authentication
        self.api_key = settings.RAGFLOW_API_KEY or settings.RAGFLOW_CLIENT_ID
        self.default_chat_id = settings.RAGFLOW_CHAT_ID
        self.timeout_sec = settings.RAGFLOW_TIMEOUT_SECONDS
        self.default_dataset = settings.RAGFLOW_DEFAULT_SCOPE
        self.default_dataset_id = settings.RAGFLOW_DATASET_ID

        # Session with connection pooling and retries
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _headers(self) -> Dict[str, str]:
        """Generate authorization headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        """Construct full URL."""
        return f"{self.base_url}{path}"

    def is_configured(self) -> bool:
        """Check if RAGFlow is properly configured."""
        return bool(self.base_url and self.api_key)

    # ─────────────────────────────────────────────────────────────────
    # Health & System
    # ─────────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Check RAGFlow health status."""
        try:
            resp = self.session.get(
                self._url("/api/v1/system/healthz"),
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("status") == "ok"
        except Exception as e:
            logger.warning(f"RAGFlow health check failed: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────
    # Dataset Operations
    # ─────────────────────────────────────────────────────────────────

    def list_datasets(
        self, name: str = "", page: int = 1, page_size: int = 30
    ) -> List[Dict[str, Any]]:
        """List datasets, optionally filtered by name."""
        try:
            params = {"page": page, "page_size": page_size}
            if name:
                params["name"] = name

            resp = self.session.get(
                self._url("/api/v1/datasets"),
                headers=self._headers(),
                params=params,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Handle different response formats
            if data.get("data"):
                datasets = data["data"]
                if isinstance(datasets, list):
                    return datasets
                if isinstance(datasets, dict):
                    return datasets.get("datasets", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return []

    def get_or_create_dataset(
        self,
        name: str,
        description: str = "",
        chunk_method: str = "naive",
    ) -> Optional[Dict[str, Any]]:
        """Get existing dataset or create if it doesn't exist."""
        try:
            # Check if exists
            existing = self.list_datasets(name=name)
            if existing:
                logger.info(f"Using existing dataset: {name}")
                return existing[0]

            # Create new dataset
            logger.info(f"Creating new dataset: {name}")
            resp = self.session.post(
                self._url("/api/v1/datasets"),
                headers=self._headers(),
                json={
                    "name": name,
                    "description": description,
                    "chunk_method": chunk_method,
                },
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("data"):
                return data["data"]
            return None
        except Exception as e:
            logger.error(f"Failed to get/create dataset {name}: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────
    # Retrieval Operations
    # ─────────────────────────────────────────────────────────────────

    def retrieve_chunks(
        self,
        question: str,
        dataset_ids: List[str],
        top_k: int = 6,
        similarity_threshold: float = 0.4,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from datasets."""
        if not dataset_ids:
            dataset_ids = [self.default_dataset_id] if self.default_dataset_id else []

        if not dataset_ids:
            logger.warning("No dataset IDs available for retrieval")
            return []

        try:
            resp = self.session.post(
                self._url("/api/v1/retrieval"),
                headers=self._headers(),
                json={
                    "question": question,
                    "dataset_ids": dataset_ids,
                    "top_k": top_k,
                    "similarity_threshold": similarity_threshold,
                },
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Extract chunks from response
            chunks = []
            if data.get("data"):
                raw_chunks = data["data"]
                if isinstance(raw_chunks, dict):
                    chunks = raw_chunks.get("chunks", [])
                elif isinstance(raw_chunks, list):
                    chunks = raw_chunks
            
            # Nice print statement for developer logging/debugging
            print(f"\n=========================================")
            print(f"[RAGFLOW] RAGFLOW RETRIEVAL SUCCESSFUL")
            print(f"[QUERY] Question : '{question}'")
            print(f"[DATASETS] Datasets : {dataset_ids}")
            print(f"[COUNT] Count    : {len(chunks)} chunk(s) retrieved")
            print(f"=========================================")
            for i, c in enumerate(chunks):
                content = c.get("content") or c.get("text") or ""
                doc_name = c.get("document_name") or c.get("source") or "Unknown Document"
                score = c.get("similarity") or c.get("similarity_score") or c.get("score") or 0.0
                print(f"  [{i+1}] Doc: '{doc_name}' | Score: {score}")
                print(f"      Content: {content.strip()}")
                print(f"  -----------------------------------------")
            print(f"=========================================\n")

            return chunks
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────
    # Content Retrieval for Lesson Planning
    # ─────────────────────────────────────────────────────────────────

    def _retrieve_lesson_content_sync(
        self,
        class_name: str,
        subject: str,
        topic: str,
        language: Optional[str] = None,
        board: Optional[str] = None,
        limit: int = 4,
    ) -> tuple[List[TextbookContent], Dict[str, Any]]:
        """
        Retrieve lesson content from RAGFlow and normalize to TextbookContent.
        Synchronous implementation using requests.
        
        Returns:
            Tuple of (TextbookContent chunks, metadata dict)
        """
        try:
            # Determine dataset to use
            dataset_id = self.default_dataset_id
            dataset_name = self.default_dataset

            if not dataset_id:
                logger.warning("No RAGFlow dataset configured, cannot retrieve content")
                return [], {"error": "no_dataset_configured"}

            # Build question for retrieval
            clean_class = class_name.replace("_", " ")
            question = f"{clean_class} {subject} {topic}"
            logger.info(f"Retrieving RAGFlow content: {question}")

            # Retrieve chunks
            chunks = self.retrieve_chunks(
                question=question,
                dataset_ids=[dataset_id],
                top_k=limit,
                similarity_threshold=0.4,
            )

            # Normalize to TextbookContent
            textbook_content = []
            for idx, chunk in enumerate(chunks):
                if isinstance(chunk, dict):
                    content = chunk.get("content") or chunk.get("text") or ""
                    source = chunk.get("document_name") or chunk.get("source") or f"RAGFlow_{idx}"
                    score = chunk.get("similarity") or chunk.get("similarity_score") or chunk.get("score")
                    
                    if content:
                        textbook_content.append(
                            TextbookContent(
                                content=content,
                                source=f"{class_name}|{subject}|{source}",
                                similarity_score=score,
                            )
                        )

            # Return empty list if no chunks retrieved to enforce RAGFlow focus
            if not textbook_content:
                logger.warning(f"No chunks retrieved from RAGFlow for: {question}")

            metadata = {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "chunks_retrieved": len(chunks),
                "question": question,
            }

            logger.info(
                f"Retrieved {len(chunks)} chunks from RAGFlow",
                extra={"class": class_name, "subject": subject, "topic": topic},
            )

            return textbook_content, metadata

        except Exception as e:
            logger.error(f"Error retrieving lesson content from RAGFlow: {e}", exc_info=True)
            return [], {"error": str(e)}

    async def retrieve_textbook_content(
        self,
        class_name: str,
        subject: str,
        topic: str,
        language: Optional[str] = None,
        board: Optional[str] = None,
        limit: int = 4,
    ) -> tuple[List[TextbookContent], Dict[str, Any]]:
        """
        Async wrapper for lesson content retrieval.
        Runs the synchronous implementation in a thread pool to avoid blocking.
        """
        return await asyncio.to_thread(
            self._retrieve_lesson_content_sync,
            class_name,
            subject,
            topic,
            language,
            board,
            limit,
        )

    # ─────────────────────────────────────────────────────────────────
    # Chat Session Management (for future use)
    # ─────────────────────────────────────────────────────────────────

    def _resolve_chat_id(self, chat_id: str = "") -> str:
        """Resolve chat ID, falling back to default configuration if needed."""
        cid = (chat_id or self.default_chat_id or "").strip()
        if not cid:
            raise ValueError("No RAGFlow chat_id configured or provided")
        return cid

    def create_chat_session(
        self,
        name: str = "Default Session",
        dataset_ids: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a chat session in RAGFlow."""
        if not dataset_ids:
            dataset_ids = [self.default_dataset_id] if self.default_dataset_id else []

        try:
            resp = self.session.post(
                self._url("/api/v1/chats"),
                headers=self._headers(),
                json={
                    "name": name,
                    "dataset_ids": dataset_ids,
                },
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("data"):
                return data["data"]
            return None
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return None

    def list_sessions(self, chat_id: str = "") -> List[Dict[str, Any]]:
        """List all sessions for a chat assistant."""
        try:
            cid = self._resolve_chat_id(chat_id)
            resp = self.session.get(
                self._url(f"/api/v1/chats/{cid}/sessions"),
                headers=self._headers(),
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("sessions", data.get("list", [])) or []
            return []
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def delete_session(self, chat_id: str, session_id: str) -> Dict[str, Any]:
        """Delete a chat session by ID."""
        try:
            cid = self._resolve_chat_id(chat_id)
            resp = self.session.delete(
                self._url(f"/api/v1/chats/{cid}/sessions"),
                headers=self._headers(),
                json={"ids": [session_id]},
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_chat_session(self, chat_id: str, session_id: str) -> Dict[str, Any]:
        """Retrieve details of a specific chat session."""
        try:
            cid = self._resolve_chat_id(chat_id)
            resp = self.session.get(
                self._url(f"/api/v1/chats/{cid}/sessions/{session_id}"),
                headers=self._headers(),
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get chat session: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────
    # Document Operations
    # ─────────────────────────────────────────────────────────────────

    def list_documents(
        self, dataset_id: str, page: int = 1, page_size: int = 30
    ) -> List[Dict[str, Any]]:
        """List documents inside a dataset."""
        try:
            resp = self.session.get(
                self._url(f"/api/v1/datasets/{dataset_id}/documents"),
                headers=self._headers(),
                params={"page": page, "page_size": page_size},
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if isinstance(data, dict):
                return data.get("docs", data.get("documents", [])) or []
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"Failed to list documents for dataset {dataset_id}: {e}")
            return []

    def upload_document(self, dataset_id: str, file_path: str) -> Dict[str, Any]:
        """Upload a local document file to a dataset."""
        try:
            from pathlib import Path
            file_name = Path(file_path).name
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            with open(file_path, "rb") as f:
                resp = self.session.post(
                    self._url(f"/api/v1/datasets/{dataset_id}/documents"),
                    headers=headers,
                    files={"file": (file_name, f, "application/pdf")},
                    timeout=self.timeout_sec,
                )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to upload document {file_path} to dataset {dataset_id}: {e}")
            return {"success": False, "error": str(e)}

    def parse_documents(self, dataset_id: str, document_ids: List[str]) -> Dict[str, Any]:
        """Trigger document chunking/parsing."""
        try:
            resp = self.session.post(
                self._url(f"/api/v1/datasets/{dataset_id}/chunks"),
                headers=self._headers(),
                json={"document_ids": document_ids},
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to parse documents {document_ids}: {e}")
            return {"success": False, "error": str(e)}

    def delete_documents(self, dataset_id: str, document_ids: List[str]) -> Dict[str, Any]:
        """Delete documents from a dataset."""
        try:
            resp = self.session.delete(
                self._url(f"/api/v1/datasets/{dataset_id}/documents"),
                headers=self._headers(),
                json={"ids": document_ids},
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to delete documents {document_ids}: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────
    # Chat Completion & Streaming
    # ─────────────────────────────────────────────────────────────────

    def chat_completion(
        self, question: str, chat_id: str = "", session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a question to RAGFlow's chat completion assistant."""
        try:
            cid = self._resolve_chat_id(chat_id)
            payload = {
                "model": "model",
                "messages": [{"role": "user", "content": question}],
                "stream": False,
                "extra_body": {
                    "reference": True,
                    "reference_metadata": {
                        "include": True
                    }
                }
            }
            if session_id:
                payload["session_id"] = session_id

            resp = self.session.post(
                self._url(f"/api/v1/openai/{cid}/chat/completions"),
                headers=self._headers(),
                json=payload,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            return {"success": False, "error": str(e)}

    def chat_completion_stream(
        self,
        question: str,
        chat_id: str = "",
        session_id: Optional[str] = None,
        **kwargs,
    ) -> Generator[str, None, None]:
        """Get a streaming chat completion response from RAGFlow."""
        try:
            cid = self._resolve_chat_id(chat_id)
            payload = {
                "model": "model",
                "messages": [{"role": "user", "content": question}],
                "stream": True,
                "extra_body": {
                    "reference": True,
                    "reference_metadata": {
                        "include": True
                    }
                }
            }
            if session_id:
                payload["session_id"] = session_id
            if "dataset_ids" in kwargs and kwargs["dataset_ids"]:
                payload["dataset_ids"] = kwargs["dataset_ids"]

            resp = self.session.post(
                self._url(f"/api/v1/openai/{cid}/chat/completions"),
                headers=self._headers(),
                json=payload,
                stream=True,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()

            references = []
            for chunk in resp.iter_lines():
                if not chunk:
                    continue
                
                chunk_str = chunk.decode("utf-8")
                if not chunk_str.startswith("data:"):
                    continue
                
                data_str = chunk_str[5:].strip()
                if data_str == "[DONE]":
                    break
                
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta") or {}
                    ref = delta.get("reference") or []
                    if ref:
                        references = ref
                    yield f"data: {data_str}\n\n"
                except json.JSONDecodeError:
                    continue
            
            yield f'event: metadata\ndata: {json.dumps({"references": references})}\n\n'
        except Exception as e:
            logger.error(f"Error in chat_completion_stream: {e}")
            yield f'event: error\ndata: {json.dumps({"error": str(e)})}\n\n'

    def chat_completion_stream_stateless(
        self, messages: List[Dict[str, Any]], chat_id: str
    ) -> Generator[str, None, None]:
        """Stateless streaming completion where history is supplied by caller."""
        try:
            cid = self._resolve_chat_id(chat_id)
            payload = {"model": "model", "messages": messages, "stream": True}
            resp = self.session.post(
                self._url(f"/api/v1/openai/{cid}/chat/completions"),
                headers=self._headers(),
                json=payload,
                stream=True,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    yield line.decode("utf-8")
        except Exception as e:
            logger.error(f"Error in stateless stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}"

    def chat_completion_stream_stateful(
        self, question: str, session_id: str, chat_id: str
    ) -> Generator[str, None, None]:
        """Stateful streaming completion tracked by session_id in RAGFlow."""
        try:
            cid = self._resolve_chat_id(chat_id)
            payload = {
                "question": question,
                "session_id": session_id,
                "stream": True
            }
            resp = self.session.post(
                self._url(f"/api/v1/chats/{cid}/completions"),
                headers=self._headers(),
                json=payload,
                stream=True,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    yield line.decode("utf-8")
        except Exception as e:
            logger.error(f"Error in stateful stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}"

    # ─────────────────────────────────────────────────────────────────
    # Raw Chunks Retrieval for Tools (e.g. content_explainer)
    # ─────────────────────────────────────────────────────────────────

    def retrieve_raw_chunks(
        self,
        question: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks from RAGFlow and normalize them for easy consumption by tools.
        """
        dataset_id = self.default_dataset_id
        if not dataset_id:
            logger.warning("No RAGFlow dataset configured for raw chunks retrieval")
            return []

        chunks = self.retrieve_chunks(
            question=question,
            dataset_ids=[dataset_id],
            top_k=limit,
            similarity_threshold=0.4,
        )

        normalized = []
        for idx, chunk in enumerate(chunks):
            if isinstance(chunk, dict):
                content = chunk.get("content") or chunk.get("text") or ""
                source = chunk.get("document_name") or chunk.get("source") or f"RAGFlow_{idx}"
                score = chunk.get("similarity") or chunk.get("similarity_score") or chunk.get("score") or 0.0
                if content:
                    normalized.append({
                        "content": content,
                        "source": str(source),
                        "similarity": score,
                    })
        return normalized

    def create_new_session(self, chat_id: str = "", name: str = "Default Session") -> Optional[str]:
        """Create a new session under a specific chat assistant."""
        try:
            cid = self._resolve_chat_id(chat_id)
            resp = self.session.post(
                self._url(f"/api/v1/chats/{cid}/sessions"),
                headers=self._headers(),
                json={"name": name},
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("data") and isinstance(data["data"], dict):
                return data["data"].get("id")
            return None
        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            return None

    def chat_completion_stateful(
        self, question: str, chat_id: str = "", session_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a question to RAGFlow's stateful chat completions endpoint."""
        try:
            cid = self._resolve_chat_id(chat_id)
            payload = {
                "question": question,
                "stream": False
            }
            if session_id:
                payload["session_id"] = session_id
            if filters:
                payload["filters"] = filters
                
            resp = self.session.post(
                self._url(f"/api/v1/chats/{cid}/completions"),
                headers=self._headers(),
                json=payload,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Stateful chat completion error: {e}")
            return {"code": -1, "message": str(e), "success": False, "error": str(e)}

    async def retrieve_raw_chunks_async(
        self,
        question: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Async wrapper for retrieve_raw_chunks."""
        return await asyncio.to_thread(
            self.retrieve_raw_chunks,
            question,
            limit,
        )

    def close(self) -> None:
        """Close the session."""
        self.session.close()


# Global instance
ragflow_service = RAGFlowClientV2()
