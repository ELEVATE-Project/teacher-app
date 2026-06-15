"""
User-related Pydantic schemas.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str
    confirmPassword: str
    classesHandled: list[str] = []
    subjects: list[str] = []
    schoolLocation: str = ""
    preferredLanguage: list[str] = []


class UserUpdate(BaseModel):
    """Schema for user updates."""
    name: Optional[str] = None
    classesHandled: Optional[list[str]] = None
    subjects: Optional[list[str]] = None
    schoolLocation: Optional[str] = None
    preferredLanguage: Optional[list[str]] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    classesHandled: list[str]
    subjects: list[str]
    schoolLocation: str
    preferredLanguage: list[str]
    
    class Config:
        from_attributes = True
