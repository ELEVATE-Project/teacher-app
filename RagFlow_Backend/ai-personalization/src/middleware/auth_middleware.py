import functools
import jwt as pyjwt
from flask import request, jsonify, g
from auth.token_utils import verify_token


def require_token(*required_scopes: str):
    """
    Flask decorator — validates Bearer JWT and checks scopes.
    Usage:
        @require_token("chat:message:send")
        def my_route(): ...
    Sets g.client_id and g.token_scopes on success.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "missing_token", "message": "Authorization header required"}), 401

            token = auth_header.removeprefix("Bearer ").strip()
            try:
                payload = verify_token(token)
            except pyjwt.ExpiredSignatureError:
                return jsonify({"error": "token_expired", "message": "Token has expired"}), 401
            except pyjwt.PyJWTError as e:
                return jsonify({"error": "invalid_token", "message": "Token is invalid"}), 401

            token_scopes = payload.get("scopes", [])
            for scope in required_scopes:
                if scope not in token_scopes:
                    return jsonify({
                        "error": "insufficient_scope",
                        "message": f"Required scope: {scope}"
                    }), 403

            g.client_id    = payload["sub"]
            g.token_scopes = token_scopes
            return fn(*args, **kwargs)
        return wrapper
    return decorator
