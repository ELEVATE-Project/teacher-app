"""
Script to clear chat history tables and reset for testing.
Run this to clear all chat sessions and messages.
"""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.chat_session import ChatSession, ChatMessage
from models.user import User
from database import connect_to_mongo, close_mongo_connection


async def clear_chat_history():
    """Clear all chat sessions and messages."""
    print("🔄 Connecting to PostgreSQL...")
    await connect_to_mongo()
    print("✅ Connected to PostgreSQL\n")
    
    # Count existing records
    session_count = await ChatSession.count()
    message_count = await ChatMessage.count()
    
    print(f"📊 Current Records:")
    print(f"   - Chat Sessions: {session_count}")
    print(f"   - Chat Messages: {message_count}\n")
    
    if session_count == 0 and message_count == 0:
        print("ℹ️  No chat history to clear.")
        await close_mongo_connection()
        return
    
    # Ask for confirmation
    confirm = input("⚠️  Are you sure you want to clear ALL chat history? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        await close_mongo_connection()
        return
    
    print("\n🗑️  Clearing chat history...")
    
    # Delete all messages
    await ChatMessage.find_all().delete()
    print(f"   ✓ Deleted {message_count} messages")
    
    # Delete all sessions
    await ChatSession.find_all().delete()
    print(f"   ✓ Deleted {session_count} sessions")
    
    print("\n✅ Chat history cleared successfully!")
    print("\n📝 Note: User accounts are preserved. Only chat history was cleared.")
    
    # Close connection
    await close_mongo_connection()


async def show_chat_stats():
    """Show current chat statistics."""
    print("🔄 Connecting to PostgreSQL...")
    await connect_to_mongo()
    print("✅ Connected to PostgreSQL\n")
    
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
        sessions = await ChatSession.find_all().sort("-updated_at").limit(5).to_list()
        for i, session in enumerate(sessions, 1):
            print(f"   {i}. Session: {session.session_id}")
            print(f"      User ID: {session.user_id}")
            print(f"      Title: {session.title}")
            print(f"      Messages: {session.message_count}")
            print(f"      Updated: {session.updated_at}\n")
    
    # Close connection
    await close_mongo_connection()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        asyncio.run(show_chat_stats())
    else:
        asyncio.run(clear_chat_history())
