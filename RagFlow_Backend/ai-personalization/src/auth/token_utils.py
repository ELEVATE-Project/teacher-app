import os
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=False)

JWT_SECRET  = os.environ["JWT_SECRET"]
JWT_EXPIRY  = int(os.getenv("JWT_EXPIRY_SECONDS", "900"))   # 15 min default
JWT_ALGO    = "HS256"
JWT_ISSUER  = "guru-sikshan-chat-api"
JWT_AUDIENCE = "guru-sikshan-partners"


def issue_token(client_id: str, scopes: list[str]) -> tuple[str, int]:
    """Issue a signed JWT. Returns (token, expires_in_seconds)."""
    now = datetime.now(timezone.utc)
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": client_id,
        "scopes": scopes,
        "iat": now,
        "exp": now + timedelta(seconds=JWT_EXPIRY),
        "jti": str(uuid.uuid4()),   # unique token ID (replay protection)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token, JWT_EXPIRY


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT.
    Raises jwt.PyJWTError on any failure (expired, bad sig, wrong aud/iss).
    Returns decoded payload dict on success.
    """
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGO],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
    )
