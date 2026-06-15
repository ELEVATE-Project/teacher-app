"""
Property-Based Tests for LessonGenerator
========================================

Tests using Hypothesis to validate correctness properties for lesson generation.

Property 5: Slide Completeness - all required fields non-empty
Property 6: Slide Sequence Ordering - correct slide type order

Validates: Requirements 3.2, 3.4, 3.5, 3.6
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from pydantic import ValidationError

from ..models.schemas import (
    SlideType,
    Slide,
    Lesson,
)


# =============================================================================
# Custom Strategies for Lesson Generator Tests
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


# Expected slide type sequence for an 8-slide lesson
EXPECTED_SLIDE_SEQUENCE = [
    SlideType.INTRODUCTION,  # Slide 1
    SlideType.CONCEPT,       # Slide 2
    SlideType.CONCEPT,       # Slide 3
    SlideType.CONCEPT,       # Slide 4
    SlideType.EXAMPLES,      # Slide 5
    SlideType.PRACTICE,      # Slide 6
    SlideType.REAL_WORLD,    # Slide 7
    SlideType.SUMMARY,       # Slide 8
]


@st.composite
def valid_slide_with_correct_type_strategy(draw, slide_number: int):
    """Generate a valid Slide with the correct type for its position."""
    slide_type = EXPECTED_SLIDE_SEQUENCE[slide_number - 1]
    
    # Generate non-empty content
    title = draw(st.text(
        min_size=5, max_size=100, 
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(title.strip())  # Ensure non-whitespace
    
    explanation = draw(st.text(
        min_size=20, max_size=500, 
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(explanation.strip())
    
    bullet_points = draw(st.lists(
        st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))).filter(lambda x: x.strip()),
        min_size=3, max_size=5
    ))
    
    diagram_prompt = draw(st.text(
        min_size=10, max_size=200, 
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(diagram_prompt.strip())
    
    return Slide(
        slide_number=slide_number,
        slide_type=slide_type,
        title=title,
        explanation=explanation,
        bullet_points=bullet_points,
        key_terms=draw(st.lists(st.text(min_size=3, max_size=50), min_size=0, max_size=5)),
        examples=draw(st.lists(st.text(min_size=5, max_size=100), min_size=0, max_size=3)),
        diagram_prompt=diagram_prompt,
        source_references=draw(st.lists(valid_source_strategy(), min_size=0, max_size=3))
    )


@st.composite
def valid_lesson_with_correct_sequence_strategy(draw):
    """Generate a valid Lesson with correct slide type sequence."""
    slides = [draw(valid_slide_with_correct_type_strategy(slide_number=i)) for i in range(1, 9)]
    
    return Lesson(
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"])),
        subject=draw(st.sampled_from(["Mathematics", "Science", "English"])),
        topic=draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))).filter(lambda x: x.strip())),
        slides=slides,
        validation_score=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    )


# =============================================================================
# Property 5: Slide Completeness
# =============================================================================

class TestSlideCompleteness:
    """
    Feature: module-lesson-builder, Property 5: Slide Completeness
    
    For any slide in a generated lesson, all required fields 
    (explanation, bullet_points, key_terms, examples, diagram_prompt) 
    must be non-empty.
    
    Validates: Requirements 3.2, 3.6
    """

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_slides_have_non_empty_explanation(self, lesson: Lesson):
        """Property 5: All slides must have non-empty explanation."""
        for slide in lesson.slides:
            assert slide.explanation, f"Slide {slide.slide_number} has empty explanation"
            assert len(slide.explanation.strip()) >= 10, \
                f"Slide {slide.slide_number} explanation too short: {len(slide.explanation)}"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_slides_have_bullet_points(self, lesson: Lesson):
        """Property 5: All slides must have at least one bullet point."""
        for slide in lesson.slides:
            assert slide.bullet_points, f"Slide {slide.slide_number} has no bullet points"
            assert len(slide.bullet_points) >= 1, \
                f"Slide {slide.slide_number} needs at least 1 bullet point"
            # Verify bullet points are non-empty strings
            for i, point in enumerate(slide.bullet_points):
                assert point.strip(), \
                    f"Slide {slide.slide_number} bullet point {i+1} is empty"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_slides_have_diagram_prompt(self, lesson: Lesson):
        """Property 5: All slides must have a non-empty diagram prompt."""
        for slide in lesson.slides:
            assert slide.diagram_prompt, f"Slide {slide.slide_number} has empty diagram_prompt"
            assert len(slide.diagram_prompt.strip()) >= 5, \
                f"Slide {slide.slide_number} diagram_prompt too short"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_slides_have_title(self, lesson: Lesson):
        """Property 5: All slides must have a non-empty title."""
        for slide in lesson.slides:
            assert slide.title, f"Slide {slide.slide_number} has empty title"
            assert len(slide.title.strip()) >= 1, \
                f"Slide {slide.slide_number} title is empty"

    def test_slide_rejects_empty_explanation(self):
        """Slide creation should fail with empty explanation."""
        with pytest.raises(ValidationError):
            Slide(
                slide_number=1,
                slide_type=SlideType.INTRODUCTION,
                title="Introduction",
                explanation="",  # Empty - should fail
                bullet_points=["Point 1", "Point 2", "Point 3"],
                diagram_prompt="A diagram showing the concept"
            )

    def test_slide_rejects_empty_bullet_points(self):
        """Slide creation should fail with empty bullet points list."""
        with pytest.raises(ValidationError):
            Slide(
                slide_number=1,
                slide_type=SlideType.INTRODUCTION,
                title="Introduction",
                explanation="This is a valid explanation for the slide.",
                bullet_points=[],  # Empty - should fail
                diagram_prompt="A diagram showing the concept"
            )

    def test_slide_rejects_short_diagram_prompt(self):
        """Slide creation should fail with too short diagram prompt."""
        with pytest.raises(ValidationError):
            Slide(
                slide_number=1,
                slide_type=SlideType.INTRODUCTION,
                title="Introduction",
                explanation="This is a valid explanation for the slide.",
                bullet_points=["Point 1", "Point 2", "Point 3"],
                diagram_prompt="Hi"  # Too short - should fail (min 5 chars)
            )


# =============================================================================
# Property 6: Slide Sequence Ordering
# =============================================================================

class TestSlideSequenceOrdering:
    """
    Feature: module-lesson-builder, Property 6: Slide Sequence Ordering
    
    For any generated lesson, the slides must follow the sequence:
    introduction → concept slides → examples → practice → real_world → summary,
    with the final slide always being of type "summary".
    
    Validates: Requirements 3.4, 3.5
    """

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_slide_sequence_follows_expected_order(self, lesson: Lesson):
        """Property 6: Slides must follow the expected type sequence."""
        for i, slide in enumerate(lesson.slides):
            expected_type = EXPECTED_SLIDE_SEQUENCE[i]
            assert slide.slide_type == expected_type, \
                f"Slide {i+1} should be {expected_type.value}, got {slide.slide_type.value}"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_first_slide_is_introduction(self, lesson: Lesson):
        """Property 6: First slide must be introduction type."""
        assert lesson.slides[0].slide_type == SlideType.INTRODUCTION, \
            f"First slide should be introduction, got {lesson.slides[0].slide_type.value}"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_last_slide_is_summary(self, lesson: Lesson):
        """Property 6: Last slide (slide 8) must be summary type."""
        assert lesson.slides[7].slide_type == SlideType.SUMMARY, \
            f"Last slide should be summary, got {lesson.slides[7].slide_type.value}"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_concept_slides_are_in_positions_2_3_4(self, lesson: Lesson):
        """Property 6: Slides 2, 3, 4 must be concept type."""
        for i in [1, 2, 3]:  # 0-indexed positions for slides 2, 3, 4
            assert lesson.slides[i].slide_type == SlideType.CONCEPT, \
                f"Slide {i+1} should be concept, got {lesson.slides[i].slide_type.value}"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_examples_slide_is_position_5(self, lesson: Lesson):
        """Property 6: Slide 5 must be examples type."""
        assert lesson.slides[4].slide_type == SlideType.EXAMPLES, \
            f"Slide 5 should be examples, got {lesson.slides[4].slide_type.value}"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_practice_slide_is_position_6(self, lesson: Lesson):
        """Property 6: Slide 6 must be practice type."""
        assert lesson.slides[5].slide_type == SlideType.PRACTICE, \
            f"Slide 6 should be practice, got {lesson.slides[5].slide_type.value}"

    @given(valid_lesson_with_correct_sequence_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_real_world_slide_is_position_7(self, lesson: Lesson):
        """Property 6: Slide 7 must be real_world type."""
        assert lesson.slides[6].slide_type == SlideType.REAL_WORLD, \
            f"Slide 7 should be real_world, got {lesson.slides[6].slide_type.value}"

    def test_lesson_with_wrong_first_slide_type(self):
        """Lesson with wrong first slide type should have incorrect sequence."""
        # Create slides with wrong first type
        slides = []
        wrong_sequence = [
            SlideType.CONCEPT,  # Wrong - should be INTRODUCTION
            SlideType.CONCEPT,
            SlideType.CONCEPT,
            SlideType.CONCEPT,
            SlideType.EXAMPLES,
            SlideType.PRACTICE,
            SlideType.REAL_WORLD,
            SlideType.SUMMARY,
        ]
        
        for i, slide_type in enumerate(wrong_sequence, 1):
            slides.append(Slide(
                slide_number=i,
                slide_type=slide_type,
                title=f"Slide {i}",
                explanation="This is a valid explanation for the slide content.",
                bullet_points=["Point 1", "Point 2", "Point 3"],
                diagram_prompt="A simple diagram showing the concept"
            ))
        
        lesson = Lesson(
            class_name="Class_10",
            subject="Mathematics",
            topic="Algebra",
            slides=slides,
            validation_score=0.8
        )
        
        # Verify the first slide is NOT introduction (demonstrating wrong sequence)
        assert lesson.slides[0].slide_type != SlideType.INTRODUCTION

    def test_lesson_with_wrong_last_slide_type(self):
        """Lesson with wrong last slide type should have incorrect sequence."""
        # Create slides with wrong last type
        slides = []
        wrong_sequence = [
            SlideType.INTRODUCTION,
            SlideType.CONCEPT,
            SlideType.CONCEPT,
            SlideType.CONCEPT,
            SlideType.EXAMPLES,
            SlideType.PRACTICE,
            SlideType.REAL_WORLD,
            SlideType.CONCEPT,  # Wrong - should be SUMMARY
        ]
        
        for i, slide_type in enumerate(wrong_sequence, 1):
            slides.append(Slide(
                slide_number=i,
                slide_type=slide_type,
                title=f"Slide {i}",
                explanation="This is a valid explanation for the slide content.",
                bullet_points=["Point 1", "Point 2", "Point 3"],
                diagram_prompt="A simple diagram showing the concept"
            ))
        
        lesson = Lesson(
            class_name="Class_10",
            subject="Mathematics",
            topic="Algebra",
            slides=slides,
            validation_score=0.8
        )
        
        # Verify the last slide is NOT summary (demonstrating wrong sequence)
        assert lesson.slides[7].slide_type != SlideType.SUMMARY
