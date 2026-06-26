"""
Query-related Pydantic schemas for orchestrator integration.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema for query request to orchestrator."""
    query: str = Field(..., description="The user's query or question")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    session_id: Optional[str] = Field(None, description="Session ID for tracking conversation history")
    document_id: Optional[str] = Field(None, description="When set, answer using only this uploaded PDF document (chat document Q&A)")
    selected_tool: Optional[str] = Field(None, description="Manually override routing to run a specific tool directly")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How can I handle disruptive students in my classroom?",
                "context": {"subject": "Mathematics", "grade": "8"},
                "session_id": "session_123",
                "document_id": None
            }
        }


class QueryResponse(BaseModel):
    """Schema for orchestrator query response."""
    success: bool = Field(..., description="Whether the query was processed successfully")
    tool_used: str = Field(..., description="Name of the tool that handled the query")
    reasoning: str = Field(..., description="Reasoning for tool selection")
    result: Dict[str, Any] = Field(..., description="The response result from the tool")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the response")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    error: Optional[str] = Field(None, description="Error message if query failed")
    from_cache: bool = Field(False, description="True if response was served from cache (no LLM call)")
    resources: Optional[Dict[str, Any]] = Field(None, description="Additional resources from Tavily search (videos, articles, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "tool_used": "ClassroomGuidanceTool",
                "reasoning": "Query relates to classroom management",
                "result": {
                    "response": "Here are some strategies for handling disruptive students...",
                    "strategies": ["Positive reinforcement", "Clear expectations"]
                },
                "confidence": 0.92,
                "processing_time_ms": 1250.5,
                "timestamp": "2026-01-13T10:30:00Z",
                "error": None
            }
        }
