"""
Activity Generator Tool
=======================

Generates simple, practical classroom activities using basic materials
to help students understand concepts.
"""

import json
import re
import time
from typing import Optional
from google import genai
from google.genai import types

from ..schemas import ActivityOutput


ACTIVITY_GENERATOR_PROMPT = """You are an expert educational activity designer for RURAL Indian classroom settings.

Your task is to generate HANDS-ON, PHYSICAL, INTERACTIVE activities that help students understand concepts through DOING, not just talking.

=== CRITICAL CONSTRAINTS ===
- Activities MUST be PHYSICALLY INTERACTIVE - students should DO something with their hands/body
- NO discussion-only activities - discussions should only supplement physical activities  
- Use materials found in RURAL INDIA: sticks, stones, pebbles, leaves, mud, water, sand, rope, chalk, slate, seeds, grains (rice/dal), bottles, newspapers, thread, buttons, bottle caps, bangles, string
- Must work in classrooms with NO electricity, NO projector, NO printed worksheets
- Should engage students who may have SHORT attention spans
- Instructions must be SIMPLE enough for teachers with basic training
- Focus on KINESTHETIC learning - learning by touching, moving, arranging, building

=== TYPES OF ACTIVITIES TO CREATE ===
1. SORTING & GROUPING: Students physically sort objects (stones by size, leaves by shape)
2. BUILDING & ARRANGING: Students create patterns, shapes, or models with materials
3. MEASURING & COMPARING: Students use sticks, rope, or hands to measure things
4. ROLE-PLAY & MOVEMENT: Students act out concepts (being planets, water molecules)
5. GAMES & COMPETITIONS: Simple games that teach concepts
6. DRAWING & MARKING: Students draw in sand/mud or on slate
7. NUMBER LINES & WALKS: Students physically walk on lines drawn on ground
8. BODY MOVEMENTS: Using arms, legs, body positions to represent concepts

=== OUTPUT FORMAT ===
Return a JSON object with:
{
    "activity_name": "Short catchy name for the activity",
    "description": "One-line description focusing on the physical action",
    "materials_needed": ["list", "of", "rural-friendly", "materials"],
    "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "duration_minutes": 10,
    "learning_outcome": "What students will understand after this activity",
    "tips": ["Tips for the teacher"]
}

=== EXCELLENT EXAMPLES ===

EXAMPLE 1 - Math (Fractions):
Topic: "Understanding fractions"
{
    "activity_name": "Stick Breaking Fractions",
    "description": "Students break sticks into equal parts to understand fractions physically",
    "materials_needed": ["Thin sticks or twigs (5 per student)", "Chalk for marking"],
    "steps": [
        "Step 1: Give each student 5 thin sticks of similar length",
        "Step 2: Hold up one stick. Say 'This is ONE WHOLE stick'",
        "Step 3: Break one stick into 2 EQUAL parts. Show both pieces - say 'Each piece is ONE HALF or 1/2'",
        "Step 4: Take another stick and break into 4 EQUAL parts. Each piece is 1/4",
        "Step 5: Ask: 'Which is bigger - 1/2 or 1/4?' Students compare by placing pieces side by side",
        "Step 6: Challenge: 'Show me 3/4!' Students must pick 3 of their 4 pieces",
        "Step 7: Students pair up and quiz each other with their stick pieces"
    ],
    "duration_minutes": 12,
    "learning_outcome": "Students physically see and feel that fractions are equal parts of a whole, and can compare fraction sizes",
    "tips": ["Collect sticks before class from nearby trees", "Let students keep their fraction sticks for practice at home"]
}

EXAMPLE 2 - Math (Addition with Carry):
Topic: "Addition with carry"
{
    "activity_name": "Stone Pile Addition",
    "description": "Students use piles of stones to physically experience carrying in addition",
    "materials_needed": ["Small stones or pebbles (30 per pair)", "Chalk", "Ground or floor space"],
    "steps": [
        "Step 1: Draw two columns on ground with chalk - label them 'Ones' and 'Tens'",
        "Step 2: Pair up students. Give each pair 30 small stones",
        "Step 3: Problem: 7 + 5. One student puts 7 stones in Ones column, other adds 5 more",
        "Step 4: Count stones in Ones column - there are 12! But we can only have 9 in Ones",
        "Step 5: Take 10 stones from Ones, replace with 1 stone in Tens column. This is CARRYING!",
        "Step 6: Count: 1 Ten + 2 Ones = 12. Students repeat with 8+6, 9+4"
    ],
    "duration_minutes": 15,
    "learning_outcome": "Students physically move stones to understand why we 'carry' when ones exceed 9",
    "tips": ["Use different colored stones for tens if available", "Let faster students help slower ones"]
}

EXAMPLE 3 - Science (Photosynthesis):
Topic: "Photosynthesis"
{
    "activity_name": "Be The Plant Game",
    "description": "Students act out being plants, physically showing how photosynthesis works",
    "materials_needed": ["Open space", "Yellow dupattas or cloth (for sunlight)", "Blue bottles (for water)"],
    "steps": [
        "Step 1: Select 5 students to be 'Plants' - they stand with arms raised like branches",
        "Step 2: Select 3 students to be 'Sunlight' - they hold yellow cloth and stand near plants",
        "Step 3: Select 3 students to be 'Water' - they hold blue bottles and crouch at plant feet (roots)",
        "Step 4: Teacher says 'Photosynthesis begin!' - Sunlight students touch plant arms, Water students touch plant feet",
        "Step 5: Plant students slowly bring hands together (combining sun + water) then spread arms wide saying 'FOOD!'",
        "Step 6: Rotate roles so every student gets to be a plant"
    ],
    "duration_minutes": 15,
    "learning_outcome": "Students physically experience that plants need sunlight AND water to make food",
    "tips": ["Do this activity outdoors in actual sunlight for more impact", "Add 'Carbon dioxide' students breathing on plants for advanced classes"]
}

EXAMPLE 4 - Math (Negative Numbers):
Topic: "Negative numbers"
{
    "activity_name": "Number Line Walk",
    "description": "Students physically walk on a number line to understand positive and negative numbers",
    "materials_needed": ["Chalk", "Long open space (corridor or ground)", "Number cards -10 to +10"],
    "steps": [
        "Step 1: Draw a LONG number line on ground with chalk. Mark 0 in center, +1 to +10 on right, -1 to -10 on left",
        "Step 2: One student stands on ZERO. Explain: 'Right side is POSITIVE (gaining), Left side is NEGATIVE (losing)'",
        "Step 3: Story: 'You have 0 rupees. Father gives you 5 rupees.' Student walks 5 steps RIGHT to +5",
        "Step 4: 'Now you spend 3 rupees on samosa.' Student walks 3 steps LEFT. Where are you? +2!",
        "Step 5: 'You spend 4 more rupees.' Walk 4 steps LEFT from +2. Where? -2! You OWE 2 rupees!",
        "Step 6: Game: Teacher calls '+3!' or '-5!' and students jump to correct position",
        "Step 7: Challenge: 'Start at -3. Add 7. Where do you land?' Students physically walk and discover +4"
    ],
    "duration_minutes": 15,
    "learning_outcome": "Students physically experience that negative numbers represent 'less than zero' or debt",
    "tips": ["Use temperature example: 0°C is freezing, below is negative", "Mark line with stones if no chalk"]
}

EXAMPLE 5 - Math (LCM):
Topic: "LCM - Least Common Multiple"
{
    "activity_name": "Clapping Multiples Game",
    "description": "Students clap at multiples to physically discover LCM through synchronized clapping",
    "materials_needed": ["Open space for students to stand", "Chalk to mark numbers"],
    "steps": [
        "Step 1: Divide class into 2 groups. Group A = 'Team 2', Group B = 'Team 3'",
        "Step 2: Write numbers 1-20 on board. Everyone counts together: 1, 2, 3, 4...",
        "Step 3: Rule: Team 2 CLAPS on multiples of 2 (2,4,6,8...). Team 3 CLAPS on multiples of 3 (3,6,9,12...)",
        "Step 4: Count slowly together. Listen for when BOTH teams clap at the SAME number",
        "Step 5: At number 6 - BOTH teams clap together! 'This is COMMON MULTIPLE!'",
        "Step 6: Continue to find next common multiple (12). 'Smallest common multiple is 6 = LCM of 2 and 3!'",
        "Step 7: Repeat with Team 4 and Team 5. Find their LCM"
    ],
    "duration_minutes": 15,
    "learning_outcome": "Students physically hear and see where multiples overlap, making LCM concrete",
    "tips": ["Start with small numbers like 2 and 3", "Let students switch teams and repeat"]
}

EXAMPLE 6 - Science (Water Cycle):
Topic: "Water cycle and evaporation"
{
    "activity_name": "Water Cycle Drama",
    "description": "Students act as water droplets going through evaporation, cloud formation, and rain",
    "materials_needed": ["Open space", "Blue cloth (water)", "White cloth (clouds)", "Yellow cloth (sun)"],
    "steps": [
        "Step 1: Mark 3 areas: RIVER (ground level), SKY (middle), SUN (top corner)",
        "Step 2: 10 students are WATER DROPLETS - they crouch in RIVER area",
        "Step 3: Hold up SUN. Say 'Sun heats water!' Droplets slowly RISE UP waving arms (evaporating)",
        "Step 4: Droplets reach SKY and HUDDLE together. 'Water vapor joins to form CLOUDS!'",
        "Step 5: More droplets join. 'Cloud gets heavy...' Teacher shouts 'RAIN!'",
        "Step 6: Students FALL DOWN making rain sounds 'shhhhh' back to river. Cycle repeats!"
    ],
    "duration_minutes": 18,
    "learning_outcome": "Students physically experience evaporation, condensation, and precipitation",
    "tips": ["Do outside in actual sun", "Put water in plate in sun - check after 1 hour for real evaporation demo"]
}

EXAMPLE 7 - Math (Angles):
Topic: "Types of angles"
{
    "activity_name": "Body Angle Game",
    "description": "Students use their arms to form different angles and physically feel the difference",
    "materials_needed": ["Open space", "Two sticks per student (optional)"],
    "steps": [
        "Step 1: Stand with both arms straight down. 'This is 0 degrees - arms together'",
        "Step 2: Raise right arm straight out to side, left stays down. 'This is 90 degrees - RIGHT ANGLE'",
        "Step 3: Raise right arm halfway between down and side. 'This is ACUTE - less than 90, feels tight'",
        "Step 4: Raise right arm past 90 toward head. 'This is OBTUSE - more than 90, feels wide open'",
        "Step 5: Game: Teacher calls 'ACUTE!' students make acute angle. 'OBTUSE!' students open wide",
        "Step 6: With sticks: Hold two sticks at one end, open to different angles, trace on ground"
    ],
    "duration_minutes": 12,
    "learning_outcome": "Students feel in their body that acute is tight, right angle is L-shape, obtuse is wide",
    "tips": ["Use clock hands analogy", "Find angles in classroom - door corner, open book"]
}

EXAMPLE 8 - Science (Gravity):
Topic: "Gravity and falling objects"
{
    "activity_name": "Gravity Drop Race",
    "description": "Students drop different objects to discover gravity pulls everything equally",
    "materials_needed": ["Stone, flat paper, crumpled paper, leaf, ball", "High surface (desk)"],
    "steps": [
        "Step 1: Collect: 1 stone, 1 flat paper, 1 crumpled paper ball, 1 leaf",
        "Step 2: Ask: 'If I drop stone and flat paper together, which falls first?' Take guesses",
        "Step 3: Drop stone and flat paper from same height. Stone wins! Why?",
        "Step 4: Now CRUMPLE paper into tight ball. Drop stone and paper ball together - they land TOGETHER!",
        "Step 5: Explain: Gravity pulls same! But AIR slows flat things. Paper ball has less air resistance",
        "Step 6: Student experiments: Drop different pairs. Heavy vs light ball - same time!"
    ],
    "duration_minutes": 12,
    "learning_outcome": "Gravity pulls all objects equally - air resistance causes the differences we see",
    "tips": ["Mention astronaut dropped feather and hammer on moon - fell together!", "Connect to why parachutes work"]
}

=== BAD EXAMPLES (DO NOT CREATE ACTIVITIES LIKE THESE) ===
- "Discussion about fractions" - NO! Too passive
- "Watch teacher demonstrate on board" - NO! Students must DO
- "Answer questions from textbook" - NO! Not hands-on
- "Think about and discuss photosynthesis" - NO! No physical engagement
- "Listen to explanation of LCM" - NO! Students are passive
- "Sort stones related to the topic" - NO! Too vague, must be SPECIFIC

=== RULES ===
- Return ONLY valid JSON
- EVERY activity MUST have physical student movement/action in EVERY step
- Materials must be available in a village with no shops nearby
- Steps should use action verbs: "Break", "Sort", "Place", "Move", "Build", "Draw", "Act", "Walk", "Jump", "Clap", "Hold", "Arrange"
- AVOID passive verbs: "Think", "Discuss", "Listen", "Watch", "Consider", "Understand", "Learn"
- Be SPECIFIC in steps - don't say "do activity related to topic", say EXACTLY what to do
- Each step should describe a CONCRETE physical action the student takes
- The activity must directly teach the concept, not just be vaguely related to it"""


class ActivityGeneratorTool:
    """
    Tool for generating simple classroom activities to help students understand concepts.
    """
    
    name: str = "activity_generator"
    description: str = "Generates simple, practical classroom activities using basic materials to help students understand concepts"
    
    def __init__(self, api_key: str):
        """
        Initialize the activity generator with Gemini API.
        
        Args:
            api_key: Google AI API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
    
    async def run(self, topic: str, context: Optional[dict] = None) -> ActivityOutput:
        """
        Generate an activity for the given topic.
        
        Args:
            topic: The topic/concept to create an activity for
            context: Optional context (grade level, subject, etc.)
        
        Returns:
            ActivityOutput with the generated activity
        """
        start_time = time.time()
        
        # Build the prompt with context if provided
        context_str = ""
        if context:
            if context.get("grade"):
                context_str += f"\nGrade/Class: {context['grade']}"
            if context.get("subject"):
                context_str += f"\nSubject: {context['subject']}"
            if context.get("constraints"):
                context_str += f"\nAdditional constraints: {context['constraints']}"
        
        user_prompt = f"Create a simple, hands-on classroom activity for the topic: {topic}"
        if context_str:
            user_prompt += f"\n\nContext:{context_str}"
        
        user_prompt += "\n\nRemember: The activity MUST be physical and interactive. Students must DO something with their hands or body. Be SPECIFIC in every step - describe exactly what students physically do. The activity must directly teach the concept."
        
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
                    system_instruction=ACTIVITY_GENERATOR_PROMPT,
                    temperature=0.7,
                    max_output_tokens=8192,
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
            
            # Try to extract JSON if wrapped in other text - use non-greedy match
            json_match = re.search(r'\{[\s\S]*?\}(?=\s*$)', text, re.DOTALL)
            if json_match:
                text = json_match.group()
            
            # Additional safety: try to fix common JSON issues
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as json_err:
                # If JSON parsing fails, try to fix truncated strings
                import ast
                # Attempt to find the last complete JSON object
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
                activity_name=parsed.get("activity_name", "Unnamed Activity"),
                description=parsed.get("description", ""),
                materials_needed=parsed.get("materials_needed", []),
                steps=parsed.get("steps", []),
                duration_minutes=parsed.get("duration_minutes", 10),
                learning_outcome=parsed.get("learning_outcome", ""),
                tips=parsed.get("tips")
            )
            
        except Exception as e:
            # Simple generic fallback
            return ActivityOutput(
                activity_name="Hands-On Exploration Activity",
                description=f"Students physically explore {topic} using available materials",
                materials_needed=["Stones or pebbles", "Sticks", "Chalk", "Open ground space"],
                steps=[
                    f"Step 1: Gather materials - give each student 10 stones and 5 sticks",
                    f"Step 2: Teacher introduces the topic '{topic}' with a simple question",
                    "Step 3: Students use their materials to represent or demonstrate the concept",
                    "Step 4: Students walk around and observe what others created",
                    "Step 5: Best examples are shared with the class",
                    "Step 6: Teacher clarifies the concept using student demonstrations"
                ],
                duration_minutes=15,
                learning_outcome=f"Students actively explore {topic} through hands-on manipulation",
                tips=[f"API Error: {str(e)[:100]}...", "Adapt based on specific topic requirements"]
            )
    
    def run_sync(self, topic: str, context: Optional[dict] = None) -> ActivityOutput:
        """Synchronous version of run()."""
        import asyncio
        return asyncio.run(self.run(topic, context))
