"""
Chat session and message models for MongoDB using Beanie.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document, Indexed
from pydantic import Field
from bson import ObjectId


class ChatMessage(Document):
    """Individual chat message model."""
    
    session_id: Indexed(str)  # type: ignore
    user_id: Indexed(str)  # type: ignore
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content/text")
    tool_used: Optional[str] = Field(None, description="Tool used to generate response (for assistant messages)")
    confidence: Optional[float] = Field(None, description="Confidence score of response")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chat_messages"
        indexes = [
            [("session_id", 1), ("created_at", 1)],  # For fetching messages in a session
            [("user_id", 1), ("created_at", -1)],     # For user's message history
        ]


class ChatSession(Document):
    """Chat session model for organizing conversations."""
    
    session_id: Indexed(str, unique=True)  # type: ignore
    user_id: Indexed(str)  # type: ignore
    ragflow_session_id: Optional[str] = Field(None, description="Associated RAGFlow session identifier")
    ragflow_context: Optional[Dict[str, Any]] = Field(default=None, description="Context used when creating the RAGFlow session")
    title: str = Field(default="New Chat", description="Session title (first message preview)")
    message_count: int = Field(default=0, description="Number of messages in session")
    last_message_preview: Optional[str] = Field(None, description="Preview of last message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_archived: bool = Field(default=False, description="Whether session is archived")
    tool: Optional[str] = Field(None, description="The tool/mode scope of the chat session")
    
    class Settings:
        name = "chat_sessions"
        indexes = [
            [("user_id", 1), ("tool", 1), ("updated_at", -1)],  # For fetching user's sessions by tool
            [("user_id", 1), ("updated_at", -1)],  # For fetching user's sessions
            [("session_id", 1)],
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_1234567890",
                "user_id": "user_abc123",
                "title": "How to handle disruptive students?",
                "message_count": 4,
                "last_message_preview": "Here are some strategies...",
                "created_at": "2026-01-15T10:30:00Z",
                "updated_at": "2026-01-15T10:35:00Z"
            }
        }
