"""
Teacher Motivation Tool
=======================

Provides motivation, tips, and recovery strategies for teachers experiencing burnout,
stress, or lack of motivation.
"""

import json
import re
import time
from typing import Optional
from google import genai
from google.genai import types

from .base import BaseTool


TEACHER_MOTIVATION_PROMPT = """You are an empathetic mentor and coach for teachers, especially those in RURAL Indian schools.

Your task is to provide PRACTICAL, COMPASSIONATE support for teachers experiencing burnout, stress, or lack of motivation.

=== COMMON TEACHER CHALLENGES ===
1. BURNOUT: Feeling exhausted, overwhelmed, emotionally drained
2. LACK OF RECOGNITION: Feeling undervalued, unappreciated
3. DIFFICULT STUDENTS: Behavior problems, lack of respect
4. RESOURCE CONSTRAINTS: No materials, poor infrastructure
5. WORKLOAD STRESS: Too many responsibilities, paperwork
6. ISOLATION: Feeling alone, no support system
7. SELF-DOUBT: Questioning effectiveness, losing confidence
8. WORK-LIFE BALANCE: No time for family, personal life suffering

=== SUPPORT REQUIREMENTS ===
- PRACTICAL tips that work in rural Indian context
- NO expensive solutions (spa days, therapy sessions)
- Acknowledge their hard work and dedication
- Culturally appropriate for Indian teachers
- Quick wins (things they can do TODAY)
- Long-term strategies for sustainable teaching

=== OUTPUT FORMAT ===
Return a JSON object with these exact keys:
- motivation_title: Uplifting title that addresses their situation
- acknowledgment: Empathetic statement recognizing their struggle
- immediate_tips: Array of 3-5 quick actions they can take TODAY
- long_term_strategies: Array of 3-5 sustainable practices for ongoing wellbeing
- inspiration: Powerful reminder of why teaching matters
- self_care_practices: Array of simple self-care activities requiring no money/resources
- perspective_shifts: Array of mental reframes to help them see situations differently

=== IMPORTANT GUIDELINES ===
1. Always start with validation and empathy - acknowledge their pain
2. Provide BOTH immediate relief (today) and long-term sustainability
3. Keep it practical - no expensive solutions or unrealistic suggestions
4. Be culturally sensitive to Indian teaching context
5. Maintain hopeful, encouraging tone without toxic positivity
6. Remind them of their purpose and impact
7. Normalize their struggles - they're not alone or failing

Teacher's Query: {query}

Additional Context: {context}

Generate a comprehensive, empathetic response following the output format above.
Return ONLY valid JSON, no other text.
"""


class TeacherMotivationTool(BaseTool):
    """
    Tool for providing motivation and burnout recovery support to teachers.
    """
    
    name = "teacher_motivation"
    description = "Provides motivation, tips, and recovery strategies for teachers experiencing burnout or lack of motivation"
    
    def __init__(self, api_key: str):
        """Initialize with Google API key."""
        self.client = genai.Client(api_key=api_key)
        self.model_name = "models/gemini-2.5-flash"
    
    async def run(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Generate motivational support for teachers.
        
        Args:
            query: Teacher's concern or situation
            context: Optional context about the teacher or situation
        
        Returns:
            Dictionary with motivation, tips, strategies, and inspiration
        """
        context_str = json.dumps(context, indent=2) if context else "No additional context"
        
        prompt = TEACHER_MOTIVATION_PROMPT.format(
            query=query,
            context=context_str
        )
        
        # Call Gemini
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,  # Slightly higher for more empathetic, varied responses
                max_output_tokens=3000,
                response_mime_type="application/json"
            )
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Clean up response (remove markdown, extra formatting)
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            # Fallback: return structured error
            return {
                "motivation_title": "Support Available for You",
                "acknowledgment": "Teaching is challenging, and your feelings are valid.",
                "immediate_tips": [
                    "Take a few deep breaths right now",
                    "Write down one positive moment from today",
                    "Reach out to a colleague or friend for support"
                ],
                "long_term_strategies": [
                    "Set small boundaries to protect your time",
                    "Connect with other teachers for mutual support",
                    "Remember your 'why' - the reason you started teaching"
                ],
                "inspiration": "You are making a difference, even when it's hard to see. Your dedication matters.",
                "self_care_practices": [
                    "Take short breaks during the day",
                    "Get enough sleep",
                    "Do something you enjoy outside of teaching"
                ],
                "perspective_shifts": [
                    "Progress over perfection",
                    "Your worth isn't measured by student behavior",
                    "It's okay to not be okay sometimes"
                ]
            }
