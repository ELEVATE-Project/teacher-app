"""
Chat history router for managing chat sessions and messages.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from schemas.chat import (
    ChatHistoryResponse,
    SessionMessagesResponse,
    SaveMessageRequest,
    ChatMessageSchema
)
from services.chat_service import ChatService
from routers.users import get_current_user_id
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip")
):
    """
    Get chat session history for the authenticated user.
    
    Args:
        user_id: Current user ID from token
        limit: Maximum number of sessions to return
        skip: Number of sessions to skip (for pagination)
        
    Returns:
        ChatHistoryResponse with list of sessions
    """
    try:
        sessions, total = await ChatService.get_user_sessions(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        
        return ChatHistoryResponse(
            success=True,
            sessions=sessions,
            total=total
        )
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chat history: {str(e)}"
        )


@router.get("/session/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(100, ge=1, le=500, description="Number of messages to return"),
    skip: int = Query(0, ge=0, description="Number of messages to skip")
):
    """
    Get messages for a specific chat session.
    
    Args:
        session_id: Session ID
        user_id: Current user ID from token
        limit: Maximum number of messages to return
        skip: Number of messages to skip
        
    Returns:
        SessionMessagesResponse with list of messages
    """
    try:
        messages, total = await ChatService.get_session_messages(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        
        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or you don't have access to it"
            )
        
        return SessionMessagesResponse(
            success=True,
            session_id=session_id,
            messages=messages,
            total=total
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete (archive) a chat session.
    
    Args:
        session_id: Session ID to delete
        user_id: Current user ID from token
        
    Returns:
        Success message
    """
    try:
        deleted = await ChatService.delete_session(
            session_id=session_id,
            user_id=user_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or you don't have access to it"
            )
        
        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.post("/message", response_model=ChatMessageSchema)
async def save_message(
    message_data: SaveMessageRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Save a chat message (for manual message storage).
    
    Args:
        message_data: Message data to save
        user_id: Current user ID from token
        
    Returns:
        Saved message
    """
    try:
        message = await ChatService.save_message(
            session_id=message_data.session_id,
            user_id=user_id,
            role=message_data.role,
            content=message_data.content,
            tool_used=message_data.tool_used,
            confidence=message_data.confidence,
            metadata=message_data.metadata
        )
        
        return ChatMessageSchema(
            id=str(message.id),
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            tool_used=message.tool_used,
            confidence=message.confidence,
            metadata=message.metadata,
            created_at=message.created_at
        )
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save message: {str(e)}"
        )
