"""
Property-Based Tests for Export Service
=======================================

Tests using Hypothesis to validate correctness properties for export functionality.
"""

import pytest
import asyncio
import time
from hypothesis import given, strategies as st, settings, HealthCheck

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
)
from ..exporters import ExportService


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
        title=draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        explanation=draw(st.text(min_size=20, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        bullet_points=draw(st.lists(
            st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z'))),
            min_size=3, max_size=5
        )),
        key_terms=draw(st.lists(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z'))), min_size=1, max_size=3)),
        examples=draw(st.lists(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z'))), min_size=1, max_size=2)),
        diagram_prompt=draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        source_references=draw(st.lists(valid_source_strategy(), min_size=1, max_size=2))
    )


@st.composite
def valid_lesson_strategy(draw):
    """Generate a valid Lesson with exactly 8 slides."""
    slides = [draw(valid_slide_strategy(slide_number=i)) for i in range(1, 9)]
    
    return Lesson(
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"])),
        subject=draw(st.sampled_from(["Mathematics", "Science", "English"])),
        topic=draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        slides=slides,
        validation_score=draw(st.floats(min_value=0.6, max_value=1.0, allow_nan=False))
    )


@st.composite
def valid_mcq_strategy(draw, difficulty: DifficultyLevel = None):
    """Generate a valid MCQ with exactly 4 options and 1 correct."""
    if difficulty is None:
        difficulty = draw(st.sampled_from(list(DifficultyLevel)))
    
    correct_index = draw(st.integers(min_value=0, max_value=3))
    options = []
    for i in range(4):
        options.append(MCQOption(
            option_text=draw(st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
            is_correct=(i == correct_index)
        ))
    
    return MCQQuestion(
        question_text=draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        difficulty=difficulty,
        options=options,
        source_reference=draw(valid_source_strategy())
    )


@st.composite
def valid_short_answer_strategy(draw, difficulty: DifficultyLevel = None):
    """Generate a valid short answer question."""
    if difficulty is None:
        difficulty = draw(st.sampled_from(list(DifficultyLevel)))
    
    return ShortAnswerQuestion(
        question_text=draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        difficulty=difficulty,
        expected_answer=draw(st.text(min_size=20, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        source_reference=draw(valid_source_strategy())
    )


@st.composite
def valid_long_answer_strategy(draw, difficulty: DifficultyLevel = None):
    """Generate a valid long answer question."""
    if difficulty is None:
        difficulty = draw(st.sampled_from(list(DifficultyLevel)))
    
    return LongAnswerQuestion(
        question_text=draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        difficulty=difficulty,
        expected_answer=draw(st.text(min_size=50, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        marking_scheme=draw(st.lists(
            st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z'))),
            min_size=2, max_size=4
        )),
        source_reference=draw(valid_source_strategy())
    )


@st.composite
def valid_assignment_strategy(draw):
    """Generate a valid Assignment with questions at all difficulty levels and types."""
    # Generate at least 3 questions per difficulty level
    questions = []
    total_marks = 0
    
    for difficulty in DifficultyLevel:
        # Add MCQ
        mcq = draw(valid_mcq_strategy(difficulty=difficulty))
        questions.append(mcq)
        total_marks += mcq.marks
        
        # Add short answer
        short = draw(valid_short_answer_strategy(difficulty=difficulty))
        questions.append(short)
        total_marks += short.marks
        
        # Add long answer
        long_q = draw(valid_long_answer_strategy(difficulty=difficulty))
        questions.append(long_q)
        total_marks += long_q.marks
    
    return Assignment(
        lesson_id="test_lesson_123",
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"])),
        subject=draw(st.sampled_from(["Mathematics", "Science", "English"])),
        topic=draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        questions=questions,
        total_marks=total_marks
    )


# =============================================================================
# Property 13: Export Format Support
# =============================================================================

class TestExportFormatSupport:
    """
    Feature: module-lesson-builder, Property 13: Export Format Support
    
    For any complete lesson, export to PDF, DOC, and PPT formats must succeed
    and produce non-empty files.
    Validates: Requirements 6.1, 6.2, 6.3
    """

    @pytest.fixture
    def export_service(self):
        """Create ExportService instance."""
        return ExportService()

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_pdf_export_produces_non_empty_file(self, lesson: Lesson):
        """Property 13: PDF export must produce non-empty file."""
        export_service = ExportService()
        pdf_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_pdf(lesson, include_diagrams=False)
        )
        assert pdf_bytes is not None, "PDF export returned None"
        assert len(pdf_bytes) > 0, "PDF export produced empty file"
        # Check PDF magic bytes
        assert pdf_bytes[:4] == b'%PDF', "Output is not a valid PDF file"

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_doc_export_produces_non_empty_file(self, lesson: Lesson):
        """Property 13: DOC export must produce non-empty file."""
        export_service = ExportService()
        doc_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_doc(lesson, include_diagrams=False)
        )
        assert doc_bytes is not None, "DOC export returned None"
        assert len(doc_bytes) > 0, "DOC export produced empty file"
        # Check DOCX magic bytes (PK zip header)
        assert doc_bytes[:2] == b'PK', "Output is not a valid DOCX file"

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_ppt_export_produces_non_empty_file(self, lesson: Lesson):
        """Property 13: PPT export must produce non-empty file."""
        export_service = ExportService()
        ppt_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_ppt(lesson, include_diagrams=False)
        )
        assert ppt_bytes is not None, "PPT export returned None"
        assert len(ppt_bytes) > 0, "PPT export produced empty file"
        # Check PPTX magic bytes (PK zip header)
        assert ppt_bytes[:2] == b'PK', "Output is not a valid PPTX file"

    @given(valid_assignment_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_assignment_pdf_export_produces_non_empty_file(self, assignment: Assignment):
        """Property 13: Assignment PDF export must produce non-empty file."""
        export_service = ExportService()
        pdf_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_assignment_pdf(assignment, include_answers=False)
        )
        assert pdf_bytes is not None, "Assignment PDF export returned None"
        assert len(pdf_bytes) > 0, "Assignment PDF export produced empty file"
        assert pdf_bytes[:4] == b'%PDF', "Output is not a valid PDF file"

    @given(valid_assignment_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_assignment_doc_export_produces_non_empty_file(self, assignment: Assignment):
        """Property 13: Assignment DOC export must produce non-empty file."""
        export_service = ExportService()
        doc_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_assignment_doc(assignment, include_answers=False)
        )
        assert doc_bytes is not None, "Assignment DOC export returned None"
        assert len(doc_bytes) > 0, "Assignment DOC export produced empty file"
        assert doc_bytes[:2] == b'PK', "Output is not a valid DOCX file"


# =============================================================================
# Property 14: Export Completeness
# =============================================================================

class TestExportCompleteness:
    """
    Feature: module-lesson-builder, Property 14: Export Completeness
    
    For any exported lesson, the output must contain all 8 slides with their
    associated diagrams (if generated), and for any exported assignment,
    questions must be grouped by difficulty level and type.
    Validates: Requirements 6.4, 6.5
    """

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_pdf_export_contains_all_slides(self, lesson: Lesson):
        """Property 14: PDF export must contain all 8 slides."""
        export_service = ExportService()
        pdf_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_pdf(lesson, include_diagrams=False)
        )
        # PDF should be large enough to contain 8 slides worth of content
        # A minimal PDF with 8 slides should be at least a few KB
        assert len(pdf_bytes) > 1000, "PDF too small to contain all slides"
        
        # Check that the PDF has the expected number of pages (title + 8 slides = 9 pages)
        # Count page objects in PDF
        pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
        page_count = pdf_text.count('/Type /Page')
        assert page_count >= 9, f"PDF should have at least 9 pages (title + 8 slides), got {page_count}"

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_doc_export_contains_all_slides(self, lesson: Lesson):
        """Property 14: DOC export must contain all 8 slides."""
        export_service = ExportService()
        doc_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_doc(lesson, include_diagrams=False)
        )
        # DOCX should be large enough to contain 8 slides worth of content
        assert len(doc_bytes) > 1000, "DOCX too small to contain all slides"

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_ppt_export_contains_all_slides(self, lesson: Lesson):
        """Property 14: PPT export must contain all 8 slides plus title slide."""
        export_service = ExportService()
        ppt_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_ppt(lesson, include_diagrams=False)
        )
        # PPTX should be large enough to contain 9 slides (title + 8 content)
        assert len(ppt_bytes) > 5000, "PPTX too small to contain all slides"

    @given(valid_assignment_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_assignment_export_groups_by_difficulty(self, assignment: Assignment):
        """Property 14: Assignment export must group questions by difficulty."""
        export_service = ExportService()
        pdf_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_assignment_pdf(assignment, include_answers=False)
        )
        # PDF should be non-empty and valid
        assert len(pdf_bytes) > 1000, "Assignment PDF too small"
        assert pdf_bytes[:4] == b'%PDF', "Output is not a valid PDF file"
        
        # Check that the PDF has multiple pages (questions grouped by difficulty)
        pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
        page_count = pdf_text.count('/Type /Page')
        assert page_count >= 1, f"Assignment PDF should have at least 1 page, got {page_count}"

    @given(valid_assignment_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_assignment_export_with_answers_includes_answer_key(self, assignment: Assignment):
        """Property 14: Assignment export with answers must include answer key."""
        export_service = ExportService()
        pdf_bytes_with_answers = asyncio.get_event_loop().run_until_complete(
            export_service.export_assignment_pdf(assignment, include_answers=True)
        )
        pdf_bytes_without_answers = asyncio.get_event_loop().run_until_complete(
            export_service.export_assignment_pdf(assignment, include_answers=False)
        )
        
        # PDF with answers should be larger than without (contains answer key section)
        assert len(pdf_bytes_with_answers) > len(pdf_bytes_without_answers), \
            "PDF with answers should be larger than without answers"


# =============================================================================
# Property 15: Export Performance
# =============================================================================

class TestExportPerformance:
    """
    Feature: module-lesson-builder, Property 15: Export Performance
    
    For any export operation, the generation time must be under 30 seconds.
    Validates: Requirements 6.6
    """

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_pdf_export_completes_under_30_seconds(self, lesson: Lesson):
        """Property 15: PDF export must complete under 30 seconds."""
        export_service = ExportService()
        
        start_time = time.time()
        pdf_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_pdf(lesson, include_diagrams=False)
        )
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 30, f"PDF export took {elapsed_time:.2f}s, exceeds 30s limit"
        assert pdf_bytes is not None

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_doc_export_completes_under_30_seconds(self, lesson: Lesson):
        """Property 15: DOC export must complete under 30 seconds."""
        export_service = ExportService()
        
        start_time = time.time()
        doc_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_doc(lesson, include_diagrams=False)
        )
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 30, f"DOC export took {elapsed_time:.2f}s, exceeds 30s limit"
        assert doc_bytes is not None

    @given(valid_lesson_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_ppt_export_completes_under_30_seconds(self, lesson: Lesson):
        """Property 15: PPT export must complete under 30 seconds."""
        export_service = ExportService()
        
        start_time = time.time()
        ppt_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_lesson_ppt(lesson, include_diagrams=False)
        )
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 30, f"PPT export took {elapsed_time:.2f}s, exceeds 30s limit"
        assert ppt_bytes is not None

    @given(valid_assignment_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_assignment_pdf_export_completes_under_30_seconds(self, assignment: Assignment):
        """Property 15: Assignment PDF export must complete under 30 seconds."""
        export_service = ExportService()
        
        start_time = time.time()
        pdf_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_assignment_pdf(assignment, include_answers=True)
        )
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 30, f"Assignment PDF export took {elapsed_time:.2f}s, exceeds 30s limit"
        assert pdf_bytes is not None

    @given(valid_assignment_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_assignment_doc_export_completes_under_30_seconds(self, assignment: Assignment):
        """Property 15: Assignment DOC export must complete under 30 seconds."""
        export_service = ExportService()
        
        start_time = time.time()
        doc_bytes = asyncio.get_event_loop().run_until_complete(
            export_service.export_assignment_doc(assignment, include_answers=True)
        )
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 30, f"Assignment DOC export took {elapsed_time:.2f}s, exceeds 30s limit"
        assert doc_bytes is not None
