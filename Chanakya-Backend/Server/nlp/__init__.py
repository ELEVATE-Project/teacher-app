"""
Chanakya NLP Layer (Simplified)
===============================

Simple NLP layer that converts teacher utterances in any Indian language
to clear English understanding using Gemini 2.5 Flash.

NO complex classification. NO taxonomies. Just understanding.
"""

from .pipeline import NLPPipeline
from .schemas import TeacherUtterance, NLPOutput
from .gemini_processor import GeminiProcessor

__version__ = "0.2.0"
__all__ = [
    "NLPPipeline",
    "TeacherUtterance",
    "NLPOutput",
    "GeminiProcessor"
]
