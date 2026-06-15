"""
Test the Chanakya AI service for discussion forum
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import from services
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Web_server.services.chanakya_ai_service import ChanakyaAIService


async def test_chanakya_response():
    """Test Chanakya AI generating a response with context."""
    
    # Initialize service
    service = ChanakyaAIService()
    
    # Sample conversation
    original_post = "How can I make my students more engaged during math lessons?"
    
    replies = [
        {
            "author_name": "Teacher Priya",
            "body": "I've tried using real-world examples, but they still seem distracted."
        },
        {
            "author_name": "Teacher Raj",
            "body": "Have you tried group activities or hands-on manipulatives?"
        }
    ]
    
    query = "What are some specific activities for teaching addition to Class 2 students?"
    
    print("Testing Chanakya AI Service")
    print("=" * 50)
    print(f"\nOriginal Post: {original_post}")
    print(f"\nReplies: {len(replies)}")
    for i, reply in enumerate(replies, 1):
        print(f"  {i}. {reply['author_name']}: {reply['body']}")
    
    print(f"\n@chanakya Query: {query}")
    print("\nGenerating AI response...\n")
    
    try:
        response = await service.generate_response(
            query=query,
            original_post=original_post,
            replies=replies
        )
        
        print("Chanakya AI Response:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        print("\n✅ Test successful!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_chanakya_response())
