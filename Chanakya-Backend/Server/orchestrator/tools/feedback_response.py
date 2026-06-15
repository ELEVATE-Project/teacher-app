"""
Feedback Response Tool
======================

Handles teacher feedback about activities and provides constructive responses.
Also stores the last 3 messages for context analysis.
"""

import json
import re
import time
from typing import Optional
from google import genai
from google.genai import types

from .base import BaseTool


FEEDBACK_RESPONSE_PROMPT = """You are Chanakya, an empathetic and helpful AI assistant for teachers in rural Indian schools.

A teacher has provided feedback about a classroom activity or teaching approach.
Your task is to provide a SHORT, CONSTRUCTIVE, and ACTIONABLE response.

=== FEEDBACK TYPES ===
1. NEGATIVE FEEDBACK (activity didn't work, students didn't like it, waste of time)
   - Acknowledge the difficulty with empathy
   - Ask clarifying questions to understand what went wrong
   - Suggest quick modifications to fix the issue
   - Offer alternative approaches

2. POSITIVE FEEDBACK (activity worked great, students loved it, very helpful)
   - Celebrate the success
   - Ask what specifically worked well
   - Suggest ways to extend or build on this success
   - Encourage sharing with other teachers

3. MIXED FEEDBACK (some parts worked, some didn't)
   - Acknowledge both positives and negatives
   - Help identify what to keep vs. change
   - Provide targeted improvements

4. VAGUE FEEDBACK (unclear what exactly happened)
   - Ask clarifying questions
   - Help teacher reflect on specifics
   - Guide toward actionable insights

=== RESPONSE REQUIREMENTS ===
- Keep response SHORT (2-4 sentences max)
- Be EMPATHETIC and supportive - never defensive
- Focus on ACTIONABLE next steps
- Ask 1-2 specific questions to understand better
- Maintain encouraging tone even for negative feedback
- Respect teacher's time and experience

=== OUTPUT FORMAT ===
Return a JSON object with these exact keys:
- response: Short, empathetic response (2-4 sentences)
- follow_up_questions: Array of 1-2 specific questions to understand better
- quick_suggestions: Array of 2-3 quick actionable modifications to try
- sentiment: "positive", "negative", "mixed", or "unclear"

Teacher's Feedback: {feedback}

Recent Context (last 3 messages):
{context}

Generate a short, constructive response following the output format above.
Return ONLY valid JSON, no other text.
"""


class FeedbackResponseTool(BaseTool):
    """
    Tool for responding to teacher feedback about activities and teaching approaches.
    """
    
    name = "feedback_response"
    description = "Responds to teacher feedback about activities and stores conversation context"
    
    def __init__(self, api_key: str):
        """Initialize with Google API key."""
        self.client = genai.Client(api_key=api_key)
        self.model_name = "models/gemini-2.0-flash-exp"
    
    async def run(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Generate response to teacher feedback.
        
        Args:
            query: Teacher's feedback statement
            context: Optional context including recent messages
        
        Returns:
            Dictionary with response, questions, and suggestions
        """
        # Extract recent messages from context
        recent_messages = []
        if context and "recent_messages" in context:
            recent_messages = context["recent_messages"]
        
        # Format context for prompt
        context_str = self._format_recent_messages(recent_messages)
        
        prompt = FEEDBACK_RESPONSE_PROMPT.format(
            feedback=query,
            context=context_str
        )
        
        # Call Gemini
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                    response_mime_type="application/json"
                )
            )
            
            result_text = response.text.strip()
            
            # Parse JSON
            result = json.loads(result_text)
            
            # Add metadata
            result["tool_name"] = self.name
            result["timestamp"] = time.time()
            
            return result
            
        except json.JSONDecodeError as e:
            # Fallback response
            return {
                "response": "Thank you for sharing that feedback. Can you tell me more about what specifically didn't work? This will help me suggest better alternatives.",
                "follow_up_questions": [
                    "What specifically went wrong with the activity?",
                    "How did the students react?"
                ],
                "quick_suggestions": [
                    "Try breaking the activity into smaller steps",
                    "Provide more examples before starting",
                    "Use familiar local examples"
                ],
                "sentiment": "unclear",
                "tool_name": self.name,
                "timestamp": time.time(),
                "error": f"JSON parsing failed: {str(e)}"
            }
        
        except Exception as e:
            return {
                "response": "Thank you for your feedback. I'd like to understand better so I can help improve future activities. What specifically didn't work as expected?",
                "follow_up_questions": [
                    "Can you describe what happened?",
                    "What would have worked better?"
                ],
                "quick_suggestions": [],
                "sentiment": "unclear",
                "tool_name": self.name,
                "timestamp": time.time(),
                "error": str(e)
            }
    
    def _format_recent_messages(self, messages: list) -> str:
        """Format recent messages for context."""
        if not messages:
            return "No recent messages available"
        
        formatted = []
        for msg in messages[-3:]:  # Last 3 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            formatted.append(f"[{role}]: {content}")
        
        return "\n".join(formatted) if formatted else "No recent messages available"


# Export
__all__ = ["FeedbackResponseTool"]
