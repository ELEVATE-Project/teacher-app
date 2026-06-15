"""
Teaching Feedback Schemas
==========================

Data models for teaching session analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TeachingSession(BaseModel):
    """Input: Teaching session to be analyzed."""
    
    transcript: str = Field(
        ...,
        description="Text transcript of what the teacher taught (can be from audio or manual entry)",
        min_length=50
    )
    
    topic: str = Field(
        ...,
        description="Main topic being taught (e.g., 'fractions', 'photosynthesis')",
        min_length=2
    )
    
    grade_level: str = Field(
        ...,
        description="Student grade level (e.g., '5', '8', '10')"
    )
    
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Duration of teaching session in minutes",
        ge=1,
        le=120
    )
    
    language: Optional[str] = Field(
        default="en",
        description="Language of instruction (en, hi, ta, etc.)"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Unique session identifier"
    )
    
    teacher_id: Optional[str] = Field(
        default=None,
        description="Teacher identifier for tracking improvement"
    )


class ConceptCoverage(BaseModel):
    """Analysis of concepts covered vs expected."""
    
    concepts_covered: List[str] = Field(
        default_factory=list,
        description="Core concepts that were explained"
    )
    
    concepts_missed: List[str] = Field(
        default_factory=list,
        description="Important concepts not covered"
    )
    
    depth_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How thoroughly concepts were explained (0-1)"
    )


class ClarityAnalysis(BaseModel):
    """Analysis of explanation clarity."""
    
    clarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall clarity rating (0-1)"
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="What was explained clearly"
    )
    
    confusing_parts: List[str] = Field(
        default_factory=list,
        description="Parts that may confuse students"
    )
    
    language_level: str = Field(
        default="appropriate",
        description="Was language appropriate for grade level? (too_simple, appropriate, too_complex)"
    )


class EngagementAnalysis(BaseModel):
    """Analysis of student engagement techniques."""
    
    engagement_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How engaging the lesson was (0-1)"
    )
    
    techniques_used: List[str] = Field(
        default_factory=list,
        description="Engagement techniques observed (questions, examples, activities)"
    )
    
    missed_opportunities: List[str] = Field(
        default_factory=list,
        description="Where teacher could have engaged students more"
    )


class RuralContextAnalysis(BaseModel):
    """Analysis specific to rural classroom context."""
    
    rural_appropriateness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How well suited for rural schools (0-1)"
    )
    
    resource_requirements: str = Field(
        default="none",
        description="Resources mentioned (none, basic, advanced)"
    )
    
    local_context_used: bool = Field(
        default=False,
        description="Did teacher use local/familiar examples?"
    )
    
    suggestions_for_rural: List[str] = Field(
        default_factory=list,
        description="How to make more rural-appropriate"
    )


class TeachingFeedback(BaseModel):
    """Output: Comprehensive teaching feedback."""
    
    session_id: str = Field(
        ...,
        description="Session identifier"
    )
    
    topic: str = Field(
        ...,
        description="Topic taught"
    )
    
    grade_level: str = Field(
        ...,
        description="Grade level"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When feedback was generated"
    )
    
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall teaching effectiveness (0-1)"
    )
    
    concept_coverage: ConceptCoverage = Field(
        ...,
        description="What was covered vs what was missed"
    )
    
    clarity: ClarityAnalysis = Field(
        ...,
        description="How clear the explanations were"
    )
    
    engagement: EngagementAnalysis = Field(
        ...,
        description="Student engagement analysis"
    )
    
    rural_context: RuralContextAnalysis = Field(
        ...,
        description="Rural classroom appropriateness"
    )
    
    key_strengths: List[str] = Field(
        default_factory=list,
        description="Top 3-5 things teacher did well"
    )
    
    improvement_areas: List[str] = Field(
        default_factory=list,
        description="Top 3-5 areas for improvement"
    )
    
    actionable_tips: List[str] = Field(
        default_factory=list,
        description="Specific actions teacher can take next time"
    )
    
    misconceptions_addressed: List[str] = Field(
        default_factory=list,
        description="Common student misconceptions that were addressed"
    )
    
    misconceptions_missed: List[str] = Field(
        default_factory=list,
        description="Common misconceptions that should have been addressed"
    )


class FeedbackHistory(BaseModel):
    """Teacher's feedback history for tracking improvement."""
    
    teacher_id: str = Field(
        ...,
        description="Teacher identifier"
    )
    
    total_sessions: int = Field(
        default=0,
        description="Total teaching sessions analyzed"
    )
    
    average_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average overall score across sessions"
    )
    
    improvement_trend: str = Field(
        default="stable",
        description="Improving, declining, or stable"
    )
    
    recent_feedbacks: List[TeachingFeedback] = Field(
        default_factory=list,
        description="Last 5 feedback sessions"
    )
    
    common_strengths: List[str] = Field(
        default_factory=list,
        description="Consistent strengths across sessions"
    )
    
    recurring_gaps: List[str] = Field(
        default_factory=list,
        description="Areas consistently needing improvement"
    )
