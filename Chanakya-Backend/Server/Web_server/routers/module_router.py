"""
MODULE API Router
=================

API endpoints for the MODULE lesson and assignment builder.
Provides endpoints for topic selection, lesson generation, storage, and export.
"""

import time
import asyncio
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import io

import sys
import os
# Add Server directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from module.models.schemas import (
    Lesson, Assignment, LessonGenerationRequest, LessonGenerationResponse,
    ValidationReport, TopicInfo
)
from module.services.topic_selector import TopicSelectorService
from module.services.lesson_storage import LessonStorageService
from module.generators.lesson_generator import LessonGenerator
from module.generators.assignment_generator import AssignmentGenerator
from module.exporters.export_service import ExportService
from services.ragflow_v2 import ragflow_service

# Import settings for API key
try:
    from config import settings
except ImportError:
    # Fallback for different import paths
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services (lazy initialization for better startup)
_topic_selector: Optional[TopicSelectorService] = None
_lesson_storage: Optional[LessonStorageService] = None
_lesson_generator: Optional[LessonGenerator] = None
_assignment_generator: Optional[AssignmentGenerator] = None
_export_service: Optional[ExportService] = None


def get_topic_selector() -> TopicSelectorService:
    """Get or create TopicSelectorService instance."""
    global _topic_selector
    if _topic_selector is None:
        _topic_selector = TopicSelectorService()
    return _topic_selector


def get_lesson_storage() -> LessonStorageService:
    """Get or create LessonStorageService instance."""
    global _lesson_storage
    if _lesson_storage is None:
        _lesson_storage = LessonStorageService()
    return _lesson_storage


def get_lesson_generator() -> LessonGenerator:
    """Get or create LessonGenerator instance."""
    global _lesson_generator
    if _lesson_generator is None:
        _lesson_generator = LessonGenerator(api_key=settings.GEMINI_API_KEY)
    return _lesson_generator


def get_assignment_generator() -> AssignmentGenerator:
    """Get or create AssignmentGenerator instance."""
    global _assignment_generator
    if _assignment_generator is None:
        _assignment_generator = AssignmentGenerator(api_key=settings.GEMINI_API_KEY)
    return _assignment_generator


def get_export_service() -> ExportService:
    """Get or create ExportService instance."""
    global _export_service
    if _export_service is None:
        _export_service = ExportService()
    return _export_service


# =============================================================================
# Response Models
# =============================================================================

class TopicsHierarchyResponse(BaseModel):
    """Response model for hierarchical topics."""
    classes: List[str] = Field(..., description="Available classes")


class SubjectsResponse(BaseModel):
    """Response model for subjects."""
    class_name: str
    subjects: List[str]


class TopicsResponse(BaseModel):
    """Response model for topics."""
    class_name: str
    subject: str
    topics: List[TopicInfo]


class LessonListItem(BaseModel):
    """Summary item for lesson list."""
    id: str
    class_name: str
    subject: str
    topic: str
    created_at: str
    validation_score: float


class LessonListResponse(BaseModel):
    """Response model for lesson list."""
    lessons: List[LessonListItem]
    total: int


class LessonDetailResponse(BaseModel):
    """Response model for lesson detail."""
    lesson: Lesson
    assignment: Optional[Assignment] = None


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


# =============================================================================
# Topic Selection Endpoints
# =============================================================================

@router.get("/topics", response_model=TopicsHierarchyResponse)
async def get_available_classes():
    """
    Get available classes from the textbook database.
    
    Returns list of classes that have content available.
    """
    try:
        topic_selector = get_topic_selector()
        classes = await topic_selector.get_available_classes()
        return TopicsHierarchyResponse(classes=classes)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Textbook database not available: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get classes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve classes: {str(e)}"
        )


@router.get("/topics/{class_name}/subjects", response_model=SubjectsResponse)
async def get_subjects_for_class(class_name: str):
    """
    Get available subjects for a specific class.
    
    Args:
        class_name: The class to get subjects for (e.g., "Class_6")
    """
    try:
        topic_selector = get_topic_selector()
        subjects = await topic_selector.get_subjects_for_class(class_name)
        
        if not subjects:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No subjects found for class: {class_name}"
            )
        
        return SubjectsResponse(class_name=class_name, subjects=subjects)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subjects for {class_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subjects: {str(e)}"
        )


@router.get("/topics/{class_name}/{subject}", response_model=TopicsResponse)
async def get_topics_for_subject(class_name: str, subject: str):
    """
    Get available topics for a specific class and subject.
    
    Args:
        class_name: The class (e.g., "Class_6")
        subject: The subject (e.g., "Mathematics")
    """
    try:
        topic_selector = get_topic_selector()
        topics = await topic_selector.get_topics_for_subject(class_name, subject)
        
        if not topics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No topics found for {class_name}/{subject}"
            )
        
        return TopicsResponse(
            class_name=class_name,
            subject=subject,
            topics=topics
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get topics for {class_name}/{subject}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve topics: {str(e)}"
        )


# =============================================================================
# Lesson Generation Endpoint
# =============================================================================

@router.post("/generate", response_model=LessonGenerationResponse)
async def generate_lesson(request: LessonGenerationRequest):
    """
    Generate a complete lesson and assignment for the specified topic.
    
    This endpoint:
    1. Retrieves textbook content for the topic
    2. Generates an 8-slide lesson
    3. Generates an assignment with questions
    4. Validates content against source material
    5. Saves the lesson and assignment
    
    Args:
        request: LessonGenerationRequest with class_name, subject, topic
        
    Returns:
        LessonGenerationResponse with lesson, assignment, and validation report
    """
    start_time = time.time()
    
    try:
        # Get services
        topic_selector = get_topic_selector()
        lesson_gen = get_lesson_generator()
        assignment_gen = get_assignment_generator()
        storage = get_lesson_storage()
        
        # Step 1: Retrieve textbook content from RAGFlow, with local fallback if needed
        logger.info(f"Retrieving content for {request.class_name}/{request.subject}/{request.topic}")
        textbook_content = []
        retrieval_meta = {"dataset_id": None, "dataset_name": None, "rag_chunks_used": 0, "ragflow_session_id": None}
        try:
            textbook_content, retrieval_meta = await ragflow_service.retrieve_textbook_content(
                request.class_name,
                request.subject,
                request.topic,
                language=request.language,
                board=request.board,
            )
        except Exception as exc:
            logger.warning(f"RAGFlow retrieval failed, falling back to local topic selector: {exc}")
            textbook_content = await topic_selector.get_content_for_topic(
                request.class_name,
                request.subject,
                request.topic
            )
            retrieval_meta = {"dataset_id": None, "dataset_name": None, "rag_chunks_used": len(textbook_content), "ragflow_session_id": None}
        
        if not textbook_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No content found for {request.class_name}/{request.subject}/{request.topic}"
            )
        
        # Step 2: Generate lesson
        logger.info("Generating lesson...")
        lesson, validation_report = await lesson_gen.generate_lesson(
            textbook_content=textbook_content,
            class_name=request.class_name,
            subject=request.subject,
            topic=request.topic
        )
        
        # Step 3: Generate assignment
        logger.info("Generating assignment...")
        assignment = await assignment_gen.generate_assignment(
            lesson=lesson,
            textbook_content=textbook_content
        )
        
        # Create a new RAGFlow chat session for this lesson
        ragflow_session_id = None
        try:
            session_name = f"Lesson: {request.class_name} - {request.subject} - {request.topic}"
            logger.info(f"Creating new RAGFlow chat session for lesson: '{session_name}'")
            module_chat_id = getattr(settings, "RAGFLOW_MODULE_CHAT_ID", None) or settings.RAGFLOW_CHAT_ID
            ragflow_session_id = await asyncio.to_thread(
                ragflow_service.create_new_session,
                chat_id=module_chat_id,
                name=session_name
            )
            logger.info(f"Successfully created RAGFlow chat session with ID: {ragflow_session_id}")
        except Exception as e:
            logger.error(f"Failed to create RAGFlow chat session for lesson: {e}")
            
        # Store in lesson
        lesson.ragflow_session_id = ragflow_session_id

        saved_id = None
        if request.save:
            # Step 4: Save lesson and assignment
            logger.info("Saving lesson and assignment...")
            lesson_id = await storage.save_lesson(lesson, assignment)

            # Update lesson with saved ID
            lesson.id = lesson_id
            assignment.lesson_id = lesson_id
            saved_id = lesson_id
        
        generation_time_ms = (time.time() - start_time) * 1000
        logger.info(f"Generation completed in {generation_time_ms:.0f}ms")
        
        return LessonGenerationResponse(
            lesson=lesson,
            assignment=assignment,
            generation_time_ms=generation_time_ms,
            validation_report=validation_report,
            dataset_id=retrieval_meta.get("dataset_id"),
            dataset_name=retrieval_meta.get("dataset_name"),
            rag_chunks_used=retrieval_meta.get("rag_chunks_used"),
            saved_id=saved_id,
            ragflow_session_id=ragflow_session_id,
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Lesson generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lesson generation failed: {str(e)}"
        )


# =============================================================================
# Lesson Storage Endpoints
# =============================================================================

@router.get("/lessons", response_model=LessonListResponse)
async def list_lessons(
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID"),
    class_name: Optional[str] = Query(None, description="Filter by class"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip")
):
    """
    List saved lessons with optional filtering.
    
    Args:
        teacher_id: Optional filter by teacher
        class_name: Optional filter by class
        subject: Optional filter by subject
        limit: Maximum number of results (1-100)
        offset: Number of results to skip for pagination
    """
    try:
        storage = get_lesson_storage()
        
        lessons = await storage.list_lessons(
            teacher_id=teacher_id,
            class_name=class_name,
            subject=subject,
            limit=limit,
            offset=offset
        )
        
        total = await storage.count_lessons(teacher_id=teacher_id)
        
        lesson_items = [
            LessonListItem(
                id=lesson.id,
                class_name=lesson.class_name,
                subject=lesson.subject,
                topic=lesson.topic,
                created_at=lesson.created_at.isoformat(),
                validation_score=lesson.validation_score
            )
            for lesson in lessons
        ]
        
        return LessonListResponse(lessons=lesson_items, total=total)
        
    except Exception as e:
        logger.error(f"Failed to list lessons: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list lessons: {str(e)}"
        )


@router.get("/lessons/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(lesson_id: str):
    """
    Get a specific lesson by ID.
    
    Args:
        lesson_id: The ID of the lesson to retrieve
        
    Returns:
        Lesson with its associated assignment
    """
    try:
        storage = get_lesson_storage()
        
        lesson = await storage.get_lesson(lesson_id)
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson not found: {lesson_id}"
            )
        
        assignment = await storage.get_assignment_for_lesson(lesson_id)
        
        return LessonDetailResponse(lesson=lesson, assignment=assignment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lesson {lesson_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lesson: {str(e)}"
        )


@router.delete("/lessons/{lesson_id}", response_model=MessageResponse)
async def delete_lesson(lesson_id: str):
    """
    Delete a lesson and its associated assignment.
    
    Args:
        lesson_id: The ID of the lesson to delete
    """
    try:
        storage = get_lesson_storage()
        
        deleted = await storage.delete_lesson(lesson_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson not found: {lesson_id}"
            )
        
        return MessageResponse(
            message=f"Lesson {lesson_id} deleted successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete lesson {lesson_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson: {str(e)}"
        )


# =============================================================================
# Export Endpoints
# =============================================================================

@router.get("/lessons/{lesson_id}/export/pdf")
async def export_lesson_pdf(
    lesson_id: str,
    include_diagrams: bool = Query(True, description="Include diagrams in export")
):
    """
    Export a lesson as PDF.
    
    Args:
        lesson_id: The ID of the lesson to export
        include_diagrams: Whether to include diagrams (default: True)
        
    Returns:
        PDF file download
    """
    try:
        storage = get_lesson_storage()
        export_service = get_export_service()
        
        # Get lesson
        lesson = await storage.get_lesson(lesson_id)
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson not found: {lesson_id}"
            )
        
        # Generate PDF
        pdf_bytes = await export_service.export_lesson_pdf(
            lesson=lesson,
            include_diagrams=include_diagrams
        )
        
        # Create filename
        filename = f"{lesson.topic.replace(' ', '_')}_{lesson.class_name}_lesson.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export lesson {lesson_id} as PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export lesson: {str(e)}"
        )


@router.get("/lessons/{lesson_id}/export/doc")
async def export_lesson_doc(
    lesson_id: str,
    include_diagrams: bool = Query(True, description="Include diagrams in export")
):
    """
    Export a lesson as Word document (DOCX).
    
    Args:
        lesson_id: The ID of the lesson to export
        include_diagrams: Whether to include diagrams (default: True)
        
    Returns:
        DOCX file download
    """
    try:
        storage = get_lesson_storage()
        export_service = get_export_service()
        
        # Get lesson
        lesson = await storage.get_lesson(lesson_id)
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson not found: {lesson_id}"
            )
        
        # Generate DOCX
        doc_bytes = await export_service.export_lesson_doc(
            lesson=lesson,
            include_diagrams=include_diagrams
        )
        
        # Create filename
        filename = f"{lesson.topic.replace(' ', '_')}_{lesson.class_name}_lesson.docx"
        
        return StreamingResponse(
            io.BytesIO(doc_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export lesson {lesson_id} as DOC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export lesson: {str(e)}"
        )


@router.get("/lessons/{lesson_id}/export/ppt")
async def export_lesson_ppt(
    lesson_id: str,
    include_diagrams: bool = Query(True, description="Include diagrams in export")
):
    """
    Export a lesson as PowerPoint presentation (PPTX).
    
    Args:
        lesson_id: The ID of the lesson to export
        include_diagrams: Whether to include diagrams (default: True)
        
    Returns:
        PPTX file download
    """
    try:
        storage = get_lesson_storage()
        export_service = get_export_service()
        
        # Get lesson
        lesson = await storage.get_lesson(lesson_id)
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson not found: {lesson_id}"
            )
        
        # Generate PPTX
        ppt_bytes = await export_service.export_lesson_ppt(
            lesson=lesson,
            include_diagrams=include_diagrams
        )
        
        # Create filename
        filename = f"{lesson.topic.replace(' ', '_')}_{lesson.class_name}_lesson.pptx"
        
        return StreamingResponse(
            io.BytesIO(ppt_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export lesson {lesson_id} as PPT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export lesson: {str(e)}"
        )


@router.get("/assignments/{lesson_id}/export/pdf")
async def export_assignment_pdf(
    lesson_id: str,
    include_answers: bool = Query(False, description="Include answer key")
):
    """
    Export an assignment as PDF.
    
    Args:
        lesson_id: The ID of the lesson whose assignment to export
        include_answers: Whether to include answer key (default: False)
        
    Returns:
        PDF file download
    """
    try:
        storage = get_lesson_storage()
        export_service = get_export_service()
        
        # Get assignment
        assignment = await storage.get_assignment_for_lesson(lesson_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found for lesson: {lesson_id}"
            )
        
        # Generate PDF
        pdf_bytes = await export_service.export_assignment_pdf(
            assignment=assignment,
            include_answers=include_answers
        )
        
        # Create filename
        suffix = "_with_answers" if include_answers else ""
        filename = f"{assignment.topic.replace(' ', '_')}_{assignment.class_name}_assignment{suffix}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export assignment for lesson {lesson_id} as PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export assignment: {str(e)}"
        )


@router.get("/assignments/{lesson_id}/export/doc")
async def export_assignment_doc(
    lesson_id: str,
    include_answers: bool = Query(False, description="Include answer key")
):
    """
    Export an assignment as Word document (DOCX).
    
    Args:
        lesson_id: The ID of the lesson whose assignment to export
        include_answers: Whether to include answer key (default: False)
        
    Returns:
        DOCX file download
    """
    try:
        storage = get_lesson_storage()
        export_service = get_export_service()
        
        # Get assignment
        assignment = await storage.get_assignment_for_lesson(lesson_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found for lesson: {lesson_id}"
            )
        
        # Generate DOCX
        doc_bytes = await export_service.export_assignment_doc(
            assignment=assignment,
            include_answers=include_answers
        )
        
        # Create filename
        suffix = "_with_answers" if include_answers else ""
        filename = f"{assignment.topic.replace(' ', '_')}_{assignment.class_name}_assignment{suffix}.docx"
        
        return StreamingResponse(
            io.BytesIO(doc_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export assignment for lesson {lesson_id} as DOC: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export assignment: {str(e)}"
        )
