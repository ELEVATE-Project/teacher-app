"""
Analytics Router - Analytics and reporting endpoints.
Async implementation using Beanie/MongoDB.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models.classroom import Class, Student, ClassSession, StudentResponse as DBStudentResponse

router = APIRouter()


@router.get("/class/{class_id}/overview")
async def get_class_overview(class_id: str) -> Dict[str, Any]:
    """Get an overview of class performance and engagement."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    students = await Student.find(Student.class_id == class_id).to_list()
    sessions = await ClassSession.find(ClassSession.class_id == class_id).to_list()
    
    # Calculate class-wide stats
    total_students = len(students)
    total_sessions = len(sessions)
    
    # Level distribution
    level_distribution = {"weak": 0, "medium": 0, "strong": 0}
    total_confidence = 0.0
    
    for student in students:
        if student.level in level_distribution:
            level_distribution[student.level] += 1
        total_confidence += student.confidence
    
    avg_class_confidence = total_confidence / total_students if total_students > 0 else 0
    
    # Recent sessions (last 5)
    recent_sessions = sorted(sessions, key=lambda s: s.started_at, reverse=True)[:5]
    
    return {
        "class_id": class_id,
        "class_name": db_class.name,
        "subject": db_class.subject,
        "total_students": total_students,
        "total_sessions": total_sessions,
        "level_distribution": level_distribution,
        "average_confidence": round(avg_class_confidence, 2),
        "recent_sessions": [
            {
                "id": str(s.id),
                "topic": s.topic,
                "started_at": s.started_at.isoformat(),
                "is_active": s.is_active
            } for s in recent_sessions
        ]
    }


@router.get("/class/{class_id}/students/performance")
async def get_students_performance(class_id: str) -> List[Dict[str, Any]]:
    """Get performance metrics for all students in a class."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    students = await Student.find(Student.class_id == class_id).to_list()
    
    performance_data = []
    for student in students:
        # Get all non-skipped responses for this student
        responses = await DBStudentResponse.find(
            DBStudentResponse.student_id == str(student.id),
            DBStudentResponse.skipped == False
        ).to_list()
        
        total_responses = len(responses)
        avg_rating = sum(r.rating for r in responses) / total_responses if total_responses > 0 else 0
        
        # Determine trend
        trend = "stable"
        if total_responses >= 4:
            recent = responses[:len(responses)//2]
            older = responses[len(responses)//2:]
            recent_avg = sum(r.rating for r in recent) / len(recent)
            older_avg = sum(r.rating for r in older) / len(older)
            if recent_avg > older_avg + 0.5:
                trend = "improving"
            elif recent_avg < older_avg - 0.5:
                trend = "declining"
        
        performance_data.append({
            "student_id": str(student.id),
            "name": student.name,
            "level": student.level,
            "confidence": student.confidence,
            "total_responses": total_responses,
            "average_rating": round(avg_rating, 2),
            "trend": trend,
            "consecutive_correct": student.consecutive_correct,
            "consecutive_wrong": student.consecutive_wrong
        })
    
    # Sort by confidence (lowest first for attention)
    performance_data.sort(key=lambda x: x["confidence"])
    
    return performance_data


@router.get("/class/{class_id}/topics")
async def get_topic_analytics(class_id: str) -> List[Dict[str, Any]]:
    """Get analytics by topic for a class."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    sessions = await ClassSession.find(ClassSession.class_id == class_id).to_list()
    
    topic_data = {}
    for session in sessions:
        topic = session.topic
        if topic not in topic_data:
            topic_data[topic] = {
                "topic": topic,
                "session_count": 0,
                "total_questions": 0,
                "total_rating": 0,
                "difficulty_distribution": {"easy": 0, "medium": 0, "hard": 0}
            }
        
        topic_data[topic]["session_count"] += 1
        
        # Get responses for this session
        responses = await DBStudentResponse.find(
            DBStudentResponse.session_id == str(session.id),
            DBStudentResponse.skipped == False
        ).to_list()
        
        for r in responses:
            topic_data[topic]["total_questions"] += 1
            topic_data[topic]["total_rating"] += r.rating
            if r.difficulty_asked in topic_data[topic]["difficulty_distribution"]:
                topic_data[topic]["difficulty_distribution"][r.difficulty_asked] += 1
    
    # Calculate averages
    result = []
    for topic, data in topic_data.items():
        avg_rating = data["total_rating"] / data["total_questions"] if data["total_questions"] > 0 else 0
        result.append({
            "topic": topic,
            "session_count": data["session_count"],
            "total_questions": data["total_questions"],
            "average_rating": round(avg_rating, 2),
            "difficulty_distribution": data["difficulty_distribution"]
        })
    
    return result


@router.get("/class/{class_id}/attention-needed")
async def get_students_needing_attention(class_id: str) -> List[Dict[str, Any]]:
    """Get students who need attention based on low performance."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    students = await Student.find(Student.class_id == class_id).to_list()
    
    attention_needed = []
    for student in students:
        reasons = []
        
        # Check confidence
        if student.confidence < 2.0:
            reasons.append(f"Low confidence ({student.confidence:.1f})")
        
        # Check consecutive wrong streak
        if student.consecutive_wrong >= 2:
            reasons.append(f"Struggling ({student.consecutive_wrong} wrong in a row)")
        
        # Check if weak level
        if student.level == "weak":
            reasons.append("Weak level - needs support")
        
        # Check if not participated recently
        week_ago = datetime.utcnow() - timedelta(days=7)
        if student.last_answered_at is None:
            reasons.append("Never answered a question")
        elif student.last_answered_at < week_ago:
            days_ago = (datetime.utcnow() - student.last_answered_at).days
            reasons.append(f"Hasn't participated in {days_ago} days")
        
        if reasons:
            attention_needed.append({
                "student_id": str(student.id),
                "name": student.name,
                "level": student.level,
                "confidence": student.confidence,
                "reasons": reasons,
                "priority": len(reasons)  # More reasons = higher priority
            })
    
    # Sort by priority (highest first)
    attention_needed.sort(key=lambda x: x["priority"], reverse=True)
    
    return attention_needed


@router.get("/class/{class_id}/engagement")
async def get_engagement_analytics(class_id: str, days: int = 30) -> Dict[str, Any]:
    """Get engagement analytics over time."""
    db_class = await Class.get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    sessions = await ClassSession.find(
        ClassSession.class_id == class_id,
        ClassSession.started_at >= cutoff_date
    ).to_list()
    
    students = await Student.find(Student.class_id == class_id).to_list()
    student_ids = {str(s.id) for s in students}
    total_students = len(students)
    
    # Daily engagement tracking
    daily_data = {}
    student_participation = {sid: 0 for sid in student_ids}
    
    for session in sessions:
        date_key = session.started_at.strftime("%Y-%m-%d")
        if date_key not in daily_data:
            daily_data[date_key] = {
                "sessions": 0,
                "questions_asked": 0,
                "unique_students": set()
            }
        
        daily_data[date_key]["sessions"] += 1
        
        responses = await DBStudentResponse.find(
            DBStudentResponse.session_id == str(session.id)
        ).to_list()
        
        for r in responses:
            daily_data[date_key]["questions_asked"] += 1
            if r.student_id in student_ids:
                daily_data[date_key]["unique_students"].add(r.student_id)
                student_participation[r.student_id] += 1
    
    # Convert sets to counts
    engagement_timeline = []
    for date_key in sorted(daily_data.keys()):
        data = daily_data[date_key]
        participation_rate = len(data["unique_students"]) / total_students * 100 if total_students > 0 else 0
        engagement_timeline.append({
            "date": date_key,
            "sessions": data["sessions"],
            "questions_asked": data["questions_asked"],
            "students_participated": len(data["unique_students"]),
            "participation_rate": round(participation_rate, 1)
        })
    
    # Calculate overall stats
    total_sessions = len(sessions)
    never_participated = sum(1 for count in student_participation.values() if count == 0)
    highly_engaged = sum(1 for count in student_participation.values() if count >= 5)
    
    return {
        "period_days": days,
        "total_sessions": total_sessions,
        "total_students": total_students,
        "never_participated": never_participated,
        "highly_engaged": highly_engaged,
        "engagement_timeline": engagement_timeline
    }
