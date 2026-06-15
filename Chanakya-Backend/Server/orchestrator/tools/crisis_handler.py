"""
Crisis Handler Tool
===================

Handles classroom management crises - noise, lack of focus, behavior issues.
Provides immediate, practical solutions.
"""

import json
import re
import time
from typing import Optional
from google import genai
from google.genai import types

from ..schemas import ActivityOutput


CRISIS_HANDLER_PROMPT = """You are an expert classroom management advisor for RURAL Indian schools.

Your task is to provide IMMEDIATE, PRACTICAL solutions for classroom crises.

=== TYPES OF CRISES ===
1. NOISE & CHAOS: Students talking loudly, not listening, general disorder
2. LOSS OF FOCUS: Students distracted, not paying attention, bored
3. DISRUPTIVE BEHAVIOR: Fighting, arguing, refusing to cooperate
4. LOW ENERGY: Students tired, sleepy, unmotivated
5. RESTLESSNESS: Students unable to sit still, fidgeting

=== SOLUTION REQUIREMENTS ===
- Must work INSTANTLY (1-2 minutes max)
- NO equipment needed (no projector, no electricity)
- Work in classrooms with 40-60 students
- Simple for teachers with basic training
- Culturally appropriate for rural India
- Can be done IN THE CLASSROOM (no need to go outside)

=== OUTPUT FORMAT ===
Return a JSON object with:
{
    "activity_name": "Quick catchy name",
    "description": "One-line description of the intervention",
    "materials_needed": ["Usually nothing or very basic items"],
    "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "duration_minutes": 2,
    "learning_outcome": "What this achieves (restore order, regain focus, calm energy)",
    "tips": ["Quick tips for effectiveness"]
}

=== EXAMPLES OF GOOD CRISIS INTERVENTIONS ===

EXAMPLE 1 - Noise Control:
{
    "activity_name": "Silent Signal Game",
    "description": "Teacher uses hand signals, students must copy silently",
    "materials_needed": ["Nothing"],
    "steps": [
        "Step 1: Teacher raises one hand high in the air and stays completely silent",
        "Step 2: Students who notice must stop talking and raise their hand too",
        "Step 3: Within 15 seconds, all hands should be up and room silent",
        "Step 4: Teacher gives thumbs up and quietly says 'Thank you, let's continue'",
        "Step 5: Resume lesson immediately while students are focused"
    ],
    "duration_minutes": 1,
    "learning_outcome": "Immediate silence and attention restoration without shouting",
    "tips": [
        "Practice this signal daily so students know it automatically",
        "Never speak while hand is raised - silence is the signal",
        "Praise students who respond quickly"
    ]
}

EXAMPLE 2 - Focus Recovery:
{
    "activity_name": "5-Second Body Reset",
    "description": "Quick physical movement to refresh attention",
    "materials_needed": ["Nothing"],
    "steps": [
        "Step 1: Teacher says 'Stand up everyone!' with enthusiasm",
        "Step 2: 'Touch your toes - 1, 2, 3!'",
        "Step 3: 'Reach for the sky - 1, 2, 3!'",
        "Step 4: 'Turn around once - go!'",
        "Step 5: 'Sit down quietly and eyes on me - NOW!'",
        "Step 6: Immediately start teaching while they're alert"
    ],
    "duration_minutes": 1,
    "learning_outcome": "Physical movement breaks monotony and restores alertness",
    "tips": [
        "Do this with high energy and quick pace",
        "End with students seated and focused",
        "Use when you see students zoning out"
    ]
}

EXAMPLE 3 - Restlessness Control:
{
    "activity_name": "Whisper Challenge",
    "description": "Switch to whisper mode to calm hyperactive energy",
    "materials_needed": ["Nothing"],
    "steps": [
        "Step 1: Teacher suddenly starts whispering very softly",
        "Step 2: Students must lean in and be completely quiet to hear",
        "Step 3: Ask a simple question in whisper voice",
        "Step 4: Students raise hands but answer in whispers only",
        "Step 5: Continue lesson in whisper mode for 2 minutes",
        "Step 6: Gradually return to normal speaking voice"
    ],
    "duration_minutes": 2,
    "learning_outcome": "Loud environment transforms to calm focus through voice control",
    "tips": [
        "The quieter you speak, the quieter students become",
        "Make it mysterious and fun",
        "Works instantly for over-excited classes"
    ]
}

EXAMPLE 4 - Behavior Reset:
{
    "activity_name": "Freeze Dance - Classroom Version",
    "description": "Quick game that gives control back to teacher",
    "materials_needed": ["Nothing"],
    "steps": [
        "Step 1: Teacher claps hands rhythmically",
        "Step 2: Students must copy the clapping pattern while standing",
        "Step 3: When teacher suddenly stops - EVERYONE MUST FREEZE",
        "Step 4: Anyone moving even slightly must sit down immediately",
        "Step 5: Frozen students win and sit down carefully",
        "Step 6: Resume lesson with energy redirected"
    ],
    "duration_minutes": 2,
    "learning_outcome": "Channels chaos into controlled fun, then back to learning",
    "tips": [
        "Keep it fast and exciting",
        "Praise students who freeze perfectly",
        "Don't drag it out - quick burst only"
    ]
}

EXAMPLE 5 - Low Energy Boost:
{
    "activity_name": "Power Clap Wake-Up",
    "description": "Energizing group activity using only clapping",
    "materials_needed": ["Nothing"],
    "steps": [
        "Step 1: Teacher says 'When I say GO, clap as loud as you can - ready?'",
        "Step 2: 'GO!' - everyone claps loudly 3 times together",
        "Step 3: 'Now clap softly!' - gentle clapping 3 times",
        "Step 4: 'Now clap SUPER loud!' - maximum energy 5 times",
        "Step 5: 'STOP! Hands down, eyes up!' - sudden focus",
        "Step 6: Start lesson immediately while energy is high"
    ],
    "duration_minutes": 1,
    "learning_outcome": "Group energy synchronized and attention captured",
    "tips": [
        "Use dramatic voice changes - loud to soft to loud",
        "End abruptly when energy peaks",
        "Perfect after lunch when students are drowsy"
    ]
}

=== RULES ===
- Solutions must be INSTANT (under 3 minutes)
- NO props, no preparation needed
- Works for 40-60 students in one room
- Teacher stays in control throughout
- Immediately transitions back to lesson
- NEVER suggest: videos, printed materials, complex setups, technology
- Steps must be ULTRA-SPECIFIC - exact words, exact actions

Return ONLY valid JSON."""


class CrisisHandlerTool:
    """
    Tool for handling classroom management crises.
    """
    
    name: str = "crisis_handler"
    description: str = "Provides immediate solutions for classroom management issues like noise, chaos, lack of focus, or disruptive behavior"
    
    def __init__(self, api_key: str):
        """
        Initialize the crisis handler with Gemini API.
        
        Args:
            api_key: Google AI API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
    
    async def run(self, crisis_description: str, context: Optional[dict] = None) -> ActivityOutput:
        """
        Generate immediate crisis intervention.
        
        Args:
            crisis_description: Description of the classroom crisis
            context: Optional context (grade level, subject, detected_language, etc.)
        
        Returns:
            ActivityOutput with the crisis intervention
        """
        start_time = time.time()
        
        # Detect target language from context
        target_lang = 'English'
        if context and context.get('detected_language'):
            target_lang = context['detected_language']
        
        # Build the prompt with context if provided
        context_str = ""
        if context:
            if context.get("grade"):
                context_str += f"\nGrade/Class: {context['grade']}"
            if context.get("subject"):
                context_str += f"\nSubject: {context['subject']}"
            if context.get("class_size"):
                context_str += f"\nClass size: {context['class_size']} students"
        
        user_prompt = f"Classroom crisis: {crisis_description}"
        if context_str:
            user_prompt += f"\n\nContext:{context_str}"
        
        user_prompt += "\n\nProvide an IMMEDIATE intervention that works in under 2 minutes. The teacher needs help RIGHT NOW."
        
        # Add language instruction if not English
        if target_lang != 'English':
            user_prompt += f"\n\nIMPORTANT: Generate the response in {target_lang} language. All text fields (activity_name, description, steps, tips, learning_outcome) must be in {target_lang}."
        
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
                    system_instruction=CRISIS_HANDLER_PROMPT,
                    temperature=0.8,
                    max_output_tokens=10000,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = response.text.strip()
            
            # Clean markdown if present
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Try to extract JSON if wrapped in other text
            json_match = re.search(r'\{[\s\S]*?\}(?=\s*$)', text, re.DOTALL)
            if json_match:
                text = json_match.group()
            
            # Additional safety: try to fix common JSON issues
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as json_err:
                # If JSON parsing fails, try to fix truncated strings
                brace_count = 0
                last_valid_pos = -1
                for i, char in enumerate(text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_valid_pos = i + 1
                
                if last_valid_pos > 0:
                    text = text[:last_valid_pos]
                    parsed = json.loads(text)
                else:
                    raise json_err
            
            return ActivityOutput(
                activity_name=parsed.get("activity_name", "Quick Intervention"),
                description=parsed.get("description", ""),
                materials_needed=parsed.get("materials_needed", []),
                steps=parsed.get("steps", []),
                duration_minutes=parsed.get("duration_minutes", 2),
                learning_outcome=parsed.get("learning_outcome", ""),
                tips=parsed.get("tips")
            )
            
        except Exception:
            # Simple fallback for crisis situations
            return ActivityOutput(
                activity_name="Silent Hand Signal",
                description="Quick attention grabber using hand signals",
                materials_needed=["Nothing"],
                steps=[
                    "Step 1: Raise your hand high and stay completely silent",
                    "Step 2: Students who see you must stop talking and raise their hand",
                    "Step 3: Wait 20 seconds for all hands to go up",
                    "Step 4: Give thumbs up and whisper 'Thank you'",
                    "Step 5: Resume lesson in a calm, quiet voice"
                ],
                duration_minutes=1,
                learning_outcome="Restore immediate silence and attention",
                tips=["Practice this signal daily for best results", "Make eye contact with students as they raise their hands"]
            )
    
    def run_sync(self, crisis_description: str, context: Optional[dict] = None) -> ActivityOutput:
        """Synchronous version of run()."""
        import asyncio
        return asyncio.run(self.run(crisis_description, context))
