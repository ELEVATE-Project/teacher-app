"""
User document model for MongoDB using Beanie.
"""
from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import EmailStr, Field


class User(Document):
    """User document model for MongoDB."""
    
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., unique=True)
    hashed_password: str
    role: str = Field(default="teacher")
    classes_handled: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    school_location: Optional[str] = None
    preferred_language: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "users"
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "role": "teacher",
                "classes_handled": ["Class 6", "Class 7"],
                "subjects": ["Mathematics", "Science"],
                "school_location": "Delhi",
                "preferred_language": ["English", "Hindi"],
                "is_active": True
            }
        }
