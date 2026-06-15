"""
Engines for Chanakya Web Server.
Business logic for classroom management and AI features.
"""
from .ai_questions import generate_questions_for_topic, generate_fallback_questions
from .confidence import update_student_confidence, update_student_level, calculate_confidence_trend, CONFIDENCE_DELTA
from .selection import calculate_priority_score, determine_difficulty, generate_reason, get_next_student_suggestion
from .reflection_analyzer import analyze_class_transcript, generate_smart_fallback

__all__ = [
    "generate_questions_for_topic",
    "generate_fallback_questions",
    "update_student_confidence",
    "update_student_level",
    "calculate_confidence_trend",
    "CONFIDENCE_DELTA",
    "calculate_priority_score",
    "determine_difficulty",
    "generate_reason",
    "get_next_student_suggestion",
    "analyze_class_transcript",
    "generate_smart_fallback",
]
