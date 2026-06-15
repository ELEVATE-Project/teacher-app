"""
Property-Based Tests for ImageGenerator
=======================================

Tests using Hypothesis to validate correctness properties for image generation.

Property 7: Diagram Generation Success - returns result or graceful failure
Property 8: Diagram-Slide Association - one diagram per slide

Validates: Requirements 4.1, 4.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import asyncio
import sys
import os

# Add the Server directory to path for direct imports
server_path = os.path.join(os.path.dirname(__file__), '..', '..')
if server_path not in sys.path:
    sys.path.insert(0, server_path)

# Import directly from the image_generator module file to avoid __init__.py chain
import importlib.util
spec = importlib.util.spec_from_file_location(
    "image_generator", 
    os.path.join(os.path.dirname(__file__), '..', 'generators', 'image_generator.py')
)
image_generator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image_generator_module)

ImageGenerator = image_generator_module.ImageGenerator
PlaceholderImageAPI = image_generator_module.PlaceholderImageAPI
DiagramResult = image_generator_module.DiagramResult

# Import schemas directly
from module.models.schemas import (
    Slide,
    SlideType,
    Lesson,
)


# =============================================================================
# Custom Strategies for Image Generator Tests
# =============================================================================

@st.composite
def valid_prompt_strategy(draw):
    """Generate valid diagram prompts."""
    prompt_types = [
        "A labeled diagram showing",
        "A simple flowchart depicting",
        "An illustrated comparison of",
        "A step-by-step visual guide for",
        "A concept map connecting",
    ]
    
    prompt_start = draw(st.sampled_from(prompt_types))
    topic = draw(st.text(
        min_size=5, max_size=100,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'Z'))
    ))
    assume(topic.strip())
    
    return f"{prompt_start} {topic}"


@st.composite
def valid_class_level_strategy(draw):
    """Generate valid class levels."""
    return draw(st.sampled_from([
        "Class_1", "Class_2", "Class_3", "Class_4", "Class_5",
        "Class_6", "Class_7", "Class_8", "Class_9", "Class_10"
    ]))


@st.composite
def valid_style_strategy(draw):
    """Generate valid diagram styles."""
    return draw(st.sampled_from(["educational", "simple", "detailed"]))


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
    SlideType.INTRODUCTION,
    SlideType.CONCEPT,
    SlideType.CONCEPT,
    SlideType.CONCEPT,
    SlideType.EXAMPLES,
    SlideType.PRACTICE,
    SlideType.REAL_WORLD,
    SlideType.SUMMARY,
]


@st.composite
def valid_slide_strategy(draw, slide_number: int):
    """Generate a valid Slide with the correct type for its position."""
    slide_type = EXPECTED_SLIDE_SEQUENCE[slide_number - 1]
    
    title = draw(st.text(
        min_size=5, max_size=100,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(title.strip())
    
    explanation = draw(st.text(
        min_size=20, max_size=500,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(explanation.strip())
    
    bullet_points = draw(st.lists(
        st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))).filter(lambda x: x.strip()),
        min_size=3, max_size=5
    ))
    
    diagram_prompt = draw(valid_prompt_strategy())
    
    return Slide(
        slide_number=slide_number,
        slide_type=slide_type,
        title=title,
        explanation=explanation,
        bullet_points=bullet_points,
        key_terms=draw(st.lists(st.text(min_size=3, max_size=50), min_size=0, max_size=5)),
        examples=draw(st.lists(st.text(min_size=5, max_size=100), min_size=0, max_size=3)),
        diagram_prompt=diagram_prompt,
        diagram_url=None,  # No diagram generated yet
        source_references=draw(st.lists(valid_source_strategy(), min_size=0, max_size=3))
    )


@st.composite
def valid_lesson_strategy(draw):
    """Generate a valid Lesson with 8 slides."""
    slides = [draw(valid_slide_strategy(slide_number=i)) for i in range(1, 9)]
    
    return Lesson(
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"])),
        subject=draw(st.sampled_from(["Mathematics", "Science", "English"])),
        topic=draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))).filter(lambda x: x.strip())),
        slides=slides,
        validation_score=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    )


# =============================================================================
# Property 7: Diagram Generation Success
# =============================================================================

class TestDiagramGenerationSuccess:
    """
    Feature: module-lesson-builder, Property 7: Diagram Generation Success
    
    For any valid diagram prompt, the Image_Generator must return either 
    a successful result with image data or a graceful failure with error information.
    
    Validates: Requirements 4.1
    """

    @given(
        prompt=valid_prompt_strategy(),
        class_level=valid_class_level_strategy(),
        style=valid_style_strategy()
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_generate_diagram_returns_diagram_result(self, prompt, class_level, style):
        """Property 7: generate_diagram always returns a DiagramResult."""
        generator = ImageGenerator(api_backend="placeholder")
        
        result = asyncio.get_event_loop().run_until_complete(
            generator.generate_diagram(prompt=prompt, style=style, class_level=class_level)
        )
        
        # Must return a DiagramResult
        assert isinstance(result, DiagramResult), \
            f"Expected DiagramResult, got {type(result)}"
        
        # Must have prompt_used field populated
        assert result.prompt_used is not None, "prompt_used must not be None"
        assert len(result.prompt_used) > 0, "prompt_used must not be empty"

    @given(
        prompt=valid_prompt_strategy(),
        class_level=valid_class_level_strategy()
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_generate_diagram_success_or_graceful_failure(self, prompt, class_level):
        """Property 7: Result is either success with data or failure with error."""
        generator = ImageGenerator(api_backend="placeholder")
        
        result = asyncio.get_event_loop().run_until_complete(
            generator.generate_diagram(prompt=prompt, class_level=class_level)
        )
        
        # Either success is True OR error is populated
        if result.success:
            # Success case: may have image_url or image_base64 (placeholder won't have actual data)
            # But prompt_used must be set
            assert result.prompt_used, "Successful result must have prompt_used"
        else:
            # Failure case: must have error message
            assert result.error is not None, "Failed result must have error message"
            assert len(result.error) > 0, "Error message must not be empty"

    @given(prompt=st.text(min_size=0, max_size=5))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_empty_or_short_prompt_handled_gracefully(self, prompt):
        """Property 7: Empty or very short prompts are handled gracefully."""
        generator = ImageGenerator(api_backend="placeholder")
        
        result = asyncio.get_event_loop().run_until_complete(
            generator.generate_diagram(prompt=prompt)
        )
        
        # Must return a DiagramResult (not raise exception)
        assert isinstance(result, DiagramResult)
        
        # Empty prompts should fail gracefully
        if not prompt or not prompt.strip():
            assert result.success is False or result.error is not None

    def test_placeholder_api_returns_success(self):
        """Placeholder API should return success with no actual image."""
        generator = ImageGenerator(api_backend="placeholder")
        
        result = asyncio.get_event_loop().run_until_complete(
            generator.generate_diagram(
                prompt="A labeled diagram showing the water cycle",
                class_level="Class_6"
            )
        )
        
        assert result.success is True
        assert result.prompt_used is not None
        # Placeholder doesn't generate actual images
        assert result.image_url is None
        assert result.image_base64 is None

    def test_unknown_api_backend_falls_back_to_placeholder(self):
        """Unknown API backend should fall back to placeholder."""
        generator = ImageGenerator(api_backend="unknown_api")
        
        assert generator.api_backend == "placeholder"
        
        result = asyncio.get_event_loop().run_until_complete(
            generator.generate_diagram(prompt="Test diagram")
        )
        
        assert isinstance(result, DiagramResult)

    def test_supported_apis_list(self):
        """ImageGenerator should list supported APIs."""
        generator = ImageGenerator()
        
        supported = generator.get_supported_apis()
        
        assert "placeholder" in supported
        assert "openai" in supported
        assert "stability" in supported

    def test_current_api_getter(self):
        """ImageGenerator should report current API backend."""
        generator = ImageGenerator(api_backend="placeholder")
        assert generator.get_current_api() == "placeholder"


# =============================================================================
# Property 8: Diagram-Slide Association
# =============================================================================

class TestDiagramSlideAssociation:
    """
    Feature: module-lesson-builder, Property 8: Diagram-Slide Association
    
    For any lesson with generated diagrams, each diagram must be associated 
    with exactly one slide, and each slide must have at most one diagram.
    
    Validates: Requirements 4.5
    """

    @given(lesson=valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_each_slide_has_at_most_one_diagram_url(self, lesson: Lesson):
        """Property 8: Each slide has at most one diagram_url field."""
        for slide in lesson.slides:
            # diagram_url is a single Optional[str], not a list
            # This is enforced by the schema, but we verify the invariant
            assert not isinstance(slide.diagram_url, list), \
                f"Slide {slide.slide_number} has multiple diagram URLs"
            
            # If diagram_url is set, it should be a string
            if slide.diagram_url is not None:
                assert isinstance(slide.diagram_url, str), \
                    f"Slide {slide.slide_number} diagram_url is not a string"

    @given(lesson=valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_each_slide_has_exactly_one_diagram_prompt(self, lesson: Lesson):
        """Property 8: Each slide has exactly one diagram_prompt."""
        for slide in lesson.slides:
            # diagram_prompt is a required string field
            assert slide.diagram_prompt is not None, \
                f"Slide {slide.slide_number} has no diagram_prompt"
            assert isinstance(slide.diagram_prompt, str), \
                f"Slide {slide.slide_number} diagram_prompt is not a string"
            assert len(slide.diagram_prompt) >= 5, \
                f"Slide {slide.slide_number} diagram_prompt is too short"

    @given(lesson=valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_diagram_generation_maintains_one_to_one_association(self, lesson: Lesson):
        """Property 8: Generating diagrams maintains one-to-one slide association."""
        generator = ImageGenerator(api_backend="placeholder")
        
        # Generate diagrams for each slide
        diagram_results = []
        for slide in lesson.slides:
            result = asyncio.get_event_loop().run_until_complete(
                generator.generate_diagram(
                    prompt=slide.diagram_prompt,
                    class_level=lesson.class_name
                )
            )
            diagram_results.append((slide.slide_number, result))
        
        # Verify one result per slide
        assert len(diagram_results) == 8, "Should have one diagram result per slide"
        
        # Verify each slide number appears exactly once
        slide_numbers = [sr[0] for sr in diagram_results]
        assert len(set(slide_numbers)) == 8, "Each slide should have exactly one diagram"

    def test_slide_diagram_url_is_single_value(self):
        """Slide schema enforces single diagram_url value."""
        slide = Slide(
            slide_number=1,
            slide_type=SlideType.INTRODUCTION,
            title="Introduction to Photosynthesis",
            explanation="This slide introduces the concept of photosynthesis.",
            bullet_points=["Plants make food", "Sunlight is needed", "Oxygen is released"],
            diagram_prompt="A labeled diagram showing the photosynthesis process",
            diagram_url="https://example.com/diagram.png"
        )
        
        # diagram_url is a single string, not a list
        assert isinstance(slide.diagram_url, str)
        assert slide.diagram_url == "https://example.com/diagram.png"

    def test_slide_without_diagram_url_is_valid(self):
        """Slides without diagram_url are valid (diagram not yet generated)."""
        slide = Slide(
            slide_number=1,
            slide_type=SlideType.INTRODUCTION,
            title="Introduction to Photosynthesis",
            explanation="This slide introduces the concept of photosynthesis.",
            bullet_points=["Plants make food", "Sunlight is needed", "Oxygen is released"],
            diagram_prompt="A labeled diagram showing the photosynthesis process",
            diagram_url=None  # No diagram generated yet
        )
        
        assert slide.diagram_url is None
        # But diagram_prompt is still required
        assert slide.diagram_prompt is not None


# =============================================================================
# Additional Tests for Prompt Enhancement
# =============================================================================

class TestPromptEnhancement:
    """Tests for the prompt enhancement functionality."""

    @given(
        prompt=valid_prompt_strategy(),
        class_level=valid_class_level_strategy()
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_enhanced_prompt_contains_original(self, prompt, class_level):
        """Enhanced prompt should contain the original prompt content."""
        generator = ImageGenerator(api_backend="placeholder")
        
        enhanced = generator._enhance_prompt_for_education(
            prompt=prompt,
            class_level=class_level
        )
        
        # Original prompt content should be in enhanced version
        assert prompt.strip() in enhanced, \
            "Enhanced prompt should contain original prompt"

    @given(class_level=valid_class_level_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_enhanced_prompt_includes_style_keywords(self, class_level):
        """Enhanced prompt should include educational style keywords."""
        generator = ImageGenerator(api_backend="placeholder")
        
        enhanced = generator._enhance_prompt_for_education(
            prompt="A diagram of a cell",
            class_level=class_level
        )
        
        # Should include some educational keywords
        educational_keywords = ["educational", "diagram", "clear", "labeled", "simple"]
        has_keyword = any(kw in enhanced.lower() for kw in educational_keywords)
        assert has_keyword, "Enhanced prompt should include educational keywords"

    def test_different_styles_produce_different_prefixes(self):
        """Different styles should produce different prompt prefixes."""
        generator = ImageGenerator(api_backend="placeholder")
        
        educational = generator._enhance_prompt_for_education(
            prompt="Test", class_level="Class_8", style="educational"
        )
        simple = generator._enhance_prompt_for_education(
            prompt="Test", class_level="Class_8", style="simple"
        )
        detailed = generator._enhance_prompt_for_education(
            prompt="Test", class_level="Class_8", style="detailed"
        )
        
        # Each style should have different prefix
        assert "Educational diagram" in educational
        assert "Simple" in simple or "minimalist" in simple
        assert "Detailed" in detailed
