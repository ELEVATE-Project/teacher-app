"""
Script to clear chat history tables and reset for testing.
Run this to clear all chat sessions and messages.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chat_session import ChatSession, ChatMessage
from models.user import User
from config import settings


async def clear_chat_history():
    """Clear all chat sessions and messages."""
    print("🔄 Connecting to MongoDB...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    
    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[User, ChatSession, ChatMessage]
    )
    
    print("✅ Connected to MongoDB\n")
    
    # Count existing records
    session_count = await ChatSession.count()
    message_count = await ChatMessage.count()
    
    print(f"📊 Current Records:")
    print(f"   - Chat Sessions: {session_count}")
    print(f"   - Chat Messages: {message_count}\n")
    
    if session_count == 0 and message_count == 0:
        print("ℹ️  No chat history to clear.")
        return
    
    # Ask for confirmation
    confirm = input("⚠️  Are you sure you want to clear ALL chat history? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        return
    
    print("\n🗑️  Clearing chat history...")
    
    # Delete all messages
    deleted_messages = await ChatMessage.find_all().delete()
    print(f"   ✓ Deleted {message_count} messages")
    
    # Delete all sessions
    deleted_sessions = await ChatSession.find_all().delete()
    print(f"   ✓ Deleted {session_count} sessions")
    
    print("\n✅ Chat history cleared successfully!")
    print("\n📝 Note: User accounts are preserved. Only chat history was cleared.")
    
    # Close connection
    client.close()


async def show_chat_stats():
    """Show current chat statistics."""
    print("🔄 Connecting to MongoDB...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    
    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[User, ChatSession, ChatMessage]
    )
    
    print("✅ Connected to MongoDB\n")
    
    # Get counts
    user_count = await User.count()
    session_count = await ChatSession.count()
    message_count = await ChatMessage.count()
    
    print("📊 Database Statistics:")
    print(f"   - Users: {user_count}")
    print(f"   - Chat Sessions: {session_count}")
    print(f"   - Chat Messages: {message_count}\n")
    
    # Get recent sessions
    if session_count > 0:
        print("📝 Recent Sessions:")
        sessions = await ChatSession.find_all().sort(-ChatSession.updated_at).limit(5).to_list()
        for i, session in enumerate(sessions, 1):
            print(f"   {i}. Session: {session.session_id}")
            print(f"      User ID: {session.user_id}")
            print(f"      Title: {session.title}")
            print(f"      Messages: {session.message_count}")
            print(f"      Updated: {session.updated_at}\n")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        asyncio.run(show_chat_stats())
    else:
        asyncio.run(clear_chat_history())
