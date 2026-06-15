"""
ragflow_client.py — RAGFlow /api/v1/* wrapper for the project

Provides low-level HTTP client functions for interacting with RAGFlow's REST API.
Handles authentication, request/response parsing, and error handling.
"""
# NOTE : Almost every function has been implemented but not in use (some of em) by ragflow_routes.
import os
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional
import json

import requests
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=False)

# Configuration
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost:80").rstrip("/")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "").strip()
RAGFLOW_CHAT_ID = os.getenv("RAGFLOW_CHAT_ID", "").strip()
RAGFLOW_TIMEOUT_SEC = int(os.getenv("RAGFLOW_TIMEOUT_SEC", "30"))

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def _auth_headers(json_content: bool = True) -> Dict[str, str]:
    """Generate authorization headers for RAGFlow API requests."""
    if not RAGFLOW_API_KEY:
        raise ValueError("RAGFLOW_API_KEY is not set")

    headers = {"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
    if json_content:
        headers["Content-Type"] = "application/json"
    return headers


def _url(path: str) -> str:
    """Construct full URL from RAGFlow base URL and path."""
    return f"{RAGFLOW_BASE_URL}{path}"


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute GET request to RAGFlow API."""
    resp = requests.get(
        _url(path),
        headers=_auth_headers(json_content=True),
        params=params,
        timeout=RAGFLOW_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    return resp.json()


def _post(
    path: str,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    stream: bool = False,
    timeout: Optional[int] = None,
):
    """Execute POST request to RAGFlow API."""
    headers = _auth_headers(json_content=(json is not None and files is None))
    resp = requests.post(
        _url(path),
        headers=headers,
        json=json,
        files=files,
        timeout=timeout or RAGFLOW_TIMEOUT_SEC,
        stream=stream,
    )
    resp.raise_for_status()
    return resp


def _delete(path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute DELETE request to RAGFlow API."""
    resp = requests.delete(
        _url(path),
        headers=_auth_headers(json_content=True),
        json=json,
        timeout=RAGFLOW_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    return resp.json()

# ─────────────────────────────────────────────────────────────────────────────
# Chat Assistant Management Core Functions
# ─────────────────────────────────────────────────────────────────────────────

def _get_headers() -> Dict[str, str]:
    """Alias for _auth_headers — used by chat assistant management functions."""
    return _auth_headers(json_content=True)

def create_chat_assistant(name: str, dataset_ids: List[str], **kwargs) -> Dict[str, Any]:
    """Create a new RAGFlow chat assistant."""
    payload = {"name": name, "dataset_ids": dataset_ids, **kwargs}
    return _post("/api/v1/chats", json=payload)

def get_chat_assistant(chat_id: str) -> Dict[str, Any]:
    """Retrieve details for a specific chat assistant."""
    return _get(f"/api/v1/chats/{chat_id}")

def update_chat_assistant(chat_id: str, name: str, dataset_ids: List[str], **kwargs) -> Dict[str, Any]:
    """Full update (PUT) of a chat assistant's configuration."""
    payload = {"name": name, "dataset_ids": dataset_ids, **kwargs}
    return _put(f"/api/v1/chats/{chat_id}", json=payload)

def patch_chat_assistant(chat_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Partial update (PATCH) of a chat assistant's configuration."""
    return _patch(f"/api/v1/chats/{chat_id}", json=payload)

def delete_chat_assistant(chat_id: str) -> Dict[str, Any]:
    """Delete a single chat assistant."""
    return _delete(f"/api/v1/chats/{chat_id}")

def list_chat_assistants(page: int = 1, page_size: int = 30, **kwargs) -> Dict[str, Any]:
    """List chat assistants with pagination filters."""
    params = {"page": page, "page_size": page_size, **kwargs}
    return _get("/api/v1/chats", params=params)

# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────


def health_check() -> bool:
    """Check if RAGFlow API is healthy."""
    try:
        resp = requests.get(_url("/api/v1/system/healthz"), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("status") == "ok"
    except Exception:
        return False


def health_detail() -> Dict[str, Any]:
    """Get detailed health information from RAGFlow API."""
    resp = requests.get(_url("/api/v1/system/healthz"), timeout=5)
    resp.raise_for_status()
    return resp.json()


# ─────────────────────────────────────────────────────────────────────────────
# Dataset Operations
# ─────────────────────────────────────────────────────────────────────────────


def list_datasets(name: str = "", page: int = 1, page_size: int = 30) -> List[Dict[str, Any]]:
    """List all datasets, optionally filtered by name."""
    params: Dict[str, Any] = {"page": page, "page_size": page_size}
    if name:
        params["name"] = name

    data = _get("/api/v1/datasets", params=params).get("data", {})
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("datasets", data.get("list", [])) or []
    return []


def create_dataset(
    name: str, description: str = "", chunk_method: str = "naive"
) -> Dict[str, Any]:
    """Create a new dataset in RAGFlow."""
    resp = _post(
        "/api/v1/datasets",
        json={
            "name": name,
            "description": description,
            "chunk_method": chunk_method,
        },
    ).json()
    return resp


def get_or_create_dataset(
    name: str, description: str = "", chunk_method: str = "naive"
) -> Dict[str, Any]:
    """Get existing dataset or create if it doesn't exist."""
    existing = list_datasets(name=name)
    if existing:
        return existing[0]

    created = create_dataset(name, description, chunk_method)
    return created.get("data", created)


def delete_dataset(dataset_id: str) -> Dict[str, Any]:
    """Delete a dataset by ID."""
    return _delete("/api/v1/datasets", json={"ids": [dataset_id]})


# ─────────────────────────────────────────────────────────────────────────────
# Document Operations
# ─────────────────────────────────────────────────────────────────────────────


def list_documents(
    dataset_id: str, page: int = 1, page_size: int = 30
) -> List[Dict[str, Any]]:
    """List documents in a dataset."""
    data = _get(
        f"/api/v1/datasets/{dataset_id}/documents",
        params={"page": page, "page_size": page_size},
    ).get("data", {})

    if isinstance(data, dict):
        return data.get("docs", data.get("documents", [])) or []
    if isinstance(data, list):
        return data
    return []


def upload_document(dataset_id: str, file_path: str) -> Dict[str, Any]:
    """Upload a document file to a dataset."""
    file_name = Path(file_path).name
    with open(file_path, "rb") as f:
        resp = _post(
            f"/api/v1/datasets/{dataset_id}/documents",
            files={"file": (file_name, f, "application/pdf")},
            timeout=60,
        )
    return resp.json()


def parse_documents(dataset_id: str, document_ids: List[str]) -> Dict[str, Any]:
    """Trigger chunking/parsing of documents in a dataset."""
    return _post(
        f"/api/v1/datasets/{dataset_id}/chunks",
        json={"document_ids": document_ids},
    ).json()


def delete_documents(dataset_id: str, document_ids: List[str]) -> Dict[str, Any]:
    """Delete documents from a dataset."""
    return _delete(
        f"/api/v1/datasets/{dataset_id}/documents",
        json={"ids": document_ids},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval Operations
# ─────────────────────────────────────────────────────────────────────────────


def retrieve_chunks(
    question: str,
    dataset_ids: List[str],
    top_k: int = 6,
    similarity_threshold: float = 0.2,
) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks from datasets based on a question."""
    resp = _post(
        "/api/v1/retrieval",
        json={
            "question": question,
            "dataset_ids": dataset_ids,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
        },
    ).json()

    data = resp.get("data", {})
    if isinstance(data, dict):
        return data.get("chunks", [])
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Chat & Completion Operations
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_chat_id(chat_id: str = "") -> str:
    """Resolve chat ID, falling back to environment default if needed."""
    cid = (chat_id or RAGFLOW_CHAT_ID).strip()
    if not cid:
        raise ValueError("No RAGFLOW_CHAT_ID configured")
    return cid


def chat_completion(
    question: str, chat_id: str = "", session_id: Optional[str] = None
) -> Dict[str, Any]:
    cid = _resolve_chat_id(chat_id)

    payload:Dict[str,Any] = {
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

    return _post(
        f"/api/v1/openai/{cid}/chat/completions",
        json=payload,
        timeout=90,
    ).json()


def chat_completion_stream(
    question: str,
    chat_id: str = "",
    session_id: Optional[str] = None,
    **kwargs,  
) -> Generator[str, None, None]:
    """Get a chat completion response with streaming."""
    cid = _resolve_chat_id(chat_id)

    payload: Dict[str, Any] = {
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

    resp = _post(
        f"/api/v1/openai/{cid}/chat/completions",
        json=payload,
        stream=True,
        timeout=120,
    )
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

def chat_completion_stream_stateless(messages: List[Dict[str, Any]], chat_id: str) -> Generator[str, None, None]:
    """Stateless streaming: caller passes the full message history array."""
    cid = (chat_id or RAGFLOW_CHAT_ID).strip()
    url = f"{RAGFLOW_BASE_URL}/api/v1/openai/{cid}/chat/completions"
    payload = {"model": "model", "messages": messages, "stream": True}
    resp = requests.post(url, json=payload, headers=_auth_headers(), stream=True, timeout=120)
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            yield line.decode("utf-8")

def chat_completion_stream_stateful(
    question: str,
    session_id: str,
    chat_id: str
) -> Generator[str, None, None]:
    """Stateful streaming: RAGFlow tracks history server-side via session_id."""
    cid = (chat_id or RAGFLOW_CHAT_ID).strip()
    url = f"{RAGFLOW_BASE_URL}/api/v1/chats/{cid}/completions"
    payload = {
        "question": question,
        "session_id": session_id,
        "stream": True
    }
    resp = requests.post(
        url,
        json=payload,
        headers=_auth_headers(),
        stream=True,
        timeout=120
    )
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            yield line.decode("utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# Session Operations
# ─────────────────────────────────────────────────────────────────────────────


def create_session(chat_id: str = "", name: str = "Guru-Sikshan Session") -> Dict[str, Any]:
    """Create a new chat session."""
    cid = _resolve_chat_id(chat_id)
    print("[ragflow_client] session url:", _url(f"/api/v1/chats/{cid}/sessions"))
    print("[ragflow_client] chat id:", cid)
    cid = _resolve_chat_id(chat_id)
    return _post(
        f"/api/v1/chats/{cid}/sessions",
        json={"name": name},
    ).json()


def list_sessions(chat_id: str = "") -> List[Dict[str, Any]]:
    """List all sessions for a chat."""
    cid = _resolve_chat_id(chat_id)
    data = _get(f"/api/v1/chats/{cid}/sessions").get("data", {})
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("sessions", data.get("list", [])) or []
    return []


def delete_session(chat_id: str, session_id: str) -> Dict[str, Any]:
    """Delete a session."""
    cid = _resolve_chat_id(chat_id)
    return _delete(
        f"/api/v1/chats/{cid}/sessions",
        json={"ids": [session_id]},
    )

def get_chat_session(chat_id: str, session_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific chat session's history and messages.
    """
    return _get(f"/api/v1/chats/{chat_id}/sessions/{session_id}")

