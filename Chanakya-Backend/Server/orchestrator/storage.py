"""
PostgreSQL storage for conversation context.
Async persistent storage for chat history using asyncpg.
"""

import asyncpg
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from .config import Config


class ConversationStorage:
    """Async PostgreSQL-based storage for conversation history."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with database DSN."""
        # Use DB_URL from environment or fallback to default local postgres
        self.dsn = os.getenv("DB_URL") or "postgresql://teacher_user:securepass123@localhost:5432/Shikshalokam"
        self._pool = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database is initialized (lazy initialization)."""
        if not self._initialized:
            if not self._pool:
                self._pool = await asyncpg.create_pool(dsn=self.dsn)
            await self._init_db()
            self._initialized = True
            
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
    
    async def _init_db(self):
        """Create tables if they don't exist."""
        async with self._pool.acquire() as conn:
            # Conversations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES conversations(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Feedback context table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_context (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES conversations(session_id) ON DELETE CASCADE,
                    feedback_content TEXT NOT NULL,
                    message_1 TEXT,
                    message_2 TEXT,
                    message_3 TEXT,
                    timestamp TEXT NOT NULL,
                    sentiment TEXT,
                    response TEXT
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_session 
                ON feedback_context(session_id)
            """)
    
    async def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> bool:
        """Create a new conversation session."""
        await self._ensure_initialized()
        now = datetime.utcnow().isoformat()
        
        async with self._pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO conversations (session_id, created_at, updated_at, metadata)
                    VALUES ($1, $2, $3, $4)
                """, session_id, now, now, json.dumps(metadata or {}))
                return True
            except asyncpg.UniqueViolationError:
                return False
    
    async def add_message(self, session_id: str, role: str, content: str, 
                          metadata: Optional[Dict] = None) -> int:
        """Add a message to a conversation."""
        await self._ensure_initialized()
        now = datetime.utcnow().isoformat()
        
        async with self._pool.acquire() as conn:
            # Ensure session exists
            await conn.execute("""
                INSERT INTO conversations (session_id, created_at, updated_at, metadata)
                VALUES ($1, $2, $3, '{}')
                ON CONFLICT (session_id) DO NOTHING
            """, session_id, now, now)
            
            # Add message
            message_id = await conn.fetchval("""
                INSERT INTO messages (session_id, role, content, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, session_id, role, content, now, json.dumps(metadata or {}))
            
            # Update conversation timestamp
            await conn.execute("""
                UPDATE conversations SET updated_at = $1 WHERE session_id = $2
            """, now, session_id)
            
            return message_id
    
    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get messages for a conversation."""
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            if limit:
                rows = await conn.fetch("""
                    SELECT role, content, timestamp, metadata
                    FROM messages
                    WHERE session_id = $1
                    ORDER BY id DESC
                    LIMIT $2
                """, session_id, limit)
                rows = list(reversed(rows))  # Reverse to get chronological order
            else:
                rows = await conn.fetch("""
                    SELECT role, content, timestamp, metadata
                    FROM messages
                    WHERE session_id = $1
                    ORDER BY id ASC
                """, session_id)
            
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
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT session_id, created_at, updated_at, metadata
                FROM conversations
                WHERE session_id = $1
            """, session_id)
            
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
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 1 FROM conversations WHERE session_id = $1
            """, session_id)
            return row is not None
    
    async def get_message_count(self, session_id: str) -> int:
        """Get number of messages in a session."""
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM messages WHERE session_id = $1
            """, session_id)
            return count or 0
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM messages WHERE session_id = $1", session_id)
            result = await conn.execute("DELETE FROM conversations WHERE session_id = $1", session_id)
            return result != "DELETE 0"
    
    async def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get most recent sessions."""
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT c.session_id, c.created_at, c.updated_at, c.metadata,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.session_id = m.session_id
                GROUP BY c.session_id, c.created_at, c.updated_at, c.metadata
                ORDER BY c.updated_at DESC
                LIMIT $1
            """, limit)
            
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
        
        async with self._pool.acquire() as conn:
            # Get sessions to delete
            rows = await conn.fetch("""
                SELECT session_id FROM conversations WHERE updated_at < $1
            """, cutoff)
            
            for row in rows:
                session_id = row["session_id"]
                await conn.execute("DELETE FROM messages WHERE session_id = $1", session_id)
                await conn.execute("DELETE FROM conversations WHERE session_id = $1", session_id)
                
            return len(rows)
            
    async def store_feedback_context(self, session_id: str, feedback_content: str, 
                                     recent_messages: List[Dict], sentiment: Optional[str] = None,
                                     response: Optional[str] = None) -> int:
        """
        Store feedback along with the last 3 messages for context.
        """
        await self._ensure_initialized()
        now = datetime.utcnow().isoformat()
        
        # Extract last 3 messages
        last_messages = recent_messages[-3:] if len(recent_messages) >= 3 else recent_messages
        
        # Pad with None if less than 3 messages
        msg1 = json.dumps(last_messages[0]) if len(last_messages) > 0 else None
        msg2 = json.dumps(last_messages[1]) if len(last_messages) > 1 else None
        msg3 = json.dumps(last_messages[2]) if len(last_messages) > 2 else None
        
        async with self._pool.acquire() as conn:
            feedback_id = await conn.fetchval("""
                INSERT INTO feedback_context 
                (session_id, feedback_content, message_1, message_2, message_3, 
                 timestamp, sentiment, response)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, session_id, feedback_content, msg1, msg2, msg3, now, sentiment, response)
            
            return feedback_id
    
    async def get_feedback_history(self, session_id: Optional[str] = None, 
                                   limit: int = 10) -> List[Dict]:
        """
        Get feedback history, optionally filtered by session.
        """
        await self._ensure_initialized()
        
        async with self._pool.acquire() as conn:
            if session_id:
                rows = await conn.fetch("""
                    SELECT * FROM feedback_context
                    WHERE session_id = $1
                    ORDER BY id DESC
                    LIMIT $2
                """, session_id, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM feedback_context
                    ORDER BY id DESC
                    LIMIT $1
                """, limit)
            
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