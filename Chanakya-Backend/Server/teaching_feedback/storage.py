"""
Teaching Feedback Storage
==========================

Handles database storage of teaching feedback (without storing transcripts).
"""

import json
import sqlite3
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from .schemas import TeachingFeedback, FeedbackHistory


class FeedbackStorage:
    """
    Stores teaching feedback in SQLite database.
    Does NOT store transcripts - only feedback and metadata.
    """
    
    def __init__(self, db_path: str = "data/teaching_feedback.db"):
        """Initialize storage with database path."""
        self.db_path = Path(db_path)
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Feedback table - stores only feedback, NOT transcripts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teaching_feedback (
                session_id TEXT PRIMARY KEY,
                teacher_id TEXT,
                topic TEXT NOT NULL,
                grade_level TEXT NOT NULL,
                duration_minutes INTEGER,
                language TEXT,
                timestamp TEXT NOT NULL,
                overall_score REAL NOT NULL,
                concept_coverage TEXT NOT NULL,
                clarity TEXT NOT NULL,
                engagement TEXT NOT NULL,
                rural_context TEXT NOT NULL,
                key_strengths TEXT NOT NULL,
                improvement_areas TEXT NOT NULL,
                actionable_tips TEXT NOT NULL,
                misconceptions_addressed TEXT NOT NULL,
                misconceptions_missed TEXT NOT NULL
            )
        """)
        
        # Index for teacher queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_teacher_timestamp 
            ON teaching_feedback(teacher_id, timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_feedback(self, feedback: TeachingFeedback, teacher_id: Optional[str] = None) -> bool:
        """
        Save teaching feedback to database.
        
        Args:
            feedback: TeachingFeedback object
            teacher_id: Optional teacher identifier
        
        Returns:
            True if saved successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO teaching_feedback (
                    session_id, teacher_id, topic, grade_level, duration_minutes, 
                    language, timestamp, overall_score, concept_coverage, clarity,
                    engagement, rural_context, key_strengths, improvement_areas,
                    actionable_tips, misconceptions_addressed, misconceptions_missed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.session_id,
                teacher_id,
                feedback.topic,
                feedback.grade_level,
                None,  # duration not stored in feedback object currently
                None,  # language not stored in feedback object currently
                feedback.timestamp.isoformat(),
                feedback.overall_score,
                json.dumps(feedback.concept_coverage.model_dump()),
                json.dumps(feedback.clarity.model_dump()),
                json.dumps(feedback.engagement.model_dump()),
                json.dumps(feedback.rural_context.model_dump()),
                json.dumps(feedback.key_strengths),
                json.dumps(feedback.improvement_areas),
                json.dumps(feedback.actionable_tips),
                json.dumps(feedback.misconceptions_addressed),
                json.dumps(feedback.misconceptions_missed)
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
    
    def get_feedback(self, session_id: str) -> Optional[TeachingFeedback]:
        """
        Retrieve feedback for a specific session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            TeachingFeedback object or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM teaching_feedback WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return self._row_to_feedback(row)
            
        except Exception as e:
            print(f"Error retrieving feedback: {e}")
            return None
    
    def get_teacher_history(self, teacher_id: str, limit: int = 5) -> FeedbackHistory:
        """
        Get feedback history for a teacher.
        
        Args:
            teacher_id: Teacher identifier
            limit: Number of recent feedbacks to include
        
        Returns:
            FeedbackHistory with statistics and recent sessions
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all feedbacks for teacher
            cursor.execute("""
                SELECT * FROM teaching_feedback 
                WHERE teacher_id = ? 
                ORDER BY timestamp DESC
            """, (teacher_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return FeedbackHistory(
                    teacher_id=teacher_id,
                    total_sessions=0,
                    average_score=0.0,
                    improvement_trend="stable",
                    recent_feedbacks=[],
                    common_strengths=[],
                    recurring_gaps=[]
                )
            
            # Calculate statistics
            all_feedbacks = [self._row_to_feedback(row) for row in rows]
            total_sessions = len(all_feedbacks)
            average_score = sum(f.overall_score for f in all_feedbacks) / total_sessions
            
            # Determine trend (compare last 3 vs previous 3)
            improvement_trend = "stable"
            if total_sessions >= 6:
                recent_avg = sum(f.overall_score for f in all_feedbacks[:3]) / 3
                older_avg = sum(f.overall_score for f in all_feedbacks[3:6]) / 3
                if recent_avg > older_avg + 0.1:
                    improvement_trend = "improving"
                elif recent_avg < older_avg - 0.1:
                    improvement_trend = "declining"
            
            # Find common patterns
            all_strengths = []
            all_gaps = []
            for f in all_feedbacks:
                all_strengths.extend(f.key_strengths)
                all_gaps.extend(f.improvement_areas)
            
            # Count frequency
            strength_counts = {}
            for s in all_strengths:
                strength_counts[s] = strength_counts.get(s, 0) + 1
            
            gap_counts = {}
            for g in all_gaps:
                gap_counts[g] = gap_counts.get(g, 0) + 1
            
            # Top recurring items
            common_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            recurring_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return FeedbackHistory(
                teacher_id=teacher_id,
                total_sessions=total_sessions,
                average_score=average_score,
                improvement_trend=improvement_trend,
                recent_feedbacks=all_feedbacks[:limit],
                common_strengths=[s[0] for s in common_strengths],
                recurring_gaps=[g[0] for g in recurring_gaps]
            )
            
        except Exception as e:
            print(f"Error retrieving teacher history: {e}")
            return FeedbackHistory(
                teacher_id=teacher_id,
                total_sessions=0,
                average_score=0.0,
                improvement_trend="stable",
                recent_feedbacks=[],
                common_strengths=[],
                recurring_gaps=[]
            )
    
    def _row_to_feedback(self, row) -> TeachingFeedback:
        """Convert database row to TeachingFeedback object."""
        from .schemas import ConceptCoverage, ClarityAnalysis, EngagementAnalysis, RuralContextAnalysis
        
        return TeachingFeedback(
            session_id=row[0],
            topic=row[2],
            grade_level=row[3],
            timestamp=datetime.fromisoformat(row[6]),
            overall_score=row[7],
            concept_coverage=ConceptCoverage(**json.loads(row[8])),
            clarity=ClarityAnalysis(**json.loads(row[9])),
            engagement=EngagementAnalysis(**json.loads(row[10])),
            rural_context=RuralContextAnalysis(**json.loads(row[11])),
            key_strengths=json.loads(row[12]),
            improvement_areas=json.loads(row[13]),
            actionable_tips=json.loads(row[14]),
            misconceptions_addressed=json.loads(row[15]),
            misconceptions_missed=json.loads(row[16])
        )
