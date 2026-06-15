"""
Content Explainer Tool
======================

Retrieves relevant NCERT content using RAG embeddings and generates
grounded explanations for teachers.
"""

import json
import structlog
import numpy as np
from typing import Optional, List, Dict
from google import genai
from google.genai import types

from ..schemas import ContentExplanationOutput
from .base import BaseTool

logger = structlog.get_logger(__name__)


CONTENT_EXPLAINER_PROMPT = """You are an expert educational content explainer for Indian teachers using NCERT curriculum.

=== CRITICAL: LANGUAGE REQUIREMENT ===
TEACHER'S LANGUAGE: {language}
YOU MUST RESPOND IN: {language}

If {language} is "Hinglish", you MUST write in Hinglish (mix Hindi and English words):
- Use Hindi words: hai, hota, hoti, mein, ka, ke, ko, se, aur, yeh, ek, etc.
- Use English for technical terms: photosynthesis, carbon dioxide, chlorophyll
- Example: "Photosynthesis ek process hai jismein plants apna food banate hain. Isme chlorophyll sunlight ko capture karta hai aur carbon dioxide aur water ko use karke carbohydrates banate hain."

If {language} is "English", use pure English.
If {language} is "Hindi", use Devanagari script.

=== CONTENT GUIDELINES ===
- Answer ONLY using information from the retrieved NCERT passages below
- If the passages don't contain enough information, say "The retrieved content doesn't fully cover this topic"
- Explain concepts in SIMPLE language suitable for rural Indian teachers
- Include PRACTICAL EXAMPLES from the Indian context
- Keep explanations CONCISE (2-3 paragraphs maximum)

=== RETRIEVED NCERT CONTENT ===
{retrieved_content}

=== TEACHER'S QUESTION ===
{question}

=== REMINDER: RESPOND IN {language} ===
Do NOT translate. Write naturally in {language} as shown in the examples above.

=== OUTPUT FORMAT ===
Provide your response in JSON format:
{{
    "explanation": "Clear, simple explanation based on retrieved content",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "examples": ["Example 1 from Indian context", "Example 2"],
    "sources": ["Class X | Mathematics | Chapter 3", "Class IX | Science | Chapter 5"],
    "confidence": 0.9,
    "coverage": "complete"
}}

Where:
- explanation: Main answer to the teacher's question (2-3 paragraphs)
- key_points: 3-5 important takeaways
- examples: Practical examples for classroom use
- sources: List the NCERT sources (Class|Subject|Book|Page)
- confidence: 0.0-1.0 based on how well retrieved content answers the question
- coverage: "complete", "partial", or "insufficient"

IMPORTANT: Base your answer ONLY on the retrieved content. Do not add external knowledge."""


class MockDatabase:
    """Mock database to maintain backward compatibility with legacy scripts."""
    def get_document_count(self) -> int:
        return 0
    def close(self):
        pass


class ContentExplainerTool(BaseTool):
    """
    Retrieves relevant NCERT content and generates grounded explanations.
    """
    
    name = "content_explainer"
    description = "Explains concepts using NCERT textbook content via RAG embeddings"
    
    def __init__(
        self,
        model_name: str = "models/gemini-2.5-flash",
        top_k: int = 5,
        temperature: float = 0.3,
        *args,
        **kwargs
    ):
        """
        Initialize the Content Explainer tool.
        
        Args:
            model_name: Gemini model for text generation
            top_k: Number of relevant passages to retrieve
            temperature: Generation temperature (low for factual content)
        """
        self.db = MockDatabase()
        self.client = genai.Client(api_key=self._get_api_key())
        self.model_name = model_name
        self.top_k = top_k
        self.temperature = temperature
        
        logger.info("ContentExplainerTool initialized with RAGFlow backend")
    
    def _get_api_key(self) -> str:
        """Get Gemini API key from environment."""
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        return api_key
    
    async def _retrieve_relevant_content(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Retrieve relevant NCERT passages using RAGFlow.
        
        Args:
            query: Teacher's question
            filters: Optional filters (e.g., {"class": "10", "subject": "Mathematics"})
            
        Returns:
            List of relevant documents with content and metadata
        """
        from services.ragflow_v2 import ragflow_service

        # Build retrieval query using filters to guide search
        query_parts = []
        if filters:
            if filters.get("class"):
                query_parts.append(filters["class"])
            if filters.get("subject"):
                query_parts.append(filters["subject"])
            if filters.get("language"):
                query_parts.append(filters["language"])
        query_parts.append(query)
        search_query = " ".join(query_parts)

        logger.info(f"Querying RAGFlow with: {search_query}")
        results = await ragflow_service.retrieve_raw_chunks_async(
            question=search_query,
            limit=self.top_k
        )
        
        logger.info("rag_search_complete",
            query_preview=query[:50],
            num_results=len(results),
            top_result_similarity=results[0].get('similarity', 0.0) if results else 0.0
        )
        return results
    
    def _format_retrieved_content(self, results: List[Dict]) -> str:
        """
        Format retrieved passages for prompt.
        
        Args:
            results: List of retrieved documents
            
        Returns:
            Formatted string with numbered passages
        """
        if not results:
            return "No relevant NCERT content found in database."
        
        formatted = []
        for i, doc in enumerate(results, 1):
            source = doc['source']
            content = doc['content']
            similarity = doc.get('similarity', 0.0)
            
            formatted.append(
                f"[Passage {i}] (Source: {source}, Relevance: {similarity:.2f})\n{content}\n"
            )
        
        return "\n".join(formatted)
    
    async def run(self, query: str, context: Optional[dict] = None) -> dict:
        """
        Execute the content explainer tool.
        
        Args:
            query: Teacher's question about content
            context: Optional context with filters (class, subject, language)
            
        Returns:
            ContentExplanationOutput dictionary
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
                    # Capitalize subject for database matching (Science, Mathematics, etc.)
                    filters["subject"] = context["subject"].capitalize()
                if context.get("language"):
                    # Capitalize language for database matching (English, Hindi, etc.)
                    filters["language"] = context["language"].capitalize()
            
            # Retrieve relevant content
            retrieved_docs = await self._retrieve_relevant_content(query, filters)
            
            if not retrieved_docs:
                return {
                    "explanation": "I couldn't find relevant content in the NCERT database for this question.",
                    "key_points": [],
                    "examples": [],
                    "sources": [],
                    "confidence": 0.0,
                    "coverage": "insufficient",
                    "retrieved_passages": 0
                }
            
            # Format content for prompt
            formatted_content = self._format_retrieved_content(retrieved_docs)
            
            # Get detected language from context
            detected_language = context.get('detected_language', 'English') if context else 'English'
            
            logger.info("content_explainer_language", detected=detected_language, query=query[:50])
            
            # Generate explanation using Gemini
            prompt = CONTENT_EXPLAINER_PROMPT.format(
                retrieved_content=formatted_content,
                question=query,
                language=detected_language
            )
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            result = json.loads(response.text)
            
            # Add metadata
            result["retrieved_passages"] = len(retrieved_docs)
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
