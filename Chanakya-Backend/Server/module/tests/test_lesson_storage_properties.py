"""
Property-Based Tests for LessonStorageService
==============================================

Tests using Hypothesis to validate correctness properties for lesson storage.

Feature: module-lesson-builder
Properties: 18, 19, 20
Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
"""

import pytest
import asyncio
import tempfile
import os
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timezone

from ..services.lesson_storage import LessonStorageService
from ..models.schemas import (
    Lesson, Slide, SlideType, Assignment,
    MCQQuestion, ShortAnswerQuestion, LongAnswerQuestion,
    MCQOption, DifficultyLevel, QuestionType
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Cleanup
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass  # Windows may hold file locks


@pytest.fixture
def storage_service(temp_db_path):
    """Create a LessonStorageService instance with temp database."""
    return LessonStorageService(db_path=temp_db_path)


def run_async(coro):
    """Helper to run async functions in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def create_temp_db():
    """Create a temporary database for a single test run."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return path


def cleanup_temp_db(path):
    """Clean up temporary database."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def slide_strategy(draw, slide_number: int = 1):
    """Generate a valid Slide object."""
    slide_types = [SlideType.INTRODUCTION, SlideType.CONCEPT, SlideType.EXAMPLES,
                   SlideType.PRACTICE, SlideType.REAL_WORLD, SlideType.SUMMARY]
    
    return Slide(
        slide_number=slide_number,
        slide_type=draw(st.sampled_from(slide_types)),
        title=f"Slide {slide_number} Title",
        explanation=f"This is the explanation for slide {slide_number}. It contains enough text.",
        bullet_points=[f"Point {i}" for i in range(1, draw(st.integers(min_value=1, max_value=3)) + 1)],
        key_terms=[f"Term {i}" for i in range(draw(st.integers(min_value=0, max_value=2)))],
        examples=[f"Example {i}" for i in range(draw(st.integers(min_value=0, max_value=2)))],
        diagram_prompt=f"Generate a diagram for slide {slide_number}",
        diagram_url=draw(st.one_of(st.none(), st.just("http://example.com/diagram.png"))),
        source_references=[f"Source {i}" for i in range(draw(st.integers(min_value=0, max_value=2)))]
    )


@st.composite
def lesson_strategy(draw):
    """Generate a valid Lesson object with exactly 8 slides."""
    slides = [draw(slide_strategy(i)) for i in range(1, 9)]
    
    return Lesson(
        id=draw(st.one_of(st.none(), st.uuids().map(str))),
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"])),
        subject=draw(st.sampled_from(["Mathematics", "Science", "Social_Science", "English"])),
        topic=draw(st.sampled_from(["Algebra", "Geometry", "Physics", "Chemistry", "History"])),
        slides=slides,
        teacher_id=draw(st.one_of(st.none(), st.uuids().map(str))),
        validation_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        created_at=datetime.now(timezone.utc)
    )


@st.composite
def mcq_question_strategy(draw):
    """Generate a valid MCQ question."""
    correct_idx = draw(st.integers(min_value=0, max_value=3))
    options = [
        MCQOption(
            option_text=f"Option {i+1}",
            is_correct=(i == correct_idx)
        )
        for i in range(4)
    ]
    
    return MCQQuestion(
        question_text="What is the correct answer to this question?",
        difficulty=draw(st.sampled_from(list(DifficultyLevel))),
        marks=1,
        source_reference="Class_6|Mathematics|NCERT|English|42",
        options=options
    )


@st.composite
def short_answer_strategy(draw):
    """Generate a valid short answer question."""
    return ShortAnswerQuestion(
        question_text="Explain the concept briefly.",
        difficulty=draw(st.sampled_from(list(DifficultyLevel))),
        marks=2,
        source_reference="Class_6|Mathematics|NCERT|English|42",
        expected_answer="This is the expected answer with enough characters."
    )


@st.composite
def long_answer_strategy(draw):
    """Generate a valid long answer question."""
    return LongAnswerQuestion(
        question_text="Describe the process in detail.",
        difficulty=draw(st.sampled_from(list(DifficultyLevel))),
        marks=5,
        source_reference="Class_6|Mathematics|NCERT|English|42",
        expected_answer="This is a long expected answer that contains enough characters to meet the minimum requirement of fifty characters for validation.",
        marking_scheme=["Point 1", "Point 2", "Point 3"]
    )


@st.composite
def assignment_strategy(draw, lesson_id: str = "test-lesson-id"):
    """Generate a valid Assignment object."""
    # Generate a mix of question types
    mcqs = [draw(mcq_question_strategy()) for _ in range(draw(st.integers(min_value=1, max_value=2)))]
    short_answers = [draw(short_answer_strategy())]
    long_answers = [draw(long_answer_strategy())]
    
    questions = mcqs + short_answers + long_answers
    total_marks = sum(q.marks for q in questions)
    
    return Assignment(
        id=draw(st.one_of(st.none(), st.uuids().map(str))),
        lesson_id=lesson_id,
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8"])),
        subject=draw(st.sampled_from(["Mathematics", "Science"])),
        topic=draw(st.text(min_size=3, max_size=50).filter(lambda x: len(x.strip()) >= 3)),
        questions=questions,
        total_marks=total_marks,
        created_at=datetime.now(timezone.utc)
    )


# =============================================================================
# Property 18: Lesson Persistence Round-Trip
# =============================================================================

class TestLessonPersistenceRoundTrip:
    """
    Feature: module-lesson-builder, Property 18: Lesson Persistence Round-Trip
    
    For any lesson that is saved, retrieving it by ID must return an identical 
    lesson with all 8 slides and the associated assignment.
    
    Validates: Requirements 8.1, 8.2, 8.4
    """

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_lesson_round_trip_preserves_data(self, lesson: Lesson):
        """
        Property 18.1: Saving and retrieving a lesson preserves all data.
        
        **Validates: Requirements 8.1, 8.2, 8.4**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            # Save the lesson
            lesson_id = run_async(service.save_lesson(lesson))
            
            # Retrieve the lesson
            retrieved = run_async(service.get_lesson(lesson_id))
            
            # Verify lesson was retrieved
            assert retrieved is not None, "Lesson should be retrievable after save"
            
            # Verify core fields match
            assert retrieved.class_name == lesson.class_name
            assert retrieved.subject == lesson.subject
            assert retrieved.topic == lesson.topic
            assert retrieved.teacher_id == lesson.teacher_id
            assert abs(retrieved.validation_score - lesson.validation_score) < 0.0001
            
            # Verify exactly 8 slides
            assert len(retrieved.slides) == 8, "Retrieved lesson must have exactly 8 slides"
        finally:
            cleanup_temp_db(temp_db_path)

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_lesson_slides_preserved_on_round_trip(self, lesson: Lesson):
        """
        Property 18.2: All slide data is preserved on round-trip.
        
        **Validates: Requirements 8.1, 8.4**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            lesson_id = run_async(service.save_lesson(lesson))
            retrieved = run_async(service.get_lesson(lesson_id))
            
            assert retrieved is not None
            
            for i, (orig_slide, ret_slide) in enumerate(zip(lesson.slides, retrieved.slides)):
                assert ret_slide.slide_number == orig_slide.slide_number, f"Slide {i+1} number mismatch"
                assert ret_slide.slide_type == orig_slide.slide_type, f"Slide {i+1} type mismatch"
                assert ret_slide.title == orig_slide.title, f"Slide {i+1} title mismatch"
                assert ret_slide.explanation == orig_slide.explanation, f"Slide {i+1} explanation mismatch"
                assert ret_slide.bullet_points == orig_slide.bullet_points, f"Slide {i+1} bullet_points mismatch"
                assert ret_slide.key_terms == orig_slide.key_terms, f"Slide {i+1} key_terms mismatch"
                assert ret_slide.examples == orig_slide.examples, f"Slide {i+1} examples mismatch"
                assert ret_slide.diagram_prompt == orig_slide.diagram_prompt, f"Slide {i+1} diagram_prompt mismatch"
        finally:
            cleanup_temp_db(temp_db_path)

    @given(lesson_strategy(), assignment_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_assignment_round_trip_preserves_data(self, lesson: Lesson, assignment: Assignment):
        """
        Property 18.3: Saving and retrieving an assignment preserves all data.
        
        **Validates: Requirements 8.1, 8.4**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            # Update assignment's lesson_id to match the lesson we'll save
            # We need to save lesson and assignment together in one call
            assignment_with_lesson = Assignment(
                id=assignment.id,
                lesson_id="will-be-set",  # Will be overwritten
                class_name=assignment.class_name,
                subject=assignment.subject,
                topic=assignment.topic,
                questions=assignment.questions,
                total_marks=assignment.total_marks,
                created_at=assignment.created_at
            )
            
            # Save lesson with assignment in one call
            lesson_id = run_async(service.save_lesson(lesson, assignment_with_lesson))
            
            # Retrieve assignment
            retrieved = run_async(service.get_assignment_for_lesson(lesson_id))
            
            assert retrieved is not None, "Assignment should be retrievable after save"
            assert retrieved.lesson_id == lesson_id
            assert retrieved.class_name == assignment_with_lesson.class_name
            assert retrieved.subject == assignment_with_lesson.subject
            assert retrieved.topic == assignment_with_lesson.topic
            assert retrieved.total_marks == assignment_with_lesson.total_marks
            assert len(retrieved.questions) == len(assignment_with_lesson.questions)
        finally:
            cleanup_temp_db(temp_db_path)


# =============================================================================
# Property 19: Lesson Metadata Completeness
# =============================================================================

class TestLessonMetadataCompleteness:
    """
    Feature: module-lesson-builder, Property 19: Lesson Metadata Completeness
    
    For any stored lesson, the metadata fields (class_name, subject, topic, 
    created_at) must all be non-null and valid.
    
    Validates: Requirements 8.3
    """

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_stored_lesson_has_complete_metadata(self, lesson: Lesson):
        """
        Property 19.1: All metadata fields are present and valid after storage.
        
        **Validates: Requirements 8.3**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            lesson_id = run_async(service.save_lesson(lesson))
            retrieved = run_async(service.get_lesson(lesson_id))
            
            assert retrieved is not None
            
            # Verify all metadata fields are non-null
            assert retrieved.id is not None, "Lesson ID must not be null"
            assert retrieved.class_name is not None and len(retrieved.class_name) > 0, \
                "class_name must not be null or empty"
            assert retrieved.subject is not None and len(retrieved.subject) > 0, \
                "subject must not be null or empty"
            assert retrieved.topic is not None and len(retrieved.topic) > 0, \
                "topic must not be null or empty"
            assert retrieved.created_at is not None, "created_at must not be null"
            assert retrieved.validation_score is not None, "validation_score must not be null"
            assert 0.0 <= retrieved.validation_score <= 1.0, \
                "validation_score must be between 0 and 1"
        finally:
            cleanup_temp_db(temp_db_path)

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_lesson_id_is_assigned_on_save(self, lesson: Lesson):
        """
        Property 19.2: A lesson without an ID gets one assigned on save.
        
        **Validates: Requirements 8.1**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            # Create lesson without ID
            lesson_without_id = Lesson(
                id=None,
                class_name=lesson.class_name,
                subject=lesson.subject,
                topic=lesson.topic,
                slides=lesson.slides,
                teacher_id=lesson.teacher_id,
                validation_score=lesson.validation_score,
                created_at=lesson.created_at
            )
            
            lesson_id = run_async(service.save_lesson(lesson_without_id))
            
            assert lesson_id is not None, "save_lesson must return a valid ID"
            assert len(lesson_id) > 0, "Returned ID must not be empty"
            
            # Verify the lesson can be retrieved with this ID
            retrieved = run_async(service.get_lesson(lesson_id))
            assert retrieved is not None, "Lesson must be retrievable with assigned ID"
            assert retrieved.id == lesson_id, "Retrieved lesson ID must match"
        finally:
            cleanup_temp_db(temp_db_path)

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_created_at_is_preserved(self, lesson: Lesson):
        """
        Property 19.3: The created_at timestamp is preserved on storage.
        
        **Validates: Requirements 8.3**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            lesson_id = run_async(service.save_lesson(lesson))
            retrieved = run_async(service.get_lesson(lesson_id))
            
            assert retrieved is not None
            
            # Timestamps should be close (within 1 second due to serialization)
            time_diff = abs((retrieved.created_at - lesson.created_at).total_seconds())
            assert time_diff < 1.0, f"created_at timestamp drift too large: {time_diff}s"
        finally:
            cleanup_temp_db(temp_db_path)


# =============================================================================
# Property 20: Lesson Deletion
# =============================================================================

class TestLessonDeletion:
    """
    Feature: module-lesson-builder, Property 20: Lesson Deletion
    
    For any lesson that is deleted, subsequent retrieval attempts must 
    return a "not found" error.
    
    Validates: Requirements 8.5
    """

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_deleted_lesson_not_retrievable(self, lesson: Lesson):
        """
        Property 20.1: A deleted lesson cannot be retrieved.
        
        **Validates: Requirements 8.5**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            # Save the lesson
            lesson_id = run_async(service.save_lesson(lesson))
            
            # Verify it exists
            retrieved = run_async(service.get_lesson(lesson_id))
            assert retrieved is not None, "Lesson should exist before deletion"
            
            # Delete the lesson
            deleted = run_async(service.delete_lesson(lesson_id))
            assert deleted is True, "delete_lesson should return True for existing lesson"
            
            # Verify it no longer exists
            retrieved_after = run_async(service.get_lesson(lesson_id))
            assert retrieved_after is None, "Deleted lesson should not be retrievable"
        finally:
            cleanup_temp_db(temp_db_path)

    @given(lesson_strategy(), assignment_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_deleted_lesson_assignment_also_deleted(self, lesson: Lesson, assignment: Assignment):
        """
        Property 20.2: Deleting a lesson also deletes its assignment.
        
        **Validates: Requirements 8.5**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            # Create assignment (lesson_id will be set by save_lesson)
            assignment_with_lesson = Assignment(
                id=assignment.id,
                lesson_id="will-be-set",
                class_name=assignment.class_name,
                subject=assignment.subject,
                topic=assignment.topic,
                questions=assignment.questions,
                total_marks=assignment.total_marks,
                created_at=assignment.created_at
            )
            
            # Save lesson with assignment in one call
            lesson_id = run_async(service.save_lesson(lesson, assignment_with_lesson))
            
            # Verify assignment exists
            retrieved_assignment = run_async(service.get_assignment_for_lesson(lesson_id))
            assert retrieved_assignment is not None, "Assignment should exist before deletion"
            
            # Delete the lesson
            run_async(service.delete_lesson(lesson_id))
            
            # Verify assignment is also deleted
            retrieved_after = run_async(service.get_assignment_for_lesson(lesson_id))
            assert retrieved_after is None, "Assignment should be deleted with lesson"
        finally:
            cleanup_temp_db(temp_db_path)

    def test_delete_nonexistent_lesson_returns_false(self):
        """
        Property 20.3: Deleting a non-existent lesson returns False.
        
        **Validates: Requirements 8.5**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            result = run_async(service.delete_lesson("nonexistent-id-12345"))
            assert result is False, "delete_lesson should return False for non-existent lesson"
        finally:
            cleanup_temp_db(temp_db_path)

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_lesson_exists_returns_false_after_deletion(self, lesson: Lesson):
        """
        Property 20.4: lesson_exists returns False after deletion.
        
        **Validates: Requirements 8.5**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            # Save and verify exists
            lesson_id = run_async(service.save_lesson(lesson))
            exists_before = run_async(service.lesson_exists(lesson_id))
            assert exists_before is True, "Lesson should exist after save"
            
            # Delete and verify not exists
            run_async(service.delete_lesson(lesson_id))
            exists_after = run_async(service.lesson_exists(lesson_id))
            assert exists_after is False, "Lesson should not exist after deletion"
        finally:
            cleanup_temp_db(temp_db_path)

    @given(lesson_strategy())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_deleted_lesson_not_in_list(self, lesson: Lesson):
        """
        Property 20.5: A deleted lesson does not appear in list_lessons.
        
        **Validates: Requirements 8.2, 8.5**
        """
        temp_db_path = create_temp_db()
        try:
            service = LessonStorageService(db_path=temp_db_path)
            
            # Save the lesson
            lesson_id = run_async(service.save_lesson(lesson))
            
            # Verify it appears in list
            lessons_before = run_async(service.list_lessons())
            lesson_ids_before = [l.id for l in lessons_before]
            assert lesson_id in lesson_ids_before, "Saved lesson should appear in list"
            
            # Delete the lesson
            run_async(service.delete_lesson(lesson_id))
            
            # Verify it no longer appears in list
            lessons_after = run_async(service.list_lessons())
            lesson_ids_after = [l.id for l in lessons_after]
            assert lesson_id not in lesson_ids_after, "Deleted lesson should not appear in list"
        finally:
            cleanup_temp_db(temp_db_path)
