"""
Pydantic schemas for Reflection API request/response.
Adapted from feedback_system/backend/models.py with string IDs for MongoDB.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReflectionCreate(BaseModel):
    """Request model for creating a class reflection analysis."""
    topic: str = Field(..., min_length=1, max_length=200, description="Topic taught in the class")
    subject: str = Field(..., min_length=1, max_length=100, description="Subject name")
    class_level: str = Field(..., min_length=1, max_length=50, description="Class level, e.g., 'Class 6'")
    transcript: str = Field(..., min_length=10, description="Transcript of the class audio")


class ReflectionFeedback(BaseModel):
    """AI-generated feedback structure."""
    strengths: List[str] = Field(default_factory=list, description="Things the teacher did well")
    issues: List[str] = Field(default_factory=list, description="Areas that need improvement")
    classroom_atmosphere: str = Field(default="Unknown", description="Overall classroom atmosphere")
    topic_feedback: List[str] = Field(default_factory=list, description="Topic-specific feedback")
    suggestions: List[str] = Field(default_factory=list, description="Actionable suggestions for improvement")


class ReflectionResponse(BaseModel):
    """Response model for a class reflection."""
    id: str  # MongoDB ObjectId as string
    topic: str
    subject: str
    class_level: str
    transcript: str
    feedback: ReflectionFeedback
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReflectionListItem(BaseModel):
    """Simplified reflection item for history listing."""
    id: str  # MongoDB ObjectId as string
    topic: str
    subject: str
    class_level: str
    created_at: datetime
    strengths_count: int
    issues_count: int
    
    class Config:
        from_attributes = True


class ReflectionHistoryResponse(BaseModel):
    """Response model for reflection history."""
    reflections: List[ReflectionListItem]
    total: int
