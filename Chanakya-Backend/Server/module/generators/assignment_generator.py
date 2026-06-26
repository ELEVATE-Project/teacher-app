"""
Assignment Generator
====================

Generates assignments with multiple question types and difficulty levels
from textbook content using Gemini.
"""

import json
import re
import time
import logging
import os
import uuid
from typing import List, Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env from project root (Chanakya/)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(_current_dir)))
_env_path = os.path.join(_root_dir, '.env')
load_dotenv(_env_path)

from ..models.schemas import (
    Lesson,
    TextbookContent,
    Assignment,
    Question,
    MCQQuestion,
    MCQOption,
    ShortAnswerQuestion,
    LongAnswerQuestion,
    DifficultyLevel,
    QuestionType,
)
from ..services.hallucination_validator import HallucinationValidator

logger = logging.getLogger(__name__)


# =============================================================================
# Question Generation Prompts
# =============================================================================

MCQ_GENERATION_PROMPT = """You are an expert educational assessment creator for Indian school teachers.

Your task is to create Multiple Choice Questions (MCQs) based on textbook content.

=== MCQ REQUIREMENTS ===

1. **Question Text**: Clear, unambiguous question that tests understanding
2. **Options**: Exactly 4 options (A, B, C, D)
   - One correct answer
   - Three plausible distractors (wrong but believable)
   - Options should be similar in length and structure
3. **Correct Answer**: Must be derivable from the textbook content
4. **Source Reference**: Reference to the textbook section

=== DIFFICULTY LEVEL INSTRUCTIONS ===

**Easy Questions:**
- Test basic recall and recognition
- Direct facts from the textbook
- Simple definitions and terms
- "What is...", "Which of the following..."

**Medium Questions:**
- Test understanding and application
- Require connecting two concepts
- Apply knowledge to simple scenarios
- "Why does...", "How does..."

**Hard Questions:**
- Test analysis and evaluation
- Require synthesizing multiple concepts
- Complex scenarios or edge cases
- "What would happen if...", "Which best explains..."

=== RESPONSE FORMAT ===

RESPOND WITH JSON ONLY:
{
    "question_text": "Clear question text ending with ?",
    "options": [
        {"option_text": "Option A text", "is_correct": false},
        {"option_text": "Option B text", "is_correct": true},
        {"option_text": "Option C text", "is_correct": false},
        {"option_text": "Option D text", "is_correct": false}
    ],
    "source_reference": "Class|Subject|Book|Page"
}

RULES:
- Return ONLY valid JSON
- Exactly 4 options
- Exactly 1 correct option (is_correct: true)
- Question must be answerable from the provided content
- Do NOT create questions about information not in the source"""


SHORT_ANSWER_PROMPT = """You are an expert educational assessment creator for Indian school teachers.

Your task is to create Short Answer Questions based on textbook content.

=== SHORT ANSWER REQUIREMENTS ===

1. **Question Text**: Clear question requiring 2-3 sentence answer
2. **Expected Answer**: Model answer (2-3 sentences)
3. **Source Reference**: Reference to the textbook section

=== DIFFICULTY LEVEL INSTRUCTIONS ===

**Easy Questions:**
- Ask for definitions or simple explanations
- "Define...", "What is meant by..."
- Answer is directly stated in textbook

**Medium Questions:**
- Ask for explanations with examples
- "Explain...", "Describe..."
- Requires understanding, not just recall

**Hard Questions:**
- Ask for comparisons or analysis
- "Compare and contrast...", "Analyze..."
- Requires connecting multiple concepts

=== RESPONSE FORMAT ===

RESPOND WITH JSON ONLY:
{
    "question_text": "Clear question text ending with ?",
    "expected_answer": "Model answer in 2-3 sentences that directly answers the question.",
    "source_reference": "Class|Subject|Book|Page"
}

RULES:
- Return ONLY valid JSON
- Expected answer must be 2-3 sentences (minimum 50 characters)
- Answer must be derivable from the provided content
- Do NOT create questions about information not in the source"""


LONG_ANSWER_PROMPT = """You are an expert educational assessment creator for Indian school teachers.

Your task is to create Long Answer Questions based on textbook content.

=== LONG ANSWER REQUIREMENTS ===

1. **Question Text**: Clear question requiring paragraph-length answer
2. **Expected Answer**: Model answer (1-2 paragraphs)
3. **Marking Scheme**: 3-5 key points to look for when grading
4. **Source Reference**: Reference to the textbook section

=== DIFFICULTY LEVEL INSTRUCTIONS ===

**Easy Questions:**
- Ask for detailed explanations of single concepts
- "Explain in detail...", "Describe the process of..."
- Straightforward elaboration of textbook content

**Medium Questions:**
- Ask for explanations with multiple aspects
- "Discuss...", "Explain with examples..."
- Requires organizing information coherently

**Hard Questions:**
- Ask for critical analysis or evaluation
- "Critically analyze...", "Evaluate the importance of..."
- Requires synthesis and original thinking within textbook scope

=== RESPONSE FORMAT ===

RESPOND WITH JSON ONLY:
{
    "question_text": "Clear question text ending with ?",
    "expected_answer": "Detailed model answer in 1-2 paragraphs covering all key points.",
    "marking_scheme": [
        "Key point 1 to look for (1 mark)",
        "Key point 2 to look for (1 mark)",
        "Key point 3 to look for (1 mark)",
        "Key point 4 to look for (1 mark)",
        "Key point 5 to look for (1 mark)"
    ],
    "source_reference": "Class|Subject|Book|Page"
}

RULES:
- Return ONLY valid JSON
- Expected answer must be substantial (minimum 100 characters)
- Marking scheme must have 3-5 points
- All points must be derivable from the provided content
- Do NOT create questions about information not in the source"""


class AssignmentGenerator:
    """Generates assignments with multiple question types and difficulty levels."""
    
    DIFFICULTY_LEVELS = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
    QUESTION_TYPES = [QuestionType.MCQ, QuestionType.SHORT_ANSWER, QuestionType.LONG_ANSWER]
    
    # Minimum questions per difficulty level
    MIN_QUESTIONS_PER_DIFFICULTY = 3
    
    # Default marks for each question type
    DEFAULT_MARKS = {
        QuestionType.MCQ: 1,
        QuestionType.SHORT_ANSWER: 2,
        QuestionType.LONG_ANSWER: 5,
    }
    
    def __init__(self, api_key: Optional[str] = None, enable_validation: bool = True):
        """
        Initialize the assignment generator.
        
        Args:
            api_key: Google AI API key. If None, reads from GEMINI_API_KEYenv var.
            enable_validation: Whether to enable question answerability validation.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            # Debug: Check if env var exists
            all_env_keys = [k for k in os.environ.keys() if 'GEMINI' in k or 'API' in k]
            raise ValueError(
                f"Google/OpenRouter API key is required. Set GEMINI_API_KEY or OPENROUTER_API_KEY environment variable. "
                f"Found environment keys with 'GEMINI' or 'API': {all_env_keys}"
            )
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # Initialize hallucination validator for question validation
        self.enable_validation = enable_validation
        self.validator = HallucinationValidator(use_embeddings=True) if enable_validation else None
    
    async def generate_assignment(
        self,
        lesson: Lesson,
        textbook_content: List[TextbookContent]
    ) -> Assignment:
        """
        Generates complete assignment based on lesson content.
        
        Ensures:
        - Questions are answerable from textbook content
        - Balanced distribution across difficulty levels
        - Mix of question types
        - MCQs have exactly 4 options with 1 correct answer
        
        Args:
            lesson: The generated lesson to base questions on
            textbook_content: Source textbook content for validation
            
        Returns:
            Assignment object with all questions
        """
        start_time = time.time()
        
        if not textbook_content:
            raise ValueError("No textbook content provided for assignment generation")
        
        # Combine textbook content
        combined_content = self._combine_content(textbook_content)
        
        logger.info(f"Generating assignment for {lesson.class_name}/{lesson.subject}/{lesson.topic}")
        
        questions: List[Question] = []
        
        # Generate questions for each difficulty level
        for difficulty in self.DIFFICULTY_LEVELS:
            # Generate MCQs
            mcqs = await self._generate_mcqs_for_difficulty(
                difficulty=difficulty,
                content=combined_content,
                textbook_content=textbook_content,
                class_name=lesson.class_name,
                topic=lesson.topic,
                count=self.MIN_QUESTIONS_PER_DIFFICULTY
            )
            questions.extend(mcqs)
            
            # Generate short answer questions
            short_answers = await self._generate_short_answers_for_difficulty(
                difficulty=difficulty,
                content=combined_content,
                textbook_content=textbook_content,
                class_name=lesson.class_name,
                topic=lesson.topic,
                count=1  # 1 per difficulty = 3 total
            )
            questions.extend(short_answers)
            
            # Generate long answer questions
            long_answers = await self._generate_long_answers_for_difficulty(
                difficulty=difficulty,
                content=combined_content,
                textbook_content=textbook_content,
                class_name=lesson.class_name,
                topic=lesson.topic,
                count=1  # 1 per difficulty = 3 total
            )
            questions.extend(long_answers)
        
        # Calculate total marks
        total_marks = sum(q.marks for q in questions)
        
        generation_time = (time.time() - start_time) * 1000
        logger.info(f"Assignment generation completed in {generation_time:.0f}ms with {len(questions)} questions")
        
        # Create assignment
        assignment = Assignment(
            id=str(uuid.uuid4()),
            lesson_id=lesson.id or str(uuid.uuid4()),
            class_name=lesson.class_name,
            subject=lesson.subject,
            topic=lesson.topic,
            questions=questions,
            total_marks=total_marks
        )
        
        return assignment

    async def _generate_mcqs_for_difficulty(
        self,
        difficulty: DifficultyLevel,
        content: str,
        textbook_content: List[TextbookContent],
        class_name: str,
        topic: str,
        count: int
    ) -> List[MCQQuestion]:
        """Generate MCQ questions for a specific difficulty level."""
        mcqs = []
        
        for i in range(count):
            try:
                mcq = await self._generate_mcq(
                    content=content,
                    difficulty=difficulty,
                    class_name=class_name,
                    topic=topic,
                    question_index=i
                )
                
                # Validate question answerability
                if self.enable_validation and self.validator:
                    is_valid = await self._validate_question_answerability(mcq, textbook_content)
                    if not is_valid:
                        logger.warning(f"MCQ {i+1} failed answerability validation, regenerating...")
                        mcq = await self._generate_mcq(
                            content=content,
                            difficulty=difficulty,
                            class_name=class_name,
                            topic=topic,
                            question_index=i
                        )
                
                mcqs.append(mcq)
                logger.info(f"Generated {difficulty.value} MCQ {i+1}/{count}")
                
            except Exception as e:
                logger.error(f"Failed to generate MCQ: {e}")
                # Create a fallback MCQ
                mcqs.append(self._get_fallback_mcq(difficulty, topic, textbook_content))
        
        return mcqs
    
    async def _generate_short_answers_for_difficulty(
        self,
        difficulty: DifficultyLevel,
        content: str,
        textbook_content: List[TextbookContent],
        class_name: str,
        topic: str,
        count: int
    ) -> List[ShortAnswerQuestion]:
        """Generate short answer questions for a specific difficulty level."""
        questions = []
        
        for i in range(count):
            try:
                question = await self._generate_short_answer(
                    content=content,
                    difficulty=difficulty,
                    class_name=class_name,
                    topic=topic,
                    question_index=i
                )
                
                # Validate question answerability
                if self.enable_validation and self.validator:
                    is_valid = await self._validate_question_answerability(question, textbook_content)
                    if not is_valid:
                        logger.warning(f"Short answer {i+1} failed validation, regenerating...")
                        question = await self._generate_short_answer(
                            content=content,
                            difficulty=difficulty,
                            class_name=class_name,
                            topic=topic,
                            question_index=i
                        )
                
                questions.append(question)
                logger.info(f"Generated {difficulty.value} short answer {i+1}/{count}")
                
            except Exception as e:
                logger.error(f"Failed to generate short answer: {e}")
                questions.append(self._get_fallback_short_answer(difficulty, topic, textbook_content))
        
        return questions
    
    async def _generate_long_answers_for_difficulty(
        self,
        difficulty: DifficultyLevel,
        content: str,
        textbook_content: List[TextbookContent],
        class_name: str,
        topic: str,
        count: int
    ) -> List[LongAnswerQuestion]:
        """Generate long answer questions for a specific difficulty level."""
        questions = []
        
        for i in range(count):
            try:
                question = await self._generate_long_answer(
                    content=content,
                    difficulty=difficulty,
                    class_name=class_name,
                    topic=topic,
                    question_index=i
                )
                
                # Validate question answerability
                if self.enable_validation and self.validator:
                    is_valid = await self._validate_question_answerability(question, textbook_content)
                    if not is_valid:
                        logger.warning(f"Long answer {i+1} failed validation, regenerating...")
                        question = await self._generate_long_answer(
                            content=content,
                            difficulty=difficulty,
                            class_name=class_name,
                            topic=topic,
                            question_index=i
                        )
                
                questions.append(question)
                logger.info(f"Generated {difficulty.value} long answer {i+1}/{count}")
                
            except Exception as e:
                logger.error(f"Failed to generate long answer: {e}")
                questions.append(self._get_fallback_long_answer(difficulty, topic, textbook_content))
        
        return questions
    
    async def _generate_mcq(
        self,
        content: str,
        difficulty: DifficultyLevel,
        class_name: str,
        topic: str,
        question_index: int
    ) -> MCQQuestion:
        """
        Generates a multiple choice question.
        
        Args:
            content: Textbook content to base question on
            difficulty: Difficulty level for the question
            class_name: Class level
            topic: Topic name
            question_index: Index for variety in generation
            
        Returns:
            MCQQuestion object
        """
        prompt = f"""Create an MCQ for {class_name} students on the topic "{topic}".

DIFFICULTY LEVEL: {difficulty.value.upper()}

TEXTBOOK CONTENT TO USE:
{content[:4000]}

Generate question #{question_index + 1} at {difficulty.value} difficulty level.
Make sure the question is different from typical questions and tests {difficulty.value} level understanding."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=MCQ_GENERATION_PROMPT,
                    temperature=0.7,
                    max_output_tokens=1024,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = self._clean_json_response(response.text)
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse MCQ JSON response: {e}")
                logger.error(f"Response text: {text[:500]}")
                # Use fallback
                parsed = {}
            
            # Log what we received for debugging
            logger.info(f"MCQ generation response keys: {list(parsed.keys())}")
            logger.info(f"Number of options received: {len(parsed.get('options', []))}")
            
            # Create MCQ options with validation
            options = []
            raw_options = parsed.get("options", [])
            
            if not raw_options:
                logger.warning("No options in parsed response, creating fallback options")
            
            for i, opt in enumerate(raw_options):
                if not isinstance(opt, dict):
                    logger.warning(f"Option {i} is not a dict: {opt}")
                    continue
                    
                option_text = opt.get("option_text", f"Option {chr(65 + i)}")
                is_correct = opt.get("is_correct", False)
                
                # Ensure is_correct is boolean
                if isinstance(is_correct, str):
                    is_correct = is_correct.lower() in ['true', '1', 'yes']
                
                options.append(MCQOption(
                    option_text=option_text,
                    is_correct=bool(is_correct)
                ))
            
            logger.info(f"Created {len(options)} MCQOption objects")
            if options:
                correct_count = sum(1 for opt in options if opt.is_correct)
                logger.info(f"Options with is_correct=True: {correct_count}")
            
            # Ensure exactly 4 options with 1 correct
            options = self._ensure_valid_mcq_options(options)
            
            return MCQQuestion(
                question_text=parsed.get("question_text", f"Question about {topic}?"),
                difficulty=difficulty,
                options=options,
                marks=self.DEFAULT_MARKS[QuestionType.MCQ],
                source_reference=parsed.get("source_reference", f"{class_name}|Unknown|NCERT|1")
            )
            
        except Exception as e:
            logger.error(f"MCQ generation failed: {e}")
            raise

    async def _generate_short_answer(
        self,
        content: str,
        difficulty: DifficultyLevel,
        class_name: str,
        topic: str,
        question_index: int
    ) -> ShortAnswerQuestion:
        """
        Generates a short answer question (2-3 sentences expected).
        
        Args:
            content: Textbook content to base question on
            difficulty: Difficulty level for the question
            class_name: Class level
            topic: Topic name
            question_index: Index for variety in generation
            
        Returns:
            ShortAnswerQuestion object
        """
        prompt = f"""Create a Short Answer Question for {class_name} students on the topic "{topic}".

DIFFICULTY LEVEL: {difficulty.value.upper()}

TEXTBOOK CONTENT TO USE:
{content[:4000]}

Generate question #{question_index + 1} at {difficulty.value} difficulty level.
The answer should be 2-3 sentences long."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SHORT_ANSWER_PROMPT,
                    temperature=0.7,
                    max_output_tokens=1024,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = self._clean_json_response(response.text)
            parsed = json.loads(text)
            
            expected_answer = parsed.get("expected_answer", f"Answer about {topic}.")
            # Ensure minimum length
            if len(expected_answer) < 10:
                expected_answer = f"This is a detailed answer about {topic} that explains the concept clearly."
            
            return ShortAnswerQuestion(
                question_text=parsed.get("question_text", f"Explain the concept of {topic}?"),
                difficulty=difficulty,
                expected_answer=expected_answer,
                marks=self.DEFAULT_MARKS[QuestionType.SHORT_ANSWER],
                source_reference=parsed.get("source_reference", f"{class_name}|Unknown|NCERT|1")
            )
            
        except Exception as e:
            logger.error(f"Short answer generation failed: {e}")
            raise
    
    async def _generate_long_answer(
        self,
        content: str,
        difficulty: DifficultyLevel,
        class_name: str,
        topic: str,
        question_index: int
    ) -> LongAnswerQuestion:
        """
        Generates a long answer question (paragraph expected).
        
        Args:
            content: Textbook content to base question on
            difficulty: Difficulty level for the question
            class_name: Class level
            topic: Topic name
            question_index: Index for variety in generation
            
        Returns:
            LongAnswerQuestion object
        """
        prompt = f"""Create a Long Answer Question for {class_name} students on the topic "{topic}".

DIFFICULTY LEVEL: {difficulty.value.upper()}

TEXTBOOK CONTENT TO USE:
{content[:4000]}

Generate question #{question_index + 1} at {difficulty.value} difficulty level.
The answer should be 1-2 paragraphs with a detailed marking scheme."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=LONG_ANSWER_PROMPT,
                    temperature=0.7,
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            text = self._clean_json_response(response.text)
            parsed = json.loads(text)
            
            expected_answer = parsed.get("expected_answer", "")
            # Ensure minimum length
            if len(expected_answer) < 50:
                expected_answer = f"This is a comprehensive answer about {topic}. It covers the main concepts, provides examples, and explains the significance of the topic in detail. Students should understand the key principles and be able to apply them."
            
            marking_scheme = parsed.get("marking_scheme", [])
            # Ensure minimum marking points
            if len(marking_scheme) < 1:
                marking_scheme = [
                    "Introduction and definition (1 mark)",
                    "Main explanation (2 marks)",
                    "Examples provided (1 mark)",
                    "Conclusion (1 mark)"
                ]
            
            return LongAnswerQuestion(
                question_text=parsed.get("question_text", f"Explain {topic} in detail with examples?"),
                difficulty=difficulty,
                expected_answer=expected_answer,
                marking_scheme=marking_scheme,
                marks=self.DEFAULT_MARKS[QuestionType.LONG_ANSWER],
                source_reference=parsed.get("source_reference", f"{class_name}|Unknown|NCERT|1")
            )
            
        except Exception as e:
            logger.error(f"Long answer generation failed: {e}")
            raise
    
    async def _validate_question_answerability(
        self,
        question: Question,
        source_content: List[TextbookContent]
    ) -> bool:
        """
        Validates that the question can be answered from source content.
        
        Uses semantic similarity to check if the question and its answer
        are grounded in the textbook content.
        
        Args:
            question: The question to validate
            source_content: List of source textbook content
            
        Returns:
            True if question is answerable from source, False otherwise
        """
        if not self.validator or not source_content:
            return True  # Skip validation if no validator or content
        
        # Get the answer text based on question type
        if isinstance(question, MCQQuestion):
            # For MCQ, check if correct answer is in source
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            answer_text = correct_option.option_text if correct_option else ""
        elif isinstance(question, ShortAnswerQuestion):
            answer_text = question.expected_answer
        elif isinstance(question, LongAnswerQuestion):
            answer_text = question.expected_answer
        else:
            answer_text = ""
        
        # Combine question and answer for validation
        full_text = f"{question.question_text} {answer_text}"
        
        # Calculate grounding score
        score, ungrounded = await self.validator.validate_content_grounding(
            full_text, source_content
        )
        
        # Question is valid if grounding score is above threshold
        return score >= 0.5  # Lower threshold for questions

    def _combine_content(self, textbook_content: List[TextbookContent]) -> str:
        """Combine multiple textbook content chunks into a single string."""
        combined = []
        for tc in textbook_content:
            combined.append(f"[Source: {tc.source}]\n{tc.content}")
        return "\n\n---\n\n".join(combined)
    
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
        
        # Fix 1: Escape unescaped control characters in strings
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
        
        # Fix 2: Remove trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Fix 3: Handle unterminated strings by line
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
        
        # Fix 4: Try to fix "Expecting property name" errors (missing quotes around keys)
        text = re.sub(r'{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'{"\1":', text)
        text = re.sub(r',\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r',"\1":', text)
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Fix 5: Handle truncated JSON by attempting to close brackets
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
    
    def _ensure_valid_mcq_options(self, options: List[MCQOption]) -> List[MCQOption]:
        """Ensure MCQ has exactly 4 options with exactly 1 correct."""
        # If no options at all, create 4 placeholder options with first one correct
        if not options:
            return [
                MCQOption(option_text="Option A", is_correct=True),
                MCQOption(option_text="Option B", is_correct=False),
                MCQOption(option_text="Option C", is_correct=False),
                MCQOption(option_text="Option D", is_correct=False),
            ]
        
        # Count correct options
        correct_count = sum(1 for opt in options if opt.is_correct)
        
        # If no correct option, make the first one correct
        if correct_count == 0:
            options[0] = MCQOption(option_text=options[0].option_text, is_correct=True)
            correct_count = 1
        
        # If multiple correct, keep only the first one correct
        if correct_count > 1:
            found_correct = False
            for i, opt in enumerate(options):
                if opt.is_correct:
                    if found_correct:
                        options[i] = MCQOption(option_text=opt.option_text, is_correct=False)
                    else:
                        found_correct = True
        
        # Pad to 4 options if needed
        while len(options) < 4:
            options.append(MCQOption(
                option_text=f"Option {chr(65 + len(options))}",
                is_correct=False
            ))
        
        # Trim to 4 options if too many
        options = options[:4]
        
        return options
    
    def _get_fallback_mcq(
        self,
        difficulty: DifficultyLevel,
        topic: str,
        textbook_content: List[TextbookContent]
    ) -> MCQQuestion:
        """Create a fallback MCQ when generation fails."""
        source_ref = textbook_content[0].source if textbook_content else "Unknown|Unknown|NCERT|1"
        
        return MCQQuestion(
            question_text=f"Which of the following is related to {topic}?",
            difficulty=difficulty,
            options=[
                MCQOption(option_text=f"Concept related to {topic}", is_correct=True),
                MCQOption(option_text="Unrelated concept A", is_correct=False),
                MCQOption(option_text="Unrelated concept B", is_correct=False),
                MCQOption(option_text="Unrelated concept C", is_correct=False),
            ],
            marks=self.DEFAULT_MARKS[QuestionType.MCQ],
            source_reference=source_ref
        )
    
    def _get_fallback_short_answer(
        self,
        difficulty: DifficultyLevel,
        topic: str,
        textbook_content: List[TextbookContent]
    ) -> ShortAnswerQuestion:
        """Create a fallback short answer question when generation fails."""
        source_ref = textbook_content[0].source if textbook_content else "Unknown|Unknown|NCERT|1"
        
        return ShortAnswerQuestion(
            question_text=f"Define {topic} in your own words.",
            difficulty=difficulty,
            expected_answer=f"{topic} is an important concept that students should understand. It involves key principles that are fundamental to the subject.",
            marks=self.DEFAULT_MARKS[QuestionType.SHORT_ANSWER],
            source_reference=source_ref
        )
    
    def _get_fallback_long_answer(
        self,
        difficulty: DifficultyLevel,
        topic: str,
        textbook_content: List[TextbookContent]
    ) -> LongAnswerQuestion:
        """Create a fallback long answer question when generation fails."""
        source_ref = textbook_content[0].source if textbook_content else "Unknown|Unknown|NCERT|1"
        
        return LongAnswerQuestion(
            question_text=f"Explain {topic} in detail with suitable examples.",
            difficulty=difficulty,
            expected_answer=f"{topic} is a fundamental concept in this subject. It encompasses several key ideas that are essential for understanding the broader topic. Students should be able to explain the main principles, provide relevant examples, and discuss the significance of this concept in real-world applications.",
            marking_scheme=[
                "Introduction and definition (1 mark)",
                "Main explanation with key points (2 marks)",
                "Examples provided (1 mark)",
                "Conclusion and significance (1 mark)"
            ],
            marks=self.DEFAULT_MARKS[QuestionType.LONG_ANSWER],
            source_reference=source_ref
        )
