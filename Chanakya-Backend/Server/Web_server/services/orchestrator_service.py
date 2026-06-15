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
            if not settings.GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY not found in configuration")
                raise ValueError("GEMINI_API_KEY is required for orchestrator initialization")
            
            logger.info("Initializing ChanakyaOrchestrator")
            self.orchestrator = ChanakyaOrchestrator(api_key=settings.GEMINI_API_KEY)
            self.initialized = True
            logger.info("ChanakyaOrchestrator initialized successfully")
            
        except Exception as e:
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
        
        # Return cached response for repeated identical query (no LLM call)
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
                session_id=query_request.session_id or "default"
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


# Global instance
orchestrator_service = OrchestratorService()
