"""
JWT token utilities.
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from config import settings


def create_access_token(user_id: str, role: Optional[str] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User ID to encode in token
        role: Optional role of the user (e.g. admin, teacher)
        
    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    if role:
        to_encode["role"] = role
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None
