"""
Lesson Storage Service
======================

Service for persisting and retrieving lessons and assignments using PostgreSQL.
Provides CRUD operations for lesson management.
"""

import asyncpg
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
    """Service for storing and retrieving lessons using PostgreSQL."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the lesson storage service.
        
        Args:
            db_path: Path parameter (ignored, kept for backward compatibility).
        """
        self.dsn = os.getenv("DB_URL") or "postgresql://teacher_user:securepass123@localhost:5432/Shikshalokam"
        self._pool = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure database pool and tables are initialized (lazy initialization)."""
        if not self._initialized:
            if not self._pool:
                self._pool = await asyncpg.create_pool(dsn=self.dsn)
            await self._init_database()
            self._initialized = True
            
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
    
    async def _init_database(self) -> None:
        """Initialize database schema if not exists."""
        async with self._pool.acquire() as conn:
            # Create lessons table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    class_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    teacher_id TEXT,
                    validation_score REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    slides_json TEXT NOT NULL,
                    ragflow_session_id TEXT
                )
            """)
            
            # Idempotent ALTER TABLE migration to ensure ragflow_session_id exists on existing tables
            await conn.execute("""
                ALTER TABLE lessons ADD COLUMN IF NOT EXISTS ragflow_session_id TEXT
            """)
            
            # Create assignments table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
                    class_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    total_marks INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    questions_json TEXT NOT NULL
                )
            """)
            
            # Create indexes for efficient queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lessons_teacher_id 
                ON lessons(teacher_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lessons_created_at 
                ON lessons(created_at)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_assignments_lesson_id 
                ON assignments(lesson_id)
            """)
            
            logger.info("PostgreSQL database tables and indexes initialized")

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
        await self._ensure_initialized()
        
        # Generate ID if not present
        lesson_id = lesson.id or str(uuid.uuid4())
        lesson.id = lesson_id
        
        # Serialize slides to JSON
        slides_json = json.dumps([self._serialize_slide(s) for s in lesson.slides])
        
        # Format datetime for storage
        created_at = lesson.created_at.isoformat()
        
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Insert or update lesson
                await conn.execute("""
                    INSERT INTO lessons 
                    (id, class_name, subject, topic, teacher_id, validation_score, created_at, slides_json, ragflow_session_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO UPDATE SET
                        class_name = EXCLUDED.class_name,
                        subject = EXCLUDED.subject,
                        topic = EXCLUDED.topic,
                        teacher_id = EXCLUDED.teacher_id,
                        validation_score = EXCLUDED.validation_score,
                        created_at = EXCLUDED.created_at,
                        slides_json = EXCLUDED.slides_json,
                        ragflow_session_id = EXCLUDED.ragflow_session_id
                """, 
                    lesson_id,
                    lesson.class_name,
                    lesson.subject,
                    lesson.topic,
                    lesson.teacher_id,
                    lesson.validation_score,
                    created_at,
                    slides_json,
                    lesson.ragflow_session_id
                )
                
                # Save assignment if provided
                if assignment:
                    assignment_id = assignment.id or str(uuid.uuid4())
                    assignment.id = assignment_id
                    questions_json = json.dumps([
                        self._serialize_question(q) for q in assignment.questions
                    ])
                    assignment_created_at = assignment.created_at.isoformat()
                    
                    await conn.execute("""
                        INSERT INTO assignments
                        (id, lesson_id, class_name, subject, topic, total_marks, created_at, questions_json)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (id) DO UPDATE SET
                            lesson_id = EXCLUDED.lesson_id,
                            class_name = EXCLUDED.class_name,
                            subject = EXCLUDED.subject,
                            topic = EXCLUDED.topic,
                            total_marks = EXCLUDED.total_marks,
                            created_at = EXCLUDED.created_at,
                            questions_json = EXCLUDED.questions_json
                    """, 
                        assignment_id,
                        lesson_id,
                        assignment.class_name,
                        assignment.subject,
                        assignment.topic,
                        assignment.total_marks,
                        assignment_created_at,
                        questions_json
                    )
            
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
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM lessons WHERE id = $1",
                lesson_id
            )
            
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
                slides=slides,
                ragflow_session_id=row["ragflow_session_id"]
            )
    
    async def get_assignment_for_lesson(self, lesson_id: str) -> Optional[Assignment]:
        """
        Retrieve the assignment associated with a lesson.
        
        Args:
            lesson_id: The ID of the lesson
            
        Returns:
            The Assignment object if found, None otherwise
        """
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM assignments WHERE lesson_id = $1",
                lesson_id
            )
            
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
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            # Build query with filters
            query = "SELECT * FROM lessons WHERE 1=1"
            params = []
            param_idx = 1
            
            if teacher_id:
                query += f" AND teacher_id = ${param_idx}"
                params.append(teacher_id)
                param_idx += 1
            
            if class_name:
                query += f" AND class_name = ${param_idx}"
                params.append(class_name)
                param_idx += 1
            
            if subject:
                query += f" AND subject = ${param_idx}"
                params.append(subject)
                param_idx += 1
            
            query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx+1}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
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
                    slides=slides,
                    ragflow_session_id=row["ragflow_session_id"]
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
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            # Check if lesson exists
            exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM lessons WHERE id = $1)", lesson_id)
            if not exists:
                return False
            
            # Delete assignment first
            await conn.execute(
                "DELETE FROM assignments WHERE lesson_id = $1",
                lesson_id
            )
            
            # Delete lesson
            await conn.execute(
                "DELETE FROM lessons WHERE id = $1",
                lesson_id
            )
            
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
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM lessons WHERE id = $1)",
                lesson_id
            )
    
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
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            if teacher_id:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM lessons WHERE teacher_id = $1",
                    teacher_id
                )
            else:
                return await conn.fetchval("SELECT COUNT(*) FROM lessons")
