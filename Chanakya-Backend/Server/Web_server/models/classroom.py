"""
Classroom-related Beanie document models for MongoDB.
Converted from SQLAlchemy models in feedback_system/backend/database.py
"""
from datetime import datetime
from typing import Optional, Dict, Any
from beanie import Document, Indexed
from pydantic import Field


class Class(Document):
    """Classroom document model for MongoDB."""
    
    name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[str] = Field(None, description="Reference to User who created this class")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "classes"
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Class 6A",
                "subject": "Mathematics",
                "user_id": "user_abc123"
            }
        }


class Student(Document):
    """Student document model for MongoDB."""
    
    class_id: Indexed(str)  # type: ignore - Reference to Class
    name: str = Field(..., min_length=1, max_length=100)
    level: str = Field(default="medium", description="Student level: weak, medium, strong")
    confidence: float = Field(default=2.5, ge=1.0, le=5.0, description="Confidence score 1-5")
    last_answered_at: Optional[datetime] = None
    consecutive_correct: int = Field(default=0)
    consecutive_wrong: int = Field(default=0)
    topic_performance: Dict[str, float] = Field(default_factory=dict, description="Topic-wise performance scores")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "students"
        indexes = [
            [("class_id", 1)],
            [("class_id", 1), ("name", 1)],
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "class_id": "class_abc123",
                "name": "Rahul Kumar",
                "level": "medium",
                "confidence": 2.5
            }
        }


class Question(Document):
    """Question document model for MongoDB."""
    
    topic: Indexed(str)  # type: ignore
    difficulty: str = Field(..., description="Difficulty: easy, medium, hard")
    text: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "questions"
        indexes = [
            [("topic", 1)],
            [("topic", 1), ("difficulty", 1)],
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Fractions",
                "difficulty": "medium",
                "text": "What is 1/2 + 1/4?"
            }
        }


class ClassSession(Document):
    """Class session document model for MongoDB."""
    
    class_id: Indexed(str)  # type: ignore - Reference to Class
    topic: str = Field(..., min_length=1, max_length=200)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    
    class Settings:
        name = "class_sessions"
        indexes = [
            [("class_id", 1)],
            [("class_id", 1), ("is_active", 1)],
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "class_id": "class_abc123",
                "topic": "Introduction to Fractions",
                "is_active": True
            }
        }


class StudentResponse(Document):
    """Student response document model for MongoDB."""
    
    session_id: Indexed(str)  # type: ignore - Reference to ClassSession
    student_id: Indexed(str)  # type: ignore - Reference to Student
    question_id: Optional[str] = Field(None, description="Reference to Question")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    difficulty_asked: str = Field(..., description="Difficulty: easy, medium, hard")
    answered_at: datetime = Field(default_factory=datetime.utcnow)
    skipped: bool = Field(default=False)
    
    class Settings:
        name = "student_responses"
        indexes = [
            [("session_id", 1)],
            [("student_id", 1)],
            [("session_id", 1), ("student_id", 1)],
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "student_id": "student_xyz789",
                "question_id": "question_123",
                "rating": 4,
                "difficulty_asked": "medium",
                "skipped": False
            }
        }
