"""
Lesson Storage Service
======================

Service for persisting and retrieving lessons and assignments using SQLite.
Provides CRUD operations for lesson management.
"""

import sqlite3
import json
import logging
import os
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from ..models.schemas import (
    Lesson, Assignment, Slide, SlideType,
    MCQQuestion, ShortAnswerQuestion, LongAnswerQuestion,
    MCQOption, DifficultyLevel, QuestionType
)

logger = logging.getLogger(__name__)


class LessonStorageService:
    """Service for storing and retrieving lessons using SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the lesson storage service.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            this_file_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(this_file_dir, "..", "data", "lessons.db")
            db_path = os.path.normpath(db_path)
            
            # Ensure data directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self) -> None:
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create lessons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    class_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    teacher_id TEXT,
                    validation_score REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    slides_json TEXT NOT NULL
                )
            """)
            
            # Create assignments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    total_marks INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    questions_json TEXT NOT NULL,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lessons_teacher_id 
                ON lessons(teacher_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lessons_created_at 
                ON lessons(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_assignments_lesson_id 
                ON assignments(lesson_id)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def _serialize_slide(self, slide: Slide) -> dict:
        """Serialize a Slide object to a dictionary."""
        return {
            "slide_number": slide.slide_number,
            "slide_type": slide.slide_type.value,
            "title": slide.title,
            "explanation": slide.explanation,
            "bullet_points": slide.bullet_points,
            "key_terms": slide.key_terms,
            "examples": slide.examples,
            "diagram_prompt": slide.diagram_prompt,
            "diagram_url": slide.diagram_url,
            "source_references": slide.source_references
        }
    
    def _deserialize_slide(self, data: dict) -> Slide:
        """Deserialize a dictionary to a Slide object."""
        return Slide(
            slide_number=data["slide_number"],
            slide_type=SlideType(data["slide_type"]),
            title=data["title"],
            explanation=data["explanation"],
            bullet_points=data["bullet_points"],
            key_terms=data.get("key_terms", []),
            examples=data.get("examples", []),
            diagram_prompt=data["diagram_prompt"],
            diagram_url=data.get("diagram_url"),
            source_references=data.get("source_references", [])
        )
    
    def _serialize_question(self, question) -> dict:
        """Serialize a Question object to a dictionary."""
        base = {
            "question_text": question.question_text,
            "difficulty": question.difficulty.value,
            "question_type": question.question_type.value,
            "marks": question.marks,
            "source_reference": question.source_reference
        }
        
        if isinstance(question, MCQQuestion):
            base["options"] = [
                {"option_text": opt.option_text, "is_correct": opt.is_correct}
                for opt in question.options
            ]
        elif isinstance(question, ShortAnswerQuestion):
            base["expected_answer"] = question.expected_answer
        elif isinstance(question, LongAnswerQuestion):
            base["expected_answer"] = question.expected_answer
            base["marking_scheme"] = question.marking_scheme
        
        return base
    
    def _deserialize_question(self, data: dict):
        """Deserialize a dictionary to a Question object."""
        question_type = QuestionType(data["question_type"])
        difficulty = DifficultyLevel(data["difficulty"])
        
        if question_type == QuestionType.MCQ:
            return MCQQuestion(
                question_text=data["question_text"],
                difficulty=difficulty,
                marks=data["marks"],
                source_reference=data["source_reference"],
                options=[
                    MCQOption(option_text=opt["option_text"], is_correct=opt["is_correct"])
                    for opt in data["options"]
                ]
            )
        elif question_type == QuestionType.SHORT_ANSWER:
            return ShortAnswerQuestion(
                question_text=data["question_text"],
                difficulty=difficulty,
                marks=data["marks"],
                source_reference=data["source_reference"],
                expected_answer=data["expected_answer"]
            )
        else:  # LONG_ANSWER
            return LongAnswerQuestion(
                question_text=data["question_text"],
                difficulty=difficulty,
                marks=data["marks"],
                source_reference=data["source_reference"],
                expected_answer=data["expected_answer"],
                marking_scheme=data["marking_scheme"]
            )

    async def save_lesson(
        self, 
        lesson: Lesson, 
        assignment: Optional[Assignment] = None
    ) -> str:
        """
        Save a lesson and optionally its assignment to the database.
        
        Args:
            lesson: The Lesson object to save
            assignment: Optional Assignment object to save with the lesson
            
        Returns:
            The ID of the saved lesson
        """
        # Generate ID if not present
        lesson_id = lesson.id or str(uuid.uuid4())
        
        # Serialize slides to JSON
        slides_json = json.dumps([self._serialize_slide(s) for s in lesson.slides])
        
        # Format datetime for storage
        created_at = lesson.created_at.isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert or replace lesson
            cursor.execute("""
                INSERT OR REPLACE INTO lessons 
                (id, class_name, subject, topic, teacher_id, validation_score, created_at, slides_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lesson_id,
                lesson.class_name,
                lesson.subject,
                lesson.topic,
                lesson.teacher_id,
                lesson.validation_score,
                created_at,
                slides_json
            ))
            
            # Save assignment if provided
            if assignment:
                assignment_id = assignment.id or str(uuid.uuid4())
                questions_json = json.dumps([
                    self._serialize_question(q) for q in assignment.questions
                ])
                assignment_created_at = assignment.created_at.isoformat()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO assignments
                    (id, lesson_id, class_name, subject, topic, total_marks, created_at, questions_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    assignment_id,
                    lesson_id,
                    assignment.class_name,
                    assignment.subject,
                    assignment.topic,
                    assignment.total_marks,
                    assignment_created_at,
                    questions_json
                ))
            
            conn.commit()
            logger.info(f"Saved lesson {lesson_id}")
            
        return lesson_id
    
    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """
        Retrieve a lesson by its ID.
        
        Args:
            lesson_id: The ID of the lesson to retrieve
            
        Returns:
            The Lesson object if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM lessons WHERE id = ?",
                (lesson_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Deserialize slides
            slides_data = json.loads(row["slides_json"])
            slides = [self._deserialize_slide(s) for s in slides_data]
            
            # Parse datetime
            created_at = datetime.fromisoformat(row["created_at"])
            
            return Lesson(
                id=row["id"],
                class_name=row["class_name"],
                subject=row["subject"],
                topic=row["topic"],
                teacher_id=row["teacher_id"],
                validation_score=row["validation_score"],
                created_at=created_at,
                slides=slides
            )
    
    async def get_assignment_for_lesson(self, lesson_id: str) -> Optional[Assignment]:
        """
        Retrieve the assignment associated with a lesson.
        
        Args:
            lesson_id: The ID of the lesson
            
        Returns:
            The Assignment object if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM assignments WHERE lesson_id = ?",
                (lesson_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Deserialize questions
            questions_data = json.loads(row["questions_json"])
            questions = [self._deserialize_question(q) for q in questions_data]
            
            # Parse datetime
            created_at = datetime.fromisoformat(row["created_at"])
            
            return Assignment(
                id=row["id"],
                lesson_id=row["lesson_id"],
                class_name=row["class_name"],
                subject=row["subject"],
                topic=row["topic"],
                total_marks=row["total_marks"],
                created_at=created_at,
                questions=questions
            )

    async def list_lessons(
        self, 
        teacher_id: Optional[str] = None,
        class_name: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Lesson]:
        """
        List lessons with optional filtering.
        
        Args:
            teacher_id: Filter by teacher ID
            class_name: Filter by class name
            subject: Filter by subject
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of Lesson objects matching the filters
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT * FROM lessons WHERE 1=1"
            params = []
            
            if teacher_id:
                query += " AND teacher_id = ?"
                params.append(teacher_id)
            
            if class_name:
                query += " AND class_name = ?"
                params.append(class_name)
            
            if subject:
                query += " AND subject = ?"
                params.append(subject)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            lessons = []
            for row in rows:
                slides_data = json.loads(row["slides_json"])
                slides = [self._deserialize_slide(s) for s in slides_data]
                created_at = datetime.fromisoformat(row["created_at"])
                
                lessons.append(Lesson(
                    id=row["id"],
                    class_name=row["class_name"],
                    subject=row["subject"],
                    topic=row["topic"],
                    teacher_id=row["teacher_id"],
                    validation_score=row["validation_score"],
                    created_at=created_at,
                    slides=slides
                ))
            
            return lessons
    
    async def delete_lesson(self, lesson_id: str) -> bool:
        """
        Delete a lesson and its associated assignment.
        
        Args:
            lesson_id: The ID of the lesson to delete
            
        Returns:
            True if the lesson was deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if lesson exists
            cursor.execute("SELECT id FROM lessons WHERE id = ?", (lesson_id,))
            if cursor.fetchone() is None:
                return False
            
            # Delete assignment first (foreign key)
            cursor.execute(
                "DELETE FROM assignments WHERE lesson_id = ?",
                (lesson_id,)
            )
            
            # Delete lesson
            cursor.execute(
                "DELETE FROM lessons WHERE id = ?",
                (lesson_id,)
            )
            
            conn.commit()
            logger.info(f"Deleted lesson {lesson_id}")
            
            return True
    
    async def lesson_exists(self, lesson_id: str) -> bool:
        """
        Check if a lesson exists.
        
        Args:
            lesson_id: The ID of the lesson to check
            
        Returns:
            True if the lesson exists, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM lessons WHERE id = ?",
                (lesson_id,)
            )
            count = cursor.fetchone()[0]
            return count > 0
    
    async def count_lessons(
        self, 
        teacher_id: Optional[str] = None
    ) -> int:
        """
        Count total lessons, optionally filtered by teacher.
        
        Args:
            teacher_id: Optional teacher ID to filter by
            
        Returns:
            Number of lessons
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if teacher_id:
                cursor.execute(
                    "SELECT COUNT(*) FROM lessons WHERE teacher_id = ?",
                    (teacher_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM lessons")
            
            return cursor.fetchone()[0]
