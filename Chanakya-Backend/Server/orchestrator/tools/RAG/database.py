"""
PostgreSQL database operations for storing documents and embeddings.
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class Database:
    """Handle PostgreSQL database operations for document storage and retrieval"""
    
    def __init__(self, db_path: str = "orchestrator/tools/RAG/ncert_books.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path parameter (ignored, database URL used instead)
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_schema()
    
    def _connect(self):
        """Establish database connection"""
        self.dsn = os.getenv("DB_URL") or "postgresql://teacher_user:securepass123@localhost:5432/Shikshalokam"
        try:
            self.conn = psycopg2.connect(self.dsn)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def _create_schema(self):
        """Create database schema if it doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BYTEA NOT NULL,
                source TEXT NOT NULL
            )
        """)
        
        # Create index on source for faster filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source ON documents(source)
        """)
        
        self.conn.commit()
        cursor.close()
        logger.info("Database schema created/verified")
    
    def insert_document(self, content: str, embedding: np.ndarray, source: str) -> int:
        """
        Insert a document with its embedding into the database
        
        Args:
            content: Text content of the document
            embedding: NumPy array of the embedding vector
            source: Source string in format "class|subject|bookname|language|page_number"
        
        Returns:
            ID of the inserted document
        """
        try:
            # Convert numpy array to bytes
            embedding_bytes = embedding.tobytes()
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO documents (content, embedding, source)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (content, embedding_bytes, source))
            
            row = cursor.fetchone()
            self.conn.commit()
            doc_id = row[0] if row else None
            cursor.close()
            logger.debug(f"Inserted document with ID {doc_id}, source: {source}")
            return doc_id
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            self.conn.rollback()
            raise
    
    def insert_documents_batch(self, documents: List[Tuple[str, np.ndarray, str]]):
        """
        Insert multiple documents in a batch
        
        Args:
            documents: List of tuples (content, embedding, source)
        """
        try:
            cursor = self.conn.cursor()
            data = [
                (content, embedding.tobytes(), source)
                for content, embedding, source in documents
            ]
            
            execute_values(cursor, """
                INSERT INTO documents (content, embedding, source)
                VALUES %s
            """, data)
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Inserted {len(documents)} documents in batch")
        except Exception as e:
            logger.error(f"Error inserting documents batch: {e}")
            self.conn.rollback()
            raise
    
    def get_all_documents(self) -> List[Dict]:
        """
        Retrieve all documents from the database
        
        Returns:
            List of dictionaries with document data
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, content, embedding, source FROM documents")
        
        results = []
        for row in cursor.fetchall():
            embedding = np.frombuffer(row['embedding'], dtype=np.float32)
            results.append({
                'id': row['id'],
                'content': row['content'],
                'embedding': embedding,
                'source': row['source']
            })
        cursor.close()
        return results
    
    def search_similar(self, query_embedding: np.ndarray, top_k: int = 5, 
                      filters: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        Find similar documents using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            filters: Optional dict with keys: class, subject, language
        
        Returns:
            List of dictionaries with similar documents, sorted by similarity
        """
        # Get all documents (or filtered subset)
        all_docs = self.get_all_documents()
        
        # Apply filters if provided
        if filters:
            filtered_docs = []
            for doc in all_docs:
                source_parts = doc['source'].split('|')
                if len(source_parts) >= 4:
                    doc_class = source_parts[0]
                    doc_subject = source_parts[1]
                    doc_language = source_parts[3]
                    
                    match = True
                    if 'class' in filters and doc_class != filters['class']:
                        match = False
                    if 'subject' in filters and doc_subject != filters['subject']:
                        match = False
                    if 'language' in filters and doc_language != filters['language']:
                        match = False
                    
                    if match:
                        filtered_docs.append(doc)
            
            all_docs = filtered_docs
        
        # Calculate cosine similarities
        similarities = []
        query_norm = np.linalg.norm(query_embedding)
        
        for doc in all_docs:
            doc_embedding = doc['embedding']
            doc_norm = np.linalg.norm(doc_embedding)
            
            if query_norm > 0 and doc_norm > 0:
                cosine_sim = np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
                similarities.append((cosine_sim, doc))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k results with similarity scores
        results = []
        for similarity, doc in similarities[:top_k]:
            result_doc = doc.copy()
            result_doc['similarity'] = float(similarity)  # Add similarity score
            results.append(result_doc)
        
        logger.debug(f"Found {len(results)} similar documents (top_k={top_k})")
        if results:
            logger.debug(f"Top similarity: {results[0]['similarity']:.4f}")
        
        return results
    
    def get_document_count(self) -> int:
        """Get total number of documents in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0
    
    def get_documents_by_source(self, source_pattern: str) -> List[Dict]:
        """
        Get documents matching a source pattern (supports LIKE wildcards)
        
        Args:
            source_pattern: Pattern to match (e.g., "Class_10|Mathematics|%")
        
        Returns:
            List of matching documents
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, content, embedding, source 
            FROM documents 
            WHERE source LIKE %s
        """, (source_pattern,))
        
        results = []
        for row in cursor.fetchall():
            embedding = np.frombuffer(row['embedding'], dtype=np.float32)
            results.append({
                'id': row['id'],
                'content': row['content'],
                'embedding': embedding,
                'source': row['source']
            })
        cursor.close()
        return results
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
