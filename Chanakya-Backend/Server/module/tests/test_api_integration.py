"""
Integration Tests for MODULE API Router
=======================================

Tests for the MODULE API endpoints including topic selection,
lesson generation, storage, and export functionality.

Feature: module-lesson-builder
Validates: Requirements 1.1, 1.2, 1.3, 6.1, 6.2, 6.3, 6.5, 8.1, 8.2, 8.4, 8.5
"""

import pytest
import asyncio
import tempfile
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

# Add the Web_server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Web_server'))

from fastapi.testclient import TestClient
from fastapi import FastAPI

from ..models.schemas import (
    Lesson, Slide, SlideType, Assignment,
    MCQQuestion, ShortAnswerQuestion, LongAnswerQuestion,
    MCQOption, DifficultyLevel, QuestionType, TopicInfo,
    TextbookContent, ValidationReport
)
from ..services.lesson_storage import LessonStorageService
from ..services.topic_selector import TopicSelectorService
from ..exporters.export_service import ExportService


# =============================================================================
# Test Fixtures
# =============================================================================

def create_test_lesson(lesson_id: str = "test-lesson-123") -> Lesson:
    """Create a test lesson with 8 slides."""
    slides = []
    slide_types = [
        SlideType.INTRODUCTION, SlideType.CONCEPT, SlideType.CONCEPT,
        SlideType.CONCEPT, SlideType.EXAMPLES, SlideType.PRACTICE,
        SlideType.REAL_WORLD, SlideType.SUMMARY
    ]
    
    for i, slide_type in enumerate(slide_types, 1):
        slides.append(Slide(
            slide_number=i,
            slide_type=slide_type,
            title=f"Test Slide {i}",
            explanation=f"This is the explanation for slide {i}. It contains enough text to be valid.",
            bullet_points=[f"Point {j}" for j in range(1, 4)],
            key_terms=[f"Term {j}" for j in range(1, 3)],
            examples=[f"Example {j}" for j in range(1, 3)],
            diagram_prompt=f"Generate a diagram for slide {i}",
            source_references=["Class_6|Mathematics|NCERT|English|42"]
        ))
    
    return Lesson(
        id=lesson_id,
        class_name="Class_6",
        subject="Mathematics",
        topic="Algebra",
        slides=slides,
        teacher_id="teacher-123",
        validation_score=0.85,
        created_at=datetime.now(timezone.utc)
    )


def create_test_assignment(lesson_id: str = "test-lesson-123") -> Assignment:
    """Create a test assignment with various question types."""
    questions = [
        MCQQuestion(
            question_text="What is 2 + 2?",
            difficulty=DifficultyLevel.EASY,
            marks=1,
            source_reference="Class_6|Mathematics|NCERT|English|42",
            options=[
                MCQOption(option_text="3", is_correct=False),
                MCQOption(option_text="4", is_correct=True),
                MCQOption(option_text="5", is_correct=False),
                MCQOption(option_text="6", is_correct=False),
            ]
        ),
        ShortAnswerQuestion(
            question_text="Explain what algebra is.",
            difficulty=DifficultyLevel.MEDIUM,
            marks=2,
            source_reference="Class_6|Mathematics|NCERT|English|42",
            expected_answer="Algebra is a branch of mathematics dealing with symbols."
        ),
        LongAnswerQuestion(
            question_text="Describe the importance of algebra in daily life.",
            difficulty=DifficultyLevel.HARD,
            marks=5,
            source_reference="Class_6|Mathematics|NCERT|English|42",
            expected_answer="Algebra is important in daily life because it helps us solve problems involving unknown quantities. It is used in finance, engineering, and science.",
            marking_scheme=["Definition (1 mark)", "Examples (2 marks)", "Conclusion (2 marks)"]
        )
    ]
    
    return Assignment(
        id="test-assignment-123",
        lesson_id=lesson_id,
        class_name="Class_6",
        subject="Mathematics",
        topic="Algebra",
        questions=questions,
        total_marks=8,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass


@pytest.fixture
def storage_service(temp_db_path):
    """Create a LessonStorageService instance with temp database."""
    return LessonStorageService(db_path=temp_db_path)


@pytest.fixture
def export_service():
    """Create an ExportService instance."""
    return ExportService()


def run_async(coro):
    """Helper to run async functions in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =============================================================================
# Topic Selection Tests
# =============================================================================

class TestTopicSelectionEndpoints:
    """Tests for topic selection API endpoints."""

    def test_topic_selector_service_initialization(self):
        """Test that TopicSelectorService can be initialized."""
        # This test verifies the service can be created
        # In production, it would connect to the actual database
        try:
            service = TopicSelectorService()
            assert service is not None
        except FileNotFoundError:
            # Expected if database doesn't exist in test environment
            pytest.skip("Textbook database not available in test environment")

    def test_topic_info_model_validation(self):
        """Test TopicInfo model validation."""
        topic = TopicInfo(
            topic_name="Algebra",
            chapter_number=1,
            page_range="1-20",
            content_count=10
        )
        
        assert topic.topic_name == "Algebra"
        assert topic.chapter_number == 1
        assert topic.page_range == "1-20"
        assert topic.content_count == 10

    def test_topic_info_without_optional_fields(self):
        """Test TopicInfo with only required fields."""
        topic = TopicInfo(
            topic_name="Geometry",
            content_count=5
        )
        
        assert topic.topic_name == "Geometry"
        assert topic.chapter_number is None
        assert topic.page_range is None
        assert topic.content_count == 5


# =============================================================================
# Lesson Storage Tests
# =============================================================================

class TestLessonStorageEndpoints:
    """Tests for lesson storage API endpoints."""

    def test_save_and_retrieve_lesson(self, storage_service):
        """Test saving and retrieving a lesson."""
        lesson = create_test_lesson()
        
        # Save lesson
        lesson_id = run_async(storage_service.save_lesson(lesson))
        assert lesson_id is not None
        
        # Retrieve lesson
        retrieved = run_async(storage_service.get_lesson(lesson_id))
        assert retrieved is not None
        assert retrieved.class_name == lesson.class_name
        assert retrieved.subject == lesson.subject
        assert retrieved.topic == lesson.topic
        assert len(retrieved.slides) == 8

    def test_save_lesson_with_assignment(self, storage_service):
        """Test saving a lesson with its assignment."""
        lesson = create_test_lesson()
        assignment = create_test_assignment()
        
        # Save lesson with assignment
        lesson_id = run_async(storage_service.save_lesson(lesson, assignment))
        
        # Retrieve assignment
        retrieved_assignment = run_async(storage_service.get_assignment_for_lesson(lesson_id))
        assert retrieved_assignment is not None
        assert len(retrieved_assignment.questions) == 3
        assert retrieved_assignment.total_marks == 8

    def test_list_lessons(self, storage_service):
        """Test listing lessons."""
        # Save multiple lessons
        for i in range(3):
            lesson = create_test_lesson(f"lesson-{i}")
            run_async(storage_service.save_lesson(lesson))
        
        # List lessons
        lessons = run_async(storage_service.list_lessons())
        assert len(lessons) == 3

    def test_list_lessons_with_filter(self, storage_service):
        """Test listing lessons with filters."""
        # Save lessons with different classes
        lesson1 = create_test_lesson("lesson-1")
        lesson1 = Lesson(
            id="lesson-1",
            class_name="Class_6",
            subject="Mathematics",
            topic="Algebra",
            slides=lesson1.slides,
            teacher_id="teacher-1",
            validation_score=0.85
        )
        
        lesson2 = create_test_lesson("lesson-2")
        lesson2 = Lesson(
            id="lesson-2",
            class_name="Class_7",
            subject="Science",
            topic="Physics",
            slides=lesson2.slides,
            teacher_id="teacher-2",
            validation_score=0.90
        )
        
        run_async(storage_service.save_lesson(lesson1))
        run_async(storage_service.save_lesson(lesson2))
        
        # Filter by class
        class_6_lessons = run_async(storage_service.list_lessons(class_name="Class_6"))
        assert len(class_6_lessons) == 1
        assert class_6_lessons[0].class_name == "Class_6"

    def test_delete_lesson(self, storage_service):
        """Test deleting a lesson."""
        lesson = create_test_lesson()
        
        # Save lesson
        lesson_id = run_async(storage_service.save_lesson(lesson))
        
        # Verify it exists
        assert run_async(storage_service.lesson_exists(lesson_id)) is True
        
        # Delete lesson
        deleted = run_async(storage_service.delete_lesson(lesson_id))
        assert deleted is True
        
        # Verify it's gone
        assert run_async(storage_service.lesson_exists(lesson_id)) is False

    def test_delete_nonexistent_lesson(self, storage_service):
        """Test deleting a non-existent lesson returns False."""
        deleted = run_async(storage_service.delete_lesson("nonexistent-id"))
        assert deleted is False

    def test_get_nonexistent_lesson(self, storage_service):
        """Test getting a non-existent lesson returns None."""
        lesson = run_async(storage_service.get_lesson("nonexistent-id"))
        assert lesson is None


# =============================================================================
# Export Service Tests
# =============================================================================

class TestExportEndpoints:
    """Tests for export API endpoints."""

    def test_export_lesson_pdf(self, export_service):
        """Test exporting a lesson as PDF."""
        lesson = create_test_lesson()
        
        pdf_bytes = run_async(export_service.export_lesson_pdf(lesson))
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        # PDF files start with %PDF
        assert pdf_bytes[:4] == b'%PDF'

    def test_export_lesson_doc(self, export_service):
        """Test exporting a lesson as DOCX."""
        lesson = create_test_lesson()
        
        doc_bytes = run_async(export_service.export_lesson_doc(lesson))
        
        assert doc_bytes is not None
        assert len(doc_bytes) > 0
        # DOCX files are ZIP archives starting with PK
        assert doc_bytes[:2] == b'PK'

    def test_export_lesson_ppt(self, export_service):
        """Test exporting a lesson as PPTX."""
        lesson = create_test_lesson()
        
        ppt_bytes = run_async(export_service.export_lesson_ppt(lesson))
        
        assert ppt_bytes is not None
        assert len(ppt_bytes) > 0
        # PPTX files are ZIP archives starting with PK
        assert ppt_bytes[:2] == b'PK'

    def test_export_assignment_pdf(self, export_service):
        """Test exporting an assignment as PDF."""
        assignment = create_test_assignment()
        
        pdf_bytes = run_async(export_service.export_assignment_pdf(assignment))
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    def test_export_assignment_pdf_with_answers(self, export_service):
        """Test exporting an assignment as PDF with answer key."""
        assignment = create_test_assignment()
        
        pdf_bytes = run_async(export_service.export_assignment_pdf(
            assignment, include_answers=True
        ))
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    def test_export_assignment_doc(self, export_service):
        """Test exporting an assignment as DOCX."""
        assignment = create_test_assignment()
        
        doc_bytes = run_async(export_service.export_assignment_doc(assignment))
        
        assert doc_bytes is not None
        assert len(doc_bytes) > 0
        assert doc_bytes[:2] == b'PK'


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for API error handling."""

    def test_lesson_validation_requires_8_slides(self):
        """Test that lesson validation requires exactly 8 slides."""
        slides = [
            Slide(
                slide_number=i,
                slide_type=SlideType.CONCEPT,
                title=f"Slide {i}",
                explanation="Test explanation with enough text.",
                bullet_points=["Point 1", "Point 2"],
                diagram_prompt="Test diagram prompt"
            )
            for i in range(1, 6)  # Only 5 slides
        ]
        
        with pytest.raises(ValueError) as exc_info:
            Lesson(
                class_name="Class_6",
                subject="Mathematics",
                topic="Algebra",
                slides=slides,
                validation_score=0.85
            )
        
        assert "exactly 8 slides" in str(exc_info.value)

    def test_mcq_requires_4_options(self):
        """Test that MCQ validation requires exactly 4 options."""
        with pytest.raises(ValueError) as exc_info:
            MCQQuestion(
                question_text="Test question?",
                difficulty=DifficultyLevel.EASY,
                marks=1,
                source_reference="Class_6|Math|NCERT|English|1",
                options=[
                    MCQOption(option_text="A", is_correct=True),
                    MCQOption(option_text="B", is_correct=False),
                ]  # Only 2 options
            )
        
        assert "exactly 4 options" in str(exc_info.value)

    def test_mcq_requires_one_correct_option(self):
        """Test that MCQ validation requires exactly 1 correct option."""
        with pytest.raises(ValueError) as exc_info:
            MCQQuestion(
                question_text="Test question?",
                difficulty=DifficultyLevel.EASY,
                marks=1,
                source_reference="Class_6|Math|NCERT|English|1",
                options=[
                    MCQOption(option_text="A", is_correct=True),
                    MCQOption(option_text="B", is_correct=True),  # Two correct
                    MCQOption(option_text="C", is_correct=False),
                    MCQOption(option_text="D", is_correct=False),
                ]
            )
        
        assert "exactly 1 correct" in str(exc_info.value)

    def test_assignment_total_marks_validation(self):
        """Test that assignment total_marks must match sum of question marks."""
        questions = [
            MCQQuestion(
                question_text="Test?",
                difficulty=DifficultyLevel.EASY,
                marks=1,
                source_reference="Class_6|Math|NCERT|English|1",
                options=[
                    MCQOption(option_text="A", is_correct=True),
                    MCQOption(option_text="B", is_correct=False),
                    MCQOption(option_text="C", is_correct=False),
                    MCQOption(option_text="D", is_correct=False),
                ]
            )
        ]
        
        with pytest.raises(ValueError) as exc_info:
            Assignment(
                lesson_id="test",
                class_name="Class_6",
                subject="Math",
                topic="Test",
                questions=questions,
                total_marks=10  # Should be 1
            )
        
        assert "total_marks" in str(exc_info.value)


# =============================================================================
# Integration Flow Tests
# =============================================================================

class TestFullGenerationFlow:
    """Tests for the complete generation flow."""

    def test_full_lesson_lifecycle(self, storage_service, export_service):
        """Test complete lesson lifecycle: create, save, retrieve, export, delete."""
        # Create lesson and assignment
        lesson = create_test_lesson()
        assignment = create_test_assignment()
        
        # Save
        lesson_id = run_async(storage_service.save_lesson(lesson, assignment))
        assert lesson_id is not None
        
        # Retrieve
        retrieved_lesson = run_async(storage_service.get_lesson(lesson_id))
        assert retrieved_lesson is not None
        assert len(retrieved_lesson.slides) == 8
        
        retrieved_assignment = run_async(storage_service.get_assignment_for_lesson(lesson_id))
        assert retrieved_assignment is not None
        
        # Export
        pdf_bytes = run_async(export_service.export_lesson_pdf(retrieved_lesson))
        assert len(pdf_bytes) > 0
        
        doc_bytes = run_async(export_service.export_lesson_doc(retrieved_lesson))
        assert len(doc_bytes) > 0
        
        ppt_bytes = run_async(export_service.export_lesson_ppt(retrieved_lesson))
        assert len(ppt_bytes) > 0
        
        assignment_pdf = run_async(export_service.export_assignment_pdf(retrieved_assignment))
        assert len(assignment_pdf) > 0
        
        # Delete
        deleted = run_async(storage_service.delete_lesson(lesson_id))
        assert deleted is True
        
        # Verify deletion
        assert run_async(storage_service.get_lesson(lesson_id)) is None
        assert run_async(storage_service.get_assignment_for_lesson(lesson_id)) is None

    def test_multiple_lessons_management(self, storage_service):
        """Test managing multiple lessons."""
        lesson_ids = []
        
        # Create multiple lessons
        for i in range(5):
            lesson = Lesson(
                id=f"lesson-{i}",
                class_name=f"Class_{6 + i % 3}",
                subject=["Mathematics", "Science", "English"][i % 3],
                topic=f"Topic {i}",
                slides=create_test_lesson().slides,
                teacher_id="teacher-1",
                validation_score=0.8 + i * 0.02
            )
            lesson_id = run_async(storage_service.save_lesson(lesson))
            lesson_ids.append(lesson_id)
        
        # List all
        all_lessons = run_async(storage_service.list_lessons())
        assert len(all_lessons) == 5
        
        # Count
        count = run_async(storage_service.count_lessons())
        assert count == 5
        
        # Filter by class
        class_6_lessons = run_async(storage_service.list_lessons(class_name="Class_6"))
        assert len(class_6_lessons) >= 1
        
        # Delete some
        for lesson_id in lesson_ids[:2]:
            run_async(storage_service.delete_lesson(lesson_id))
        
        # Verify count decreased
        remaining = run_async(storage_service.list_lessons())
        assert len(remaining) == 3
