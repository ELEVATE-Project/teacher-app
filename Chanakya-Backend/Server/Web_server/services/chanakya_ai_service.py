"""
Chanakya AI Service for Discussion Forum
==========================================

Handles @chanakya mentions in discussion forum by:
1. Retrieving conversation history
2. Calling Gemini API with context
3. Generating helpful responses
"""

import json
from typing import List, Dict, Optional
from google import genai
from google.genai import types

from config import Settings

settings = Settings()


class ChanakyaAIService:
    """Service for handling AI-powered responses in discussion forum."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Chanakya AI service with Gemini."""
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Chanakya AI")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"
    
    def _build_conversation_context(
        self, 
        original_post: str, 
        replies: List[Dict[str, str]]
    ) -> str:
        """Build conversation context from post and replies."""
        context = f"Original Question:\n{original_post}\n\n"
        
        if replies:
            context += "Discussion History:\n"
            for i, reply in enumerate(replies, 1):
                author = reply.get("author_name", "User")
                body = reply.get("body", "")
                context += f"{i}. {author}: {body}\n"
        else:
            context += "No replies yet in this discussion.\n"
        
        return context
    
    async def generate_response(
        self,
        query: str,
        original_post: str,
        replies: List[Dict[str, str]]
    ) -> str:
        """
        Generate AI response to a @chanakya query.
        
        Args:
            query: The user's query (text after @chanakya)
            original_post: The original post body
            replies: List of replies with author_name and body
            
        Returns:
            AI-generated response string
        """
        # Build context from conversation
        conversation_context = self._build_conversation_context(original_post, replies)
        
        # System prompt for Chanakya
        system_prompt = """You are Chanakya, an AI educational assistant for Indian teachers.
You help teachers with pedagogical questions, classroom management, teaching strategies, and educational content.

When responding to questions in the discussion forum:
1. Keep responses UNDER 250 words - be concise and focused
2. Provide practical, actionable advice
3. Consider the Indian educational context
4. Reference the conversation history when relevant
5. Use bullet points or numbered lists for clarity
6. Stay focused on education and teaching

Your responses should be supportive, constructive, and brief - helping teachers improve their practice without overwhelming them."""
        
        # Build the full prompt
        user_prompt = f"""Conversation Context:
{conversation_context}

User's Question:
{query}

Please provide a helpful response based on the conversation context and the user's question."""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=user_prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=1300,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate AI response: {str(e)}")


# Singleton instance
_chanakya_service: Optional[ChanakyaAIService] = None


def get_chanakya_service() -> ChanakyaAIService:
    """Get or create Chanakya AI service instance."""
    global _chanakya_service
    if _chanakya_service is None:
        _chanakya_service = ChanakyaAIService()
    return _chanakya_service
