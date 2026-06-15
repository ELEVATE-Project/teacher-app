"""
Pydantic schemas for Classroom API request/response.
Adapted from feedback_system/backend/models.py with string IDs for MongoDB.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ==================== Class Schemas ====================

class ClassCreate(BaseModel):
    """Request model for creating a class."""
    name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=100)


class ClassResponse(BaseModel):
    """Response model for a class."""
    id: str  # MongoDB ObjectId as string
    name: str
    subject: str
    created_at: datetime
    student_count: int = 0
    
    class Config:
        from_attributes = True


class ClassListResponse(BaseModel):
    """Response model for list of classes."""
    classes: List[ClassResponse]


# ==================== Student Schemas ====================

class StudentCreate(BaseModel):
    """Request model for creating a student."""
    name: str = Field(..., min_length=1, max_length=100)
    level: str = Field(default="medium", pattern="^(weak|medium|strong)$")
    confidence: float = Field(default=2.5, ge=1.0, le=5.0)


class StudentBulkCreate(BaseModel):
    """Request model for bulk creating students."""
    students: List[StudentCreate]


class StudentResponse(BaseModel):
    """Response model for a student."""
    id: str  # MongoDB ObjectId as string
    class_id: str
    name: str
    level: str
    confidence: float
    last_answered_at: Optional[datetime] = None
    consecutive_correct: int = 0
    consecutive_wrong: int = 0
    topic_performance: Dict[str, float] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class StudentUpdate(BaseModel):
    """Request model for updating a student."""
    name: Optional[str] = None
    level: Optional[str] = Field(default=None, pattern="^(weak|medium|strong)$")
    confidence: Optional[float] = Field(default=None, ge=1.0, le=5.0)


class StudentProfileResponse(BaseModel):
    """Response model for detailed student profile."""
    student: StudentResponse
    total_responses: int
    average_rating: float
    participation_rate: float
    improvement_trend: float
    recent_history: List[dict]


# ==================== Question Schemas ====================

class QuestionCreate(BaseModel):
    """Request model for creating a question."""
    topic: str = Field(..., min_length=1, max_length=200)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    text: str = Field(..., min_length=1)


class QuestionBulkCreate(BaseModel):
    """Request model for bulk creating questions."""
    questions: List[QuestionCreate]


class QuestionResponse(BaseModel):
    """Response model for a question."""
    id: str  # MongoDB ObjectId as string
    topic: str
    difficulty: str
    text: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuestionGenerateRequest(BaseModel):
    """Request model for AI question generation."""
    topic: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=100)
    easy_count: int = Field(default=3, ge=1, le=10)
    medium_count: int = Field(default=3, ge=1, le=10)
    hard_count: int = Field(default=3, ge=1, le=10)


class QuestionsByDifficulty(BaseModel):
    """Response model for questions grouped by difficulty."""
    easy: List[QuestionResponse]
    medium: List[QuestionResponse]
    hard: List[QuestionResponse]


# ==================== Session Schemas ====================

class SessionCreate(BaseModel):
    """Request model for creating a session."""
    class_id: str  # MongoDB ObjectId as string
    topic: str = Field(..., min_length=1, max_length=200)


class SessionResponse(BaseModel):
    """Response model for a session."""
    id: str  # MongoDB ObjectId as string
    class_id: str
    topic: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class SuggestionResponse(BaseModel):
    """Response model for student suggestion."""
    student_id: str
    student_name: str
    difficulty: str
    question_id: Optional[str] = None
    question_text: Optional[str] = None
    reason: str
    priority_score: float


class ResponseCreate(BaseModel):
    """Request model for recording a student response."""
    student_id: str
    question_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    difficulty_asked: str = Field(..., pattern="^(easy|medium|hard)$")
    skipped: bool = False


class ResponseSubmit(BaseModel):
    """Request model for submitting a response rating."""
    rating: int = Field(..., ge=1, le=5)


# ==================== Summary Schemas ====================

class StudentSummary(BaseModel):
    """Summary of a student's performance in a session."""
    student_id: str
    student_name: str
    times_called: int
    average_rating: float
    confidence_change: float
    improved: bool


class SessionSummaryResponse(BaseModel):
    """Response model for session summary."""
    session_id: str
    topic: str
    duration_minutes: float
    total_questions_asked: int
    participation_percentage: float
    students_called: int
    students_not_called: int
    average_rating: float
    difficulty_distribution: Dict[str, int]
    students_improved: List[StudentSummary]
    students_need_attention: List[StudentSummary]
    all_student_summaries: List[StudentSummary]
