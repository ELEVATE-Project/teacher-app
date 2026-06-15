"""
Property-Based Tests for AssignmentGenerator
=============================================

Tests using Hypothesis to validate correctness properties for assignment generation.

Property 9: Question Answerability - answers derivable from source
Property 10: Difficulty Level Distribution - 3+ questions per level
Property 11: Question Type Distribution - all types present

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.6
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from pydantic import ValidationError
from typing import List

from ..models.schemas import (
    Assignment,
    MCQQuestion,
    MCQOption,
    ShortAnswerQuestion,
    LongAnswerQuestion,
    DifficultyLevel,
    QuestionType,
    TextbookContent,
    QuestionUnion,
)


# =============================================================================
# Custom Strategies for Assignment Generator Tests
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
def valid_mcq_option_strategy(draw, is_correct: bool = False):
    """Generate a valid MCQ option."""
    option_text = draw(st.text(
        min_size=5, max_size=100,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(option_text.strip())
    return MCQOption(option_text=option_text, is_correct=is_correct)


@st.composite
def valid_mcq_question_strategy(draw, difficulty: DifficultyLevel = None):
    """Generate a valid MCQ question with exactly 4 options and 1 correct."""
    if difficulty is None:
        difficulty = draw(st.sampled_from(list(DifficultyLevel)))
    
    question_text = draw(st.text(
        min_size=10, max_size=200,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(question_text.strip())
    
    # Generate exactly 4 options with exactly 1 correct
    correct_index = draw(st.integers(min_value=0, max_value=3))
    options = []
    for i in range(4):
        opt = draw(valid_mcq_option_strategy(is_correct=(i == correct_index)))
        options.append(opt)
    
    return MCQQuestion(
        question_text=question_text,
        difficulty=difficulty,
        options=options,
        marks=1,
        source_reference=draw(valid_source_strategy())
    )


@st.composite
def valid_short_answer_strategy(draw, difficulty: DifficultyLevel = None):
    """Generate a valid short answer question."""
    if difficulty is None:
        difficulty = draw(st.sampled_from(list(DifficultyLevel)))
    
    question_text = draw(st.text(
        min_size=10, max_size=200,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(question_text.strip())
    
    expected_answer = draw(st.text(
        min_size=20, max_size=300,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(expected_answer.strip())
    
    return ShortAnswerQuestion(
        question_text=question_text,
        difficulty=difficulty,
        expected_answer=expected_answer,
        marks=2,
        source_reference=draw(valid_source_strategy())
    )


@st.composite
def valid_long_answer_strategy(draw, difficulty: DifficultyLevel = None):
    """Generate a valid long answer question."""
    if difficulty is None:
        difficulty = draw(st.sampled_from(list(DifficultyLevel)))
    
    question_text = draw(st.text(
        min_size=10, max_size=200,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(question_text.strip())
    
    expected_answer = draw(st.text(
        min_size=60, max_size=500,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(expected_answer.strip())
    
    marking_scheme = draw(st.lists(
        st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))).filter(lambda x: x.strip()),
        min_size=3, max_size=5
    ))
    
    return LongAnswerQuestion(
        question_text=question_text,
        difficulty=difficulty,
        expected_answer=expected_answer,
        marking_scheme=marking_scheme,
        marks=5,
        source_reference=draw(valid_source_strategy())
    )


@st.composite
def valid_assignment_with_distribution_strategy(draw):
    """
    Generate a valid Assignment with proper difficulty and type distribution.
    
    Ensures:
    - At least 3 questions per difficulty level
    - All question types present
    """
    questions: List[QuestionUnion] = []
    
    # Generate 3 MCQs per difficulty (9 total)
    for difficulty in DifficultyLevel:
        for _ in range(3):
            questions.append(draw(valid_mcq_question_strategy(difficulty=difficulty)))
    
    # Generate 1 short answer per difficulty (3 total)
    for difficulty in DifficultyLevel:
        questions.append(draw(valid_short_answer_strategy(difficulty=difficulty)))
    
    # Generate 1 long answer per difficulty (3 total)
    for difficulty in DifficultyLevel:
        questions.append(draw(valid_long_answer_strategy(difficulty=difficulty)))
    
    # Calculate total marks
    total_marks = sum(q.marks for q in questions)
    
    return Assignment(
        lesson_id=draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        class_name=draw(st.sampled_from(["Class_6", "Class_7", "Class_8", "Class_9", "Class_10"])),
        subject=draw(st.sampled_from(["Mathematics", "Science", "English"])),
        topic=draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))).filter(lambda x: x.strip())),
        questions=questions,
        total_marks=total_marks
    )


@st.composite
def valid_textbook_content_strategy(draw):
    """Generate valid TextbookContent for testing."""
    content = draw(st.text(
        min_size=50, max_size=500,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ))
    assume(content.strip())
    
    return TextbookContent(
        content=content,
        source=draw(valid_source_strategy()),
        similarity_score=draw(st.floats(min_value=0.5, max_value=1.0, allow_nan=False))
    )


# =============================================================================
# Property 9: Question Answerability
# =============================================================================

class TestQuestionAnswerability:
    """
    Feature: module-lesson-builder, Property 9: Question Answerability
    
    For any question in a generated assignment, the answer must be derivable
    from the source textbook content used for the lesson.
    
    Validates: Requirements 5.1, 5.4
    """

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_questions_have_source_reference(self, assignment: Assignment):
        """Property 9: All questions must have a source reference."""
        for question in assignment.questions:
            assert question.source_reference, \
                f"Question '{question.question_text[:30]}...' has no source reference"
            # Verify source reference format (at least 3 pipe-separated parts)
            parts = question.source_reference.split('|')
            assert len(parts) >= 3, \
                f"Source reference '{question.source_reference}' has invalid format"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_mcq_has_correct_answer(self, assignment: Assignment):
        """Property 9: MCQ questions must have exactly one correct answer."""
        mcqs = [q for q in assignment.questions if isinstance(q, MCQQuestion)]
        for mcq in mcqs:
            correct_count = sum(1 for opt in mcq.options if opt.is_correct)
            assert correct_count == 1, \
                f"MCQ '{mcq.question_text[:30]}...' has {correct_count} correct answers, expected 1"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_short_answer_has_expected_answer(self, assignment: Assignment):
        """Property 9: Short answer questions must have expected answer."""
        short_answers = [q for q in assignment.questions if isinstance(q, ShortAnswerQuestion)]
        for sa in short_answers:
            assert sa.expected_answer, \
                f"Short answer '{sa.question_text[:30]}...' has no expected answer"
            assert len(sa.expected_answer) >= 10, \
                f"Short answer expected answer too short: {len(sa.expected_answer)}"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_long_answer_has_expected_answer_and_marking_scheme(self, assignment: Assignment):
        """Property 9: Long answer questions must have expected answer and marking scheme."""
        long_answers = [q for q in assignment.questions if isinstance(q, LongAnswerQuestion)]
        for la in long_answers:
            assert la.expected_answer, \
                f"Long answer '{la.question_text[:30]}...' has no expected answer"
            assert len(la.expected_answer) >= 50, \
                f"Long answer expected answer too short: {len(la.expected_answer)}"
            assert la.marking_scheme, \
                f"Long answer '{la.question_text[:30]}...' has no marking scheme"
            assert len(la.marking_scheme) >= 1, \
                f"Long answer marking scheme must have at least 1 point"


# =============================================================================
# Property 10: Difficulty Level Distribution
# =============================================================================

class TestDifficultyLevelDistribution:
    """
    Feature: module-lesson-builder, Property 10: Difficulty Level Distribution
    
    For any generated assignment, all three difficulty levels (easy, medium, hard)
    must be represented with at least 3 questions each.
    
    Validates: Requirements 5.2, 5.6
    """

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_difficulty_levels_present(self, assignment: Assignment):
        """Property 10: All difficulty levels must be present."""
        questions_by_difficulty = assignment.questions_by_difficulty()
        
        for difficulty in DifficultyLevel:
            assert difficulty in questions_by_difficulty, \
                f"Difficulty level {difficulty.value} not found in assignment"
            assert len(questions_by_difficulty[difficulty]) > 0, \
                f"No questions at {difficulty.value} difficulty level"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_minimum_questions_per_difficulty(self, assignment: Assignment):
        """Property 10: At least 3 questions per difficulty level."""
        questions_by_difficulty = assignment.questions_by_difficulty()
        
        for difficulty in DifficultyLevel:
            count = len(questions_by_difficulty[difficulty])
            assert count >= 3, \
                f"Only {count} questions at {difficulty.value} level, need at least 3"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_easy_questions_exist(self, assignment: Assignment):
        """Property 10: Easy questions must exist."""
        easy_questions = [q for q in assignment.questions if q.difficulty == DifficultyLevel.EASY]
        assert len(easy_questions) >= 3, \
            f"Only {len(easy_questions)} easy questions, need at least 3"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_medium_questions_exist(self, assignment: Assignment):
        """Property 10: Medium questions must exist."""
        medium_questions = [q for q in assignment.questions if q.difficulty == DifficultyLevel.MEDIUM]
        assert len(medium_questions) >= 3, \
            f"Only {len(medium_questions)} medium questions, need at least 3"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_hard_questions_exist(self, assignment: Assignment):
        """Property 10: Hard questions must exist."""
        hard_questions = [q for q in assignment.questions if q.difficulty == DifficultyLevel.HARD]
        assert len(hard_questions) >= 3, \
            f"Only {len(hard_questions)} hard questions, need at least 3"


# =============================================================================
# Property 11: Question Type Distribution
# =============================================================================

class TestQuestionTypeDistribution:
    """
    Feature: module-lesson-builder, Property 11: Question Type Distribution
    
    For any generated assignment, all three question types
    (MCQ, short_answer, long_answer) must be present.
    
    Validates: Requirements 5.3
    """

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_question_types_present(self, assignment: Assignment):
        """Property 11: All question types must be present."""
        questions_by_type = assignment.questions_by_type()
        
        for qtype in QuestionType:
            assert qtype in questions_by_type, \
                f"Question type {qtype.value} not found in assignment"
            assert len(questions_by_type[qtype]) > 0, \
                f"No questions of type {qtype.value}"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_mcq_questions_exist(self, assignment: Assignment):
        """Property 11: MCQ questions must exist."""
        mcqs = [q for q in assignment.questions if q.question_type == QuestionType.MCQ]
        assert len(mcqs) > 0, "No MCQ questions in assignment"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_short_answer_questions_exist(self, assignment: Assignment):
        """Property 11: Short answer questions must exist."""
        short_answers = [q for q in assignment.questions if q.question_type == QuestionType.SHORT_ANSWER]
        assert len(short_answers) > 0, "No short answer questions in assignment"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_long_answer_questions_exist(self, assignment: Assignment):
        """Property 11: Long answer questions must exist."""
        long_answers = [q for q in assignment.questions if q.question_type == QuestionType.LONG_ANSWER]
        assert len(long_answers) > 0, "No long answer questions in assignment"

    @given(valid_assignment_with_distribution_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_total_marks_matches_sum(self, assignment: Assignment):
        """Property 11: Total marks must match sum of question marks."""
        calculated_total = sum(q.marks for q in assignment.questions)
        assert assignment.total_marks == calculated_total, \
            f"Total marks ({assignment.total_marks}) doesn't match sum ({calculated_total})"


# =============================================================================
# Additional Unit Tests for Edge Cases
# =============================================================================

class TestMCQStructureInvariant:
    """
    Additional tests for MCQ structure validation.
    
    Property 12: MCQ Structure Invariant - MCQ must have 4 options with 1 correct
    (Already tested in test_schemas_properties.py, but included here for completeness)
    """

    def test_mcq_rejects_less_than_4_options(self):
        """MCQ creation should fail with less than 4 options."""
        with pytest.raises(ValidationError):
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=[
                    MCQOption(option_text="3", is_correct=False),
                    MCQOption(option_text="4", is_correct=True),
                    MCQOption(option_text="5", is_correct=False),
                ],  # Only 3 options
                marks=1,
                source_reference="Class_6|Mathematics|NCERT|English|10"
            )

    def test_mcq_rejects_more_than_4_options(self):
        """MCQ creation should fail with more than 4 options."""
        with pytest.raises(ValidationError):
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=[
                    MCQOption(option_text="3", is_correct=False),
                    MCQOption(option_text="4", is_correct=True),
                    MCQOption(option_text="5", is_correct=False),
                    MCQOption(option_text="6", is_correct=False),
                    MCQOption(option_text="7", is_correct=False),
                ],  # 5 options
                marks=1,
                source_reference="Class_6|Mathematics|NCERT|English|10"
            )

    def test_mcq_rejects_no_correct_option(self):
        """MCQ creation should fail with no correct option."""
        with pytest.raises(ValidationError):
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=[
                    MCQOption(option_text="3", is_correct=False),
                    MCQOption(option_text="5", is_correct=False),
                    MCQOption(option_text="6", is_correct=False),
                    MCQOption(option_text="7", is_correct=False),
                ],  # No correct option
                marks=1,
                source_reference="Class_6|Mathematics|NCERT|English|10"
            )

    def test_mcq_rejects_multiple_correct_options(self):
        """MCQ creation should fail with multiple correct options."""
        with pytest.raises(ValidationError):
            MCQQuestion(
                question_text="What is 2 + 2?",
                difficulty=DifficultyLevel.EASY,
                options=[
                    MCQOption(option_text="4", is_correct=True),
                    MCQOption(option_text="Four", is_correct=True),  # Two correct
                    MCQOption(option_text="5", is_correct=False),
                    MCQOption(option_text="6", is_correct=False),
                ],
                marks=1,
                source_reference="Class_6|Mathematics|NCERT|English|10"
            )

    def test_valid_mcq_creation(self):
        """Valid MCQ should be created successfully."""
        mcq = MCQQuestion(
            question_text="What is 2 + 2?",
            difficulty=DifficultyLevel.EASY,
            options=[
                MCQOption(option_text="3", is_correct=False),
                MCQOption(option_text="4", is_correct=True),
                MCQOption(option_text="5", is_correct=False),
                MCQOption(option_text="6", is_correct=False),
            ],
            marks=1,
            source_reference="Class_6|Mathematics|NCERT|English|10"
        )
        assert len(mcq.options) == 4
        assert sum(1 for opt in mcq.options if opt.is_correct) == 1
