"""
Reflection Router - Teaching reflection analysis endpoints.
Async implementation using Beanie/MongoDB.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from models.reflection import ClassReflection
from schemas.reflection import (
    ReflectionCreate, ReflectionResponse, ReflectionFeedback,
    ReflectionListItem, ReflectionHistoryResponse
)
from engines.reflection_analyzer import analyze_class_transcript

router = APIRouter()


@router.post("/", response_model=ReflectionResponse)
async def create_reflection(data: ReflectionCreate):
    """
    Analyze a class transcript and generate teaching feedback.
    Uses AI to provide insights on teaching effectiveness.
    """
    # Analyze the transcript using AI
    feedback = await analyze_class_transcript(
        transcript=data.transcript,
        topic=data.topic,
        subject=data.subject,
        class_level=data.class_level
    )
    
    # Create the reflection record
    db_reflection = ClassReflection(
        topic=data.topic,
        subject=data.subject,
        class_level=data.class_level,
        transcript=data.transcript,
        feedback_json=feedback
    )
    await db_reflection.insert()
    
    return ReflectionResponse(
        id=str(db_reflection.id),
        topic=db_reflection.topic,
        subject=db_reflection.subject,
        class_level=db_reflection.class_level,
        transcript=db_reflection.transcript,
        feedback=ReflectionFeedback(**feedback),
        created_at=db_reflection.created_at
    )


@router.get("/history", response_model=ReflectionHistoryResponse)
async def get_reflection_history(skip: int = 0, limit: int = 20):
    """Get reflection history with pagination."""
    reflections = await ClassReflection.find_all()\
        .sort(-ClassReflection.created_at)\
        .skip(skip)\
        .limit(limit)\
        .to_list()
    
    total = await ClassReflection.count()
    
    items = []
    for r in reflections:
        feedback = r.feedback_json or {}
        items.append(ReflectionListItem(
            id=str(r.id),
            topic=r.topic,
            subject=r.subject,
            class_level=r.class_level,
            created_at=r.created_at,
            strengths_count=len(feedback.get("strengths", [])),
            issues_count=len(feedback.get("issues", []))
        ))
    
    return ReflectionHistoryResponse(
        reflections=items,
        total=total
    )


@router.get("/{reflection_id}", response_model=ReflectionResponse)
async def get_reflection(reflection_id: str):
    """Get a specific reflection by ID."""
    reflection = await ClassReflection.get(reflection_id)
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    feedback = reflection.feedback_json or {
        "strengths": [],
        "issues": [],
        "classroom_atmosphere": "Unknown",
        "topic_feedback": [],
        "suggestions": []
    }
    
    return ReflectionResponse(
        id=str(reflection.id),
        topic=reflection.topic,
        subject=reflection.subject,
        class_level=reflection.class_level,
        transcript=reflection.transcript,
        feedback=ReflectionFeedback(**feedback),
        created_at=reflection.created_at
    )


@router.delete("/{reflection_id}")
async def delete_reflection(reflection_id: str):
    """Delete a reflection."""
    reflection = await ClassReflection.get(reflection_id)
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    await reflection.delete()
    return {"message": "Reflection deleted successfully"}


@router.get("/subject/{subject}", response_model=ReflectionHistoryResponse)
async def get_reflections_by_subject(subject: str, skip: int = 0, limit: int = 20):
    """Get reflections filtered by subject."""
    reflections = await ClassReflection.find(ClassReflection.subject == subject)\
        .sort(-ClassReflection.created_at)\
        .skip(skip)\
        .limit(limit)\
        .to_list()
    
    total = await ClassReflection.find(ClassReflection.subject == subject).count()
    
    items = []
    for r in reflections:
        feedback = r.feedback_json or {}
        items.append(ReflectionListItem(
            id=str(r.id),
            topic=r.topic,
            subject=r.subject,
            class_level=r.class_level,
            created_at=r.created_at,
            strengths_count=len(feedback.get("strengths", [])),
            issues_count=len(feedback.get("issues", []))
        ))
    
    return ReflectionHistoryResponse(
        reflections=items,
        total=total
    )


@router.post("/{reflection_id}/reanalyze", response_model=ReflectionResponse)
async def reanalyze_reflection(reflection_id: str):
    """Re-analyze an existing reflection with the latest AI model."""
    reflection = await ClassReflection.get(reflection_id)
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    # Re-analyze the transcript
    feedback = await analyze_class_transcript(
        transcript=reflection.transcript,
        topic=reflection.topic,
        subject=reflection.subject,
        class_level=reflection.class_level
    )
    
    # Update the reflection
    reflection.feedback_json = feedback
    await reflection.save()
    
    return ReflectionResponse(
        id=str(reflection.id),
        topic=reflection.topic,
        subject=reflection.subject,
        class_level=reflection.class_level,
        transcript=reflection.transcript,
        feedback=ReflectionFeedback(**feedback),
        created_at=reflection.created_at
    )
