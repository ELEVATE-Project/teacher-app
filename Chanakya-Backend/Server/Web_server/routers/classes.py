"""
Classes Router - CRUD operations for classroom management.
Async implementation using Beanie/MongoDB.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from models.classroom import Class, Student
from schemas.classroom import ClassCreate, ClassResponse, ClassListResponse

router = APIRouter()


@router.post("/", response_model=ClassResponse)
async def create_class(class_data: ClassCreate):
    """Create a new class."""
    db_class = Class(
        name=class_data.name,
        subject=class_data.subject
    )
    await db_class.insert()
    
    return ClassResponse(
        id=str(db_class.id),
        name=db_class.name,
        subject=db_class.subject,
        created_at=db_class.created_at,
        student_count=0
    )


@router.get("/", response_model=ClassListResponse)
async def get_all_classes():
    """Get all classes with student counts."""
    classes = await Class.find_all().to_list()
    result = []
    
    for c in classes:
        student_count = await Student.find(Student.class_id == str(c.id)).count()
        result.append(ClassResponse(
            id=str(c.id),
            name=c.name,
            subject=c.subject,
            created_at=c.created_at,
            student_count=student_count
        ))
    
    return ClassListResponse(classes=result)


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(class_id: str):
    """Get a specific class by ID."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    student_count = await Student.find(Student.class_id == class_id).count()
    
    return ClassResponse(
        id=str(db_class.id),
        name=db_class.name,
        subject=db_class.subject,
        created_at=db_class.created_at,
        student_count=student_count
    )


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(class_id: str, class_data: ClassCreate):
    """Update a class."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    db_class.name = class_data.name
    db_class.subject = class_data.subject
    await db_class.save()
    
    student_count = await Student.find(Student.class_id == class_id).count()
    
    return ClassResponse(
        id=str(db_class.id),
        name=db_class.name,
        subject=db_class.subject,
        created_at=db_class.created_at,
        student_count=student_count
    )


@router.delete("/{class_id}")
async def delete_class(class_id: str):
    """Delete a class and all its students."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Delete all students in this class
    await Student.find(Student.class_id == class_id).delete()
    
    # Delete the class
    await db_class.delete()
    
    return {"message": "Class deleted successfully"}
