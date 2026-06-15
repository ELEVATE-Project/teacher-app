"""
Questions Router - CRUD operations and AI generation for questions.
Async implementation using Beanie/MongoDB.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from models.classroom import Question
from schemas.classroom import (
    QuestionCreate, QuestionBulkCreate, QuestionResponse,
    QuestionGenerateRequest, QuestionsByDifficulty
)
from engines.ai_questions import generate_questions_for_topic

router = APIRouter()


@router.post("/", response_model=QuestionResponse)
async def create_question(question_data: QuestionCreate):
    """Create a single question."""
    db_question = Question(
        topic=question_data.topic,
        difficulty=question_data.difficulty,
        text=question_data.text
    )
    await db_question.insert()
    
    return QuestionResponse(
        id=str(db_question.id),
        topic=db_question.topic,
        difficulty=db_question.difficulty,
        text=db_question.text,
        created_at=db_question.created_at
    )


@router.post("/bulk", response_model=List[QuestionResponse])
async def create_questions_bulk(data: QuestionBulkCreate):
    """Create multiple questions at once."""
    created_questions = []
    
    for q in data.questions:
        db_question = Question(
            topic=q.topic,
            difficulty=q.difficulty,
            text=q.text
        )
        await db_question.insert()
        
        created_questions.append(QuestionResponse(
            id=str(db_question.id),
            topic=db_question.topic,
            difficulty=db_question.difficulty,
            text=db_question.text,
            created_at=db_question.created_at
        ))
    
    return created_questions


@router.post("/generate", response_model=QuestionsByDifficulty)
async def generate_questions(request: QuestionGenerateRequest):
    """
    Generate questions using AI for a topic.
    Creates the questions in the database and returns them grouped by difficulty.
    """
    # Generate questions using AI
    generated = await generate_questions_for_topic(
        topic=request.topic,
        subject=request.subject,
        easy_count=request.easy_count,
        medium_count=request.medium_count,
        hard_count=request.hard_count
    )
    
    # Store in database and build response
    result = {"easy": [], "medium": [], "hard": []}
    
    for difficulty in ["easy", "medium", "hard"]:
        for text in generated.get(difficulty, []):
            db_question = Question(
                topic=request.topic,
                difficulty=difficulty,
                text=text
            )
            await db_question.insert()
            
            result[difficulty].append(QuestionResponse(
                id=str(db_question.id),
                topic=db_question.topic,
                difficulty=db_question.difficulty,
                text=db_question.text,
                created_at=db_question.created_at
            ))
    
    return QuestionsByDifficulty(**result)


@router.get("/topic/{topic}", response_model=QuestionsByDifficulty)
async def get_questions_by_topic(topic: str):
    """Get all questions for a topic, grouped by difficulty."""
    questions = await Question.find(Question.topic == topic).to_list()
    
    result = {"easy": [], "medium": [], "hard": []}
    
    for q in questions:
        response = QuestionResponse(
            id=str(q.id),
            topic=q.topic,
            difficulty=q.difficulty,
            text=q.text,
            created_at=q.created_at
        )
        if q.difficulty in result:
            result[q.difficulty].append(response)
    
    return QuestionsByDifficulty(**result)


@router.get("/", response_model=List[QuestionResponse])
async def get_all_questions(skip: int = 0, limit: int = 100):
    """Get all questions with pagination."""
    questions = await Question.find_all().skip(skip).limit(limit).to_list()
    
    return [
        QuestionResponse(
            id=str(q.id),
            topic=q.topic,
            difficulty=q.difficulty,
            text=q.text,
            created_at=q.created_at
        ) for q in questions
    ]


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str):
    """Get a specific question by ID."""
    question = await Question.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return QuestionResponse(
        id=str(question.id),
        topic=question.topic,
        difficulty=question.difficulty,
        text=question.text,
        created_at=question.created_at
    )


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: str, question_data: QuestionCreate):
    """Update a question."""
    question = await Question.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question.topic = question_data.topic
    question.difficulty = question_data.difficulty
    question.text = question_data.text
    await question.save()
    
    return QuestionResponse(
        id=str(question.id),
        topic=question.topic,
        difficulty=question.difficulty,
        text=question.text,
        created_at=question.created_at
    )


@router.delete("/{question_id}")
async def delete_question(question_id: str):
    """Delete a question."""
    question = await Question.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await question.delete()
    return {"message": "Question deleted successfully"}


@router.delete("/topic/{topic}")
async def delete_questions_by_topic(topic: str):
    """Delete all questions for a topic."""
    result = await Question.find(Question.topic == topic).delete()
    return {"message": f"Deleted questions for topic: {topic}"}
