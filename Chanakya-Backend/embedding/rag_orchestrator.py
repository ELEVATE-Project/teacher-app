"""
RAG Orchestrator: Retrieval-Augmented Generation system using Gemini
"""

import os
import logging
import warnings
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# Suppress FutureWarning about deprecated package BEFORE importing
warnings.filterwarnings('ignore', category=FutureWarning)
from google import genai
from google.genai import types

from .database import Database
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """RAG system that retrieves relevant context and generates answers using Gemini"""
    
    def __init__(self, db_path: str = "embedding/ncert_books.db", 
                 gemini_api_key: Optional[str] = None,
                 model_name: str = "models/gemini-2.5-flash"):
        """
        Initialize RAG orchestrator
        
        Args:
            db_path: Path to SQLite database
            gemini_api_key: Gemini API key (if None, reads from GEMINI_API_KEY env var)
            model_name: Name of the Gemini model to use
        """
        self.db_path = db_path
        self.model_name = model_name
        
        # Get API key
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.gemini_api_key or self.gemini_api_key.strip() == "":
            raise ValueError(
                "Gemini API key not provided or is empty.\n"
                "Please set GEMINI_API_KEY in your .env file:\n"
                "  1. Edit .env file\n"
                "  2. Add: GEMINI_API_KEY=your_actual_api_key_here\n"
                "  3. Get your API key from: https://makersuite.google.com/app/apikey\n"
                "Or pass gemini_api_key parameter when initializing RAGOrchestrator."
            )
        
        # Validate API key format (should not be placeholder)
        if self.gemini_api_key.strip() in ["your_gemini_api_key_here", "your_api_key_here"]:
            raise ValueError(
                "Gemini API key is set to placeholder value.\n"
                "Please update .env file with your actual API key from: "
                "https://makersuite.google.com/app/apikey"
            )
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.gemini_api_key)
        
        # Initialize model - ensure it has models/ prefix if not already present
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        
        self.model_name = model_name
        logger.info(f"Successfully initialized Gemini model: {model_name}")
        
        # Initialize components
        self.database = Database(db_path=db_path)
        self.embedding_service = EmbeddingService()
        
        logger.info(f"RAG Orchestrator initialized with model: {model_name}")
    
    def query(self, query_text: str, top_k: int = 5, 
              filters: Optional[Dict[str, str]] = None,
              temperature: float = 0.7) -> Dict[str, Any]:
        """
        Query the RAG system with a question
        
        Args:
            query_text: User's question
            top_k: Number of relevant documents to retrieve
            filters: Optional filters (class, subject, language)
            temperature: Temperature for Gemini generation (0.0-1.0)
        
        Returns:
            Dictionary containing:
            - 'answer': Generated answer
            - 'sources': List of source documents used
            - 'query': Original query
        """
        logger.info(f"Processing query: {query_text[:100]}...")
        
        try:
            # Step 1: Generate query embedding
            query_embedding = self.embedding_service.generate_query_embedding(query_text)
            
            # Step 2: Retrieve relevant context
            relevant_docs = self.database.search_similar(
                query_embedding, 
                top_k=top_k,
                filters=filters
            )
            
            if not relevant_docs:
                logger.warning("No relevant documents found")
                return {
                    'answer': "I couldn't find any relevant information in the NCERT books to answer your question.",
                    'sources': [],
                    'query': query_text
                }
            
            # Step 3: Format context for Gemini
            context = self._format_context(relevant_docs)
            
            # Step 4: Generate answer using Gemini
            answer = self._generate_answer(query_text, context, temperature)
            
            # Step 5: Format sources
            sources = self._format_sources(relevant_docs)
            
            logger.info(f"Generated answer with {len(relevant_docs)} sources")
            
            return {
                'answer': answer,
                'sources': sources,
                'query': query_text
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    def _format_context(self, documents: List[Dict]) -> str:
        """
        Format retrieved documents into context string for Gemini
        
        Args:
            documents: List of document dictionaries
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            source_parts = doc['source'].split('|')
            if len(source_parts) >= 5:
                class_name = source_parts[0]
                subject = source_parts[1]
                bookname = source_parts[2]
                language = source_parts[3]
                page_num = source_parts[4]
                
                context_parts.append(
                    f"[Source {i} - {class_name}, {subject}, {bookname} ({language}), Page {page_num}]:\n"
                    f"{doc['content']}\n"
                )
            else:
                context_parts.append(
                    f"[Source {i} - {doc['source']}]:\n"
                    f"{doc['content']}\n"
                )
        
        return "\n".join(context_parts)
    
    def _format_sources(self, documents: List[Dict]) -> List[Dict[str, str]]:
        """
        Format sources for return
        
        Args:
            documents: List of document dictionaries
        
        Returns:
            List of formatted source dictionaries
        """
        sources = []
        
        for doc in documents:
            source_parts = doc['source'].split('|')
            if len(source_parts) >= 5:
                sources.append({
                    'class': source_parts[0],
                    'subject': source_parts[1],
                    'bookname': source_parts[2],
                    'language': source_parts[3],
                    'page_number': source_parts[4],
                    'content_preview': doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                })
            else:
                sources.append({
                    'source': doc['source'],
                    'content_preview': doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                })
        
        return sources
    
    def _generate_answer(self, query: str, context: str, temperature: float = 0.7) -> str:
        """
        Generate answer using Gemini model
        
        Args:
            query: User's question
            context: Retrieved context from documents
            temperature: Temperature for generation
        
        Returns:
            Generated answer string
        """
        prompt = f"""You are a helpful assistant that answers questions based on NCERT (National Council of Educational Research and Training) textbook content.

Use the following excerpts from NCERT books to answer the question. If the information is not available in the provided context, say so clearly.

Context from NCERT books:
{context}

Question: {query}

Please provide a clear, accurate answer based on the NCERT book excerpts above. Include relevant details and cite the source (class, subject, book, page number) when appropriate."""

        try:
            # Configure generation parameters
            generation_config = types.GenerateContentConfig(
                temperature=temperature,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating answer with Gemini: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the database"""
        total_docs = self.database.get_document_count()
        return {
            'total_documents': total_docs,
            'model': self.model_name
        }
    
    def close(self):
        """Close database connection"""
        self.database.close()
