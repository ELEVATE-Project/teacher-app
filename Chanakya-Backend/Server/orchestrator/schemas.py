"""
Orchestrator Schemas
====================

Pydantic models for orchestrator input/output and tool responses.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class OrchestratorInput(BaseModel):
    """
    Input to the orchestrator layer.
    """
    
    query: str = Field(
        ...,
        description="The teacher's query in English (post-NLP processing)",
        min_length=1
    )
    
    context: Optional[dict] = Field(
        default=None,
        description="Additional context (class info, subject, previous interactions)"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation tracking"
    )
    
    quick_answer_mode: Optional[bool] = Field(
        default=False,
        description="Force quick answer mode for fast, short responses"
    )
    
    selected_tool: Optional[str] = Field(
        default=None,
        description="Manually override routing to run a specific tool directly"
    )


class ActivityOutput(BaseModel):
    """
    Output from the Activity Generator tool.
    """
    
    activity_name: str = Field(
        ...,
        description="Name of the activity"
    )
    
    description: str = Field(
        ...,
        description="Brief description of the activity"
    )
    
    materials_needed: List[str] = Field(
        default_factory=list,
        description="Simple materials needed (commonly available in classrooms)"
    )
    
    steps: List[str] = Field(
        ...,
        description="Step-by-step instructions for the teacher"
    )
    
    duration_minutes: int = Field(
        default=10,
        description="Estimated duration in minutes"
    )
    
    learning_outcome: str = Field(
        ...,
        description="What students will understand after this activity"
    )
    
    tips: Optional[List[str]] = Field(
        default=None,
        description="Optional tips for the teacher"
    )


class ContentExplanationOutput(BaseModel):
    """
    Output from the Content Explainer tool.
    """
    
    explanation: str = Field(
        ...,
        description="Clear explanation based on NCERT content"
    )
    
    key_points: List[str] = Field(
        default_factory=list,
        description="Important takeaways from the explanation"
    )
    
    examples: List[str] = Field(
        default_factory=list,
        description="Practical examples for classroom use"
    )
    
    sources: List[str] = Field(
        default_factory=list,
        description="NCERT sources used (Class|Subject|Book format)"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence that retrieved content answers the question"
    )
    
    coverage: str = Field(
        default="partial",
        description="Coverage level: complete, partial, or insufficient"
    )
    
    retrieved_passages: int = Field(
        default=0,
        description="Number of NCERT passages retrieved"
    )
    
    filters_applied: Optional[dict] = Field(
        default=None,
        description="Filters applied during retrieval (class, subject, etc.)"
    )


class ClassroomGuidanceOutput(BaseModel):
    """
    Output from the Classroom Guidance tool.
    """
    
    situation_analysis: str = Field(
        ...,
        description="Understanding of the teaching challenge"
    )
    
    immediate_tips: List[str] = Field(
        default_factory=list,
        description="Quick tips teacher can use today"
    )
    
    step_by_step_strategies: List[dict] = Field(
        default_factory=list,
        description="Detailed strategies with steps and reasoning"
    )
    
    long_term_approach: str = Field(
        default="",
        description="Sustainable practices for preventing the issue"
    )
    
    rural_adaptations: str = Field(
        default="",
        description="How to implement with limited resources"
    )
    
    encouragement: str = Field(
        default="",
        description="Supportive message for the teacher"
    )


class OrchestratorOutput(BaseModel):
    """
    Output from the orchestrator layer.
    """
    
    tool_used: str = Field(
        ...,
        description="Which tool was selected to handle the query"
    )
    
    reasoning: str = Field(
        ...,
        description="Why this tool was selected"
    )
    
    result: ActivityOutput | dict = Field(
        ...,
        description="The result from the selected tool"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the tool selection and response"
    )
    
    processing_time_ms: float = Field(
        default=0.0,
        description="Total processing time"
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When processing completed"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )


class ConversationMessage(BaseModel):
    """
    A single message in the conversation history.
    """
    
    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="Role of the message sender"
    )
    
    content: str = Field(
        ...,
        description="Message content"
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the message was sent"
    )


class ConversationContext(BaseModel):
    """
    Maintains conversation context for the orchestrator.
    """
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="Conversation history"
    )
    
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (class, subject, grade, etc.)"
    )
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append(ConversationMessage(role=role, content=content))
    
    def get_history_text(self, max_messages: int = 10) -> str:
        """Get recent conversation history as text."""
        recent = self.messages[-max_messages:]
        return "\n".join([f"{m.role}: {m.content}" for m in recent])


class ExpertTeacherOutput(BaseModel):
    """
    Output from the Expert Teacher tool.
    """
    
    query: str = Field(
        ...,
        description="The original query"
    )
    
    explanation: str = Field(
        ...,
        description="Detailed explanation of the concept",
        min_length=50
    )
    
    key_points: List[str] = Field(
        ...,
        description="Key points to remember (3-5 points)"
    )
    
    teaching_tips: List[str] = Field(
        ...,
        description="Practical tips for teaching this concept (2-3 tips)"
    )
    
    examples: List[str] = Field(
        default_factory=list,
        description="Real-world examples or analogies"
    )
    
    common_misconceptions: List[str] = Field(
        default_factory=list,
        description="Common student misconceptions to watch for"
    )
    
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Questions to check student understanding"
    )
    
    grade_level: str = Field(
        default="middle school",
        description="Target grade level"
    )
    
    subject: str = Field(
        default="general",
        description="Subject area"
    )
    
    confidence: float = Field(
        default=0.85,
        description="Confidence score for this response",
        ge=0.0,
        le=1.0
    )


class ResourceLink(BaseModel):
    """A single resource link (video, article, etc.)."""
    
    title: str = Field(..., description="Title of the resource")
    url: str = Field(..., description="URL to the resource")
    description: str = Field(default="", description="Brief description")
    resource_type: str = Field(default="web", description="Type: video, article, pdf, etc.")


class ResourceFinderOutput(BaseModel):
    """
    Output from the Resource Finder tool.
    """
    
    query: str = Field(
        ...,
        description="The topic searched for"
    )
    
    summary: str = Field(
        default="",
        description="AI-generated summary of the topic"
    )
    
    web_resources: List[ResourceLink] = Field(
        default_factory=list,
        description="General web resources and articles"
    )
    
    video_resources: List[ResourceLink] = Field(
        default_factory=list,
        description="Video resources (YouTube, etc.)"
    )
    
    educational_resources: List[ResourceLink] = Field(
        default_factory=list,
        description="Educational resources (lesson plans, PDFs, etc.)"
    )
    
    total_results: int = Field(
        default=0,
        description="Total number of resources found"
    )
    
    confidence: float = Field(
        default=0.85,
        description="Confidence score",
        ge=0.0,
        le=1.0
    )