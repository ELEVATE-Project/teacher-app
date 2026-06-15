"""
Gemini 2.5 Flash Processor (Simplified)
=======================================

Simple processor that converts teacher utterances in any Indian language
to clear English understanding.
"""

import time
from typing import Optional
from datetime import datetime, timezone
from google import genai
from google.genai import types

from .schemas import TeacherUtterance, NLPOutput


SYSTEM_PROMPT = """You are a translator and interpreter for Chanakya, a classroom support system for Indian teachers.

Your ONLY job is to understand what the teacher said and provide a clear English version.

INPUT: Teacher utterances in ANY Indian language (Hindi, Tamil, Bengali, Telugu, Marathi, Kannada, Malayalam, Gujarati, Odia, Punjabi, Assamese, Urdu, or code-mixed with English)

OUTPUT: A JSON object with:
1. "english_understanding": A clear, natural English sentence explaining what the teacher said or is asking for
2. "detected_language": The language code (hi, ta, bn, te, mr, kn, ml, gu, or, pa, as, ur, en, or "mixed" for code-mixed)
3. "confidence": How confident you are in the understanding (0.0 to 1.0)

EXAMPLES:

Input: "Bachche sun nahi rahe hain"
Output: {"english_understanding": "The children are not listening", "detected_language": "hi", "confidence": 0.95}

Input: "இந்த பாடம் புரியவில்லை அவர்களுக்கு"
Output: {"english_understanding": "They are not understanding this lesson", "detected_language": "ta", "confidence": 0.92}

Input: "Addition ka carry samajh nahi aa raha inko"
Output: {"english_understanding": "They are not understanding the carry concept in addition", "detected_language": "mixed", "confidence": 0.90}

Input: "কিভাবে এই টপিক শেষ করব?"
Output: {"english_understanding": "How should I complete this topic?", "detected_language": "bn", "confidence": 0.88}

RULES:
- Return ONLY valid JSON, nothing else
- Keep the English natural and clear
- Preserve the teacher's intent and meaning
- If input is already in English, still return JSON format
- If you can't understand, set confidence low and do your best guess"""


class GeminiProcessor:
    """
    Simple Gemini 2.5 Flash processor for understanding teacher utterances.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini processor.
        
        Args:
            api_key: Google AI API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
    
    async def process(self, utterance: TeacherUtterance) -> NLPOutput:
        """
        Process teacher utterance and return English understanding.
        """
        start_time = time.time()
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f'Understand this teacher utterance: "{utterance.text}"')]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    max_output_tokens=256,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            import json
            text = response.text.strip()
            
            # Clean markdown if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            parsed = json.loads(text.strip())
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return NLPOutput(
                english_understanding=parsed.get("english_understanding", utterance.text),
                detected_language=parsed.get("detected_language", "unknown"),
                raw_input=utterance.text,
                confidence=parsed.get("confidence", 0.8),
                processing_time_ms=processing_time_ms,
                error=None
            )
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            
            return NLPOutput(
                english_understanding=utterance.text,  # Fallback to original
                detected_language="unknown",
                raw_input=utterance.text,
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                error=str(e)
            )
    
    def process_sync(self, utterance: TeacherUtterance) -> NLPOutput:
        """Synchronous version of process()."""
        import asyncio
        return asyncio.run(self.process(utterance))
