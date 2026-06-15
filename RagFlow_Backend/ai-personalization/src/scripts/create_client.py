# NOTE : Only run once and save it.
import argparse
import secrets
import os
import bcrypt
from dotenv import load_dotenv, find_dotenv
from supabase import create_client

load_dotenv(find_dotenv(), override=False)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Human-readable client name")
    parser.add_argument(
        "--scopes",
        default="chat:session:create,chat:message:send",
        help="Comma-separated scopes",
    )
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]
    if not scopes:
        raise SystemExit("At least one scope is required")

    client_id = "gsc_" + secrets.token_urlsafe(24)
    client_secret = secrets.token_urlsafe(48)
    secret_hash = bcrypt.hashpw(client_secret.encode(), bcrypt.gensalt()).decode()

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    resp = sb.table("api_clients").insert({
        "name": args.name,
        "client_id": client_id,
        "client_secret_hash": secret_hash,
        "allowed_scopes": scopes,
        "is_active": True,
    }).execute()

    if not getattr(resp, "data", None):
        raise SystemExit("Failed to create API client")

    print("\nAPI Client created. Store these NOW — secret is never shown again.\n")
    print(f"  client_id    : {client_id}")
    print(f"  client_secret: {client_secret}")
    print(f"  scopes       : {scopes}\n")

if __name__ == "__main__":
    main()