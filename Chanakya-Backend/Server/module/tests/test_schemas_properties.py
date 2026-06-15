"""
Property-Based Tests for MODULE Data Models
===========================================

Tests using Hypothesis to validate correctness properties.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from pydantic import ValidationError

from ..models.schemas import (
    DifficultyLevel,
    QuestionType,
    SlideType,
    Slide,
    Lesson,
    MCQOption,
    MCQQuestion,
    ShortAnswerQuestion,
    LongAnswerQuestion,
    Assignment,
    TopicInfo,
    TextbookContent,
)


# =============================================================================
# Custom Strategies
# =============================================================================

@st.composite
def valid_source_strategy(draw):
    """Generate valid source strings in format Class|Subject|Book|Language|Page."""
    class_name = draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"]))
    subject = draw(st.sampled_from(["Mathematics", "Science", "English", "Social_Science"]))
    book = draw(st.sampled_from(["NCERT", "NCERT_Exemplar"]))
    language = draw(st.sampled_from(["English", "Hindi"]))
    page = draw(st.integers(min_value=1, max_value=500))
    return f"{class_name}|{subject}|{book}|{language}|{page}"


@st.composite
def valid_slide_strategy(draw, slide_number: int = None):
    """Generate a valid Slide."""
    if slide_number is None:
        slide_number = draw(st.integers(min_value=1, max_value=8))
    
    slide_types = [SlideType.INTRODUCTION, SlideType.CONCEPT, SlideType.CONCEPT, 
                   SlideType.CONCEPT, SlideType.EXAMPLES, SlideType.PRACTICE,
                   SlideType.REAL_WORLD, SlideType.SUMMARY]
    slide_type = slide_types[slide_number - 1] if slide_number <= 8 else SlideType.CONCEPT
    
    return Slide(
        slide_number=slide_number,
        slide_type=slide_type,
        title=draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        explanation=draw(st.text(min_size=20, max_size=500, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        bullet_points=draw(st.lists(
            st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))),
            min_size=3, max_size=5
        )),
        key_terms=draw(st.lists(st.text(min_size=3, max_size=50), min_size=0, max_size=5)),
        examples=draw(st.lists(st.text(min_size=5, max_size=100), min_size=0, max_size=3)),
        diagram_prompt=draw(st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        source_references=draw(st.lists(valid_source_strategy(), min_size=0, max_size=3))
    )


@st.composite
def valid_lesson_strategy(draw):
    """Generate a valid Lesson with exactly 8 slides."""
    slides = [draw(valid_slide_strategy(slide_number=i)) for i in range(1, 9)]
    
    return Lesson(
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"])),
        subject=draw(st.sampled_from(["Mathematics", "Science", "English"])),
        topic=draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        slides=slides,
        validation_score=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    )


@st.composite
def valid_mcq_option_strategy(draw, is_correct: bool = None):
    """Generate a valid MCQ option."""
    if is_correct is None:
        is_correct = draw(st.booleans())
    return MCQOption(
        option_text=draw(st.text(min_size=3, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        is_correct=is_correct
    )


@st.composite
def valid_mcq_strategy(draw):
    """Generate a valid MCQ with exactly 4 options and 1 correct."""
    correct_index = draw(st.integers(min_value=0, max_value=3))
    options = []
    for i in range(4):
        options.append(draw(valid_mcq_option_strategy(is_correct=(i == correct_index))))
    
    return MCQQuestion(
        question_text=draw(st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        difficulty=draw(st.sampled_from(list(DifficultyLevel))),
        options=options,
        source_reference=draw(valid_source_strategy())
    )


# =============================================================================
# Property 4: Lesson Structure Invariant
# =============================================================================

class TestLessonStructureInvariant:
    """
    Feature: module-lesson-builder, Property 4: Lesson Structure Invariant
    
    For any generated lesson, the number of slides must equal exactly 8.
    Validates: Requirements 3.1
    """

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_lesson_has_exactly_8_slides(self, lesson: Lesson):
        """Property 4: Lesson must have exactly 8 slides."""
        assert len(lesson.slides) == 8, f"Expected 8 slides, got {len(lesson.slides)}"

    @given(st.lists(valid_slide_strategy(), min_size=1, max_size=7))
    @settings(max_examples=10)
    def test_lesson_rejects_fewer_than_8_slides(self, slides):
        """Lesson creation should fail with fewer than 8 slides."""
        # Renumber slides
        for i, slide in enumerate(slides, 1):
            slide.slide_number = i
        
        with pytest.raises(ValidationError) as exc_info:
            Lesson(
                class_name="Class_10",
                subject="Mathematics",
                topic="Algebra",
                slides=slides,
                validation_score=0.8
            )
        assert "8 slides" in str(exc_info.value).lower()

    @given(st.lists(valid_slide_strategy(), min_size=9, max_size=12))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_lesson_rejects_more_than_8_slides(self, slides):
        """Lesson creation should fail with more than 8 slides."""
        # Renumber slides
        for i, slide in enumerate(slides, 1):
            slide.slide_number = i
        
        with pytest.raises(ValidationError) as exc_info:
            Lesson(
                class_name="Class_10",
                subject="Mathematics",
                topic="Algebra",
                slides=slides,
                validation_score=0.8
            )
        assert "8 slides" in str(exc_info.value).lower()

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_slides_are_numbered_1_to_8(self, lesson: Lesson):
        """Slides must be numbered sequentially from 1 to 8."""
        for i, slide in enumerate(lesson.slides, 1):
            assert slide.slide_number == i, f"Slide {i} has number {slide.slide_number}"


# =============================================================================
# Property 12: MCQ Structure Invariant
# =============================================================================

class TestMCQStructureInvariant:
    """
    Feature: module-lesson-builder, Property 12: MCQ Structure Invariant
    
    For any MCQ question, there must be exactly 4 options, 
    and exactly one option must be marked as correct.
    Validates: Requirements 5.5
    """

    @given(valid_mcq_strategy())
    @settings(max_examples=10)
    def test_mcq_has_exactly_4_options(self, mcq: MCQQuestion):
        """Property 12: MCQ must have exactly 4 options."""
        assert len(mcq.options) == 4, f"Expected 4 options, got {len(mcq.options)}"

    @given(valid_mcq_strategy())
    @settings(max_examples=10)
    def test_mcq_has_exactly_one_correct_option(self, mcq: MCQQuestion):
        """Property 12: MCQ must have exactly 1 correct option."""
        correct_count = sum(1 for opt in mcq.options if opt.is_correct)
        assert correct_count == 1, f"Expected 1 correct option, got {correct_count}"

    @given(st.lists(valid_mcq_option_strategy(is_correct=False), min_size=3, max_size=3))
    @settings(max_examples=10)
    def test_mcq_rejects_fewer_than_4_options(self, options):
        """MCQ creation should fail with fewer than 4 options."""
        with pytest.raises(ValidationError) as exc_info:
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=options,
                source_reference="Class_10|Mathematics|NCERT|English|42"
            )
        assert "4 options" in str(exc_info.value).lower()

    @given(st.lists(valid_mcq_option_strategy(is_correct=False), min_size=5, max_size=6))
    @settings(max_examples=10)
    def test_mcq_rejects_more_than_4_options(self, options):
        """MCQ creation should fail with more than 4 options."""
        with pytest.raises(ValidationError) as exc_info:
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=options,
                source_reference="Class_10|Mathematics|NCERT|English|42"
            )
        assert "4 options" in str(exc_info.value).lower()

    def test_mcq_rejects_zero_correct_options(self):
        """MCQ creation should fail with no correct options."""
        options = [
            MCQOption(option_text="Option A", is_correct=False),
            MCQOption(option_text="Option B", is_correct=False),
            MCQOption(option_text="Option C", is_correct=False),
            MCQOption(option_text="Option D", is_correct=False),
        ]
        with pytest.raises(ValidationError) as exc_info:
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=options,
                source_reference="Class_10|Mathematics|NCERT|English|42"
            )
        assert "1 correct" in str(exc_info.value).lower()

    def test_mcq_rejects_multiple_correct_options(self):
        """MCQ creation should fail with multiple correct options."""
        options = [
            MCQOption(option_text="Option A", is_correct=True),
            MCQOption(option_text="Option B", is_correct=True),
            MCQOption(option_text="Option C", is_correct=False),
            MCQOption(option_text="Option D", is_correct=False),
        ]
        with pytest.raises(ValidationError) as exc_info:
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=options,
                source_reference="Class_10|Mathematics|NCERT|English|42"
            )
        assert "1 correct" in str(exc_info.value).lower()
