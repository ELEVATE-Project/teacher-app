"""
Content Explainer Tool
======================

Retrieves relevant NCERT content using RAGFlow Chat Assistant
and generates grounded explanations for teachers.
"""

import json
import structlog
import asyncio
import numpy as np
from typing import Optional, List, Dict
from google import genai
from google.genai import types

from ..schemas import ContentExplanationOutput
from .base import BaseTool

logger = structlog.get_logger(__name__)

# Prompt to structure the RAGFlow assistant output
STRUCTURING_PROMPT = """You are an expert helper that formats a RAG assistant's response and retrieved sources into a clean JSON structure for classroom teachers.

Original Assistant Response:
{assistant_response}

Retrieved Sources:
{retrieved_sources}

Teacher's Original Question:
{question}

=== OUTPUT FORMAT ===
You must respond with a JSON object conforming exactly to this structure:
{{
    "explanation": "Main answer formatted into 2-3 paragraphs. Keep it clear, simple, and grounded in the retrieved content.",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "examples": ["Indian context practical classroom example 1", "Example 2"],
    "sources": ["Class|Subject|Chapter name or document source 1", "Source 2"],
    "confidence": 0.85,
    "coverage": "complete"
}}

Where:
- explanation: Main detailed explanation.
- key_points: 3-5 key takeaways.
- examples: Classroom examples.
- sources: List of source documents from retrieved sources.
- confidence: A float score between 0.0 and 1.0 indicating how well the explanation is grounded in the retrieved sources. Use lower confidence (e.g., < 0.4) if the retrieved sources do not support or are irrelevant to the answer.
- coverage: Set to "complete", "partial", or "insufficient" based on how much of the question's required information is covered by the retrieved sources.

IMPORTANT: Return ONLY valid JSON, do not wrap in markdown block formatting."""

class MockDatabase:
    """Mock database to maintain backward compatibility with legacy scripts."""
    def get_document_count(self) -> int:
        return 0
    def close(self):
        pass

class ContentExplainerTool(BaseTool):
    """
    Converses with RAGFlow Chat Assistant and generates structured explanations.
    """
    
    name = "content_explainer"
    description = "Explains concepts using NCERT textbook content via RAGFlow stateful Chat Assistant"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/gemini-2.5-flash",
        top_k: int = 5,
        temperature: float = 0.3,
        *args,
        **kwargs
    ):
        """
        Initialize the Content Explainer tool.
        """
        self.db = MockDatabase()
        self.client = genai.Client(api_key=self._get_api_key(api_key))
        self.model_name = model_name
        self.top_k = top_k
        self.temperature = temperature
        
        logger.info("ContentExplainerTool initialized with RAGFlow stateful Chat Assistant")
    
    def _get_api_key(self, api_key: Optional[str] = None) -> str:
        """Get API key from parameter or environment."""
        import os
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("Neither GEMINI_API_KEY nor OPENROUTER_API_KEY environment variable is set")
        return key

    async def run(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Execute the content explainer tool.
        
        Converses with RAGFlow Chat Assistant, then formats the output into structured JSON.
        """
        try:
            logger.info("content_explainer_start",
                query_preview=query[:100],
                has_context=bool(context)
            )
            
            # Extract filters from context
            filters = {}
            if context:
                if context.get("class"):
                    filters["class"] = context["class"]
                if context.get("subject"):
                    filters["subject"] = context["subject"].capitalize()
                if context.get("language"):
                    filters["language"] = context["language"].capitalize()
            
            # Get FastAPI session_id
            fastapi_session_id = (context or {}).get("session_id") or "default_session"
            
            # Import ragflow_service and settings to resolve content chatbot ID
            from services.ragflow_v2 import ragflow_service
            from config import settings
            content_chat_id = settings.RAGFLOW_CHAT_ID
            
            # Try lookup in MongoDB ChatSession
            ragflow_session_id = None
            chat_session = None
            try:
                from models.chat_session import ChatSession as MongoChatSession
                chat_session = await MongoChatSession.find_one(MongoChatSession.session_id == fastapi_session_id)
                if chat_session and chat_session.ragflow_session_id:
                    ragflow_session_id = chat_session.ragflow_session_id
                    logger.info(f"Retrieved existing ragflow_session_id from MongoDB: {ragflow_session_id}")
            except Exception as db_err:
                logger.warning(f"MongoDB/Beanie not initialized or lookup failed: {db_err}")
            
            # Fallback to listing RAGFlow sessions
            if not ragflow_session_id:
                sessions = await asyncio.to_thread(
                    ragflow_service.list_sessions,
                    chat_id=content_chat_id
                )
                for s in sessions:
                    if s.get("name") == fastapi_session_id:
                        ragflow_session_id = s.get("id")
                        break
            
            # If not found, create new session in RAGFlow
            if not ragflow_session_id:
                if chat_session and chat_session.title and chat_session.title != "New Chat":
                    session_name = chat_session.title
                else:
                    session_name = f"Chat: {query[:50]}"
                
                logger.info(f"Creating new RAGFlow chat session for: '{session_name}'")
                ragflow_session_id = await asyncio.to_thread(
                    ragflow_service.create_new_session,
                    chat_id=content_chat_id,
                    name=session_name
                )
                
                # Save new ragflow_session_id to MongoDB
                if ragflow_session_id and chat_session:
                    try:
                        chat_session.ragflow_session_id = ragflow_session_id
                        await chat_session.save()
                        logger.info(f"Saved new ragflow_session_id {ragflow_session_id} to MongoDB for session {fastapi_session_id}")
                    except Exception as save_err:
                        logger.error(f"Failed to save ragflow_session_id to MongoDB: {save_err}")
            
            if not ragflow_session_id:
                raise Exception("Failed to get or create RAGFlow chat session")
 
            # 3. Call RAGFlow stateful completions
            logger.info(f"Querying RAGFlow Chat Assistant for: '{query}' with session: {ragflow_session_id} and chat ID: {content_chat_id} and filters: {filters}")
            resp = await asyncio.to_thread(
                ragflow_service.chat_completion_stateful,
                question=query,
                chat_id=content_chat_id,
                session_id=ragflow_session_id,
                filters=filters
            )
            
            # 4. Parse RAGFlow response
            if not resp or resp.get("code") != 0:
                error_msg = resp.get("message") or "Failed to get response from RAGFlow"
                raise Exception(error_msg)
                
            assistant_response = resp.get("data", {}).get("answer", "")
            chunks = resp.get("data", {}).get("reference", {}).get("chunks", []) or []
            
            # Use all chunks returned by RAGFlow (similarity filtering is already handled on the RAGFlow server side)
            valid_chunks = chunks
            
            # If no content and no chunks were returned by RAGFlow, return fallback/refusal
            if not valid_chunks and not assistant_response:
                logger.info("No content or chunks returned by RAGFlow. Returning insufficient confidence to trigger fallback.")
                return {
                    "explanation": "I couldn't find any relevant content in the textbooks to answer this query.",
                    "key_points": [],
                    "examples": [],
                    "sources": [],
                    "confidence": 0.0,
                    "coverage": "insufficient",
                    "retrieved_passages": 0,
                    "filters_applied": filters if filters else None
                }
            
            # 5. Format retrieved sources for prompt
            formatted_sources = []
            for i, chunk in enumerate(valid_chunks, 1):
                doc_name = chunk.get("document_name") or chunk.get("source") or f"Doc_{i}"
                content = chunk.get("content") or chunk.get("text") or ""
                formatted_sources.append(f"[{i}] Source: {doc_name}\nContent: {content}\n")
            
            sources_str = "\n".join(formatted_sources) if formatted_sources else "No retrieved sources."
            
            # 6. Format RAGFlow assistant output using Gemini/OpenRouter to fit our schema
            prompt = STRUCTURING_PROMPT.format(
                assistant_response=assistant_response,
                retrieved_sources=sources_str,
                question=query
            )
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    response_mime_type="application/json"
                )
            )
            
            # Parse structured JSON response
            result = json.loads(response.text)
            
            # Parse confidence and coverage from LLM result naturally
            if "confidence" not in result:
                result["confidence"] = 0.8
            if "coverage" not in result:
                result["coverage"] = "complete"
            
            # Add metadata (set to actual number of valid chunks)
            result["retrieved_passages"] = len(valid_chunks)
            result["filters_applied"] = filters if filters else None
            
            logger.info(f"ContentExplainer completed with confidence: {result.get('confidence', 0.0)}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "explanation": "Error processing the response. Please try again.",
                "key_points": [],
                "examples": [],
                "sources": [],
                "confidence": 0.0,
                "coverage": "insufficient",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"ContentExplainer error: {e}")
            return {
                "explanation": f"An error occurred: {str(e)}",
                "key_points": [],
                "examples": [],
                "sources": [],
                "confidence": 0.0,
                "coverage": "insufficient",
                "error": str(e)
            }
            
    def close(self):
        """Close database connection."""
        self.db.close()
        logger.info("ContentExplainerTool closed")
