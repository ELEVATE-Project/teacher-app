"""
PostgreSQL database operations for storing documents and embeddings.
Also stores PDF compiler page/section results for chat document Q&A.
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
    
    def __init__(self, db_path: str = "embedding/ncert_books.db"):
        """
        Initialize database connection
        
        Args:
            db_path: SQLite DB path parameter (kept for backward compatibility, used to find SQLite file for migration).
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

        # PDF compiler: page-level results (one row per page per document)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_page_results (
                id SERIAL PRIMARY KEY,
                document_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                confidence_flags TEXT,
                pipeline_type TEXT NOT NULL,
                image_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pdf_page_document_id ON pdf_page_results(document_id)
        """)

        # PDF compiler: section-level results (consolidated 5-10 pages)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_section_results (
                id SERIAL PRIMARY KEY,
                document_id TEXT NOT NULL,
                section_index INTEGER NOT NULL,
                page_start INTEGER NOT NULL,
                page_end INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pdf_section_document_id ON pdf_section_results(document_id)
        """)
        
        self.conn.commit()
        cursor.close()
        logger.info("Database schema created/verified")
        
        # Check if we should migrate data from SQLite to PostgreSQL
        self._check_and_run_migration()
        
    def _check_and_run_migration(self):
        """Check if documents table is empty, and automatically migrate from SQLite if available."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        cursor.close()
        
        if count == 0:
            logger.info("PostgreSQL documents table is empty. Scanning for existing SQLite database to migrate...")
            self._migrate_from_sqlite()
        else:
            logger.info(f"PostgreSQL documents table already has {count} records. Migration skipped.")

    def _migrate_from_sqlite(self):
        """Migrate existing documents from SQLite to PostgreSQL if PostgreSQL is empty."""
        import sqlite3
        
        # Check possible SQLite locations
        sqlite_paths = [
            self.db_path,
            "embedding/ncert_books.db",
            "embedding/ncert_books_.db",
            "Chanakya-Backend/embedding/ncert_books.db",
            "Chanakya-Backend/embedding/ncert_books_.db",
            "../embedding/ncert_books.db",
            "../../embedding/ncert_books.db",
            "../embedding/ncert_books_.db",
            "../../embedding/ncert_books_.db"
        ]
        
        found_sqlite_path = None
        for p in sqlite_paths:
            if p and os.path.exists(p) and os.path.isfile(p):
                # Check if it has data
                try:
                    conn = sqlite3.connect(p)
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM documents")
                    sqlite_count = c.fetchone()[0]
                    conn.close()
                    if sqlite_count > 0:
                        found_sqlite_path = p
                        break
                except Exception:
                    pass
                    
        if not found_sqlite_path:
            logger.info("No source SQLite database with document content found for migration.")
            return
            
        logger.info(f"Found SQLite database for migration at: {found_sqlite_path}. Migrating documents...")
        try:
            sqlite_conn = sqlite3.connect(found_sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute("SELECT content, embedding, source FROM documents")
            rows = sqlite_cursor.fetchall()
            
            if rows:
                pg_cursor = self.conn.cursor()
                execute_values(pg_cursor, """
                    INSERT INTO documents (content, embedding, source)
                    VALUES %s
                """, rows)
                self.conn.commit()
                pg_cursor.close()
                logger.info(f"Successfully migrated {len(rows)} documents from SQLite to PostgreSQL.")
            sqlite_conn.close()
        except Exception as e:
            logger.error(f"Failed to migrate documents from SQLite to PostgreSQL: {e}", exc_info=True)

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
        
        # Return top_k results
        results = [doc for _, doc in similarities[:top_k]]
        
        logger.debug(f"Found {len(results)} similar documents (top_k={top_k})")
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

    # ---------- PDF compiler page/section storage ----------

    def insert_pdf_page_result(
        self,
        document_id: str,
        page_number: int,
        result_json: Dict[str, Any],
        pipeline_type: str = "text",
        confidence_flags: Optional[Dict[str, Any]] = None,
        image_ref: Optional[str] = None,
    ) -> int:
        """Insert a single page result from the PDF compiler."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO pdf_page_results (document_id, page_number, result_json, confidence_flags, pipeline_type, image_ref)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    document_id,
                    page_number,
                    json.dumps(result_json),
                    json.dumps(confidence_flags) if confidence_flags else None,
                    pipeline_type,
                    image_ref,
                ),
            )
            row = cursor.fetchone()
            self.conn.commit()
            last_id = row[0] if row else None
            return last_id
        except Exception as e:
            logger.error(f"Error inserting PDF page result: {e}")
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def get_pdf_page_results(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all page results for a document, ordered by page_number."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT page_number, result_json, pipeline_type, confidence_flags
            FROM pdf_page_results
            WHERE document_id = %s
            ORDER BY page_number
            """,
            (document_id,),
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "page_number": row[0],
                "result": json.loads(row[1]),
                "pipeline_type": row[2],
                "confidence_flags": json.loads(row[3]) if row[3] else None,
            })
        cursor.close()
        return results

    def insert_pdf_section_result(
        self,
        document_id: str,
        section_index: int,
        page_start: int,
        page_end: int,
        result_json: Dict[str, Any],
    ) -> int:
        """Insert a section consolidation result."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO pdf_section_results (document_id, section_index, page_start, page_end, result_json)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (document_id, section_index, page_start, page_end, json.dumps(result_json)),
            )
            row = cursor.fetchone()
            self.conn.commit()
            last_id = row[0] if row else None
            return last_id
        except Exception as e:
            logger.error(f"Error inserting PDF section result: {e}")
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def get_pdf_section_results(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all section results for a document, ordered by section_index."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT section_index, page_start, page_end, result_json
            FROM pdf_section_results
            WHERE document_id = %s
            ORDER BY section_index
            """,
            (document_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {
                "section_index": row[0],
                "page_start": row[1],
                "page_end": row[2],
                "result": json.loads(row[3]),
            }
            for row in rows
        ]

    def get_pdf_document_text_for_rag(self, document_id: str, max_chars: Optional[int] = None) -> str:
        """
        Get concatenated text from page and section results for a document, for RAG/query.
        Prefers section content when available; falls back to page content.
        """
        sections = self.get_pdf_section_results(document_id)
        if sections:
            parts = []
            for s in sections:
                r = s["result"]
                title = r.get("section_title") or ""
                content = r.get("content") or ""
                tables = r.get("tables") or []
                if title:
                    parts.append(f"## {title}\n{content}")
                else:
                    parts.append(content)
                for t in tables:
                    parts.append(str(t))
            text = "\n\n".join(parts)
        else:
            pages = self.get_pdf_page_results(document_id)
            parts = []
            for p in pages:
                r = p["result"]
                for key in ("headings", "content", "paragraphs", "tables"):
                    val = r.get(key)
                    if isinstance(val, list):
                        parts.extend(str(x) for x in val)
                    elif isinstance(val, str):
                        parts.append(val)
            text = "\n\n".join(parts)
        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + "..."
        return text

    def delete_pdf_document_results(self, document_id: str) -> None:
        """Delete all page and section results for a document (e.g. on recompile)."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM pdf_page_results WHERE document_id = %s", (document_id,))
            cursor.execute("DELETE FROM pdf_section_results WHERE document_id = %s", (document_id,))
            self.conn.commit()
            logger.info("Deleted PDF results for document_id=%s", document_id)
        except Exception as e:
            logger.error(f"Error deleting PDF document results: {e}")
            self.conn.rollback()
            raise
        finally:
            cursor.close()
    
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
