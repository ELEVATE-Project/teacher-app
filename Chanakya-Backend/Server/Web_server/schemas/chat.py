"""
Chat history related schemas.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatMessageSchema(BaseModel):
    """Schema for individual chat message."""
    id: str = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session ID")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    tool_used: Optional[str] = Field(None, description="Tool used (for assistant messages)")
    confidence: Optional[float] = Field(None, description="Confidence score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_123",
                "session_id": "session_123",
                "role": "user",
                "content": "How can I handle disruptive students?",
                "created_at": "2026-01-15T10:30:00Z"
            }
        }


class ChatSessionSchema(BaseModel):
    """Schema for chat session summary."""
    id: str = Field(..., description="Session document ID")
    session_id: str = Field(..., description="Session identifier")
    title: str = Field(..., description="Session title")
    message_count: int = Field(..., description="Number of messages")
    last_message_preview: Optional[str] = Field(None, description="Last message preview")
    created_at: datetime = Field(..., description="Session creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "65a1b2c3d4e5f6g7h8i9j0k1",
                "session_id": "session_123",
                "title": "How to handle disruptive students?",
                "message_count": 4,
                "last_message_preview": "Here are some strategies...",
                "created_at": "2026-01-15T10:30:00Z",
                "updated_at": "2026-01-15T10:35:00Z"
            }
        }


class ChatHistoryResponse(BaseModel):
    """Response containing chat session history."""
    success: bool = Field(..., description="Whether request was successful")
    sessions: List[ChatSessionSchema] = Field(..., description="List of chat sessions")
    total: int = Field(..., description="Total number of sessions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "sessions": [],
                "total": 10
            }
        }


class SessionMessagesResponse(BaseModel):
    """Response containing messages for a session."""
    success: bool = Field(..., description="Whether request was successful")
    session_id: str = Field(..., description="Session ID")
    messages: List[ChatMessageSchema] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "session_123",
                "messages": [],
                "total": 4
            }
        }


class SaveMessageRequest(BaseModel):
    """Request to save a chat message."""
    session_id: str = Field(..., description="Session ID")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    tool_used: Optional[str] = Field(None, description="Tool used (for assistant messages)")
    confidence: Optional[float] = Field(None, description="Confidence score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
