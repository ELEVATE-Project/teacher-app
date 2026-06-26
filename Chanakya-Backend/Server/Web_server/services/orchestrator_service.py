"""
Orchestrator service for handling queries with ChanakyaOrchestrator.
"""
import asyncio
import sys
import os
import json
import re
import time
import threading
from datetime import datetime

# Add parent directory to path to import orchestrator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cachetools import TTLCache
from orchestrator import ChanakyaOrchestrator
from orchestrator.schemas import OrchestratorInput
# pyrefly: ignore [missing-import]
import structlog
from fastapi import HTTPException
from config import settings
from schemas.query import QueryRequest, QueryResponse
from services.document_qa_service import get_document_answer

logger = structlog.get_logger(__name__)

# Leading phrases to strip for cache key only (conservative list to avoid merging different intents)
_CACHE_NORMALIZE_PREFIXES = (
    "what is ",
    "what's ",
    "tell me ",
    "explain ",
    "can you tell me ",
    "can you explain ",
)


def _normalize_query_for_cache(query: str) -> str:
    """
    Normalize query for cache key so variants like "what is 2+2", "2+2", "2 + 2" hit the same entry.
    Used only for building the cache key; original query is still sent to the orchestrator.
    """
    if not query:
        return ""
    s = query.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.rstrip("?")
    s = s.strip()
    for prefix in _CACHE_NORMALIZE_PREFIXES:
        if s.startswith(prefix):
            rest = s[len(prefix) :].strip()
            if rest:
                s = rest
            break
    return s


def _query_cache_key(query_request: QueryRequest) -> tuple:
    """Build a hashable cache key from normalized query and context (excludes session_id)."""
    query_normalized = _normalize_query_for_cache(query_request.query)
    context_str = json.dumps(query_request.context or {}, sort_keys=True)
    return (query_normalized, context_str)


class OrchestratorService:
    """Service for processing queries using ChanakyaOrchestrator."""
    
    def __init__(self):
        """Initialize the orchestrator service."""
        self.orchestrator = None
        self.initialized = False
        self._cache_enabled = getattr(settings, "QUERY_CACHE_ENABLED", True)
        self._query_cache: TTLCache | None = None
        self._cache_lock = threading.Lock()
        if self._cache_enabled:
            maxsize = getattr(settings, "QUERY_CACHE_MAX_SIZE", 500)
            ttl = getattr(settings, "QUERY_CACHE_TTL_SECONDS", 3600)
            self._query_cache = TTLCache(maxsize=maxsize, ttl=ttl)
            logger.info("Query cache enabled", maxsize=maxsize, ttl_seconds=ttl)
        
    def initialize(self):
        """Initialize the ChanakyaOrchestrator with API key."""
        try:
            api_key = os.getenv("OPENROUTER_API_KEY") or settings.GEMINI_API_KEY
            if not api_key:
                logger.error("Neither OPENROUTER_API_KEY nor GEMINI_API_KEY found in configuration")
                raise ValueError("An API key (OPENROUTER_API_KEY or GEMINI_API_KEY) is required for orchestrator initialization")
            
            logger.info("Initializing ChanakyaOrchestrator")
            self.orchestrator = ChanakyaOrchestrator(api_key=api_key)
            self.initialized = True
            logger.info("ChanakyaOrchestrator initialized successfully")
            
        except Exception as e:
            import traceback
            print("="*80)
            print("❌ OrchestratorService.initialize failed:")
            traceback.print_exc()
            print("="*80)
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            raise
    
    async def process_query(self, query_request: QueryRequest) -> QueryResponse:
        """
        Process a query using the orchestrator.
        
        Args:
            query_request: The query request containing query text and context
            
        Returns:
            QueryResponse with the orchestrator's response
            
        Raises:
            HTTPException: If orchestrator is not initialized or processing fails
        """
        if not self.initialized or not self.orchestrator:
            logger.error("Orchestrator not initialized")
            raise HTTPException(
                status_code=503,
                detail="Orchestrator service not initialized. Please try again later."
            )
        
        # Document Q&A: when document_id is set, answer using only that PDF's content
        if getattr(query_request, "document_id", None):
            start_time = time.time()
            try:
                loop = asyncio.get_event_loop()
                answer = await loop.run_in_executor(
                    None,
                    get_document_answer,
                    query_request.document_id,
                    query_request.query,
                    settings.GEMINI_API_KEY,
                    None,
                    None,
                )
                processing_time_ms = (time.time() - start_time) * 1000
                return QueryResponse(
                    success=True,
                    tool_used="document_qa",
                    reasoning="Answer generated from uploaded document content",
                    result={"response": answer, "document_id": query_request.document_id},
                    confidence=0.9,
                    processing_time_ms=processing_time_ms,
                    timestamp=datetime.utcnow(),
                    error=None,
                )
            except Exception as e:
                processing_time_ms = (time.time() - start_time) * 1000
                logger.error("Document Q&A failed: %s", e, exc_info=True)
                return QueryResponse(
                    success=False,
                    tool_used="document_qa",
                    reasoning="Document Q&A failed",
                    result={"response": f"Sorry, I couldn't answer from the document: {str(e)}", "document_id": query_request.document_id},
                    confidence=0.0,
                    processing_time_ms=processing_time_ms,
                    timestamp=datetime.utcnow(),
                    error=str(e),
                )
        
        # Direct Tool Selection (Bypass Orchestrator Routing/Graph)
        selected_tool = getattr(query_request, "selected_tool", None) or (query_request.context and query_request.context.get("selected_tool"))
        if selected_tool:
            if selected_tool == "general":
                selected_tool = "general_conversation"
                
            # Enforce strict scope in locked modes
            is_in_scope, warning_msg = await self._check_query_scope(query_request.query, selected_tool)
            if not is_in_scope:
                # Save user message to database history
                if query_request.session_id and self.orchestrator.storage:
                    await self.orchestrator.storage.add_message(query_request.session_id, "user", query_request.query)
                # Save warning response to database history
                if query_request.session_id and self.orchestrator.storage:
                    metadata = {
                        "tool_used": selected_tool,
                        "reasoning": f"Query out of scope for locked tool {selected_tool}",
                        "confidence": 1.0,
                        "result": {"response": warning_msg},
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.orchestrator.storage.add_message(query_request.session_id, "assistant", warning_msg, metadata=metadata)
                
                return QueryResponse(
                    success=False,
                    tool_used=selected_tool,
                    reasoning=f"Query out of scope for locked tool {selected_tool}",
                    result={"response": warning_msg},
                    confidence=1.0,
                    processing_time_ms=0.0,
                    timestamp=datetime.utcnow(),
                    error=warning_msg
                )
                
            start_time = time.time()
            try:
                logger.info(
                    "Direct tool execution (bypassing orchestrator)",
                    tool=selected_tool,
                    query=query_request.query[:100],
                    session_id=query_request.session_id
                )
                
                if selected_tool not in self.orchestrator.tools:
                    raise ValueError(f"Unknown tool requested: {selected_tool}")
                
                tool = self.orchestrator.tools[selected_tool]
                
                # Setup context
                context = dict(query_request.context or {})
                context['session_id'] = query_request.session_id or "default"
                if getattr(query_request, "document_id", None):
                    context["document_id"] = query_request.document_id
                
                # Save user message to database history
                if query_request.session_id and self.orchestrator.storage:
                    await self.orchestrator.storage.add_message(query_request.session_id, "user", query_request.query)
                
                # Run the tool directly
                result = await tool.run(query_request.query, context)
                
                # Serialize result properly
                result_dict = result
                if hasattr(result, 'model_dump'):
                    result_dict = result.model_dump()
                elif hasattr(result, 'dict'):
                    result_dict = result.dict()
                elif not isinstance(result_dict, dict):
                    result_dict = {"response": str(result_dict)}
                
                # Save assistant message to database history
                if query_request.session_id and self.orchestrator.storage:
                    assistant_message = result_dict.get("response") or result_dict.get("explanation") or result_dict.get("description") or f"Generated {selected_tool}"
                    metadata = {
                        "tool_used": selected_tool,
                        "reasoning": f"Bypassed orchestrator: ran {selected_tool} directly",
                        "confidence": 1.0,
                        "result": result_dict,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.orchestrator.storage.add_message(query_request.session_id, "assistant", assistant_message, metadata=metadata)
                
                processing_time_ms = (time.time() - start_time) * 1000
                
                return QueryResponse(
                    success=True,
                    tool_used=selected_tool,
                    reasoning=f"Bypassed orchestrator: ran {selected_tool} directly",
                    result=result_dict,
                    confidence=1.0,
                    processing_time_ms=processing_time_ms,
                    timestamp=datetime.utcnow(),
                    error=None
                )
            except Exception as e:
                processing_time_ms = (time.time() - start_time) * 1000
                logger.error(f"Direct tool execution failed: {e}", exc_info=True)
                return QueryResponse(
                    success=False,
                    tool_used=selected_tool,
                    reasoning=f"Bypassed orchestrator: direct execution of {selected_tool} failed",
                    result={"error": str(e)},
                    confidence=0.0,
                    processing_time_ms=processing_time_ms,
                    timestamp=datetime.utcnow(),
                    error=str(e)
                )
        if self._cache_enabled and self._query_cache is not None:
            key = _query_cache_key(query_request)
            with self._cache_lock:
                cached = self._query_cache.get(key)
            if cached is not None:
                logger.info("Returning cached response for query", query=query_request.query[:100])
                return cached.model_copy(update={"from_cache": True})
        
        start_time = time.time()
        
        try:
            logger.info(
                "Processing query",
                query=query_request.query[:100],  # Log first 100 chars
                session_id=query_request.session_id
            )

            # Create orchestrator input (include document_id in context if present for future use)
            context = dict(query_request.context or {})
            if getattr(query_request, "document_id", None):
                context["document_id"] = query_request.document_id

            orchestrator_input = OrchestratorInput(
                query=query_request.query,
                context=context,
                session_id=query_request.session_id or "default",
                selected_tool=getattr(query_request, "selected_tool", None)
            )

            # Process the query
            result = await self.orchestrator.process(orchestrator_input)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            logger.info(
                "Query processed successfully",
                tool_used=result.tool_used,
                confidence=result.confidence,
                processing_time_ms=processing_time_ms
            )
            
            # Convert orchestrator result to QueryResponse
            # OrchestratorOutput doesn't have 'success' field - determine from error
            success = result.error is None

            # Convert result to dict if it's a Pydantic model
            result_dict = result.result
            if hasattr(result_dict, 'model_dump'):
                result_dict = result_dict.model_dump()
            elif hasattr(result_dict, 'dict'):
                result_dict = result_dict.dict()
            elif not isinstance(result_dict, dict):
                # If it's not a dict and not a model, convert to dict
                result_dict = {"data": str(result_dict)}

            # Extract resources from result if present (they're added by orchestrator)
            resources = None
            if isinstance(result_dict, dict) and "resources" in result_dict:
                resources = result_dict.pop("resources", None)

            response = QueryResponse(
                success=success,
                tool_used=result.tool_used,
                reasoning=result.reasoning,
                result=result_dict,
                confidence=result.confidence,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.utcnow(),
                error=result.error,
                resources=resources
            )
            if self._cache_enabled and self._query_cache is not None and success:
                key = _query_cache_key(query_request)
                with self._cache_lock:
                    self._query_cache[key] = response
            return response
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Error processing query: {str(e)}"
            
            logger.error(
                "Query processing failed",
                error=str(e),
                processing_time_ms=processing_time_ms
            )
            
            # Return error response instead of raising exception
            return QueryResponse(
                success=False,
                tool_used="error",
                reasoning="An error occurred during processing",
                result={"error": str(e)},
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.utcnow(),
                error=error_msg
            )
    
    def get_available_tools(self) -> list[dict]:
        """
        Get list of available tools from orchestrator.
        
        Returns:
            List of tool information dictionaries
        """
        if not self.initialized or not self.orchestrator:
            logger.warning("Orchestrator not initialized, returning empty tool list")
            return []
        
        try:
            tools = []
            if hasattr(self.orchestrator, 'tools'):
                for tool in self.orchestrator.tools:
                    tools.append({
                        "name": tool.__class__.__name__,
                        "description": getattr(tool, 'description', 'No description available')
                    })
            return tools
        except Exception as e:
            logger.error(f"Error getting available tools: {str(e)}")
            return []
    
    def is_ready(self) -> bool:
        """Check if orchestrator is initialized and ready."""
        return self.initialized and self.orchestrator is not None
    
    async def get_recent_sessions(self, limit: int = 20) -> list[dict]:
        """
        Get recent chat sessions from storage.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session information dictionaries
        """
        try:
            if self.orchestrator.storage:
                sessions = await self.orchestrator.storage.get_recent_sessions(limit)
                # Add first user message as title for each session
                for session in sessions:
                    messages = await self.orchestrator.storage.get_messages(session["session_id"])
                    if messages:
                        # Find first user message
                        user_msg = next((m for m in messages if m["role"] == "user"), None)
                        if user_msg:
                            # Truncate to first 60 chars for title
                            session["title"] = user_msg["content"][:60] + ("..." if len(user_msg["content"]) > 60 else "")
                        else:
                            session["title"] = "New conversation"
                    else:
                        session["title"] = "Empty conversation"
                return sessions
            return []
        except Exception as e:
            logger.error(f"Error getting recent sessions: {str(e)}")
            return []
    
    async def get_session_messages(self, session_id: str) -> list[dict]:
        """
        Get all messages for a specific session.
        
        Args:
            session_id: The session ID to retrieve messages for
            
        Returns:
            List of message dictionaries
        """
        try:
            if self.orchestrator.storage:
                return await self.orchestrator.storage.get_messages(session_id)
            return []
        except Exception as e:
            logger.error(f"Error getting session messages: {str(e)}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if self.orchestrator.storage:
                return await self.orchestrator.storage.delete_session(session_id)
            return False
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False

    async def _check_query_scope(self, query: str, tool_name: str) -> tuple[bool, str]:
        """
        Verify if the query is in scope for the strictly locked mode.
        Returns: (is_in_scope, warning_message)
        """
        # Always allow small talk and greetings
        query_lower = query.strip().lower()
        greetings = ["hi", "hello", "hey", "thanks", "thank you", "good morning", "good afternoon", "namaste", "yes", "no"]
        if query_lower in greetings or len(query_lower) < 4:
            return True, ""

        # Map tool to scope description and user-friendly name
        tool_scopes = {
            "module_builder": {
                "desc": "creating teaching modules, lesson plans, slide outlines, course structures, teaching chapters, syllabus guides",
                "friendly": "Module Creator",
                "warning": "This chat is strictly dedicated to creating teaching modules and lesson plans. If you'd like to ask general questions, create classroom games, or handle a classroom crisis, please start a new chat in that mode or change the mode using the dropdown."
            },
            "activity_generator": {
                "desc": "classroom games, interactive activities, learning projects, math/science experiments or demonstrations",
                "friendly": "Activity Generator",
                "warning": "This chat is strictly dedicated to generating classroom activities and games. If you'd like to create a module/lesson plan, ask educational questions, or handle a classroom crisis, please start a new chat in that mode or change the mode using the dropdown."
            },
            "expert_teacher": {
                "desc": "explaining educational concepts, answering curriculum questions, general knowledge, teaching strategy advice",
                "friendly": "Expert Q&A",
                "warning": "This chat is strictly dedicated to educational Q&A and concept explanations. If you'd like to create a lesson module or generate classroom games, please start a new chat in that mode or change the mode using the dropdown."
            }
        }

        if tool_name not in tool_scopes:
            return True, ""

        scope_info = tool_scopes[tool_name]
        prompt = f"""You are an educational assistant quality checker.
The current chat interface is strictly locked to: '{scope_info["friendly"]}' which is for: {scope_info["desc"]}.
The teacher entered this query: "{query}"

Determine if this query is relevant to this locked scope or if it is asking for something completely different (like classroom crisis management, teacher motivation, resource finder, or general unrelated topics).

Answer with ONLY "YES" or "NO".

Is the query within the scope of '{scope_info["friendly"]}'?"""

        try:
            from google.genai import types
            response = await self.orchestrator.client.aio.models.generate_content(
                model=self.orchestrator.model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=5,
                )
            )
            ans = response.text.strip().lower()
            if "no" in ans:
                return False, scope_info["warning"]
        except Exception as e:
            logger.error(f"Error checking query scope: {str(e)}")
        
        return True, ""



# Global instance
orchestrator_service = OrchestratorService()
