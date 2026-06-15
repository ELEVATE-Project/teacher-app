"""
Sessions Router - Class session management and student suggestions.
Async implementation using Beanie/MongoDB.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from models.classroom import ClassSession, Class, Student, StudentResponse as DBStudentResponse, Question
from schemas.classroom import (
    SessionCreate, SessionResponse, SuggestionResponse,
    ResponseCreate, SessionSummaryResponse, StudentSummary
)
from engines.selection import get_next_student_suggestion
from engines.confidence import update_student_confidence

router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def create_session(session_data: SessionCreate):
    """Start a new class session."""
    # Verify class exists
    db_class = await Class.get(session_data.class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if there's already an active session for this class
    active_session = await ClassSession.find_one(
        ClassSession.class_id == session_data.class_id,
        ClassSession.is_active == True
    )
    if active_session:
        raise HTTPException(
            status_code=400, 
            detail="An active session already exists for this class. End it first."
        )
    
    db_session = ClassSession(
        class_id=session_data.class_id,
        topic=session_data.topic
    )
    await db_session.insert()
    
    return SessionResponse(
        id=str(db_session.id),
        class_id=db_session.class_id,
        topic=db_session.topic,
        started_at=db_session.started_at,
        ended_at=db_session.ended_at,
        is_active=db_session.is_active
    )


@router.get("/active/{class_id}", response_model=Optional[SessionResponse])
async def get_active_session(class_id: str):
    """Get the currently active session for a class."""
    session = await ClassSession.find_one(
        ClassSession.class_id == class_id,
        ClassSession.is_active == True
    )
    
    if not session:
        return None
    
    return SessionResponse(
        id=str(session.id),
        class_id=session.class_id,
        topic=session.topic,
        started_at=session.started_at,
        ended_at=session.ended_at,
        is_active=session.is_active
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session by ID."""
    session = await ClassSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=str(session.id),
        class_id=session.class_id,
        topic=session.topic,
        started_at=session.started_at,
        ended_at=session.ended_at,
        is_active=session.is_active
    )


@router.post("/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str):
    """End an active session."""
    session = await ClassSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.is_active:
        raise HTTPException(status_code=400, detail="Session is already ended")
    
    session.is_active = False
    session.ended_at = datetime.utcnow()
    await session.save()
    
    return SessionResponse(
        id=str(session.id),
        class_id=session.class_id,
        topic=session.topic,
        started_at=session.started_at,
        ended_at=session.ended_at,
        is_active=session.is_active
    )


@router.get("/{session_id}/suggest", response_model=Optional[SuggestionResponse])
async def get_suggestion(session_id: str):
    """Get the next student suggestion for a session."""
    session = await ClassSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.is_active:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    suggestion = await get_next_student_suggestion(session)
    return suggestion


@router.post("/{session_id}/response")
async def record_response(session_id: str, response_data: ResponseCreate):
    """Record a student's response to a question."""
    session = await ClassSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.is_active:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Verify student exists
    student = await Student.get(response_data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Create response record
    db_response = DBStudentResponse(
        session_id=session_id,
        student_id=response_data.student_id,
        question_id=response_data.question_id,
        rating=response_data.rating,
        difficulty_asked=response_data.difficulty_asked,
        skipped=response_data.skipped
    )
    await db_response.insert()
    
    # Update student's last answered time
    student.last_answered_at = datetime.utcnow()
    await student.save()
    
    # Update student confidence (unless skipped)
    if not response_data.skipped:
        await update_student_confidence(
            student=student,
            rating=response_data.rating,
            topic=session.topic
        )
    
    return {
        "message": "Response recorded successfully",
        "response_id": str(db_response.id),
        "new_confidence": student.confidence,
        "new_level": student.level
    }


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: str):
    """Get a summary of the session."""
    session = await ClassSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all responses for this session
    responses = await DBStudentResponse.find(
        DBStudentResponse.session_id == session_id
    ).to_list()
    
    # Get all students in the class
    students = await Student.find(Student.class_id == session.class_id).to_list()
    total_students = len(students)
    
    # Calculate duration
    end_time = session.ended_at or datetime.utcnow()
    duration_minutes = (end_time - session.started_at).total_seconds() / 60
    
    # Calculate stats
    student_response_map = {}
    difficulty_distribution = {"easy": 0, "medium": 0, "hard": 0}
    
    for r in responses:
        if not r.skipped:
            if r.student_id not in student_response_map:
                student_response_map[r.student_id] = []
            student_response_map[r.student_id].append(r)
            if r.difficulty_asked in difficulty_distribution:
                difficulty_distribution[r.difficulty_asked] += 1
    
    students_called = len(student_response_map)
    students_not_called = total_students - students_called
    
    total_questions = sum(count for count in difficulty_distribution.values())
    total_ratings = sum(r.rating for r in responses if not r.skipped)
    average_rating = total_ratings / total_questions if total_questions > 0 else 0
    
    participation_percentage = (students_called / total_students * 100) if total_students > 0 else 0
    
    # Build student summaries
    all_student_summaries = []
    students_improved = []
    students_need_attention = []
    
    for student in students:
        student_id = str(student.id)
        student_responses = student_response_map.get(student_id, [])
        times_called = len(student_responses)
        
        if times_called > 0:
            avg_rating = sum(r.rating for r in student_responses) / times_called
            
            # Calculate confidence change (simplified - based on average rating)
            confidence_change = 0.0
            if avg_rating >= 4:
                confidence_change = 0.3
            elif avg_rating >= 3:
                confidence_change = 0.1
            elif avg_rating <= 2:
                confidence_change = -0.2
            
            improved = avg_rating >= 3.5
        else:
            avg_rating = 0.0
            confidence_change = 0.0
            improved = False
        
        summary = StudentSummary(
            student_id=student_id,
            student_name=student.name,
            times_called=times_called,
            average_rating=round(avg_rating, 2),
            confidence_change=round(confidence_change, 2),
            improved=improved
        )
        
        all_student_summaries.append(summary)
        
        if improved:
            students_improved.append(summary)
        elif times_called > 0 and avg_rating < 3:
            students_need_attention.append(summary)
    
    return SessionSummaryResponse(
        session_id=session_id,
        topic=session.topic,
        duration_minutes=round(duration_minutes, 1),
        total_questions_asked=total_questions,
        participation_percentage=round(participation_percentage, 1),
        students_called=students_called,
        students_not_called=students_not_called,
        average_rating=round(average_rating, 2),
        difficulty_distribution=difficulty_distribution,
        students_improved=students_improved,
        students_need_attention=students_need_attention,
        all_student_summaries=all_student_summaries
    )


@router.get("/class/{class_id}/history", response_model=List[SessionResponse])
async def get_class_session_history(class_id: str, limit: int = 20):
    """Get session history for a class."""
    sessions = await ClassSession.find(
        ClassSession.class_id == class_id
    ).sort(-ClassSession.started_at).limit(limit).to_list()
    
    return [
        SessionResponse(
            id=str(s.id),
            class_id=s.class_id,
            topic=s.topic,
            started_at=s.started_at,
            ended_at=s.ended_at,
            is_active=s.is_active
        ) for s in sessions
    ]
