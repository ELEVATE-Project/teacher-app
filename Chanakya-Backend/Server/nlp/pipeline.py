"""
Chanakya NLP Pipeline (Simplified)
==================================

Simple pipeline that wraps the Gemini processor.
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from .schemas import TeacherUtterance, NLPOutput
from .gemini_processor import GeminiProcessor


logger = logging.getLogger("chanakya.nlp")


class NLPPipeline:
    """
    Simple NLP pipeline for Chanakya.
    
    Usage:
        pipeline = NLPPipeline(gemini_api_key="your-key")
        result = await pipeline.process(utterance)
        print(result.english_understanding)
    """
    
    def __init__(self, gemini_api_key: str):
        """
        Initialize NLP pipeline.
        
        Args:
            gemini_api_key: API key for Gemini
        """
        self.processor = GeminiProcessor(api_key=gemini_api_key)
    
    async def process(self, utterance: TeacherUtterance) -> NLPOutput:
        """
        Process teacher utterance and return English understanding.
        """
        # Validate input
        if not utterance.text or not utterance.text.strip():
            return NLPOutput(
                english_understanding="[Empty input]",
                detected_language="unknown",
                raw_input=utterance.text or "",
                confidence=0.0,
                error="Empty utterance"
            )
        
        # Process
        result = await self.processor.process(utterance)
        
        # Log
        logger.info(f"Processed: '{utterance.text[:50]}...' -> '{result.english_understanding[:50]}...'")
        
        return result
    
    def process_sync(self, utterance: TeacherUtterance) -> NLPOutput:
        """Synchronous version of process()."""
        import asyncio
        return asyncio.run(self.process(utterance))


def create_pipeline(gemini_api_key: str) -> NLPPipeline:
    """Factory function to create NLP pipeline."""
    return NLPPipeline(gemini_api_key=gemini_api_key)
