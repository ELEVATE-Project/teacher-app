"""
Active Listening Session Router
================================

Handles session persistence and recovery for Active Listening feature.
Provides endpoints to sync STT chunks from frontend for crash recovery.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Models ==============

class SessionSyncRequest(BaseModel):
    """Request model for syncing an active listening session."""
    session_id: str = Field(..., min_length=1, description="Unique session identifier")
    topic: str = Field(..., min_length=1, description="Class topic")
    subject: str = Field(..., min_length=1, description="Subject name")
    class_level: str = Field(..., description="Class level (e.g., Class 6)")
    transcript: str = Field(default="", description="Accumulated transcript")
    timestamp: int = Field(..., description="Client timestamp in milliseconds")


class SessionSyncResponse(BaseModel):
    """Response model for session sync."""
    success: bool
    session_id: str
    message: str
    synced_at: datetime


class SessionRecoveryResponse(BaseModel):
    """Response model for session recovery."""
    session_id: str
    topic: str
    subject: str
    class_level: str
    transcript: str
    chunk_count: int
    last_sync: datetime
    is_active: bool


class SessionListResponse(BaseModel):
    """Response model for listing recoverable sessions."""
    sessions: List[SessionRecoveryResponse]
    total: int


# ============== In-Memory Storage (can be replaced with database) ==============
# For production, you'd want to use MongoDB/Redis for persistence
_active_sessions: dict = {}


# ============== Endpoints ==============

@router.post("/sync", response_model=SessionSyncResponse)
async def sync_listening_session(data: SessionSyncRequest):
    """
    Sync an active listening session from the frontend.
    
    This endpoint is called periodically by the frontend to backup
    the transcript in case of crashes or disconnections.
    """
    try:
        # Store/update session data
        session_data = {
            "session_id": data.session_id,
            "topic": data.topic,
            "subject": data.subject,
            "class_level": data.class_level,
            "transcript": data.transcript,
            "chunk_count": len(data.transcript.split()) // 50 if data.transcript else 0,  # Estimate
            "last_sync": datetime.utcnow(),
            "client_timestamp": data.timestamp,
            "is_active": True
        }
        
        _active_sessions[data.session_id] = session_data
        
        logger.info(f"[ListeningSession] Synced session {data.session_id}: {len(data.transcript)} chars")
        
        return SessionSyncResponse(
            success=True,
            session_id=data.session_id,
            message="Session synced successfully",
            synced_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"[ListeningSession] Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync session: {str(e)}")


@router.get("/recover/{session_id}", response_model=SessionRecoveryResponse)
async def get_session(session_id: str):
    """
    Retrieve a specific session for recovery.
    """
    if session_id not in _active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = _active_sessions[session_id]
    
    return SessionRecoveryResponse(
        session_id=session["session_id"],
        topic=session["topic"],
        subject=session["subject"],
        class_level=session["class_level"],
        transcript=session["transcript"],
        chunk_count=session["chunk_count"],
        last_sync=session["last_sync"],
        is_active=session["is_active"]
    )


@router.get("/active", response_model=SessionListResponse)
async def list_active_sessions():
    """
    List all active (recoverable) sessions.
    Useful for admin panel or recovery dashboard.
    """
    active = [
        SessionRecoveryResponse(
            session_id=s["session_id"],
            topic=s["topic"],
            subject=s["subject"],
            class_level=s["class_level"],
            transcript=s["transcript"],
            chunk_count=s["chunk_count"],
            last_sync=s["last_sync"],
            is_active=s["is_active"]
        )
        for s in _active_sessions.values()
        if s.get("is_active", False)
    ]
    
    return SessionListResponse(
        sessions=active,
        total=len(active)
    )


@router.post("/complete/{session_id}")
async def complete_session(session_id: str):
    """
    Mark a session as completed (no longer active).
    Called when recording is properly stopped.
    """
    if session_id in _active_sessions:
        _active_sessions[session_id]["is_active"] = False
        logger.info(f"[ListeningSession] Session {session_id} marked as completed")
        return {"success": True, "message": "Session marked as completed"}
    
    return {"success": False, "message": "Session not found"}


@router.delete("/clear/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a session from storage.
    Called after successful analysis or when user discards session.
    """
    if session_id in _active_sessions:
        del _active_sessions[session_id]
        logger.info(f"[ListeningSession] Session {session_id} cleared")
        return {"success": True, "message": "Session cleared"}
    
    return {"success": False, "message": "Session not found"}


@router.delete("/clear-all")
async def clear_all_sessions():
    """
    Clear all sessions from storage.
    Admin endpoint for cleanup.
    """
    count = len(_active_sessions)
    _active_sessions.clear()
    logger.info(f"[ListeningSession] Cleared {count} sessions")
    return {"success": True, "cleared": count}