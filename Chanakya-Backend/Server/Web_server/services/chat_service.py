"""
Chat history service for managing chat sessions and messages.
"""
from datetime import datetime
from typing import List, Optional
from models.chat_session import ChatSession, ChatMessage
from schemas.chat import ChatSessionSchema, ChatMessageSchema
from beanie import PydanticObjectId
import structlog

logger = structlog.get_logger(__name__)


class ChatService:
    """Service for managing chat sessions and messages."""
    
    @staticmethod
    async def get_or_create_session(
        session_id: str,
        user_id: str,
        ragflow_session_id: Optional[str] = None,
        ragflow_context: Optional[dict] = None,
        tool: Optional[str] = None
    ) -> ChatSession:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            user_id: User ID
            tool: Optional tool scope
            
        Returns:
            ChatSession object
        """
        # Try to find existing session
        session = await ChatSession.find_one(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id
        )
        
        if not session:
            # Create new session
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                ragflow_session_id=ragflow_session_id,
                ragflow_context=ragflow_context,
                title="New Chat",
                message_count=0,
                tool=tool
            )
            await session.insert()
            logger.info(f"Created new chat session: {session_id} for user: {user_id} with tool: {tool}")
        else:
            updated = False
            if tool and getattr(session, 'tool', None) != tool:
                session.tool = tool
                updated = True
            if ragflow_session_id and session.ragflow_session_id != ragflow_session_id:
                session.ragflow_session_id = ragflow_session_id
                updated = True
            if ragflow_context:
                if not session.ragflow_context:
                    session.ragflow_context = {}
                # Merge incoming non-None/non-empty values to prevent losing class/subject selections
                merged = {**session.ragflow_context}
                for k, v in ragflow_context.items():
                    if v is not None and v != "":
                        merged[k] = v
                if session.ragflow_context != merged:
                    session.ragflow_context = merged
                    updated = True
            if updated:
                await session.save()
        
        return session
    
    @staticmethod
    async def save_message(
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        tool_used: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[dict] = None
    ) -> ChatMessage:
        """
        Save a chat message and update session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            role: Message role ('user' or 'assistant')
            content: Message content
            tool_used: Tool used for response
            confidence: Confidence score
            metadata: Additional metadata
            
        Returns:
            Created ChatMessage
        """
        logger.info(f"Saving message - session_id: {session_id}, user_id: {user_id}, role: {role}")
        
        # Determine the tool scope from tool_used / metadata
        tool = tool_used or (metadata.get("tool_used") if metadata else None)
        
        # Get or create session
        session = await ChatService.get_or_create_session(session_id, user_id, tool=tool)
        
        # Create message
        message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            tool_used=tool_used,
            confidence=confidence,
            metadata=metadata or {}
        )
        await message.insert()
        
        # Update session
        session.message_count += 1
        session.updated_at = datetime.utcnow()
        
        # Update title from first user message
        if session.message_count == 1 and role == "user":
            session.title = content[:100]  # First 100 chars as title
        
        # Update last message preview
        if role == "assistant":
            session.last_message_preview = content[:200]
        
        await session.save()
        
        logger.info(f"Saved message for session: {session_id}, role: {role}")
        return message
    
    @staticmethod
    async def get_user_sessions(
        user_id: str,
        limit: int = 20,
        skip: int = 0,
        tool: Optional[str] = None
    ) -> tuple[List[ChatSessionSchema], int]:
        """
        Get user's chat sessions.
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            skip: Number of sessions to skip
            tool: Optional tool scope to filter by
            
        Returns:
            Tuple of (list of sessions, total count)
        """
        # Build query criteria
        criteria = [
            ChatSession.user_id == user_id,
            ChatSession.is_archived == False
        ]
        if tool:
            criteria.append(ChatSession.tool == tool)

        # Get total count
        total = await ChatSession.find(*criteria).count()
        
        # Get sessions sorted by updated_at (most recent first)
        sessions = await ChatSession.find(*criteria).sort(-ChatSession.updated_at).skip(skip).limit(limit).to_list()
        
        # Convert to schema
        session_schemas = [
            ChatSessionSchema(
                id=str(session.id),
                session_id=session.session_id,
                title=session.title,
                message_count=session.message_count,
                last_message_preview=session.last_message_preview,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            for session in sessions
        ]
        
        return session_schemas, total
    
    @staticmethod
    async def get_session_messages(
        session_id: str,
        user_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> tuple[List[ChatMessageSchema], int]:
        """
        Get messages for a specific session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            limit: Maximum number of messages
            skip: Number of messages to skip
            
        Returns:
            Tuple of (list of messages, total count)
        """
        # Verify session belongs to user
        session = await ChatSession.find_one(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id
        )
        
        if not session:
            return [], 0
        
        # Get total count
        total = await ChatMessage.find(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id
        ).count()
        
        # Get messages sorted by created_at (oldest first)
        messages = await ChatMessage.find(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id
        ).sort(ChatMessage.created_at).skip(skip).limit(limit).to_list()
        
        # Convert to schema
        message_schemas = [
            ChatMessageSchema(
                id=str(msg.id),
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                tool_used=msg.tool_used,
                confidence=msg.confidence,
                metadata=msg.metadata,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        return message_schemas, total
    
    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> bool:
        """
        Archive/delete a chat session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        session = await ChatSession.find_one(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id
        )
        
        if not session:
            return False
        
        # Archive instead of hard delete
        session.is_archived = True
        await session.save()
        
        logger.info(f"Archived session: {session_id} for user: {user_id}")
        return True

    @staticmethod
    async def backfill_session_tools():
        """Backfill the 'tool' field for existing chat sessions based on their messages."""
        logger.info("Starting backfill of chat session tools...")
        try:
            sessions = await ChatSession.find(ChatSession.tool == None).to_list()
            logger.info(f"Found {len(sessions)} sessions without a tool field")
            
            for session in sessions:
                # Find assistant messages with a tool_used
                messages = await ChatMessage.find(
                    ChatMessage.session_id == session.session_id,
                    ChatMessage.role == "assistant",
                    ChatMessage.tool_used != None
                ).sort(-ChatMessage.created_at).to_list()
                
                tool = None
                if messages:
                    # Map tool_used to one of the three modes
                    for msg in messages:
                        if msg.tool_used in ("module_builder", "expert_teacher", "activity_generator"):
                            tool = msg.tool_used
                            break
                
                # Fallback 1: check user's first query content/context
                if not tool:
                    first_user_msg = await ChatMessage.find_one(
                        ChatMessage.session_id == session.session_id,
                        ChatMessage.role == "user"
                    )
                    if first_user_msg:
                        content = first_user_msg.content.lower()
                        if any(x in content for x in ("module", "lesson plan", "syllabus", "slide")):
                            tool = "module_builder"
                        elif any(x in content for x in ("activity", "game", "demonstration", "experiment")):
                            tool = "activity_generator"
                        else:
                            tool = "expert_teacher"
                
                # Fallback 2: default to expert_teacher if still None
                if not tool:
                    tool = "expert_teacher"
                    
                session.tool = tool
                await session.save()
                logger.info(f"Backfilled session {session.session_id} with tool: {tool}")
        except Exception as e:
            logger.error(f"Error during database backfill of session tools: {str(e)}")
