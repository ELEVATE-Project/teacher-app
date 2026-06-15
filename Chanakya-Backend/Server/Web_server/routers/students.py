"""
Students Router - CRUD operations for student management.
Async implementation using Beanie/MongoDB.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from models.classroom import Student, Class, StudentResponse as DBStudentResponse, ClassSession
from schemas.classroom import (
    StudentCreate, StudentBulkCreate, StudentResponse, 
    StudentUpdate, StudentProfileResponse
)

router = APIRouter()


@router.post("/class/{class_id}", response_model=StudentResponse)
async def create_student(class_id: str, student_data: StudentCreate):
    """Add a single student to a class."""
    # Verify class exists
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Set initial confidence based on level
    initial_confidence = {
        "weak": 1.5,
        "medium": 2.5,
        "strong": 4.0
    }.get(student_data.level, 2.5)
    
    if student_data.confidence != 2.5:  # User provided custom confidence
        initial_confidence = student_data.confidence
    
    db_student = Student(
        class_id=class_id,
        name=student_data.name,
        level=student_data.level,
        confidence=initial_confidence
    )
    await db_student.insert()
    
    return StudentResponse(
        id=str(db_student.id),
        class_id=db_student.class_id,
        name=db_student.name,
        level=db_student.level,
        confidence=db_student.confidence,
        last_answered_at=db_student.last_answered_at,
        consecutive_correct=db_student.consecutive_correct,
        consecutive_wrong=db_student.consecutive_wrong,
        topic_performance=db_student.topic_performance,
        created_at=db_student.created_at
    )


@router.post("/class/{class_id}/bulk", response_model=List[StudentResponse])
async def create_students_bulk(class_id: str, data: StudentBulkCreate):
    """Add multiple students to a class at once."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    created_students = []
    for student_data in data.students:
        initial_confidence = {
            "weak": 1.5,
            "medium": 2.5,
            "strong": 4.0
        }.get(student_data.level, 2.5)
        
        if student_data.confidence != 2.5:
            initial_confidence = student_data.confidence
            
        db_student = Student(
            class_id=class_id,
            name=student_data.name,
            level=student_data.level,
            confidence=initial_confidence
        )
        await db_student.insert()
        
        created_students.append(StudentResponse(
            id=str(db_student.id),
            class_id=db_student.class_id,
            name=db_student.name,
            level=db_student.level,
            confidence=db_student.confidence,
            last_answered_at=db_student.last_answered_at,
            consecutive_correct=db_student.consecutive_correct,
            consecutive_wrong=db_student.consecutive_wrong,
            topic_performance=db_student.topic_performance,
            created_at=db_student.created_at
        ))
    
    return created_students


@router.get("/class/{class_id}", response_model=List[StudentResponse])
async def get_class_students(class_id: str):
    """Get all students in a class."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    students = await Student.find(Student.class_id == class_id).to_list()
    
    return [
        StudentResponse(
            id=str(s.id),
            class_id=s.class_id,
            name=s.name,
            level=s.level,
            confidence=s.confidence,
            last_answered_at=s.last_answered_at,
            consecutive_correct=s.consecutive_correct,
            consecutive_wrong=s.consecutive_wrong,
            topic_performance=s.topic_performance,
            created_at=s.created_at
        ) for s in students
    ]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: str):
    """Get a specific student."""
    student = await Student.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return StudentResponse(
        id=str(student.id),
        class_id=student.class_id,
        name=student.name,
        level=student.level,
        confidence=student.confidence,
        last_answered_at=student.last_answered_at,
        consecutive_correct=student.consecutive_correct,
        consecutive_wrong=student.consecutive_wrong,
        topic_performance=student.topic_performance,
        created_at=student.created_at
    )


@router.get("/{student_id}/profile", response_model=StudentProfileResponse)
async def get_student_profile(student_id: str):
    """Get detailed student profile with history and stats."""
    student = await Student.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all responses for this student
    responses = await DBStudentResponse.find(
        DBStudentResponse.student_id == student_id,
        DBStudentResponse.skipped == False
    ).sort(-DBStudentResponse.answered_at).to_list()
    
    total_responses = len(responses)
    average_rating = 0.0
    if total_responses > 0:
        average_rating = sum(r.rating for r in responses) / total_responses
    
    # Calculate participation rate (sessions participated / total sessions for their class)
    total_sessions = await ClassSession.find(
        ClassSession.class_id == student.class_id
    ).count()
    
    # Get unique sessions the student participated in
    session_ids = set(r.session_id for r in responses)
    sessions_participated = len(session_ids)
    
    participation_rate = 0.0
    if total_sessions > 0:
        participation_rate = (sessions_participated / total_sessions) * 100
    
    # Calculate improvement trend (compare recent vs older ratings)
    improvement_trend = 0.0
    if total_responses >= 4:
        recent_avg = sum(r.rating for r in responses[:len(responses)//2]) / (len(responses)//2)
        older_avg = sum(r.rating for r in responses[len(responses)//2:]) / (len(responses) - len(responses)//2)
        improvement_trend = recent_avg - older_avg
    
    # Recent history
    recent_history = []
    for r in responses[:10]:
        session = await ClassSession.get(r.session_id) if r.session_id else None
        recent_history.append({
            "session_id": r.session_id,
            "rating": r.rating,
            "difficulty": r.difficulty_asked,
            "answered_at": r.answered_at.isoformat() if r.answered_at else None,
            "question_id": r.question_id,
            "topic": session.topic if session else None
        })
    
    student_response = StudentResponse(
        id=str(student.id),
        class_id=student.class_id,
        name=student.name,
        level=student.level,
        confidence=student.confidence,
        last_answered_at=student.last_answered_at,
        consecutive_correct=student.consecutive_correct,
        consecutive_wrong=student.consecutive_wrong,
        topic_performance=student.topic_performance,
        created_at=student.created_at
    )
    
    return StudentProfileResponse(
        student=student_response,
        total_responses=total_responses,
        average_rating=round(average_rating, 2),
        participation_rate=round(participation_rate, 1),
        improvement_trend=round(improvement_trend, 2),
        recent_history=recent_history
    )


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(student_id: str, student_data: StudentUpdate):
    """Update a student's information."""
    student = await Student.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if student_data.name is not None:
        student.name = student_data.name
    if student_data.level is not None:
        student.level = student_data.level
    if student_data.confidence is not None:
        student.confidence = student_data.confidence
    
    await student.save()
    
    return StudentResponse(
        id=str(student.id),
        class_id=student.class_id,
        name=student.name,
        level=student.level,
        confidence=student.confidence,
        last_answered_at=student.last_answered_at,
        consecutive_correct=student.consecutive_correct,
        consecutive_wrong=student.consecutive_wrong,
        topic_performance=student.topic_performance,
        created_at=student.created_at
    )


@router.delete("/{student_id}")
async def delete_student(student_id: str):
    """Delete a student."""
    student = await Student.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    await student.delete()
    return {"message": "Student deleted successfully"}
