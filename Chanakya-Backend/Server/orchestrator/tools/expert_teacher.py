"""
Expert Teacher Tool
===================

Provides expert explanations for queries not covered in NCERT curriculum.
Acts as a knowledgeable teacher who can explain concepts, answer questions,
and provide educational guidance beyond the textbook content.
"""

import json
import structlog
from typing import Optional, Dict, Any
from google import genai
from google.genai import types

from .base import BaseTool
from ..schemas import ExpertTeacherOutput

logger = structlog.get_logger(__name__)


class ExpertTeacherTool(BaseTool):
    """
    Tool that acts as an expert teacher to answer educational queries
    not covered in NCERT textbooks or when additional context is needed.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/gemini-2.5-flash",
        temperature: float = 0.7,
    ):
        """
        Initialize the Expert Teacher Tool.
        
        Args:
            api_key: Google AI API key (if None, reads from GEMINI_API_KEY env var)
            model_name: Gemini model to use for generation
            temperature: Temperature for response generation (0.7 for balanced creativity)
        """
        if api_key is None:
            import os
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        
        logger.info("ExpertTeacherTool initialized")
    
    async def run(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Run method required by BaseTool.
        
        Args:
            query: Teacher's question
            context: Optional context
            
        Returns:
            Dictionary output
        """
        result = await self.execute(query, context)
        return result.model_dump() if hasattr(result, 'model_dump') else result
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpertTeacherOutput:
        """
        Generate expert teacher response for the query.
        
        Args:
            query: Teacher's question or topic to explain
            context: Optional context (grade level, subject, language, etc.)
            
        Returns:
            ExpertTeacherOutput with explanation and teaching suggestions
        """
        try:
            # Extract context parameters
            grade = context.get("grade", "middle school") if context else "middle school"
            subject = context.get("subject", "general") if context else "general"
            # Check detected_language first, then language, then default to English
            language = context.get("detected_language") or context.get("language", "English") if context else "English"
            
            logger.info(f"Expert teacher using language: {language} for query: {query[:50]}")
            
            # Build the expert teacher prompt
            prompt = self._build_expert_prompt(query, grade, subject, language)
            
            # Generate response using Gemini
            logger.info(f"Generating expert teacher response for: {query[:100]}...")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "explanation": {
                                "type": "string",
                                "description": "Clear, detailed explanation of the concept"
                            },
                            "key_points": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "3-5 key points to remember"
                            },
                            "teaching_tips": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "2-3 practical tips for teaching this"
                            },
                            "examples": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "1-2 real-world examples or analogies"
                            },
                            "common_misconceptions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Common student misconceptions to watch for"
                            },
                            "follow_up_questions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Questions to check student understanding"
                            }
                        },
                        "required": ["explanation", "key_points", "teaching_tips"]
                    }
                )
            )
            
            # Parse JSON response
            result = json.loads(response.text)
            
            # Log success
            logger.info("Expert teacher response generated successfully")
            
            # Return structured output
            return ExpertTeacherOutput(
                query=query,
                explanation=result.get("explanation", ""),
                key_points=result.get("key_points", []),
                teaching_tips=result.get("teaching_tips", []),
                examples=result.get("examples", []),
                common_misconceptions=result.get("common_misconceptions", []),
                follow_up_questions=result.get("follow_up_questions", []),
                grade_level=grade,
                subject=subject,
                confidence=0.85  # General expert knowledge confidence
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in expert teacher: {e}")
            logger.error(f"Response text: {response.text[:500]}")
            # Return a basic response
            return ExpertTeacherOutput(
                query=query,
                explanation=f"I apologize, but I encountered an error processing your question about '{query}'. Please try rephrasing your question.",
                key_points=["Unable to generate response"],
                teaching_tips=["Please try again with a rephrased question"],
                examples=[],
                common_misconceptions=[],
                follow_up_questions=[],
                grade_level=grade,
                subject=subject,
                confidence=0.1
            )
        except Exception as e:
            logger.error(f"Error in expert teacher generation: {e}", exc_info=True)
            # Return a fallback response instead of raising
            return ExpertTeacherOutput(
                query=query,
                explanation=f"I apologize, but I encountered an error: {str(e)}",
                key_points=["Error occurred"],
                teaching_tips=["Please try again"],
                examples=[],
                common_misconceptions=[],
                follow_up_questions=[],
                grade_level=grade,
                subject=subject,
                confidence=0.1
            )
    
    def _build_expert_prompt(
        self,
        query: str,
        grade: str,
        subject: str,
        language: str
    ) -> str:
        """
        Build the expert teacher prompt for Gemini.
        
        Args:
            query: The question or topic
            grade: Grade level context
            subject: Subject context
            language: Preferred language
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert teacher with deep knowledge across all subjects. A teacher has asked you a question that may not be covered in standard textbooks.

TEACHER'S QUESTION: {query}

CONTEXT:
- Grade Level: {grade}
- Subject: {subject}
- **REQUIRED RESPONSE LANGUAGE: {language}**

=== CRITICAL: LANGUAGE REQUIREMENT ===
YOU MUST RESPOND EXACTLY IN: {language}

**IF {language} is "Hindi":**
- Write ONLY in Devanagari script: न, म, त, ग, ण, व, र, क, etc.
- DO NOT use Roman/Latin script
- DO NOT use Hinglish
- Example: "वृत्त एक ज्यामितीय आकृति है जो एक निश्चित बिंदु से समान दूरी पर स्थित सभी बिंदुओं का समुच्चय होता है।"

**IF {language} is "Hinglish":**
- Mix Hindi words in Roman script with English
- Use: hai, hota, mein, ka, ke, ko, aur, yeh, ek, kya, etc.
- Example: "Circle ek geometric shape hai jo ek fixed point se equal distance par sabhi points ka collection hota hai."

**IF {language} is "English":**
- Use pure English only
- Example: "A circle is a geometric shape defined as the set of all points equidistant from a fixed center point."

IMPORTANT: {language} = Hindi means DEVANAGARI SCRIPT ONLY. If you write "hai" or "hota" in Roman script, you are writing HINGLISH, not HINDI.

YOUR TASK:
Provide a comprehensive, accurate, and pedagogically sound explanation IN {language} that helps the teacher understand and teach this concept effectively.

GUIDELINES:
1. **RESPOND IN {language}** - Use the correct script!
2. **Accuracy First**: Provide scientifically/academically accurate information
3. **Clear Explanation**: Use simple language appropriate for teachers
4. **Practical Focus**: Include practical teaching tips and real-world examples
5. **Student Perspective**: Anticipate common misconceptions students might have
6. **Engaging**: Make it interesting and relatable
7. **Age-Appropriate**: Consider the grade level in your explanation
8. **Cultural Context**: Consider Indian classroom context and examples

RESPONSE STRUCTURE (ALL IN {language}):
- explanation: A clear, detailed explanation (200-300 words) IN {language}
- key_points: 3-5 bullet points IN {language}
- teaching_tips: 2-3 practical tips IN {language}
- examples: 1-2 real-world examples IN {language}
- common_misconceptions: Common errors IN {language}
- follow_up_questions: Questions IN {language}

=== FINAL REMINDER: If language is "Hindi", use देवनागरी लिपि (Devanagari script) ONLY ==="""

    def validate(self, output: ExpertTeacherOutput) -> bool:
        """
        Validate the expert teacher output.
        
        Args:
            output: The generated output to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not output.explanation or len(output.explanation) < 50:
            logger.warning("Explanation too short or missing")
            return False
        
        if not output.key_points or len(output.key_points) < 2:
            logger.warning("Insufficient key points")
            return False
        
        if not output.teaching_tips or len(output.teaching_tips) < 1:
            logger.warning("No teaching tips provided")
            return False
        
        logger.info("Expert teacher output validation passed")
        return True
