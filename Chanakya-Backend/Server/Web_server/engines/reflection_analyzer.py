"""
Reflection Analyzer Engine

This engine analyzes class transcripts using LLM to generate
teaching feedback, student engagement insights, and improvement suggestions.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load .env from project root (Chanakya/)
_root_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=_root_dir / ".env")

# Try to import Google Generative AI, handle if not available
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-genai not installed. Using fallback analysis.")


async def analyze_class_transcript(
    transcript: str,
    topic: str,
    subject: str,
    class_level: str
) -> Dict[str, Any]:
    """
    Analyze a class transcript using AI to generate teaching feedback.
    
    Args:
        transcript: The text transcript of the class audio
        topic: The topic being taught
        subject: The subject name
        class_level: The class level (e.g., "Class 6")
    
    Returns:
        Dict containing strengths, issues, classroom_atmosphere, topic_feedback, suggestions
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # Debug logging
    print(f"GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")
    print(f"API Key present: {bool(api_key)}")
    
    # If no API key or Gemini not available, return enhanced fallback feedback
    if not api_key or not GEMINI_AVAILABLE:
        print("Using fallback feedback (AI unavailable)")
        return generate_smart_fallback(transcript, topic, subject, class_level)
    
    try:
        # Configure Gemini with new API
        client = genai.Client(api_key=api_key)
        
        prompt = f"""You are an expert teaching coach for Indian schools, analyzing a classroom transcript.

CLASS DETAILS:
- Class Level: {class_level}
- Subject: {subject}
- Topic: {topic}

TRANSCRIPT:
\"\"\"{transcript}\"\"\"

Analyze this teaching session thoroughly and provide constructive feedback.

EVALUATION CRITERIA:

1. **STRENGTHS** (2-4 points):
   - Clear explanations or definitions given
   - Good use of examples, analogies, or real-life connections
   - Effective questioning techniques
   - Appropriate pacing and structure
   - Student engagement attempts

2. **AREAS FOR IMPROVEMENT** (2-4 points):
   - Missing explanations or unclear concepts
   - Lack of student interaction
   - Pacing issues (too fast/slow)
   - Missing examples or visuals
   - No comprehension checks

3. **CLASSROOM ATMOSPHERE**:
   Choose ONE: "Very Active" | "Active" | "Balanced" | "Mostly Passive" | "Passive"
   Based on: student responses, questions asked, interaction patterns

4. **TOPIC-SPECIFIC FEEDBACK** (2-3 points):
   - What concepts were explained well for "{topic}"?
   - What important aspects of "{topic}" might have been missed?
   - Suggestions specific to teaching "{topic}" in {subject}

5. **ACTION ITEMS** (exactly 3):
   - CONTINUE: One specific thing the teacher did well to keep doing
   - IMPROVE: One specific area to work on immediately  
   - TRY NEXT TIME: One new technique or approach to experiment with

Return ONLY valid JSON (no markdown code blocks):
{{
    "strengths": ["specific strength 1", "specific strength 2"],
    "issues": ["specific issue 1", "specific issue 2"],
    "classroom_atmosphere": "one of the five options",
    "topic_feedback": ["topic-specific point 1", "topic-specific point 2"],
    "suggestions": [
        "CONTINUE: [specific action from the lesson]",
        "IMPROVE: [specific actionable improvement]",
        "TRY NEXT TIME: [specific new technique]"
    ]
}}

Be encouraging but honest. Give specific, actionable feedback based on the actual transcript content."""

        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt
        )
        content = response.text.strip()
        
        # Parse JSON response - handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
            if content.startswith("json"):
                content = content[4:].strip()
        
        feedback = json.loads(content)
        
        # Validate and normalize structure
        result = {
            "strengths": feedback.get("strengths", [])[:5],
            "issues": feedback.get("issues", [])[:5],
            "classroom_atmosphere": feedback.get("classroom_atmosphere", "Balanced"),
            "topic_feedback": feedback.get("topic_feedback", [])[:5],
            "suggestions": feedback.get("suggestions", [])[:3]
        }
        
        # Ensure we have at least 3 suggestions
        while len(result["suggestions"]) < 3:
            result["suggestions"].append("Review the lesson recording for additional insights")
        
        print("AI analysis successful")
        return result
        
    except Exception as e:
        print(f"AI analysis failed: {e}")
        return generate_smart_fallback(transcript, topic, subject, class_level)


def generate_smart_fallback(transcript: str, topic: str, subject: str, class_level: str) -> Dict[str, Any]:
    """
    Generate intelligent fallback feedback based on transcript analysis.
    Uses pattern matching and heuristics when AI is unavailable.
    """
    # Normalize transcript for analysis
    text = transcript.lower()
    words = transcript.split()
    word_count = len(words)
    sentences = re.split(r'[.!?]+', transcript)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Detect patterns
    has_questions = '?' in transcript
    question_count = transcript.count('?')
    has_examples = any(word in text for word in ['example', 'for instance', 'such as', 'like when', 'उदाहरण', 'जैसे'])
    has_definitions = any(word in text for word in ['means', 'is defined as', 'we call', 'is called', 'मतलब', 'कहते हैं'])
    has_student_check = any(phrase in text for phrase in ['understand', 'clear', 'any doubt', 'questions', 'समझ', 'doubt'])
    has_recap = any(word in text for word in ['summary', 'recap', 'learned today', 'revision', 'remember'])
    has_real_life = any(phrase in text for phrase in ['daily life', 'real life', 'around us', 'at home', 'in nature'])
    
    # Detect interaction patterns
    student_responses = len(re.findall(r'\b(yes|no|sir|ma\'am|teacher|correct|right)\b', text, re.I))
    teacher_prompts = len(re.findall(r'\b(tell me|what is|who can|raise hand|answer)\b', text, re.I))
    
    # Build strengths
    strengths: List[str] = []
    
    if word_count > 300:
        strengths.append(f"Delivered a comprehensive explanation ({word_count} words)")
    elif word_count > 100:
        strengths.append("Provided a focused, concise explanation")
    
    if has_definitions:
        strengths.append(f"Clearly defined key concepts related to {topic}")
    
    if has_examples:
        strengths.append("Used examples to illustrate concepts")
    
    if has_questions and question_count >= 2:
        strengths.append(f"Engaged students with {question_count} questions during the lesson")
    elif has_questions:
        strengths.append("Included questioning to check understanding")
    
    if has_student_check:
        strengths.append("Checked for student comprehension")
    
    if has_real_life:
        strengths.append("Connected concepts to real-life situations")
    
    if has_recap:
        strengths.append("Included a summary/recap of key points")
    
    if not strengths:
        strengths.append(f"Covered the topic '{topic}' in {subject}")
    
    # Build issues
    issues: List[str] = []
    
    if word_count < 100:
        issues.append("Lesson was very brief - consider providing more detailed explanations")
    elif word_count < 200:
        issues.append("Lesson could benefit from more elaboration on key concepts")
    
    if not has_questions:
        issues.append("No questions detected - try asking students questions to check understanding")
    
    if not has_examples:
        issues.append(f"Consider adding examples to explain {topic} more clearly")
    
    if not has_student_check:
        issues.append("Add comprehension checks like 'Is this clear?' or 'Any doubts?'")
    
    if not has_recap:
        issues.append("Consider ending with a quick recap of what was taught")
    
    if not has_real_life:
        issues.append(f"Connect {topic} to everyday situations students can relate to")
    
    if student_responses < 2 and teacher_prompts < 2:
        issues.append("Limited student-teacher interaction detected")
    
    if not issues:
        issues.append("Good lesson! Consider adding more interactive elements")
    
    # Determine atmosphere
    if student_responses >= 5 and question_count >= 3:
        atmosphere = "Active"
    elif student_responses >= 2 or question_count >= 2:
        atmosphere = "Balanced"
    elif question_count >= 1:
        atmosphere = "Mostly Passive"
    else:
        atmosphere = "Passive"
    
    # Topic-specific feedback
    topic_feedback: List[str] = []
    topic_feedback.append(f"Introduced students to {topic} in {subject}")
    
    if has_definitions:
        topic_feedback.append(f"Good: Provided definitions for {topic} concepts")
    else:
        topic_feedback.append(f"Consider: Start by defining what {topic} means")
    
    if has_examples:
        topic_feedback.append(f"Good: Used examples to explain {topic}")
    else:
        topic_feedback.append(f"Add: Include 2-3 examples related to {topic}")
    
    # Generate contextual suggestions
    suggestions: List[str] = []
    
    # CONTINUE suggestion
    if has_questions:
        suggestions.append("CONTINUE: Keep asking questions throughout the lesson - it keeps students engaged")
    elif has_definitions:
        suggestions.append("CONTINUE: Keep providing clear definitions - it builds strong foundations")
    elif has_examples:
        suggestions.append("CONTINUE: Keep using examples - they help students understand better")
    else:
        suggestions.append(f"CONTINUE: Teaching {topic} to {class_level} with dedication")
    
    # IMPROVE suggestion
    if not has_questions:
        suggestions.append("IMPROVE: Add 3-4 simple questions during the lesson to check understanding")
    elif not has_examples:
        suggestions.append(f"IMPROVE: Include real-world examples when explaining {topic}")
    elif not has_student_check:
        suggestions.append("IMPROVE: Pause after key points to ask 'Is everyone following?'")
    else:
        suggestions.append("IMPROVE: Encourage more student participation by calling on different students")
    
    # TRY NEXT TIME suggestion
    suggestions_pool = [
        f"TRY NEXT TIME: Start with a simple question about {topic} to activate prior knowledge",
        f"TRY NEXT TIME: Use a diagram or visual aid to explain {topic}",
        "TRY NEXT TIME: Have students explain the concept back to you in their own words",
        "TRY NEXT TIME: End with a 2-minute recap asking students what they learned",
        f"TRY NEXT TIME: Connect {topic} to something students see in daily life",
        "TRY NEXT TIME: Use a short story or analogy to make the concept memorable"
    ]
    
    # Pick a relevant suggestion
    if not has_real_life:
        suggestions.append(f"TRY NEXT TIME: Connect {topic} to something students see in daily life")
    elif not has_recap:
        suggestions.append("TRY NEXT TIME: End with a 2-minute recap asking students what they learned")
    else:
        suggestions.append(suggestions_pool[hash(topic) % len(suggestions_pool)])
    
    return {
        "strengths": strengths[:4],
        "issues": issues[:4],
        "classroom_atmosphere": atmosphere,
        "topic_feedback": topic_feedback[:3],
        "suggestions": suggestions[:3]
    }
