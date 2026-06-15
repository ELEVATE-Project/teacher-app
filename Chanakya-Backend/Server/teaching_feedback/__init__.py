"""
Teaching Feedback Module
=========================

Analyzes teaching sessions and provides constructive feedback to teachers.
"""

from .analyzer import TeachingFeedbackAnalyzer
from .schemas import TeachingSession, TeachingFeedback

__all__ = [
    "TeachingFeedbackAnalyzer",
    "TeachingSession",
    "TeachingFeedback",
]
