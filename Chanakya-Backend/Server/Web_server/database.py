"""
MongoDB database connection and initialization.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import settings
from models.user import User
from models.chat_session import ChatSession, ChatMessage
from models.classroom import Class, Student, Question, ClassSession, StudentResponse
from models.reflection import ClassReflection
from models.discuss import DiscussPost, DiscussReply


class Database:
    """Database connection manager."""
    
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def connect_to_mongo():
    """Create database connection."""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.database = db.client[settings.DATABASE_NAME]
    
    # Initialize Beanie with document models
    await init_beanie(
        database=db.database,
        document_models=[
            User, ChatSession, ChatMessage,
            Class, Student, Question, ClassSession, StudentResponse,
            ClassReflection,
            DiscussPost, DiscussReply,
        ]
    )
    print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        print("✅ MongoDB connection closed")


async def get_database():
    """Get database instance."""
    return db.database
