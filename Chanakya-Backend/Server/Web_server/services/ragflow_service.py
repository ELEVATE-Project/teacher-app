"""
RAGFlow integration service.
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
import structlog

from config import settings
from module.models.schemas import TextbookContent

logger = structlog.get_logger(__name__)


class RAGFlowService:
    """Client wrapper for the RAGFlow public API."""

    def __init__(self) -> None:
        self.base_url = settings.RAGFLOW_BASE_URL.rstrip("/")
        self.client_id = settings.RAGFLOW_CLIENT_ID
        self.client_secret = settings.RAGFLOW_CLIENT_SECRET
        self.grant_type = settings.RAGFLOW_GRANT_TYPE
        self.default_scope = settings.RAGFLOW_DEFAULT_SCOPE
        self.dataset_id = settings.RAGFLOW_DATASET_ID or None
        self.dataset_name = settings.RAGFLOW_DATASET_NAME or self.default_scope
        self.timeout = httpx.Timeout(settings.RAGFLOW_TIMEOUT_SECONDS)
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def is_configured(self) -> bool:
        return bool(self.base_url and self.client_id and self.client_secret)

    async def health(self) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get("/api/public/chat/health")
        response.raise_for_status()
        return response.json()

    async def get_access_token(self, force_refresh: bool = False) -> str:
        if not self.is_configured():
            raise RuntimeError("RAGFlow client credentials are not configured")

        if not force_refresh and self._token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._token

        client = await self._get_client()
        response = await client.post(
            "/api/public/auth/token",
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": self.grant_type,
            },
        )
        response.raise_for_status()
        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError("RAGFlow token response did not contain access_token")

        expires_in = int(payload.get("expires_in", settings.RAGFLOW_TOKEN_TTL_SECONDS))
        self._token = access_token
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=max(30, expires_in - 30))
        return access_token

    async def create_session(self, external_user_id: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        token = await self.get_access_token()
        client = await self._get_client()
        response = await client.post(
            "/api/public/chat/session",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "externalUserId": external_user_id,
                "context": context or {},
            },
        )
        response.raise_for_status()
        return response.json()

    async def send_message(
        self,
        session_id: str,
        message: str,
        scope: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        token = await self.get_access_token()
        client = await self._get_client()
        response = await client.post(
            "/api/public/chat/message",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "sessionId": session_id,
                "message": message,
                "scope": scope or [self.default_scope],
            },
        )
        response.raise_for_status()
        return response.json()

    async def stream_message(
        self,
        session_id: str,
        message: str,
        scope: Optional[list[str]] = None,
    ):
        token = await self.get_access_token()
        client = await self._get_client()

        async with client.stream(
            "POST",
            "/api/public/chat/message/stream",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "sessionId": session_id,
                "message": message,
                "scope": scope or [self.default_scope],
            },
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                if chunk:
                    yield chunk

    async def retrieve_textbook_content(
        self,
        class_name: str,
        subject: str,
        topic: str,
        language: Optional[str] = None,
        board: Optional[str] = None,
        limit: int = 4,
    ) -> tuple[list[TextbookContent], dict[str, Any]]:
        """Retrieve lesson context from RAGFlow and normalize it into TextbookContent chunks."""
        context = {
            "role": "teacher",
            "class_name": class_name,
            "subject": subject,
            "topic": topic,
            "language": language,
            "board": board,
            "moduleScopes": [self.default_scope],
        }
        session = await self.create_session(external_user_id=f"lesson_{int(time.time())}", context=context)
        session_id = session.get("sessionId") or session.get("session_id")
        if not session_id:
            raise RuntimeError("RAGFlow session response did not contain a session id")

        prompt = (
            f"Retrieve concise textbook context for class {class_name}, subject {subject}, topic {topic}. "
            f"Return the most relevant factual content and source references for lesson planning."
        )
        if language:
            prompt += f" Use {language}."
        if board:
            prompt += f" Follow the {board} board context."

        response = await self.send_message(session_id=session_id, message=prompt, scope=[self.default_scope])
        chunks: list[TextbookContent] = []

        sources = response.get("sources") or []
        if isinstance(sources, list):
            for index, source in enumerate(sources[:limit]):
                content = ""
                source_name = f"RAGFlow|{self.dataset_name}|{index + 1}"
                if isinstance(source, dict):
                    content = source.get("content") or source.get("text") or source.get("chunk") or ""
                    source_name = source.get("document_name") or source.get("source") or source_name
                if content:
                    chunks.append(TextbookContent(content=content, source=str(source_name), similarity_score=None))

        if not chunks:
            answer = response.get("answer") or response.get("response") or ""
            if answer:
                parts = [part.strip() for part in answer.split("\n\n") if part.strip()]
                for index, part in enumerate(parts[:limit]):
                    chunks.append(
                        TextbookContent(
                            content=part,
                            source=f"RAGFlow|{self.dataset_name}|answer_{index + 1}",
                            similarity_score=None,
                        )
                    )

        if not chunks:
            chunks.append(
                TextbookContent(
                    content=prompt,
                    source=f"RAGFlow|{self.dataset_name}|fallback",
                    similarity_score=None,
                )
            )

        return chunks, {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "ragflow_session_id": session_id,
            "meta": response.get("meta"),
            "answer": response.get("answer"),
        }


ragflow_service = RAGFlowService()