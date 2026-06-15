"""
SQLite storage for conversation context.
Async persistent storage for chat history using aiosqlite.
"""

import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from .config import Config


class ConversationStorage:
    """Async SQLite-based storage for conversation history."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with database path."""
        self.db_path = db_path or Config.db.sqlite_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Database will be initialized on first use
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database is initialized (lazy initialization)."""
        if not self._initialized:
            await self._init_db()
            self._initialized = True
    
    async def _init_db(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
                )
            """)
            
            # Feedback context table - stores last 3 messages when feedback tool is used
            await db.execute("""
                CREATE TABLE IF NOT EXISTS feedback_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    feedback_content TEXT NOT NULL,
                    message_1 TEXT,
                    message_2 TEXT,
                    message_3 TEXT,
                    timestamp TEXT NOT NULL,
                    sentiment TEXT,
                    response TEXT,
                    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
                )
            """)
            
            # Create index for faster lookups
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_session 
                ON feedback_context(session_id)
            """)
            
            await db.commit()
    
    async def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> bool:
        """Create a new conversation session."""
        await self._ensure_initialized()
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT INTO conversations (session_id, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?)
                """, (session_id, now, now, json.dumps(metadata or {})))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                # Session already exists
                return False
    
    async def add_message(self, session_id: str, role: str, content: str, 
                         metadata: Optional[Dict] = None) -> int:
        """Add a message to a conversation."""
        await self._ensure_initialized()
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Ensure session exists
            await db.execute("""
                INSERT OR IGNORE INTO conversations (session_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, '{}')
            """, (session_id, now, now))
            
            # Add message
            cursor = await db.execute("""
                INSERT INTO messages (session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, now, json.dumps(metadata or {})))
            
            # Update conversation timestamp
            await db.execute("""
                UPDATE conversations SET updated_at = ? WHERE session_id = ?
            """, (now, session_id))
            
            await db.commit()
            return cursor.lastrowid
    
    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get messages for a conversation."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if limit:
                cursor = await db.execute("""
                    SELECT role, content, timestamp, metadata
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                """, (session_id, limit))
                rows = await cursor.fetchall()
                rows = list(reversed(rows))  # Reverse to get chronological order
            else:
                cursor = await db.execute("""
                    SELECT role, content, timestamp, metadata
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY id ASC
                """, (session_id,))
                rows = await cursor.fetchall()
            
            return [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                    "metadata": json.loads(row["metadata"])
                }
                for row in rows
            ]
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session info."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT session_id, created_at, updated_at, metadata
                FROM conversations
                WHERE session_id = ?
            """, (session_id,))
            
            row = await cursor.fetchone()
            if row:
                return {
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"])
                }
            return None
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 1 FROM conversations WHERE session_id = ?
            """, (session_id,))
            result = await cursor.fetchone()
            return result is not None
    
    async def get_message_count(self, session_id: str) -> int:
        """Get number of messages in a session."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT COUNT(*) as count FROM messages WHERE session_id = ?
            """, (session_id,))
            row = await cursor.fetchone()
            return row["count"]
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor = await db.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get most recent sessions."""
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT c.session_id, c.created_at, c.updated_at, c.metadata,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.session_id = m.session_id
                GROUP BY c.session_id
                ORDER BY c.updated_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = await cursor.fetchall()
            return [
                {
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"]),
                    "message_count": row["message_count"]
                }
                for row in rows
            ]
    
    async def delete_old_sessions(self, days: int = 30) -> int:
        """Delete sessions older than specified days."""
        await self._ensure_initialized()
        
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get sessions to delete
            cursor = await db.execute("""
                SELECT session_id FROM conversations WHERE updated_at < ?
            """, (cutoff,))
            sessions = await cursor.fetchall()
            
            # Delete messages and conversations
            for session in sessions:
                session_id = session[0]
                await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                await db.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            
            await db.commit()
            return len(sessions)    
    async def store_feedback_context(self, session_id: str, feedback_content: str, 
                                     recent_messages: List[Dict], sentiment: Optional[str] = None,
                                     response: Optional[str] = None) -> int:
        """
        Store feedback along with the last 3 messages for context.
        
        Args:
            session_id: The session ID
            feedback_content: The feedback text from the teacher
            recent_messages: List of recent messages (will take last 3)
            sentiment: Optional sentiment analysis result
            response: Optional response generated for the feedback
        
        Returns:
            The ID of the stored feedback record
        """
        await self._ensure_initialized()
        now = datetime.utcnow().isoformat()
        
        # Extract last 3 messages
        last_messages = recent_messages[-3:] if len(recent_messages) >= 3 else recent_messages
        
        # Pad with None if less than 3 messages
        msg1 = json.dumps(last_messages[0]) if len(last_messages) > 0 else None
        msg2 = json.dumps(last_messages[1]) if len(last_messages) > 1 else None
        msg3 = json.dumps(last_messages[2]) if len(last_messages) > 2 else None
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO feedback_context 
                (session_id, feedback_content, message_1, message_2, message_3, 
                 timestamp, sentiment, response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, feedback_content, msg1, msg2, msg3, now, sentiment, response))
            
            await db.commit()
            return cursor.lastrowid
    
    async def get_feedback_history(self, session_id: Optional[str] = None, 
                                   limit: int = 10) -> List[Dict]:
        """
        Get feedback history, optionally filtered by session.
        
        Args:
            session_id: Optional session ID to filter by
            limit: Maximum number of records to return
        
        Returns:
            List of feedback records with context
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if session_id:
                cursor = await db.execute("""
                    SELECT * FROM feedback_context
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                """, (session_id, limit))
            else:
                cursor = await db.execute("""
                    SELECT * FROM feedback_context
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
            
            rows = await cursor.fetchall()
            
            result = []
            for row in rows:
                record = {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "feedback_content": row["feedback_content"],
                    "timestamp": row["timestamp"],
                    "sentiment": row["sentiment"],
                    "response": row["response"],
                    "context_messages": []
                }
                
                # Parse context messages
                for i in range(1, 4):
                    msg = row[f"message_{i}"]
                    if msg:
                        try:
                            record["context_messages"].append(json.loads(msg))
                        except json.JSONDecodeError:
                            pass
                
                result.append(record)
            
            return result