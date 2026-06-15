import os
import bcrypt
from supabase import create_client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=False)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

_sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def authenticate_client(client_id: str, client_secret: str) -> dict | None:
    """
    Look up the client by client_id, verify secret hash.
    Returns the client row dict on success, None on failure.
    """
    result = (
        _sb.table("api_clients")
        .select("*")
        .eq("client_id", client_id)
        .eq("is_active", True)
        .single()
        .execute()
    )
    if not result.data:
        return None

    client = result.data
    if not client.get("client_secret_hash"):
        return None
    if not bcrypt.checkpw(client_secret.encode(), client["client_secret_hash"].encode()):
        return None

    try:
        _sb.table("api_clients").update(
            {"last_used_at": "now()"}
        ).eq("client_id", client_id).execute()
    except Exception:
        pass

    return client
