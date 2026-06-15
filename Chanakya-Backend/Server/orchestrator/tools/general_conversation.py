"""
General Conversation Tool
==========================

Handles simple queries, greetings, thank you messages, clarification requests,
and out-of-scope questions.
"""

from typing import Dict, Any, Optional
from google import genai
from google.genai import types


class GeneralConversationTool:
    """
    Tool for handling general conversation that doesn't require specialized tools.
    
    Handles:
    - Greetings (hi, hello, good morning, etc.)
    - Gratitude (thank you, thanks, etc.)
    - Clarification requests (what do you mean, can you explain, etc.)
    - Out-of-scope questions (non-educational queries)
    - Unclear/ambiguous queries
    """
    
    def __init__(self, api_key: str):
        """Initialize the general conversation tool."""
        self.client = genai.Client(api_key=api_key)
        self.model_name = "models/gemini-2.5-flash"
    
    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle general conversation queries.
        
        Args:
            query: The user's query
            context: Optional context (e.g., detected_language)
        
        Returns:
            Dict with response and conversation type
        """
        context = context or {}
        detected_language = context.get('detected_language', 'en')
        
        # Prepare prompt for general conversation handling
        prompt = f"""You are Chanakya, an AI assistant for teachers in India.

Your purpose is to help teachers with:
- Classroom management
- Teaching strategies
- Educational content
- Student engagement
- Teacher wellbeing

CURRENT QUERY: "{query}"

ANALYZE THE QUERY AND RESPOND APPROPRIATELY:

1. **If it's a GREETING** (hi, hello, good morning, etc.):
   - Respond warmly and ask how you can help with their teaching today
   - Keep it brief and friendly
   
2. **If it's GRATITUDE** (thank you, thanks, etc.):
   - Acknowledge gracefully
   - Offer to help with anything else
   - Keep it brief
   
3. **If it's a CLARIFICATION REQUEST** (what do you mean, explain more, etc.):
   - Ask them to be more specific about what they need help with
   - Provide examples of what you can help with
   
4. **If it's OUT OF SCOPE** (non-educational, personal questions, unrelated topics):
   - Politely explain that you're designed to help with teaching and classroom matters
   - Redirect them to educational topics
   - Offer examples of what you can help with
   
5. **If it's UNCLEAR/AMBIGUOUS**:
   - Ask for clarification
   - Provide examples of typical queries you handle

RESPOND IN JSON FORMAT:
{{
    "response_type": "greeting" | "gratitude" | "clarification" | "out_of_scope" | "unclear",
    "response": "Your friendly, helpful response here",
    "suggested_topics": ["topic1", "topic2", "topic3"]  // Optional suggestions
}}

EXAMPLES:

Query: "Hi"
Response: {{"response_type": "greeting", "response": "Hello! I'm Chanakya, your classroom companion. How can I help you with your teaching today?", "suggested_topics": ["classroom management", "activity ideas", "teaching strategies"]}}

Query: "Thank you so much!"
Response: {{"response_type": "gratitude", "response": "You're very welcome! Happy to help. Let me know if you need anything else for your classroom.", "suggested_topics": []}}

Query: "What's the weather today?"
Response: {{"response_type": "out_of_scope", "response": "I'm designed to help with teaching and classroom matters. I can assist you with lesson planning, classroom management, activity ideas, or educational content. What would you like help with?", "suggested_topics": ["create an activity", "classroom tips", "explain a concept"]}}

Query: "I need help"
Response: {{"response_type": "unclear", "response": "I'd be happy to help! Could you tell me more about what you need? For example, I can help you with: creating activities, managing classroom situations, explaining concepts, or providing teaching strategies.", "suggested_topics": ["activity generator", "classroom guidance", "content explanation"]}}

Return ONLY valid JSON. Keep responses warm, professional, and teacher-focused."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                )
            )
            
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            import json
            result = json.loads(result_text)
            
            # Translate response if needed
            if detected_language != 'en':
                from ..orchestrator import ChanakyaOrchestrator
                # Simple translation helper (you may want to implement this properly)
                # For now, keep English responses
                pass
            
            return {
                "response_type": result.get("response_type", "general"),
                "response": result.get("response"),
                "suggested_topics": result.get("suggested_topics", []),
                "is_conversation": True
            }
            
        except Exception as e:
            # Fallback response
            return {
                "response_type": "general",
                "response": "I'm here to help you with your teaching! What would you like assistance with today?",
                "suggested_topics": ["classroom management", "teaching activities", "content explanations"],
                "is_conversation": True,
                "error": str(e)
            }
