"""
Topic Selector Service
======================

Service for hierarchical topic selection from the textbook database.
Provides methods to query available classes, subjects, topics, and content.
"""

import sqlite3
import logging
import os
from typing import List, Optional, Dict
import numpy as np

from ..models.schemas import TopicInfo, TextbookContent
from .chapter_mapping import get_chapter_name, get_book_code_from_name

logger = logging.getLogger(__name__)


class TopicSelectorService:
    """Service for hierarchical topic selection from textbook database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the topic selector service.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Try multiple possible locations for the database
            this_file_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Possible database locations
            possible_paths = [
                # Root directory (ncert_books_.db)
                os.path.join(this_file_dir, "..", "..", "..", "ncert_books_.db"),
                # RAG directory
                os.path.join(this_file_dir, "..", "..", "orchestrator", "tools", "RAG", "ncert_books.db"),
                # Alternative RAG location
                os.path.join(this_file_dir, "..", "..", "orchestrator", "tools", "ncert_books.db"),
            ]
            
            # Find the first existing database
            db_path = None
            for path in possible_paths:
                normalized = os.path.normpath(path)
                if os.path.exists(normalized):
                    db_path = normalized
                    break
            
            if db_path is None:
                raise FileNotFoundError(
                    f"Database not found. Searched in: {[os.path.normpath(p) for p in possible_paths]}"
                )
        
        self.db_path = db_path
        self._validate_database()
    
    def _validate_database(self) -> None:
        """Validate that the database exists and is accessible."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at: {self.db_path}")
        
        # Test connection
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM documents")
                count = cursor.fetchone()[0]
                logger.info(f"Connected to database with {count} documents")
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to connect to database: {e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _parse_source(self, source: str) -> Dict[str, str]:
        """
        Parse a source string into its components.
        
        Source format: Class|Subject|Book|Language|Page
        
        Args:
            source: Source string from database
            
        Returns:
            Dictionary with parsed components
        """
        parts = source.split('|')
        return {
            'class_name': parts[0] if len(parts) > 0 else '',
            'subject': parts[1] if len(parts) > 1 else '',
            'book': parts[2] if len(parts) > 2 else '',
            'language': parts[3] if len(parts) > 3 else '',
            'page': parts[4] if len(parts) > 4 else ''
        }
    
    async def get_available_classes(self) -> List[str]:
        """
        Returns list of available classes from database.
        
        Returns:
            List of class names, e.g., ["Class_6", "Class_7", "Class_8"]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT source FROM documents")
            
            classes = set()
            for row in cursor.fetchall():
                parsed = self._parse_source(row['source'])
                if parsed['class_name']:
                    classes.add(parsed['class_name'])
            
            return sorted(list(classes))
    
    async def get_subjects_for_class(self, class_name: str) -> List[str]:
        """
        Returns subjects available for a given class.
        
        Args:
            class_name: The class to filter by (e.g., "Class_6")
            
        Returns:
            List of subject names available for the class
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Use LIKE to filter by class prefix
            cursor.execute(
                "SELECT DISTINCT source FROM documents WHERE source LIKE ?",
                (f"{class_name}|%",)
            )
            
            subjects = set()
            for row in cursor.fetchall():
                parsed = self._parse_source(row['source'])
                if parsed['subject']:
                    subjects.add(parsed['subject'])
            
            return sorted(list(subjects))
    
    async def get_topics_for_subject(
        self, 
        class_name: str, 
        subject: str
    ) -> List[TopicInfo]:
        """
        Returns topics/chapters available for class+subject combination.
        
        Topics are extracted from the book codes in the source field.
        Each unique book code represents a different chapter/topic.
        
        Args:
            class_name: The class to filter by
            subject: The subject to filter by
            
        Returns:
            List of TopicInfo objects with topic details
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Filter by class and subject
            pattern = f"{class_name}|{subject}|%"
            cursor.execute(
                "SELECT source FROM documents WHERE source LIKE ?",
                (pattern,)
            )
            
            # Group by book code (which represents chapters/topics)
            topic_counts: Dict[str, int] = {}
            topic_pages: Dict[str, List[str]] = {}
            
            for row in cursor.fetchall():
                parsed = self._parse_source(row['source'])
                book = parsed['book']
                page = parsed['page']
                
                if book:
                    topic_counts[book] = topic_counts.get(book, 0) + 1
                    if book not in topic_pages:
                        topic_pages[book] = []
                    if page and page not in topic_pages[book]:
                        topic_pages[book].append(page)
            
            # Create TopicInfo objects
            topics = []
            for book, count in sorted(topic_counts.items()):
                pages = sorted(topic_pages.get(book, []), key=lambda x: int(x) if x.isdigit() else 0)
                page_range = None
                if pages:
                    if len(pages) == 1:
                        page_range = pages[0]
                    else:
                        page_range = f"{pages[0]}-{pages[-1]}"
                
                # Convert book code to human-readable chapter name
                topic_name = get_chapter_name(book)
                
                # Extract chapter number from book code if possible
                chapter_number = None
                # Book codes like "fess201" - extract numeric part
                numeric_part = ''.join(filter(str.isdigit, book))
                if numeric_part:
                    # Last digits often represent chapter number
                    chapter_number = int(numeric_part[-2:]) if len(numeric_part) >= 2 else int(numeric_part)
                
                topics.append(TopicInfo(
                    topic_name=topic_name,  # Use human-readable name instead of book code
                    chapter_number=chapter_number,
                    page_range=page_range,
                    content_count=count
                ))
            
            return topics
    
    async def get_content_for_topic(
        self,
        class_name: str,
        subject: str,
        topic: str,
        limit: Optional[int] = None
    ) -> List[TextbookContent]:
        """
        Retrieves all textbook content for the selected topic.
        
        Args:
            class_name: The class to filter by
            subject: The subject to filter by
            topic: The topic name (human-readable) or book code to retrieve content for
            limit: Optional limit on number of results
            
        Returns:
            List of TextbookContent objects with content and source info
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to convert human-readable topic name to book code
            # If topic looks like a book code (e.g., gesc114), use it directly
            # Otherwise, try reverse lookup
            topic_code = topic
            if not (topic.startswith('fesc') or topic.startswith('gesc') or 
                    topic.startswith('hesc') or topic.startswith('fess') or
                    topic.startswith('gess') or topic.startswith('hess')):
                # Looks like a human-readable name, try reverse lookup
                book_code = get_book_code_from_name(topic)
                if book_code:
                    topic_code = book_code
                    logger.info(f"Converted topic name '{topic}' to book code '{topic_code}'")
                else:
                    logger.warning(f"Could not find book code for topic: {topic}, using as-is")
            
            # Build the source pattern
            pattern = f"{class_name}|{subject}|{topic_code}|%"
            
            query = "SELECT content, source FROM documents WHERE source LIKE ?"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (pattern,))
            
            results = []
            for row in cursor.fetchall():
                results.append(TextbookContent(
                    content=row['content'],
                    source=row['source'],
                    similarity_score=None
                ))
            
            if not results:
                logger.warning(
                    f"No content found for class={class_name}, "
                    f"subject={subject}, topic={topic}"
                )
            
            return results
    
    async def search_content(
        self,
        query_embedding: np.ndarray,
        class_name: Optional[str] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        top_k: int = 10
    ) -> List[TextbookContent]:
        """
        Search for content using semantic similarity.
        
        Args:
            query_embedding: Query embedding vector
            class_name: Optional class filter
            subject: Optional subject filter
            topic: Optional topic filter
            top_k: Number of top results to return
            
        Returns:
            List of TextbookContent objects sorted by similarity
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build filter pattern
            if class_name and subject and topic:
                pattern = f"{class_name}|{subject}|{topic}|%"
            elif class_name and subject:
                pattern = f"{class_name}|{subject}|%"
            elif class_name:
                pattern = f"{class_name}|%"
            else:
                pattern = "%"
            
            cursor.execute(
                "SELECT content, embedding, source FROM documents WHERE source LIKE ?",
                (pattern,)
            )
            
            # Calculate similarities
            results_with_scores = []
            query_norm = np.linalg.norm(query_embedding)
            
            for row in cursor.fetchall():
                doc_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                doc_norm = np.linalg.norm(doc_embedding)
                
                if query_norm > 0 and doc_norm > 0:
                    similarity = float(
                        np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
                    )
                    results_with_scores.append((
                        row['content'],
                        row['source'],
                        similarity
                    ))
            
            # Sort by similarity descending
            results_with_scores.sort(key=lambda x: x[2], reverse=True)
            
            # Return top_k results
            return [
                TextbookContent(
                    content=content,
                    source=source,
                    similarity_score=score
                )
                for content, source, score in results_with_scores[:top_k]
            ]
    
    async def check_content_exists(
        self,
        class_name: str,
        subject: str,
        topic: Optional[str] = None
    ) -> bool:
        """
        Check if content exists for the given combination.
        
        Args:
            class_name: The class to check
            subject: The subject to check
            topic: Optional topic to check
            
        Returns:
            True if content exists, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if topic:
                pattern = f"{class_name}|{subject}|{topic}|%"
            else:
                pattern = f"{class_name}|{subject}|%"
            
            cursor.execute(
                "SELECT COUNT(*) FROM documents WHERE source LIKE ?",
                (pattern,)
            )
            count = cursor.fetchone()[0]
            return count > 0
