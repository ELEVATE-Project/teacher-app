"""
Confidence Update Engine

This engine handles updating student confidence scores
based on their answer ratings.

Rating to Confidence Delta Mapping:
⭐⭐⭐⭐⭐ (5) → +0.5
⭐⭐⭐⭐ (4) → +0.3
⭐⭐⭐ (3) → +0.1
⭐⭐ (2) → -0.1
⭐ (1) → -0.3

Confidence is clamped between 1.0 and 5.0
"""

from models.classroom import Student


# Rating to confidence delta mapping
CONFIDENCE_DELTA = {
    5: 0.5,   # Excellent answer
    4: 0.3,   # Good answer
    3: 0.1,   # Acceptable answer
    2: -0.1,  # Poor answer
    1: -0.3   # Very poor/no answer
}


async def update_student_confidence(
    student: Student,
    rating: int,
    topic: str
) -> None:
    """
    Update a student's confidence based on their answer rating.
    Also updates consecutive streaks and topic performance.
    Uses async Beanie operations.
    """
    # Get confidence delta
    delta = CONFIDENCE_DELTA.get(rating, 0)
    
    # Apply delta with clamping
    new_confidence = student.confidence + delta
    new_confidence = max(1.0, min(5.0, new_confidence))
    student.confidence = new_confidence
    
    # Update consecutive streaks
    if rating >= 4:  # Good or excellent
        student.consecutive_correct += 1
        student.consecutive_wrong = 0
    elif rating <= 2:  # Poor or very poor
        student.consecutive_wrong += 1
        student.consecutive_correct = 0
    else:  # Acceptable (3)
        # Reset both streaks on average performance
        student.consecutive_correct = 0
        student.consecutive_wrong = 0
    
    # Update topic performance
    topic_performance = student.topic_performance or {}
    current_topic_score = topic_performance.get(topic, 2.5)
    
    # Exponential moving average for topic score
    alpha = 0.3  # Weight for new observation
    new_topic_score = alpha * rating + (1 - alpha) * current_topic_score
    new_topic_score = max(1.0, min(5.0, new_topic_score))
    
    topic_performance[topic] = round(new_topic_score, 2)
    student.topic_performance = topic_performance
    
    # Auto-upgrade/downgrade level based on sustained performance
    update_student_level(student)
    
    # Save changes to MongoDB
    await student.save()


def update_student_level(student: Student) -> None:
    """
    Automatically adjust student level based on sustained performance.
    """
    confidence = student.confidence
    consecutive_correct = student.consecutive_correct
    consecutive_wrong = student.consecutive_wrong
    
    current_level = student.level
    
    # Upgrade conditions
    if current_level == "weak":
        # Upgrade to medium if confidence is high and performing well
        if confidence >= 3.0 and consecutive_correct >= 3:
            student.level = "medium"
    
    elif current_level == "medium":
        # Upgrade to strong
        if confidence >= 4.0 and consecutive_correct >= 4:
            student.level = "strong"
        # Downgrade to weak
        elif confidence <= 2.0 and consecutive_wrong >= 3:
            student.level = "weak"
    
    elif current_level == "strong":
        # Downgrade to medium if struggling
        if confidence <= 3.0 and consecutive_wrong >= 3:
            student.level = "medium"


def calculate_confidence_trend(ratings: list) -> str:
    """
    Calculate the trend direction from a list of recent ratings.
    Returns: "improving", "declining", "stable"
    """
    if len(ratings) < 3:
        return "stable"
    
    # Compare recent half vs older half
    mid = len(ratings) // 2
    recent_avg = sum(ratings[:mid]) / mid
    older_avg = sum(ratings[mid:]) / (len(ratings) - mid)
    
    difference = recent_avg - older_avg
    
    if difference > 0.5:
        return "improving"
    elif difference < -0.5:
        return "declining"
    else:
        return "stable"
