"""
Authentication-related Pydantic schemas.
"""
from pydantic import BaseModel, EmailStr, validator
from schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str

    @validator("password")
    def password_max_length(cls, v: str) -> str:
        """Ensure password is not longer than 72 bytes (bcrypt limitation)."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError(
                "password cannot be longer than 72 bytes, truncate manually if necessary"
            )
        return v


class SignUpRequest(BaseModel):
    """Schema for signup request."""
    name: str
    email: EmailStr
    password: str
    confirmPassword: str
    classesHandled: list[str] = []
    subjects: list[str] = []
    schoolLocation: str = ""
    preferredLanguage: list[str] = []

    @validator("password")
    def signup_password_max_length(cls, v: str) -> str:
        """Ensure signup password is not longer than 72 bytes (bcrypt limitation)."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError(
                "password cannot be longer than 72 bytes, truncate manually if necessary"
            )
        return v

    @validator("confirmPassword")
    def signup_confirm_password_max_length(cls, v: str) -> str:
        """Ensure confirmPassword is not longer than 72 bytes."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError(
                "confirmPassword cannot be longer than 72 bytes, truncate manually if necessary"
            )
        return v


class AuthResponse(BaseModel):
    """Schema for authentication response."""
    user: UserResponse
    token: str
