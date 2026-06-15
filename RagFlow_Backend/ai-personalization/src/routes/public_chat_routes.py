# NOTE : To be utilized by other teams, requires auth and whatnot. tbh they r free to use direct routes as well.
import os
import time
import uuid
import json
from flask import Blueprint, request, jsonify, stream_with_context, Response, g
from supabase import create_client
from middleware.auth_middleware import require_token
from middleware.rate_limiter import rate_limit
from middleware.audit_logger import log_request
from ragflow_client import (
    chat_completion,
    chat_completion_stream,
    create_session as ragflow_create_session,
)
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=False)

public_chat_bp = Blueprint("public_chat", __name__, url_prefix="/api/public/chat")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
_sb = create_client(SUPABASE_URL, SUPABASE_KEY)

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "86400"))  # 24 hours

print("[debug] ragflow_create_session:", ragflow_create_session)
print("[debug] module:", getattr(ragflow_create_session, "__module__", None))
print("[debug] name:", getattr(ragflow_create_session, "__name__", None))

# ── dataset routing ──────────────────────────────────────────
# TODO : Routing for multiple datasets. To be fully initialized later
DATASET_ROUTES = {
    "student_textbooks":  os.getenv("RAGFLOW_DATASET_STUDENT_TEXTBOOKS", ""),
    "teacher_training":   os.getenv("RAGFLOW_DATASET_TEACHER_TRAINING", ""),
    "teacher_resource":   os.getenv("RAGFLOW_DATASET_TEACHER_RESOURCE", ""),
    "assessments":        os.getenv("RAGFLOW_DATASET_ASSESSMENTS", ""),
    "remedial_bridge":    os.getenv("RAGFLOW_DATASET_REMEDIAL", ""),
    "policy_admin":       os.getenv("RAGFLOW_DATASET_POLICY", ""),
}
DEFAULT_DATASETS = ["teacher_training", "teacher_resource"]


def _resolve_datasets(scope_list: list[str]) -> list[str]:
    """Translate partner-facing scope names to internal RAGFlow dataset IDs."""
    ids = []
    for name in (scope_list or DEFAULT_DATASETS):
        ds_id = DATASET_ROUTES.get(name, "")
        if ds_id:
            ids.append(ds_id)
    return ids or [v for v in DATASET_ROUTES.values() if v]


def _make_session_id() -> str:
    return "sess_" + uuid.uuid4().hex


# ── health ───────────────────────────────────────────────────
@public_chat_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok":      True,
        "service": "guru-sikshan-chat-api",
        "version": "v1",
    }), 200


# ── create session ───────────────────────────────────────────
@public_chat_bp.route("/session", methods=["POST"])
@require_token("chat:session:create")
@rate_limit("session")
def create_session():
    """
    POST /api/public/chat/session
    Body: { externalUserId?, context?: { role, grade, subject, language, state } }
    Returns: { sessionId, expiresIn }
    """
    start = time.time()
    body  = request.get_json(silent=True) or {}

    external_user_id = body.get("externalUserId", "")
    context          = body.get("context", {})
    session_id       = _make_session_id()

    scopes = context.get("moduleScopes", DEFAULT_DATASETS)

    rf_session_id = None
    try:
        rf_resp = ragflow_create_session(
            name=f"Guru-Sikshan Session {session_id}"
        )
        print("[public_chat] ragflow_create_session response:", rf_resp)

        if not isinstance(rf_resp, dict):
            log_request("/chat/session", 502, start, "invalid_ragflow_response_type")
            return jsonify({
                "error": "upstream_error",
                "message": "Invalid RAGFlow response type",
                "details": str(rf_resp),
            }), 502

        if rf_resp.get("code") != 0:
            log_request("/chat/session", 502, start, rf_resp.get("message", "ragflow_error"))
            return jsonify({
                "error": "upstream_error",
                "message": rf_resp.get("message", "Could not initialise RAGFlow session"),
                "details": rf_resp,
            }), 502

        data = rf_resp.get("data") or {}
        rf_session_id = data.get("id")
        if not rf_session_id:
            log_request("/chat/session", 502, start, "missing_ragflow_session_id")
            return jsonify({
                "error": "upstream_error",
                "message": "RAGFlow session response missing id",
                "details": rf_resp,
            }), 502

    except Exception as e:
        import traceback
        traceback.print_exc()
        log_request("/chat/session", 502, start, str(e))
        return jsonify({
            "error": "upstream_error",
            "message": "Could not initialise RAGFlow session",
            "details": str(e),
        }), 502

    from datetime import datetime, timezone, timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)

    _sb.table("api_sessions").insert({
        "client_id":           g.client_id,
        "external_user_id":    external_user_id,
        "internal_session_id": session_id,
        "ragflow_session_id":  rf_session_id,
        "context_json":        context,
        "expires_at":          expires_at.isoformat(),
    }).execute()

    log_request("/chat/session", 201, start)
    return jsonify({
        "sessionId": session_id,
        "expiresIn": SESSION_TTL_SECONDS,
    }), 201


def _get_valid_session(session_id: str, client_id: str):
    """Fetch session row, enforce ownership + expiry without crashing on 0 rows."""
    from datetime import datetime, timezone
    
    result = (
        _sb.table("api_sessions")
        .select("*")
        .eq("internal_session_id", session_id)
        .eq("client_id", client_id)
        .execute()
    )
    
    if not result.data or len(result.data) == 0:
        return None, "session_not_found"

    row = result.data[0]
    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        return None, "session_expired"

    return row, None


# ── send message ─────────────────────────────────────────────
@public_chat_bp.route("/message", methods=["POST"])
@require_token("chat:message:send")
@rate_limit("message")
def send_message():
    """
    POST /api/public/chat/message
    Body: {
      sessionId: str,
      message:   str,
      scope?:    list[str]   -- optional override dataset scope
    }
    Returns: { answer, sources, sessionId }
    """
    start = time.time()
    body  = request.get_json(silent=True) or {}

    session_id = body.get("sessionId", "").strip()
    message    = body.get("message", "").strip()

    if not session_id or not message:
        log_request("/chat/message", 400, start, "missing_fields")
        return jsonify({"error": "invalid_request", "message": "sessionId and message are required"}), 400

    if len(message) > 4000:
        return jsonify({"error": "invalid_request", "message": "message too long (max 4000 chars)"}), 400

    session_row, err = _get_valid_session(session_id, g.client_id)
    if err:
        log_request("/chat/message", 401 if err == "session_not_found" else 401, start, err)
        return jsonify({"error": err}), 401

    rf_session_id = session_row.get("ragflow_session_id")
    context       = session_row.get("context_json", {})
    scope_override = body.get("scope", [])
    scopes  = scope_override or context.get("moduleScopes", DEFAULT_DATASETS)
    ds_ids  = _resolve_datasets(scopes)

    try:
        rf_resp = chat_completion(
            question=message,
            session_id=rf_session_id,
        )
    except Exception as e:
        log_request("/chat/message", 502, start, str(e))
        return jsonify({"error": "upstream_error", "message": "RAGFlow request failed","details":str(e)}), 502

    choices = rf_resp.get("choices") or []
    first = choices[0] if choices else {}
    message_obj = first.get("message") or {}
    answer = message_obj.get("content", "") or ""

    sources = _extract_sources(rf_resp)

    log_request("/chat/message", 200, start)
    return jsonify({
        "answer":    answer,
        "sources":   sources,
        "sessionId": session_id,
        "meta": {
            "datasetsQueried": scopes,
            "latencyMs": int((time.time() - start) * 1000),
        }
    }), 200


# ── streaming message ────────────────────────────────────────
@public_chat_bp.route("/message/stream", methods=["POST"])
@require_token("chat:message:send")
@rate_limit("message")
def send_message_stream():
    """
    POST /api/public/chat/message/stream
    Same body as /message but returns Server-Sent Events.
    """
    start = time.time()
    body  = request.get_json(silent=True) or {}

    session_id = body.get("sessionId", "").strip()
    message    = body.get("message", "").strip()

    if not session_id or not message:
        return jsonify({"error": "invalid_request"}), 400

    session_row, err = _get_valid_session(session_id, g.client_id)
    if err:
        return jsonify({"error": err}), 401

    rf_session_id = session_row.get("ragflow_session_id")
    context       = session_row.get("context_json", {})
    scopes        = body.get("scope") or context.get("moduleScopes", DEFAULT_DATASETS)
    ds_ids        = _resolve_datasets(scopes)

    def generate():
        try:
            for chunk in chat_completion_stream(
                session_id=rf_session_id,
                question=message,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    log_request("/chat/message/stream", 200, start)
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


def _extract_sources(rf_resp: dict) -> list[dict]:
    choices = rf_resp.get("choices") or []
    if not choices:
        return []

    first = choices[0]
    message_obj = first.get("message") or {}
    extra_body = message_obj.get("extra_body") or {}
    references = extra_body.get("reference") or []

    if not isinstance(references, list):
        return []

    sources = []
    for ref in references:
        source = {
            "id": ref.get("id"),
            "document_name": ref.get("document_name"),
            "content": (ref.get("content") or "")[:300],
            "similarity": ref.get("similarity"),
            "dataset_id": ref.get("dataset_id"),
            "document_id": ref.get("document_id"),
        }
        sources.append(source)

    return sources
