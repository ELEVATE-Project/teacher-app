import time
from flask import Blueprint, request, jsonify
from auth.client_auth import authenticate_client
from auth.token_utils import issue_token
from middleware.rate_limiter import rate_limit
from middleware.audit_logger import log_request
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=False)

public_auth_bp = Blueprint("public_auth", __name__, url_prefix="/api/public/auth")


@public_auth_bp.route("/token", methods=["POST"])
@rate_limit("auth")
def get_token():
    """
    POST /api/public/auth/token
    Body: { client_id, client_secret, grant_type: "client_credentials" }
    Returns: { access_token, token_type, expires_in, scope }
    """
    start = time.time()
    body  = request.get_json(silent=True) or {}

    if body.get("grant_type") != "client_credentials":
        log_request("/auth/token", 400, start, "invalid_grant_type")
        return jsonify({"error": "unsupported_grant_type"}), 400

    client_id     = body.get("client_id", "").strip()
    client_secret = body.get("client_secret", "").strip()

    if not client_id or not client_secret:
        log_request("/auth/token", 400, start, "missing_credentials")
        return jsonify({"error": "invalid_request", "message": "client_id and client_secret required"}), 400

    client = authenticate_client(client_id, client_secret)
    if not client:
        log_request("/auth/token", 401, start, "invalid_credentials")
        return jsonify({"error": "invalid_client", "message": "Invalid credentials"}), 401

    token, expires_in = issue_token(client["client_id"], client["allowed_scopes"])

    log_request("/auth/token", 200, start)
    return jsonify({
        "access_token": token,
        "token_type":   "Bearer",
        "expires_in":   expires_in,
        "scope":        " ".join(client["allowed_scopes"]),
    }), 200
