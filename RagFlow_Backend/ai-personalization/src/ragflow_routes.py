"""
ragflow_routes.py — Flask Blueprint: /api/ragflow/*

Flask routes for RAGFlow integration.
"""
# TODO : Make it available for multiple different datasets. Currently only made it for one dataset and it routes to env

import json
import os
import tempfile
import traceback
import time
import bcrypt
from typing import Any, Dict, List
from functools import wraps

import google.generativeai as genai
from flask import Blueprint, Response, jsonify, request, stream_with_context, g
import jwt


import ragflow_client as rf
from resource_registry import get_resources_for_cluster, get_exemplary_resources
from supabase_client import db


# Initialize Gemini API if key is available
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# Blueprint configuration
ragflow_bp = Blueprint("ragflow", __name__, url_prefix="/api/ragflow")
DEFAULT_DATASET_NAME = os.getenv("RAGFLOW_DEFAULT_DATASET", "gurusikshan-ncert")
DEFAULT_CHAT_ID = os.getenv("RAGFLOW_CHAT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET")  # NOTE : both backend api and RAGFLOW service need same key , hence global env


# ─────────────────────────────────────────────────────────────────────────────
# API Client Authentication for Backend to RAGFlow chat sessions
# ─────────────────────────────────────────────────────────────────────────────



@ragflow_bp.route("/auth/client-token", methods=["POST"])
def client_token():
    """
    Exchange client_id + client_secret for short-lived JWT token.
    
    Used ONLY by backend Node.js to authenticate with RAGFlow for chat operations.
    Frontend users NEVER see client_secret — they use JWT from login.
    
    Request body:
    {
      "client_id": "gsc_abc123...",
      "client_secret": "xyz789..."
    }
    
    Response:
    {
      "success": true,
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires_in": 900  // 15 minutes
    }
    """
    try:
        data = request.json or {}
        client_id = (data.get("client_id") or "").strip()
        client_secret = (data.get("client_secret") or "").strip()
        
        if not client_id or not client_secret:
            return jsonify(success=False, error="client_id and client_secret required"), 400
        
        result = db.client.table("api_clients")\
            .select("client_secret_hash, is_active, allowed_scopes, name")\
            .eq("client_id", client_id)\
            .single()\
            .execute()
        
        if not result.data:
            return jsonify(success=False, error="Invalid client_id"), 401
        
        client = result.data[0] if isinstance(result.data, list) else result.data
        
        if not client.get("is_active"):
            return jsonify(success=False, error="Client is disabled"), 403
        
        stored_hash = client["client_secret_hash"]
        if not bcrypt.checkpw(client_secret.encode(), stored_hash.encode()):
            return jsonify(success=False, error="Invalid client_secret"), 401
        
        # Check scopes (ensure client has chat permissions)
        scopes = client.get("allowed_scopes", [])
        required_scopes = ["chat:session:create", "chat:message:send"]
        has_required_scopes = any(scope in scopes for scope in required_scopes)
        
        if not has_required_scopes:
            return jsonify(success=False, error="Insufficient scopes for chat operations"), 403

        payload = {
            "sub": client_id,        
            "client_id": client_id,
            "name": client.get("name", "API Client"),
            "scopes": scopes,
            "role": "admin",                   
            "aud": "authenticated",            
            "iss": "guru-sikshan-ai-service",
            "iat": int(time.time()),
            "exp": int(time.time()) + 900,     # 15 minutes wrapper
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        return jsonify(
            success=True,
            token=token,
            expires_in=900,
            token_type="Bearer"
        )
    
    except Exception as e:
        traceback.print_exc()
        return jsonify(success=False, error=str(e)), 500

# ─────────────────────────────────────────────────────────────────────────────
# JWT Authentication Middleware
# ─────────────────────────────────────────────────────────────────────────────



def require_jwt(auth_required: bool = True) -> callable:
    """
    Decorator to require JWT authentication.
    
    Args:
        auth_required: If False, token is optional (attached if present)
    
    Usage:
        @ragflow_bp.route('/private', methods=['GET'])
        @require_jwt(auth_required=True)
        def private_route():
            # g.user contains decoded JWT payload
            return jsonify(success=True, user=g.user)
    """
    def decorator(f: callable) -> callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            
            if not auth_header.startswith("Bearer "):
                if auth_required:
                    return jsonify(error="Missing or invalid authorization token"), 401
                
                # Token not required ig
                g.user = None
                return f(*args, **kwargs)
            
            token = auth_header.split(" ")[1]
            
            try:
                # skip audience verification , not needed
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
                g.user = payload
            except jwt.ExpiredSignatureError:
                if auth_required:
                    return jsonify(error="Token expired"), 401
                g.user = None
            except jwt.InvalidTokenError as e:
                if auth_required:
                    return jsonify(error=f"Invalid token: {str(e)}"), 401
                g.user = None
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin_or_higher() -> callable:
    """
    Decorator to require admin or super_admin role.
    Must be used after @require_jwt.
    
    Usage:
        @ragflow_bp.route('/admin-only', methods=['POST'])
        @require_jwt(auth_required=True)
        @require_admin_or_higher()
        def admin_route():
            # g.user.role is guaranteed to be 'admin' or 'super_admin'
            return jsonify(success=True)
    """
    def decorator(f: callable) -> callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'user', None)
            
            if not user:
                return jsonify(error="Authentication required"), 401
            
            role = user.get("role", "")
            if role not in ["admin", "super_admin"]:
                return jsonify(error="Admin access required"), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────



def _teacher_cluster(teacher_id: str) -> str:
    """Get teacher's cluster/region from database."""
    try:
        result = (
            db.client.table("teachers")
            .select("cluster")
            .eq("id", teacher_id)
            .single()
            .execute()
        )
        return (result.data or {}).get("cluster", "") or ""
    except Exception:
        return ""



def _preferred_resource_context(teacher_id: str = "") -> str:
    """Build context string with teacher's preferred resources."""
    if not teacher_id:
        return ""


    cluster = _teacher_cluster(teacher_id)
    if not cluster:
        return ""


    resources = get_resources_for_cluster(cluster)
    if not resources:
        return ""


    preferred = ", ".join(r.get("name", "") for r in resources[:3] if r.get("name"))
    if not preferred:
        return ""


    return f"[Teacher from {cluster}. Prefer resources from: {preferred}]"



def _augment_question(question: str, teacher_id: str = "") -> str:
    """Augment question with teacher's context and preferences."""
    prefix = _preferred_resource_context(teacher_id)
    if not prefix:
        return question
    return f"{prefix}\n\n{question}"




def _resolve_dataset_id(dataset_id: str = "", dataset_name: str = "") -> str:
    """Resolve dataset ID from either explicit ID or name."""
    if dataset_id:
        return dataset_id


    name = (dataset_name or DEFAULT_DATASET_NAME).strip()
    if not name:
        raise ValueError("dataset_name or dataset_id required")


    dataset = rf.get_or_create_dataset(
        name=name,
        description=f"Guru-Sikshan dataset for {name}",
        chunk_method="naive",
    )
    resolved_id = dataset.get("id", "") or dataset.get("dataset_id", "") or ""
    if not resolved_id:
        raise ValueError(f"Unable to resolve dataset id for {name}")
    return resolved_id



def _extract_document_ids(payload: Any) -> List[str]:
    """Extract document IDs from various response formats."""
    if isinstance(payload, list):
        ids: List[str] = []
        for item in payload:
            if isinstance(item, dict):
                value = item.get("id") or item.get("document_id") or item.get("doc_id")
                if value:
                    ids.append(str(value))
            elif isinstance(item, str):
                ids.append(item)
        return ids


    if isinstance(payload, dict):
        for key in ("ids", "document_ids"):
            value = payload.get(key)
            if isinstance(value, list):
                return [str(v) for v in value if v]


        for key in ("id", "document_id", "doc_id"):
            value = payload.get(key)
            if value:
                return [str(value)]


        for key in ("documents", "data", "docs"):
            value = payload.get(key)
            ids = _extract_document_ids(value)
            if ids:
                return ids


    return []



# ─────────────────────────────────────────────────────────────────────────────
# Health & Status , no auth needed for these
# ─────────────────────────────────────────────────────────────────────────────


#DONE
@ragflow_bp.route("/health", methods=["GET"])
def health():
    """Check RAGFlow service health status."""
    try:
        ok = rf.health_check()
        detail = {}
        if ok:
            try:
                detail = rf.health_detail()
            except Exception:
                detail = {}


        return jsonify(
            success=ok,
            ragflow_online=ok,
            api_key_set=bool(rf.RAGFLOW_API_KEY),
            chat_id_set=bool(DEFAULT_CHAT_ID),
            default_dataset_name=DEFAULT_DATASET_NAME,
            detail=detail,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify(
            success=False,
            ragflow_online=False,
            api_key_set=bool(rf.RAGFLOW_API_KEY),
            chat_id_set=bool(DEFAULT_CHAT_ID),
            default_dataset_name=DEFAULT_DATASET_NAME,
            error=str(e),
        ), 500



# ─────────────────────────────────────────────────────────────────────────────
# Dataset Management , auth needed
# ─────────────────────────────────────────────────────────────────────────────


#DONE
@ragflow_bp.route("/datasets", methods=["GET"])
@require_jwt(auth_required=True)
def list_datasets():
    """List all datasets."""
    try:
        name = request.args.get("name", "")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 30))
        datasets = rf.list_datasets(name=name, page=page, page_size=page_size)
        return jsonify(success=True, datasets=datasets, count=len(datasets))
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


#DONE
@ragflow_bp.route("/datasets", methods=["POST"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def create_dataset():
    """Create a new dataset."""
    try:
        data = request.json or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify(error="name required"), 400


        result = rf.create_dataset(
            name=name,
            description=data.get("description", ""),
            chunk_method=data.get("chunk_method", "naive"),
        )
        return jsonify(success=True, dataset=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


#DONE
@ragflow_bp.route("/datasets/<dataset_id>", methods=["DELETE"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def delete_dataset(dataset_id: str):
    """Delete a dataset."""
    try:
        result = rf.delete_dataset(dataset_id)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


#DONE
@ragflow_bp.route("/datasets/resolve", methods=["POST"])
@require_jwt(auth_required=True)
def resolve_dataset():
    """Resolve dataset ID from name or return explicit ID."""
    try:
        data = request.json or {}
        dataset_id = _resolve_dataset_id(
            dataset_id=(data.get("dataset_id") or "").strip(),
            dataset_name=(data.get("dataset_name") or DEFAULT_DATASET_NAME).strip(),
        )
        return jsonify(success=True, dataset_id=dataset_id)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500



# ─────────────────────────────────────────────────────────────────────────────
# Document Management , admin for write requests
# ─────────────────────────────────────────────────────────────────────────────


#DONE
@ragflow_bp.route("/datasets/<dataset_id>/documents", methods=["GET"])
@require_jwt(auth_required=True)
def list_documents(dataset_id: str):
    """List documents in a dataset."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 30))
        docs = rf.list_documents(dataset_id, page=page, page_size=page_size)
        return jsonify(success=True, documents=docs, count=len(docs))
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


#DONE
@ragflow_bp.route("/datasets/<dataset_id>/documents", methods=["POST"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def upload_document(dataset_id: str):
    """Upload a document to a dataset."""
    try:
        if "file" not in request.files:
            return jsonify(error="file required"), 400


        uploaded = request.files["file"]
        if not uploaded or not uploaded.filename:
            return jsonify(error="valid file required"), 400


        suffix = os.path.splitext(uploaded.filename)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name


        try:
            result = rf.upload_document(dataset_id, tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


        document_ids = _extract_document_ids(result)
        return jsonify(success=True, result=result, document_ids=document_ids)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


#DONE
@ragflow_bp.route("/datasets/<dataset_id>/chunks", methods=["POST"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def parse_documents(dataset_id: str):
    """Trigger chunking/parsing of documents."""
    try:
        data = request.json or {}
        ids = data.get("document_ids") or data.get("ids") or []
        if not ids:
            return jsonify(error="document_ids required"), 400


        result = rf.parse_documents(dataset_id, ids)
        return jsonify(success=True, result=result, parsed_ids=ids)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


#DONE
@ragflow_bp.route("/datasets/<dataset_id>/documents", methods=["DELETE"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def delete_documents(dataset_id: str):
    """Delete documents from a dataset."""
    try:
        data = request.json or {}
        ids = data.get("ids") or data.get("document_ids") or []
        ids = [str(i) for i in ids if i]


        if not ids:
            return jsonify(error="ids required"), 400


        result = rf.delete_documents(dataset_id, ids)
        return jsonify(success=True, result=result, deleted_ids=ids)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


# Main
# TODO : Update this function such that it atomic , either do it all or do none
@ragflow_bp.route("/documents/upload-and-parse", methods=["POST"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def upload_and_parse_document():
    """Upload and automatically parse a document."""
    try:
        dataset_id = (request.form.get("dataset_id") or "").strip()
        dataset_name = (request.form.get("dataset_name") or DEFAULT_DATASET_NAME).strip()
        resolved_dataset_id = _resolve_dataset_id(dataset_id=dataset_id, dataset_name=dataset_name)


        if "file" not in request.files:
            return jsonify(error="file required"), 400


        uploaded = request.files["file"]
        if not uploaded or not uploaded.filename:
            return jsonify(error="valid file required"), 400


        suffix = os.path.splitext(uploaded.filename)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name


        try:
            upload_result = rf.upload_document(resolved_dataset_id, tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


        document_ids = _extract_document_ids(upload_result)
        parse_result = None
        if document_ids:
            parse_result = rf.parse_documents(resolved_dataset_id, document_ids)


        return jsonify(
            success=True,
            dataset_id=resolved_dataset_id,
            dataset_name=dataset_name,
            upload_result=upload_result,
            document_ids=document_ids,
            parse_result=parse_result,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


# ─────────────────────────────────────────────────────────────────────────────
# Chat Assistant Management , same as before 
# ─────────────────────────────────────────────────────────────────────────────
# NOTE : These require dataset ID's for creation
@ragflow_bp.route("/chats", methods=["POST"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def create_chat():
    """Create a new chat assistant."""
    try:
        data = request.json or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify(error="name required"), 400
        
        data["dataset_ids"] = data.get("dataset_ids", [])
        
        result = rf.create_chat_assistant(**data) if hasattr(rf, 'create_chat_assistant') else data
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

#DONE
@ragflow_bp.route("/chats/<chat_id>", methods=["GET"])
@require_jwt(auth_required=True)
def get_chat(chat_id: str):
    """Retrieve a specific chat assistant configuration."""
    try:
        result = rf.get_chat_assistant(chat_id)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

#DONE
@ragflow_bp.route("/chats/<chat_id>", methods=["PUT"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def update_chat(chat_id: str):
    """Overwrite an existing chat assistant configuration completely."""
    try:
        data = request.json or {}
        if not data.get("name"):
            return jsonify(error="name required for full overwrite"), 400

        result = rf.update_chat_assistant(chat_id, **data)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

#DONE
@ragflow_bp.route("/chats/<chat_id>", methods=["PATCH"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def patch_chat(chat_id: str):
    """Partially update subset settings on a chat assistant."""
    try:
        data = request.json or {}
        result = rf.patch_chat_assistant(chat_id, data)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

#DONE
@ragflow_bp.route("/chats/<chat_id>", methods=["DELETE"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def delete_chat(chat_id: str):
    """Delete a single chat assistant by path parameter ID."""
    try:
        result = rf.delete_chat_assistant(chat_id)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

#DONE
@ragflow_bp.route("/chats", methods=["DELETE"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def delete_chats_bulk():
    """Bulk delete assistants using IDs array or delete_all flag from request body."""
    try:
        data = request.json or {}
        result = rf.delete_chat_assistants_bulk(data)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

#DONE
@ragflow_bp.route("/chats", methods=["GET"])
@require_jwt(auth_required=True)
def list_chats():
    """List chat assistants with optional pagination and filtering options."""
    try:
        # Extract filter parameters safely from args dict
        params = {k: v for k, v in request.args.items()}
        result = rf.list_chat_assistants(**params)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500
    
#DONE 
# NOTE : Works for all chat windows but the public chat sessions are stateless so they dont store shit
@ragflow_bp.route("/chats/<chat_id>/sessions/<session_id>", methods=["GET"])
@require_jwt(auth_required=True)
def get_session_history(chat_id: str, session_id: str):
    """Retrieve history and messages for a specific session."""
    try:
        result = rf.get_chat_session(chat_id, session_id)
        if result.get("code") == 0:
            return jsonify(success=True, data=result.get("data"))
        else:
            return jsonify(success=False, error=result.get("message", "Unknown error")), 400
            
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


# ─────────────────────────────────────────────────────────────────────────────
# Choices-Based Completion Streaming Endpoints (these work)
# ─────────────────────────────────────────────────────────────────────────────

@ragflow_bp.route("/query/completion/stateless", methods=["POST"])
@require_jwt(auth_required=True)
def completion_stateless():
    """OpenAI style stateless completion requiring a full history array."""
    try:
        data = request.json or {}
        messages = data.get("messages")
        chat_id = data.get("chat_id") or DEFAULT_CHAT_ID

        if not messages:
            return jsonify(error="messages array payload is required"), 400

        def event_stream():
            try:
                for chunk in rf.chat_completion_stream_stateless(messages=messages, chat_id=chat_id):
                    yield f"{chunk}\n\n"
            except Exception as stream_err:
                yield f"data: {json.dumps({'error': str(stream_err)})}\n\n"
                yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(event_stream()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

# NOTE : These work but they are still not stateful by defination , it just saves the data in a session
@ragflow_bp.route("/query/completion/stateful", methods=["POST"])
@require_jwt(auth_required=True)
def completion_stateful():
    """Native RAGFlow stateful completion using single question + session tracking UUID."""
    try:
        data = request.json or {}
        question = (data.get("question") or "").strip()
        session_id = data.get("session_id")
        chat_id = data.get("chat_id") or DEFAULT_CHAT_ID

        if not question or not session_id:
            return jsonify(error="question and session_id are both required"), 400

        final_question = _augment_question(question, data.get("teacher_id", ""))

        def event_stream():
            try:
                for chunk in rf.chat_completion_stream_stateful(question=final_question, session_id=session_id, chat_id=chat_id):
                    yield f"{chunk}\n\n"
            except Exception as stream_err:
                yield f"data: {json.dumps({'error': str(stream_err)})}\n\n"
                yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(event_stream()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

# ─────────────────────────────────────────────────────────────────────────────
# Query & Retrieval , DONE
# ─────────────────────────────────────────────────────────────────────────────


@ragflow_bp.route("/query/ask", methods=["POST"])
@require_jwt(auth_required=True)
def ask():
    """Ask a question with optional streaming response."""
    try:
        data = request.json or {}
        question = (data.get("question") or "").strip()
        if not question:
            return jsonify(error="question required"), 400


        teacher_id = data.get("teacher_id", "") or ""
        chat_id = data.get("chat_id", "") or DEFAULT_CHAT_ID
        session_id = data.get("session_id")
        stream = bool(data.get("stream", False))


        final_question = _augment_question(question, teacher_id)


        if stream:
            def event_stream():
                try:
                    for chunk in rf.chat_completion_stream(
                        final_question,
                        chat_id=chat_id,
                        session_id=session_id,
                    ):
                        yield f"data: {chunk}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    yield "data: [DONE]\n\n"


            return Response(
                stream_with_context(event_stream()),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive",
                },
            )


        result = rf.chat_completion(
            final_question,
            chat_id=chat_id,
            session_id=session_id,
        )
        return jsonify(success=True, result=result)


    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


#DONE , works
@ragflow_bp.route("/query/retrieve", methods=["POST"])
@require_jwt(auth_required=True)
def retrieve():
    """Retrieve relevant chunks for a question."""
    try:
        data = request.json or {}
        question = (data.get("question") or "").strip()
        if not question:
            return jsonify(error="question required"), 400


        dataset_ids = data.get("dataset_ids") or []
        dataset_name = (data.get("dataset_name") or "").strip()
        if not dataset_ids:
            dataset_ids = [_resolve_dataset_id(dataset_name=dataset_name or DEFAULT_DATASET_NAME)]


        top_k = int(data.get("top_k", 6))
        similarity_threshold = float(data.get("similarity_threshold", 0.2))


        chunks = rf.retrieve_chunks(
            question=question,
            dataset_ids=dataset_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
        return jsonify(success=True, dataset_ids=dataset_ids, chunks=chunks, count=len(chunks))
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


# Test route for all in one
@ragflow_bp.route("/query/ask-from-dataset", methods=["POST"])
@require_jwt(auth_required=True)
def ask_from_dataset():
    """Ask a question using documents from a dataset as context."""
    try:
        data = request.json or {}
        question = (data.get("question") or "").strip()
        if not question:
            return jsonify(error="question required"), 400


        dataset_ids = data.get("dataset_ids") or []
        dataset_name = (data.get("dataset_name") or "").strip()
        if not dataset_ids:
            dataset_ids = [_resolve_dataset_id(dataset_name=dataset_name or DEFAULT_DATASET_NAME)]


        top_k = int(data.get("top_k", 6))
        similarity_threshold = float(data.get("similarity_threshold", 0.2))
        teacher_id = data.get("teacher_id", "") or ""
        final_question = _augment_question(question, teacher_id)


        chunks = rf.retrieve_chunks(
            question=final_question,
            dataset_ids=dataset_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )


        context = "\n\n".join(
            c.get("content", "") for c in chunks[:top_k] if isinstance(c, dict) and c.get("content")
        )
        if not context:
            return jsonify(success=True, answer="", chunks=[], count=0, dataset_ids=dataset_ids)


        prompt = (
            "Answer the user using only the provided context. "
            "If the answer is not present, say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {final_question}"
        )


        chat_id = data.get("chat_id", "") or DEFAULT_CHAT_ID
        session_id = data.get("session_id")
        result = rf.chat_completion(prompt, chat_id=chat_id, session_id=session_id)


        answer = result.get("answer") or result.get("data") or result.get("content") or result
        return jsonify(
            success=True,
            dataset_ids=dataset_ids,
            answer=answer,
            chunks=chunks,
            count=len(chunks),
            result=result,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


# ─────────────────────────────────────────────────────────────────────────────
# Session Management DONE
# ─────────────────────────────────────────────────────────────────────────────



@ragflow_bp.route("/sessions", methods=["POST"])
@require_jwt(auth_required=True)
def create_session():
    """Create a new chat session."""
    try:
        data = request.json or {}
        result = rf.create_session(
            chat_id=data.get("chat_id", "") or DEFAULT_CHAT_ID,
            name=data.get("name", "Guru-Sikshan Session"),
        )
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500



@ragflow_bp.route("/sessions", methods=["GET"])
@require_jwt(auth_required=True)
def list_sessions():
    """List all chat sessions."""
    try:
        chat_id = request.args.get("chat_id", "") or DEFAULT_CHAT_ID
        sessions = rf.list_sessions(chat_id=chat_id)
        return jsonify(success=True, sessions=sessions, count=len(sessions))
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500



@ragflow_bp.route("/sessions/<session_id>", methods=["DELETE"])
@require_jwt(auth_required=True)
@require_admin_or_higher()
def delete_session(session_id: str):
    """Delete a chat session."""
    try:
        chat_id = request.args.get("chat_id", "") or DEFAULT_CHAT_ID
        result = rf.delete_session(chat_id, session_id)
        return jsonify(success=True, result=result)
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500



# ─────────────────────────────────────────────────────────────────────────────
# Resources & Recommendations (AUTH REQUIRED)
# ─────────────────────────────────────────────────────────────────────────────



@ragflow_bp.route("/resources", methods=["GET"])
@require_jwt(auth_required=True)
def resources():
    """Get educational resources for a teacher."""
    try:
        teacher_id = request.args.get("teacher_id", "") or ""
        competency_area = request.args.get("competency_area")
        cluster = _teacher_cluster(teacher_id) if teacher_id else ""


        resources = get_resources_for_cluster(cluster, competency_area)
        cleaned = []
        for item in resources:
            row = dict(item)
            row.pop("_geo_score", None)
            cleaned.append(row)


        return jsonify(
            success=True,
            resources=cleaned,
            detected_cluster=cluster or None,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500



@ragflow_bp.route("/resources/exemplary", methods=["GET"])
@require_jwt(auth_required=True)
def exemplary():
    """Get exemplary educational resources."""
    try:
        return jsonify(success=True, resources=get_exemplary_resources())
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500