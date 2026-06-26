"""
MODULE Data Models
==================

Pydantic models for lessons, slides, assignments, and questions.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone
from enum import Enum


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    """Types of questions in assignments."""
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"


class SlideType(str, Enum):
    """Types of slides in a lesson."""
    INTRODUCTION = "introduction"
    CONCEPT = "concept"
    EXAMPLES = "examples"
    PRACTICE = "practice"
    REAL_WORLD = "real_world"
    SUMMARY = "summary"


class TopicInfo(BaseModel):
    """Information about an available topic."""
    topic_name: str = Field(..., description="Name of the topic/chapter")
    chapter_number: Optional[int] = Field(None, description="Chapter number if available")
    page_range: Optional[str] = Field(None, description="Page range in textbook")
    content_count: int = Field(..., description="Number of content chunks available", ge=0)


class TextbookContent(BaseModel):
    """Content retrieved from textbook database."""
    content: str = Field(..., description="Text content from textbook", min_length=1)
    source: str = Field(..., description="Format: Class|Subject|Book|Language|Page")
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator('source')
    @classmethod
    def validate_source_format(cls, v: str) -> str:
        """Validate source has correct pipe-separated format."""
        parts = v.split('|')
        if len(parts) < 3:
            raise ValueError("Source must have at least 3 pipe-separated parts: Class|Subject|Book")
        return v


class Slide(BaseModel):
    """A single slide in the lesson."""
    slide_number: int = Field(..., ge=1, le=8, description="Slide number (1-8)")
    slide_type: SlideType = Field(..., description="Type of slide content")
    title: str = Field(..., description="Slide title", min_length=1)
    explanation: str = Field(..., description="Simplified explanation of the concept", min_length=10)
    bullet_points: List[str] = Field(..., description="3-5 key points", min_length=1)
    key_terms: List[str] = Field(default_factory=list, description="Important vocabulary with definitions")
    examples: List[str] = Field(default_factory=list, description="Concrete examples")
    diagram_prompt: str = Field(..., description="Prompt for generating educational diagram", min_length=5)
    diagram_url: Optional[str] = Field(None, description="URL of generated diagram")
    source_references: List[str] = Field(default_factory=list, description="Textbook sources used")

    @field_validator('bullet_points')
    @classmethod
    def validate_bullet_points(cls, v: List[str]) -> List[str]:
        """Ensure bullet points are non-empty strings."""
        if not v:
            raise ValueError("At least one bullet point is required")
        for point in v:
            if not point or not point.strip():
                raise ValueError("Bullet points cannot be empty")
        return v


class Lesson(BaseModel):
    """Complete 2-slide lesson."""
    id: Optional[str] = Field(None, description="Unique lesson identifier")
    class_name: str = Field(..., description="Class/grade level", min_length=1)
    subject: str = Field(..., description="Subject name", min_length=1)
    topic: str = Field(..., description="Topic/chapter name", min_length=1)
    slides: List[Slide] = Field(..., description="Up to 8 slides")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    teacher_id: Optional[str] = Field(None, description="ID of teacher who created this")
    validation_score: float = Field(..., ge=0.0, le=1.0, description="Hallucination check score")
    ragflow_session_id: Optional[str] = Field(None, description="RAGFlow session ID associated with this lesson")

    @field_validator('slides')
    @classmethod
    def validate_up_to_8_slides(cls, v: List[Slide]) -> List[Slide]:
        """Ensure lesson has between 1 and 8 slides."""
        if not (1 <= len(v) <= 8):
            raise ValueError(f"Lesson must have between 1 and 8 slides, got {len(v)}")
        return v

    @model_validator(mode='after')
    def validate_slide_numbers(self) -> 'Lesson':
        """Ensure slides are numbered sequentially starting from 1."""
        for i, slide in enumerate(self.slides, 1):
            if slide.slide_number != i:
                raise ValueError(f"Slide {i} has incorrect slide_number: {slide.slide_number}")
        return self


class MCQOption(BaseModel):
    """A single MCQ option."""
    option_text: str = Field(..., description="Option text", min_length=1)
    is_correct: bool = Field(..., description="Whether this is the correct answer")


class Question(BaseModel):
    """Base question model."""
    question_text: str = Field(..., description="The question text", min_length=5)
    difficulty: DifficultyLevel = Field(..., description="Question difficulty")
    question_type: QuestionType = Field(..., description="Type of question")
    marks: int = Field(..., ge=1, description="Marks for this question")
    source_reference: str = Field(..., description="Textbook source for answer")


class MCQQuestion(Question):
    """Multiple choice question."""
    question_type: QuestionType = Field(default=QuestionType.MCQ)
    options: List[MCQOption] = Field(..., description="Exactly 4 options")
    marks: int = Field(default=1, ge=1)

    @field_validator('options')
    @classmethod
    def validate_exactly_4_options(cls, v: List[MCQOption]) -> List[MCQOption]:
        """Ensure MCQ has exactly 4 options."""
        if len(v) != 4:
            raise ValueError(f"MCQ must have exactly 4 options, got {len(v)}")
        return v

    @model_validator(mode='after')
    def validate_exactly_one_correct(self) -> 'MCQQuestion':
        """Ensure exactly one option is marked correct."""
        correct_count = sum(1 for opt in self.options if opt.is_correct)
        if correct_count != 1:
            raise ValueError(f"MCQ must have exactly 1 correct option, got {correct_count}")
        return self


class ShortAnswerQuestion(Question):
    """Short answer question (2-3 sentences expected)."""
    question_type: QuestionType = Field(default=QuestionType.SHORT_ANSWER)
    expected_answer: str = Field(..., description="Expected answer", min_length=10)
    marks: int = Field(default=2, ge=1)


class LongAnswerQuestion(Question):
    """Long answer question (paragraph expected)."""
    question_type: QuestionType = Field(default=QuestionType.LONG_ANSWER)
    expected_answer: str = Field(..., description="Expected answer", min_length=50)
    marking_scheme: List[str] = Field(..., description="Points to look for in answer", min_length=1)
    marks: int = Field(default=5, ge=1)


# Union type for all question types
QuestionUnion = Union[MCQQuestion, ShortAnswerQuestion, LongAnswerQuestion]


class Assignment(BaseModel):
    """Complete assignment with all question types."""
    id: Optional[str] = Field(None, description="Unique assignment identifier")
    lesson_id: str = Field(..., description="ID of associated lesson")
    class_name: str = Field(..., description="Class/grade level")
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic/chapter name")
    questions: List[QuestionUnion] = Field(..., description="All questions", min_length=1)
    total_marks: int = Field(..., ge=1, description="Total marks for assignment")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode='after')
    def validate_total_marks(self) -> 'Assignment':
        """Ensure total_marks matches sum of question marks."""
        calculated_total = sum(q.marks for q in self.questions)
        if self.total_marks != calculated_total:
            raise ValueError(f"total_marks ({self.total_marks}) doesn't match sum of question marks ({calculated_total})")
        return self

    def questions_by_difficulty(self) -> dict:
        """Group questions by difficulty level."""
        result = {level: [] for level in DifficultyLevel}
        for q in self.questions:
            result[q.difficulty].append(q)
        return result

    def questions_by_type(self) -> dict:
        """Group questions by type."""
        result = {qtype: [] for qtype in QuestionType}
        for q in self.questions:
            result[q.question_type].append(q)
        return result


class ValidationReport(BaseModel):
    """Report from hallucination validation."""
    is_valid: bool = Field(..., description="Whether content passed validation")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall validation score")
    issues: List[str] = Field(default_factory=list, description="Issues found during validation")
    flagged_content: List[str] = Field(default_factory=list, description="Content that may be hallucinated")
    recommendations: List[str] = Field(default_factory=list, description="Suggestions for improvement")


class DiagramResult(BaseModel):
    """Result from diagram generation."""
    success: bool = Field(..., description="Whether generation succeeded")
    image_url: Optional[str] = Field(None, description="URL of generated image")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image data")
    prompt_used: str = Field(..., description="Prompt used for generation")
    error: Optional[str] = Field(None, description="Error message if failed")


class LessonGenerationRequest(BaseModel):
    """API request for lesson generation."""
    class_name: str = Field(..., description="Class/grade level", min_length=1)
    subject: str = Field(..., description="Subject name", min_length=1)
    topic: str = Field(..., description="Topic/chapter name", min_length=1)
    duration_minutes: Optional[int] = Field(None, description="Optional lesson duration")
    language: Optional[str] = Field(None, description="Optional lesson language")
    board: Optional[str] = Field(None, description="Optional board/curriculum")
    save: bool = Field(True, description="Whether to persist the generated lesson")


class LessonGenerationResponse(BaseModel):
    """API response for lesson generation."""
    lesson: Lesson = Field(..., description="Generated lesson")
    assignment: Assignment = Field(..., description="Generated assignment")
    generation_time_ms: float = Field(..., ge=0, description="Time taken to generate")
    validation_report: ValidationReport = Field(..., description="Validation results")
    dataset_id: Optional[str] = Field(None, description="RAGFlow dataset identifier used for retrieval")
    dataset_name: Optional[str] = Field(None, description="RAGFlow dataset name used for retrieval")
    rag_chunks_used: Optional[int] = Field(None, description="Number of retrieved context chunks used")
    saved_id: Optional[str] = Field(None, description="Persisted lesson identifier when save=true")
    ragflow_session_id: Optional[str] = Field(None, description="New RAGFlow chat session ID created for this lesson")
