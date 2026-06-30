"""
Lesson Generator
================

Generates structured 8-slide lessons from textbook content using Gemini.
Includes hallucination validation and regeneration logic.
"""

import json
import re
import time
import logging
import os
from typing import List, Optional, Dict, Any, Tuple
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

# Load .env searching upwards to workspace root
load_dotenv(find_dotenv())

from ..models.schemas import (
    Lesson,
    Slide,
    SlideType,
    TextbookContent,
    ValidationReport,
)
from ..services.hallucination_validator import HallucinationValidator

logger = logging.getLogger(__name__)


# =============================================================================
# Slide Generation Prompts
# =============================================================================

SLIDE_GENERATION_PROMPT = """You are an expert educational content creator for Indian school teachers.

Your task is to create a single slide for a lesson based on textbook content.

SLIDE REQUIREMENTS:
1. **Title**: A clear, engaging title for the slide (5-10 words)
2. **Explanation**: A simplified explanation of the concept (2-3 paragraphs, easy to understand for the target class level)
3. **Bullet Points**: 3-5 key points that summarize the main ideas
4. **Key Terms**: Important vocabulary words with brief definitions (if applicable)
5. **Examples**: 1-3 concrete examples that illustrate the concept
6. **Diagram Prompt**: A detailed prompt for generating an educational diagram that visualizes the concept

=== LANGUAGE SIMPLIFICATION INSTRUCTIONS ===

For Class 1-5 (Primary):
- Use very simple words (1-2 syllables preferred)
- Short sentences (5-10 words)
- Relate to home, family, playground, animals
- Use "you", "we", "let's" to engage
- Avoid abstract concepts

For Class 6-8 (Middle School):
- Use clear, straightforward language
- Sentences can be 10-15 words
- Include real-world examples from daily life
- Define technical terms when first used
- Use analogies to explain complex ideas

For Class 9-10 (Secondary):
- More sophisticated vocabulary is acceptable
- Can include technical terms with explanations
- Connect to exam-relevant concepts
- Include application-based examples

GENERAL SIMPLIFICATION RULES:
- Replace complex words with simpler alternatives
- Break long sentences into shorter ones
- Use active voice instead of passive
- Add transition words (First, Next, Then, Finally)
- Include "For example..." to clarify concepts
- Avoid double negatives
- Use concrete nouns instead of abstract ones

=== DIAGRAM PROMPT GENERATION INSTRUCTIONS ===

Create a detailed prompt that describes an educational diagram. The prompt should:

1. START with the diagram type:
   - "A labeled diagram showing..."
   - "A simple flowchart depicting..."
   - "An illustrated comparison of..."
   - "A step-by-step visual guide for..."
   - "A concept map connecting..."

2. SPECIFY visual elements:
   - Main objects/shapes to include
   - Colors to use (keep it simple: 2-3 colors)
   - Arrows or connectors if needed
   - Size relationships between elements

3. INCLUDE labels:
   - What text labels should appear
   - Where labels should be positioned
   - Any numbers or measurements

4. MATCH class level:
   - Primary: Very simple, cartoon-like, colorful
   - Middle: Clear, organized, some detail
   - Secondary: More detailed, can include formulas

5. EXAMPLE DIAGRAM PROMPTS:
   - "A labeled diagram showing the water cycle with clouds, rain, rivers, and ocean. Include arrows showing evaporation going up and precipitation coming down. Label each stage: evaporation, condensation, precipitation, collection."
   - "A simple flowchart showing the steps of photosynthesis. Start with sunlight and water entering a leaf, show the process inside, and end with oxygen and glucose as outputs. Use green for the leaf and yellow for sunlight."
   - "A comparison diagram with two columns: 'Conductors' and 'Insulators'. Show 3 examples of each with small illustrations (metal spoon, copper wire, iron nail vs rubber, plastic, wood)."

RESPOND WITH JSON ONLY:
{
    "title": "Slide title",
    "explanation": "Detailed but simplified explanation...",
    "bullet_points": ["Point 1", "Point 2", "Point 3"],
    "key_terms": ["Term 1: definition", "Term 2: definition"],
    "examples": ["Example 1", "Example 2"],
    "diagram_prompt": "A simple educational diagram showing..."
}

RULES:
- Return ONLY valid JSON
- All fields must be non-empty
- Explanation must be at least 50 characters
- At least 3 bullet points
- Diagram prompt must be descriptive (at least 30 characters)
- Diagram prompt must start with a diagram type phrase"""


LESSON_STRUCTURE_PROMPT = """You are an expert curriculum designer for Indian schools.

Analyze the provided textbook content and create a structured outline for an 8-slide lesson.

=== SLIDE STRUCTURE (MUST FOLLOW EXACTLY) ===

The 8 slides MUST follow this EXACT structure and sequence:

1. **Introduction** (slide_type: "introduction")
   - Topic introduction and context
   - Learning objectives (what students will learn)
   - Hook to engage students (question, fact, or scenario)
   - Preview of what's coming

2. **Concept 1** (slide_type: "concept")
   - First key concept from the content
   - Most fundamental idea that other concepts build upon
   - Clear definition and explanation

3. **Concept 2** (slide_type: "concept")
   - Second key concept from the content
   - Builds on Concept 1
   - Introduces new terminology

4. **Concept 3** (slide_type: "concept")
   - Third key concept from the content
   - Most advanced of the three concepts
   - Connects to previous concepts

5. **Examples** (slide_type: "examples")
   - Worked examples demonstrating the concepts
   - Step-by-step solutions
   - Multiple examples of varying difficulty

6. **Practice** (slide_type: "practice")
   - Practice problems or activities for students
   - Hands-on exercises
   - Questions for students to try

7. **Real World** (slide_type: "real_world")
   - Real-world applications and connections
   - How this topic is used in daily life
   - Career connections or practical uses

8. **Summary** (slide_type: "summary")
   - Key takeaways (3-5 main points)
   - Recap of main concepts
   - What to remember for exams
   - Preview of next topic (if applicable)

=== CONTENT EXTRACTION GUIDELINES ===

For each slide, identify which portion of the textbook content should be used:
- Extract relevant definitions, explanations, and facts
- Identify examples from the textbook
- Note any diagrams or figures mentioned
- Preserve important formulas or rules
- Keep the original meaning while noting what to simplify

RESPOND WITH JSON:
{
    "slides": [
        {
            "slide_number": 1,
            "slide_type": "introduction",
            "focus": "Brief description of what this slide should cover",
            "content_to_use": "Relevant excerpt or summary from textbook content"
        },
        {
            "slide_number": 2,
            "slide_type": "concept",
            "focus": "First key concept to cover",
            "content_to_use": "Relevant textbook content for this concept"
        }
    ]
}

RULES:
- Return ONLY valid JSON
- Must have exactly 8 slides
- Slide types must follow the EXACT sequence: introduction, concept, concept, concept, examples, practice, real_world, summary
- Content must be derived from the provided textbook content only
- Do NOT invent facts or concepts not in the source material
- Each slide's content_to_use should be substantial (at least 100 characters)"""


class LessonGenerator:
    """Generates 8-slide structured lessons from textbook content."""
    
    SLIDE_STRUCTURE = [
        ("introduction", SlideType.INTRODUCTION),
        ("concept_1", SlideType.CONCEPT),
        ("concept_2", SlideType.CONCEPT),
        ("concept_3", SlideType.CONCEPT),
        ("examples", SlideType.EXAMPLES),
        ("practice", SlideType.PRACTICE),
        ("real_world", SlideType.REAL_WORLD),
        ("summary", SlideType.SUMMARY),
    ]
    
    # Minimum validation score threshold
    MIN_VALIDATION_SCORE = 0.6
    
    # Maximum regeneration attempts for low-scoring content
    MAX_REGENERATION_ATTEMPTS = 2
    
    def __init__(self, api_key: Optional[str] = None, enable_validation: bool = True):
        """
        Initialize the lesson generator.
        
        Args:
            api_key: Google AI API key. If None, reads from GEMINI_API_KEYenv var.
            enable_validation: Whether to enable hallucination validation.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            # Debug: Check if env var exists
            all_env_keys = [k for k in os.environ.keys() if 'GEMINI' in k or 'API' in k]
            raise ValueError(
                f"Google/OpenRouter API key is required. Set GEMINI_API_KEY or OPENROUTER_API_KEY environment variable. "
                f"Found environment keys with 'GEMINI' or 'API': {all_env_keys}"
            )
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "32768"))
        
        # Initialize hallucination validator
        self.enable_validation = enable_validation
        self.validator = HallucinationValidator(use_embeddings=True) if enable_validation else None
    
    async def generate_lesson(
        self,
        textbook_content: List[TextbookContent],
        class_name: str,
        subject: str,
        topic: str,
        validate: bool = True
    ) -> Tuple[Lesson, ValidationReport]:
        """
        Generates complete 8-slide lesson from textbook content.
        
        Process:
        1. Analyze textbook content to identify key concepts
        2. Structure content into 8 slides
        3. Generate each slide with simplified language
        4. Generate diagram prompts for each slide
        5. Validate against source content (hallucination check)
        6. Regenerate low-scoring slides if needed
        
        Args:
            textbook_content: List of textbook content chunks
            class_name: Class/grade level (e.g., "Class_6")
            subject: Subject name (e.g., "Mathematics")
            topic: Topic/chapter name
            validate: Whether to run hallucination validation
            
        Returns:
            Tuple of (Lesson object with 8 slides, ValidationReport)
        """
        start_time = time.time()
        
        if not textbook_content:
            raise ValueError("No textbook content provided for lesson generation")
        
        # Combine textbook content into a single string for analysis
        combined_content = self._combine_content(textbook_content)
        
        logger.info(f"Generating lesson for {class_name}/{subject}/{topic}")
        logger.info(f"Content length: {len(combined_content)} characters")
        
        # Step 1: Structure content into 8 slides
        slide_structure = await self._structure_content_into_slides(
            combined_content, class_name, subject, topic
        )
        
        # Step 2: Generate each slide with source references
        slides = []
        for i, (slide_key, slide_type) in enumerate(self.SLIDE_STRUCTURE, 1):
            slide_info = slide_structure[i - 1] if i <= len(slide_structure) else {}
            
            # Get relevant source references for this slide
            source_refs = self._get_source_references_for_content(
                slide_info.get("content_to_use", ""),
                textbook_content
            )
            
            slide = await self._generate_slide(
                slide_number=i,
                slide_type=slide_type,
                content_chunk=slide_info.get("content_to_use", combined_content[:2000]),
                focus=slide_info.get("focus", f"Slide {i} content"),
                class_level=class_name,
                subject=subject,
                topic=topic,
                source_references=source_refs
            )
            slides.append(slide)
            logger.info(f"Generated slide {i}/{len(self.SLIDE_STRUCTURE)}: {slide.title}")
        
        # Step 3: Validate and potentially regenerate
        validation_report = ValidationReport(
            is_valid=True,
            overall_score=0.8,
            issues=[],
            flagged_content=[],
            recommendations=[]
        )
        
        if validate and self.enable_validation and self.validator:
            # Create initial lesson for validation
            initial_lesson = Lesson(
                class_name=class_name,
                subject=subject,
                topic=topic,
                slides=slides,
                validation_score=0.8
            )
            
            # Validate the lesson
            validation_report = await self.validator.validate_lesson(
                initial_lesson, textbook_content
            )
            
            # Regenerate low-scoring slides if needed
            if not validation_report.is_valid:
                slides, validation_report = await self._regenerate_low_scoring_slides(
                    slides=slides,
                    textbook_content=textbook_content,
                    slide_structure=slide_structure,
                    class_name=class_name,
                    subject=subject,
                    topic=topic,
                    combined_content=combined_content
                )
        
        generation_time = (time.time() - start_time) * 1000
        logger.info(f"Lesson generation completed in {generation_time:.0f}ms")
        
        # Create final lesson object
        lesson = Lesson(
            class_name=class_name,
            subject=subject,
            topic=topic,
            slides=slides,
            validation_score=validation_report.overall_score
        )
        
        return lesson, validation_report
    
    def _combine_content(self, textbook_content: List[TextbookContent]) -> str:
        """Combine multiple textbook content chunks into a single string."""
        combined = []
        for tc in textbook_content:
            combined.append(f"[Source: {tc.source}]\n{tc.content}")
        return "\n\n---\n\n".join(combined)
    
    def _get_source_references_for_content(
        self,
        content_chunk: str,
        textbook_content: List[TextbookContent]
    ) -> List[str]:
        """
        Find the most relevant source references for a content chunk.
        
        Args:
            content_chunk: The content to find references for
            textbook_content: List of source textbook content
            
        Returns:
            List of source reference strings (up to 3)
        """
        if not textbook_content or not content_chunk:
            return [tc.source for tc in textbook_content[:3]] if textbook_content else []
        
        # Simple keyword matching to find relevant sources
        content_words = set(content_chunk.lower().split())
        scored_sources = []
        
        for tc in textbook_content:
            source_words = set(tc.content.lower().split())
            overlap = len(content_words & source_words)
            scored_sources.append((tc.source, overlap))
        
        # Sort by overlap and return top 3
        scored_sources.sort(key=lambda x: x[1], reverse=True)
        return [source for source, _ in scored_sources[:3]]
    
    async def _regenerate_low_scoring_slides(
        self,
        slides: List[Slide],
        textbook_content: List[TextbookContent],
        slide_structure: List[Dict[str, Any]],
        class_name: str,
        subject: str,
        topic: str,
        combined_content: str
    ) -> Tuple[List[Slide], ValidationReport]:
        """
        Regenerate slides that have low validation scores.
        
        Args:
            slides: Current list of slides
            textbook_content: Source textbook content
            slide_structure: Original slide structure
            class_name: Class level
            subject: Subject name
            topic: Topic name
            combined_content: Combined source content
            
        Returns:
            Tuple of (updated slides list, final validation report)
        """
        logger.info("Attempting to regenerate low-scoring slides...")
        
        # Validate each slide individually to find low-scoring ones
        combined_source = "\n\n".join(tc.content for tc in textbook_content)
        
        for attempt in range(self.MAX_REGENERATION_ATTEMPTS):
            low_scoring_indices = []
            
            for i, slide in enumerate(slides):
                slide_text = f"{slide.title} {slide.explanation} {' '.join(slide.bullet_points)}"
                score = self.validator._calculate_grounding_score(slide_text, combined_source)
                
                if score < self.MIN_VALIDATION_SCORE:
                    low_scoring_indices.append(i)
            
            if not low_scoring_indices:
                logger.info("All slides now pass validation threshold")
                break
            
            logger.info(f"Regeneration attempt {attempt + 1}: {len(low_scoring_indices)} slides need improvement")
            
            # Regenerate low-scoring slides with stricter grounding instructions
            for idx in low_scoring_indices:
                slide_info = slide_structure[idx] if idx < len(slide_structure) else {}
                slide_type = self.SLIDE_STRUCTURE[idx][1]
                
                # Get relevant source references
                source_refs = self._get_source_references_for_content(
                    slide_info.get("content_to_use", ""),
                    textbook_content
                )
                
                # Regenerate with emphasis on grounding
                new_slide = await self._generate_slide_with_grounding(
                    slide_number=idx + 1,
                    slide_type=slide_type,
                    content_chunk=slide_info.get("content_to_use", combined_content[:2000]),
                    focus=slide_info.get("focus", f"Slide {idx + 1} content"),
                    class_level=class_name,
                    subject=subject,
                    topic=topic,
                    source_references=source_refs,
                    source_content=combined_source
                )
                slides[idx] = new_slide
        
        # Final validation
        final_lesson = Lesson(
            class_name=class_name,
            subject=subject,
            topic=topic,
            slides=slides,
            validation_score=0.8
        )
        
        final_report = await self.validator.validate_lesson(final_lesson, textbook_content)
        
        return slides, final_report
    
    async def _generate_slide_with_grounding(
        self,
        slide_number: int,
        slide_type: SlideType,
        content_chunk: str,
        focus: str,
        class_level: str,
        subject: str,
        topic: str,
        source_references: List[str],
        source_content: str
    ) -> Slide:
        """
        Generate a slide with extra emphasis on grounding in source content.
        
        This method is used for regenerating slides that failed validation.
        """
        try:
            # Enhanced prompt with grounding instructions
            prompt = f"""Create slide {slide_number} of 8 for a {class_level} {subject} lesson on "{topic}".

SLIDE TYPE: {slide_type.value}
FOCUS: {focus}

CRITICAL INSTRUCTION: You MUST use ONLY information from the textbook content below.
Do NOT add any facts, examples, or concepts that are not explicitly stated in the source.
Every statement must be directly traceable to the textbook content.

TEXTBOOK CONTENT TO USE (USE ONLY THIS):
{content_chunk[:3000]}

Generate the slide content following the requirements. Stay strictly within the source material."""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SLIDE_GENERATION_PROMPT,
                    temperature=0.3,  # Lower temperature for more grounded output
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = self._clean_json_response(response.text)
            parsed = json.loads(text)
            
            # Create slide object
            slide = Slide(
                slide_number=slide_number,
                slide_type=slide_type,
                title=parsed.get("title", f"Slide {slide_number}: {slide_type.value.title()}"),
                explanation=parsed.get("explanation", f"Content about {topic}"),
                bullet_points=parsed.get("bullet_points", ["Key point 1", "Key point 2", "Key point 3"]),
                key_terms=parsed.get("key_terms", []),
                examples=parsed.get("examples", []),
                diagram_prompt=parsed.get("diagram_prompt", f"Educational diagram for {topic}"),
                source_references=source_references
            )
            
            return slide
            
        except Exception as e:
            logger.error(f"Failed to regenerate slide {slide_number}: {e}")
            return self._get_default_slide(slide_number, slide_type, topic, source_references)
    
    async def _structure_content_into_slides(
        self,
        content: str,
        class_name: str,
        subject: str,
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze content and structure it into 8 slides.
        
        Args:
            content: Combined textbook content
            class_name: Class level
            subject: Subject name
            topic: Topic name
            
        Returns:
            List of slide structure dictionaries
        """
        try:
            prompt = f"""Class: {class_name}
Subject: {subject}
Topic: {topic}

TEXTBOOK CONTENT:
{content[:8000]}  # Limit content to avoid token limits

Create an 8-slide lesson structure based on this content."""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=LESSON_STRUCTURE_PROMPT,
                    temperature=0.3,
                    max_output_tokens=4096,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = self._clean_json_response(response.text)
            parsed = json.loads(text)
            
            slides = parsed.get("slides", [])
            
            # Ensure we have exactly 8 slides
            if len(slides) < 8:
                # Pad with default structure
                for i in range(len(slides) + 1, 9):
                    slide_type = self.SLIDE_STRUCTURE[i - 1][1].value
                    slides.append({
                        "slide_number": i,
                        "slide_type": slide_type,
                        "focus": f"Content for slide {i}",
                        "content_to_use": content[:1000]
                    })
            
            return slides[:8]
            
        except Exception as e:
            logger.warning(f"Failed to structure content: {e}. Using default structure.")
            # Return default structure
            return self._get_default_structure(content)
    
    def _get_default_structure(self, content: str) -> List[Dict[str, Any]]:
        """Get default slide structure when AI structuring fails."""
        chunk_size = len(content) // 8
        return [
            {
                "slide_number": i + 1,
                "slide_type": self.SLIDE_STRUCTURE[i][1].value,
                "focus": f"Content for {self.SLIDE_STRUCTURE[i][0]}",
                "content_to_use": content[i * chunk_size:(i + 1) * chunk_size]
            }
            for i in range(8)
        ]
    
    async def _generate_slide(
        self,
        slide_number: int,
        slide_type: SlideType,
        content_chunk: str,
        focus: str,
        class_level: str,
        subject: str,
        topic: str,
        source_references: List[str]
    ) -> Slide:
        """
        Generates a single slide with all components.
        
        Args:
            slide_number: Slide number (1-8)
            slide_type: Type of slide
            content_chunk: Textbook content to use for this slide
            focus: What this slide should focus on
            class_level: Target class level
            subject: Subject name
            topic: Topic name
            source_references: List of source references
            
        Returns:
            Complete Slide object
        """
        try:
            prompt = f"""Create slide {slide_number} of 8 for a {class_level} {subject} lesson on "{topic}".

SLIDE TYPE: {slide_type.value}
FOCUS: {focus}

TEXTBOOK CONTENT TO USE:
{content_chunk[:3000]}

Generate the slide content following the requirements."""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SLIDE_GENERATION_PROMPT,
                    temperature=0.5,
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = self._clean_json_response(response.text)
            parsed = json.loads(text)
            
            # Create slide object
            slide = Slide(
                slide_number=slide_number,
                slide_type=slide_type,
                title=parsed.get("title", f"Slide {slide_number}: {slide_type.value.title()}"),
                explanation=parsed.get("explanation", f"Content about {topic}"),
                bullet_points=parsed.get("bullet_points", ["Key point 1", "Key point 2", "Key point 3"]),
                key_terms=parsed.get("key_terms", []),
                examples=parsed.get("examples", []),
                diagram_prompt=parsed.get("diagram_prompt", f"Educational diagram for {topic}"),
                source_references=source_references
            )
            
            return slide
            
        except Exception as e:
            logger.error(f"Failed to generate slide {slide_number}: {e}")
            # Return a default slide
            return self._get_default_slide(
                slide_number, slide_type, topic, source_references
            )
    
    def _get_default_slide(
        self,
        slide_number: int,
        slide_type: SlideType,
        topic: str,
        source_references: List[str]
    ) -> Slide:
        """Create a default slide when generation fails."""
        return Slide(
            slide_number=slide_number,
            slide_type=slide_type,
            title=f"Slide {slide_number}: {slide_type.value.replace('_', ' ').title()}",
            explanation=f"This slide covers {slide_type.value.replace('_', ' ')} content for the topic: {topic}. Please refer to the textbook for detailed information.",
            bullet_points=[
                f"Key point about {topic}",
                "Important concept to understand",
                "Remember this for the exam"
            ],
            key_terms=[],
            examples=[f"Example related to {topic}"],
            diagram_prompt=f"A simple educational diagram illustrating the main concept of {topic}",
            source_references=source_references
        )
    
    def _clean_json_response(self, text: str) -> str:
        """Clean and extract JSON from response text with robust error handling."""
        if not text:
            return "{}"
            
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # Find the first { and last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]
        
        # Try parsing as-is first
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Fix 1: Replace single quotes with double quotes (common LLM issue)
        # But be careful not to replace apostrophes in words
        def fix_quotes(match):
            content = match.group(1)
            # Replace single quotes that look like JSON delimiters
            return '"' + content + '"'
        
        # Fix 2: Escape unescaped control characters in strings
        def escape_control_chars(s):
            result = []
            in_string = False
            i = 0
            while i < len(s):
                char = s[i]
                if char == '"' and (i == 0 or s[i-1] != '\\'):
                    in_string = not in_string
                    result.append(char)
                elif in_string and char == '\n':
                    result.append('\\n')
                elif in_string and char == '\r':
                    result.append('\\r')
                elif in_string and char == '\t':
                    result.append('\\t')
                else:
                    result.append(char)
                i += 1
            return ''.join(result)
        
        text = escape_control_chars(text)
        
        # Try again after escaping
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Fix 3: Remove trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Fix 4: Handle unterminated strings by line
        lines = text.split('\n')
        fixed_lines = []
        for line in lines:
            # Count unescaped quotes
            quote_count = 0
            i = 0
            while i < len(line):
                if line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                    quote_count += 1
                i += 1
            
            if quote_count % 2 != 0:
                # Odd quotes - try to close the string
                line = line.rstrip()
                if line.endswith(','):
                    line = line[:-1] + '",'
                elif line.endswith(':'):
                    line = line + '""'
                else:
                    line = line + '"'
            fixed_lines.append(line)
        text = '\n'.join(fixed_lines)
        
        # Fix trailing commas again after line fixes
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Fix 5: Try to fix "Expecting property name" errors (missing quotes around keys)
        # This handles cases like {key: "value"} -> {"key": "value"}
        text = re.sub(r'{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'{"\1":', text)
        text = re.sub(r',\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r',"\1":', text)
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Fix 6: Handle truncated JSON by attempting to close brackets
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        if open_braces > 0 or open_brackets > 0:
            # Remove any trailing incomplete key-value
            text = re.sub(r',\s*"[^"]*"\s*:\s*$', '', text)
            text = re.sub(r',\s*"[^"]*"\s*:\s*"[^"]*$', '', text)
            # Close brackets
            text = text.rstrip(',\n\r\t ')
            text += ']' * open_brackets + '}' * open_braces
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        return text
    
    async def validate_against_source(
        self,
        generated_content: str,
        source_content: str
    ) -> ValidationReport:
        """
        Validates generated content doesn't hallucinate beyond source.
        
        This is a basic validation - the full HallucinationValidator
        will provide more comprehensive checking.
        
        Args:
            generated_content: The generated text to validate
            source_content: The source textbook content
            
        Returns:
            ValidationReport with validation results
        """
        # Basic validation - check if key terms from generated content
        # appear in source content
        generated_words = set(generated_content.lower().split())
        source_words = set(source_content.lower().split())
        
        # Calculate overlap
        overlap = len(generated_words & source_words)
        total = len(generated_words)
        
        if total > 0:
            score = min(1.0, overlap / total + 0.3)  # Add base score
        else:
            score = 0.5
        
        return ValidationReport(
            is_valid=score >= 0.6,
            overall_score=score,
            issues=[],
            flagged_content=[],
            recommendations=[]
        )
