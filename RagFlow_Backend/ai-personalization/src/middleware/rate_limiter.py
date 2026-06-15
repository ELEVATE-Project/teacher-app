"""
Simple in-memory sliding-window rate limiter per client_id.
Good enough for v1. Replace with Redis for multi-process or multi-instance deploys.
"""
import time
import threading
import functools
from flask import request, jsonify, g

_lock   = threading.Lock()
_windows: dict[str, list[float]] = {}

# Per-client limits
LIMITS = {
    "auth":    (5,  60),   # 5 token requests per 60 s
    "session": (30, 60),   # 30 session creates per 60 s
    "message": (60, 60),   # 60 messages per 60 s
}


def _check(key: str, max_calls: int, window_seconds: int) -> bool:
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        timestamps = _windows.get(key, [])
        timestamps = [t for t in timestamps if t > cutoff]
        if len(timestamps) >= max_calls:
            return False
        timestamps.append(now)
        _windows[key] = timestamps
    return True


def rate_limit(bucket: str):
    """
    Decorator — apply rate limit for a named bucket.
    Must be applied AFTER @require_token so g.client_id is set.
    For the /token endpoint, falls back to IP.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            identity  = getattr(g, "client_id", None) or request.remote_addr
            max_calls, window = LIMITS.get(bucket, (30, 60))
            key = f"{bucket}:{identity}"
            if not _check(key, max_calls, window):
                return jsonify({
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Limit: {max_calls} per {window}s"
                }), 429
            return fn(*args, **kwargs)
        return wrapper
    return decorator
