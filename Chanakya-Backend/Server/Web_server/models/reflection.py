"""
Reflection document model for MongoDB.
Converted from SQLAlchemy model in feedback_system/backend/database.py
"""
from datetime import datetime
from typing import Optional, Dict, Any
from beanie import Document, Indexed
from pydantic import Field


class ClassReflection(Document):
    """
    Stores post-class reflection sessions with AI-generated feedback.
    Used for analyzing teaching transcripts and providing improvement suggestions.
    """
    
    topic: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=100)
    class_level: str = Field(..., min_length=1, max_length=50, description="e.g., 'Class 6', 'Class 10'")
    transcript: str = Field(..., min_length=10, description="Transcript of the class audio")
    feedback_json: Optional[Dict[str, Any]] = Field(None, description="AI-generated feedback")
    user_id: Optional[str] = Field(None, description="Reference to User who created this reflection")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "class_reflections"
        indexes = [
            [("user_id", 1)],
            [("user_id", 1), ("created_at", -1)],
            [("subject", 1)],
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Fractions",
                "subject": "Mathematics",
                "class_level": "Class 6",
                "transcript": "Today we learned about fractions...",
                "feedback_json": {
                    "strengths": ["Good use of examples"],
                    "issues": ["Pace was too fast"],
                    "suggestions": ["Use more visual aids"]
                }
            }
        }
