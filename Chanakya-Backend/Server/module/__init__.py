"""
MODULE - AI Lesson & Assignment Builder
=======================================

AI-powered lesson preparation tool that converts textbook-aligned content
into 8-slide multimodal lessons and auto-generated assignments.
"""

from .models.schemas import (
    Lesson,
    Slide,
    Assignment,
    Question,
    MCQQuestion,
    ShortAnswerQuestion,
    LongAnswerQuestion,
    TopicInfo,
    TextbookContent,
    ValidationReport,
    LessonGenerationRequest,
    LessonGenerationResponse,
)

__all__ = [
    "Lesson",
    "Slide",
    "Assignment",
    "Question",
    "MCQQuestion",
    "ShortAnswerQuestion",
    "LongAnswerQuestion",
    "TopicInfo",
    "TextbookContent",
    "ValidationReport",
    "LessonGenerationRequest",
    "LessonGenerationResponse",
]
