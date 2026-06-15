import os
import time
import uuid
from flask import request, g
from supabase import create_client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=False)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
_sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def log_request(endpoint: str, status_code: int, start_time: float, error: str = None):
    """Fire-and-forget audit log. Never raises."""
    try:
        _sb.table("api_request_logs").insert({
            "client_id":    getattr(g, "client_id", None),
            "endpoint":     endpoint,
            "status_code":  status_code,
            "latency_ms":   int((time.time() - start_time) * 1000),
            "ip_address":   request.remote_addr,
            "request_id":   str(uuid.uuid4()),
            "error_message": error,
        }).execute()
    except Exception:
        pass
