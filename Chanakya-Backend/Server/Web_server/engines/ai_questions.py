"""
AI Question Generation Engine

This engine generates questions for topics using LLM APIs.
Supports Google Gemini models.
"""

import os
import json
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Try to import Google Generative AI, handle if not available
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


async def generate_questions_for_topic(
    topic: str,
    subject: str,
    easy_count: int = 3,
    medium_count: int = 3,
    hard_count: int = 3
) -> Dict[str, List[str]]:
    """
    Generate questions for a topic using AI.
    Returns dict with easy, medium, hard question lists.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # If no API key or Gemini not available, return sample questions
    if not api_key or not GEMINI_AVAILABLE:
        return generate_fallback_questions(topic, subject, easy_count, medium_count, hard_count)
    
    try:
        # Configure Gemini with new API
        client = genai.Client(api_key=api_key)
        
        prompt = f"""Generate classroom questions for teaching {subject}, specifically about the topic: "{topic}"

Create questions suitable for rural Indian students. Make them simple, clear, and in Language of the topic.

Generate exactly:
- {easy_count} EASY questions (recall, basic understanding)
- {medium_count} MEDIUM questions (application, comparison)
- {hard_count} HARD questions (analysis, explanation)

Return ONLY a JSON object in this exact format (no markdown, no code blocks):
{{
    "easy": ["question1", "question2", ...],
    "medium": ["question1", "question2", ...],
    "hard": ["question1", "question2", ...]
}}

Do not include any other text, just the JSON."""

        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt
        )
        content = response.text.strip()
        
        # Parse JSON response
        # Handle potential markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (``` markers)
            content = "\n".join(lines[1:-1])
            if content.startswith("json"):
                content = content[4:].strip()
        
        questions = json.loads(content)
        
        # Validate structure
        result = {
            "easy": questions.get("easy", [])[:easy_count],
            "medium": questions.get("medium", [])[:medium_count],
            "hard": questions.get("hard", [])[:hard_count]
        }
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"AI generation failed: {error_msg}")
        
        # If rate limited, inform user
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            print("Note: API rate limit reached. Using fallback questions. Please try again in a few moments.")
        
        return generate_fallback_questions(topic, subject, easy_count, medium_count, hard_count)


def generate_fallback_questions(
    topic: str,
    subject: str,
    easy_count: int,
    medium_count: int,
    hard_count: int
) -> Dict[str, List[str]]:
    """
    Generate template-based fallback questions when AI is unavailable.
    """
    easy_templates = [
        f"What is {topic}?",
        f"Give one example of {topic}.",
        f"Name the main parts of {topic}.",
        f"Where do we see {topic} in daily life?",
        f"Who discovered/invented {topic}?",
    ]
    
    medium_templates = [
        f"Explain how {topic} works.",
        f"What is the difference between {topic} and its opposite?",
        f"Why is {topic} important in {subject}?",
        f"List three characteristics of {topic}.",
        f"How is {topic} used in real life?",
    ]
    
    hard_templates = [
        f"Analyze the impact of {topic} on society.",
        f"Compare and contrast {topic} with a related concept.",
        f"What would happen if {topic} didn't exist?",
        f"Explain the scientific principle behind {topic}.",
        f"How has our understanding of {topic} changed over time?",
    ]
    
    return {
        "easy": easy_templates[:easy_count],
        "medium": medium_templates[:medium_count],
        "hard": hard_templates[:hard_count]
    }
