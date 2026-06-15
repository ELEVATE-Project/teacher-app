"""
Vision Service for Gemini Image Analysis
=========================================

Handles image analysis using Gemini Vision API for educational contexts.
"""

import base64
import time
import structlog
from typing import Optional
from google import genai
from google.genai import types

logger = structlog.get_logger(__name__)


class VisionService:
    """Service for analyzing images using Gemini Vision API."""
    
    def __init__(self, api_key: str):
        """Initialize the vision service with API key."""
        self.client = genai.Client(api_key=api_key)
        # Use gemini-2.5-flash (latest stable model)
        self.model = "models/gemini-2.5-flash"
        logger.info("VisionService initialized", model=self.model)
    
    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str,
        query: str,
        context: Optional[str] = None
    ) -> dict:
        """
        Analyze an image with an optional text query.
        
        Args:
            image_data: Raw image bytes
            mime_type: MIME type of the image (e.g., 'image/jpeg', 'image/png')
            query: User's question about the image
            context: Optional additional context
            
        Returns:
            dict with analysis result
        """
        try:
            # Build the system prompt for educational context
            system_prompt = """You are Chanakya, an AI teaching assistant for Indian school teachers.
You are analyzing an image shared by a teacher. Provide helpful, educational insights.

When analyzing images:
- If it's student work (homework, test, drawing): Provide constructive feedback and suggestions
- If it's a textbook page: Explain the content clearly and suggest teaching approaches
- If it's a diagram/chart: Explain what it shows and how to teach it effectively
- If it's a classroom situation: Provide practical advice
- If it's educational material: Analyze and provide teaching tips

Be encouraging, practical, and focused on helping the teacher.
Keep responses concise but comprehensive (under 400 words).
Use bullet points for clarity when appropriate."""

            # Build the user prompt
            user_prompt = query if query else "Please analyze this image and provide educational insights."
            if context:
                user_prompt = f"{user_prompt}\n\nAdditional context: {context}"
            
            # Create the image part
            image_part = types.Part.from_bytes(
                data=image_data,
                mime_type=mime_type
            )
            
            # Create the content with image and text
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        image_part,
                        types.Part.from_text(text=user_prompt)
                    ]
                )
            ]
            
            # Generate response with retry logic for rate limits
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.7,
                            max_output_tokens=1000,
                        )
                    )
                    break
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            raise
                    else:
                        raise
            
            # Extract the response text
            response_text = response.text if response.text else "I couldn't analyze this image. Please try again."
            
            logger.info("Image analyzed successfully", 
                       query_length=len(query),
                       response_length=len(response_text))
            
            return {
                "success": True,
                "analysis": response_text,
                "tool_used": "vision_analysis",
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis": "Sorry, I couldn't analyze this image. Please try again.",
                "tool_used": "vision_analysis",
                "confidence": 0.0
            }


# Singleton instance
_vision_service: Optional[VisionService] = None


def get_vision_service(api_key: str) -> VisionService:
    """Get or create the vision service instance."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService(api_key=api_key)
    return _vision_service
