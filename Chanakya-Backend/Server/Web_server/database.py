"""
PostgreSQL database connection and initialization.
"""
import json
from datetime import datetime
from typing import Any, Union, Dict, List
import asyncpg
from config import settings
from models.user import User
from models.chat_session import ChatSession, ChatMessage
from models.classroom import Class, Student, Question, ClassSession, StudentResponse
from models.reflection import ClassReflection
from models.discuss import DiscussPost, DiscussReply
from models.base import init_postgres_models

class RevisionIdWasChanged(Exception):
    """Dummy exception for Beanie migration compatibility."""
    pass


class Database:
    """Database connection manager."""
    pool: asyncpg.Pool = None


db = Database()


def map_type_to_postgres(field_type) -> str:
    """Map python types to PostgreSQL data types."""
    origin = getattr(field_type, "__origin__", None)
    if origin is Union:
        args = field_type.__args__
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            return map_type_to_postgres(non_none_args[0])
            
    if origin in (list, dict, List, Dict):
        return "JSONB"
        
    if field_type is int:
        return "INTEGER"
    elif field_type is float:
        return "DOUBLE PRECISION"
    elif field_type is bool:
        return "BOOLEAN"
    elif field_type is datetime:
        return "TIMESTAMP WITH TIME ZONE"
    elif field_type is str or getattr(field_type, "__name__", "") in ("EmailStr", "str"):
        return "TEXT"
    else:
        return "JSONB"


async def init_connection(conn):
    """Initialize connection options (e.g. JSON encoders)."""
    await conn.set_type_codec(
        'jsonb',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )


async def connect_to_mongo():
    """Create PostgreSQL database connection (replaces MongoDB connect)."""
    db.pool = await asyncpg.create_pool(
        dsn=settings.POSTGRES_URL,
        init=init_connection
    )
    
    # Initialize all Postgres model attributes (for comparison descriptors)
    models = [
        User, ChatSession, ChatMessage,
        Class, Student, Question, ClassSession, StudentResponse,
        ClassReflection, DiscussPost, DiscussReply
    ]
    init_postgres_models(models)
    
    # Create tables automatically
    async with db.pool.acquire() as conn:
        for model in models:
            table_name = model.get_table_name()
            columns_def = ["id VARCHAR(24) PRIMARY KEY"]
            
            for field_name, field_info in model.model_fields.items():
                if field_name == "id":
                    continue
                pg_type = map_type_to_postgres(field_info.annotation)
                columns_def.append(f"{field_name} {pg_type}")
                
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_def)})"
            await conn.execute(query)
            
            # Create indexes if defined in model_cls.Settings
            if hasattr(model, "Settings") and hasattr(model.Settings, "indexes"):
                for idx, index_spec in enumerate(model.Settings.indexes):
                    index_cols = []
                    for col_spec in index_spec:
                        if isinstance(col_spec, tuple):
                            col_name = col_spec[0]
                        else:
                            col_name = col_spec
                        index_cols.append(col_name)
                    if index_cols:
                        idx_name = f"idx_{table_name}_{'_'.join(index_cols)}_{idx}"
                        create_idx_query = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({', '.join(index_cols)})"
                        await conn.execute(create_idx_query)
                        
    print(f"[DB] Connected to PostgreSQL: {settings.POSTGRES_URL}")


async def close_mongo_connection():
    """Close PostgreSQL connection."""
    if db.pool:
        await db.pool.close()
        db.pool = None
        print("[DB] PostgreSQL connection closed")


async def get_database():
    """Get database instance (dummy for compatibility)."""
    return db.pool
