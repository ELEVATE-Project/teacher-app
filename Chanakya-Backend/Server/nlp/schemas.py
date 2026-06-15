"""
Chanakya NLP Schemas (Simplified)
=================================

Simple schemas for teacher input and English understanding output.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class TeacherUtterance(BaseModel):
    """
    Raw input from teacher (post-ASR).
    """
    
    text: str = Field(
        ...,
        description="Raw transcribed text from teacher speech",
        min_length=1,
        max_length=1000
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the utterance was captured"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for context tracking"
    )


class NLPOutput(BaseModel):
    """
    Simple output from NLP pipeline.
    
    Just provides English understanding of the teacher's query.
    """
    
    # Core output
    english_understanding: str = Field(
        ...,
        description="Clear English understanding of what the teacher said/needs"
    )
    
    detected_language: str = Field(
        default="unknown",
        description="Detected language code (hi, ta, bn, etc.)"
    )
    
    # Original input
    raw_input: str = Field(
        ...,
        description="Original input text"
    )
    
    # Metadata
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in understanding"
    )
    
    processing_time_ms: float = Field(
        default=0.0,
        description="Processing time in milliseconds"
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When processing completed"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )
