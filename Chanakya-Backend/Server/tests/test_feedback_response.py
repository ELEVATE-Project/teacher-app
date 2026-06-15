"""
Test Feedback Response Tool
============================

Test the new feedback response feature that:
1. Responds to teacher feedback
2. Stores the last 3 messages in a separate database
"""

import asyncio
import os
from dotenv import load_dotenv

# Add Server to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.orchestrator import Orchestrator
from orchestrator.storage import ConversationStorage


async def test_feedback_response():
    """Test feedback response with message storage."""
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return
    
    print("🚀 Testing Feedback Response Tool\n")
    print("=" * 60)
    
    # Initialize orchestrator
    orch = Orchestrator(api_key=api_key)
    session_id = "test_feedback_session_001"
    
    # Simulate a conversation with context
    queries = [
        "Give me an activity for teaching addition with carry",
        "I tried the activity",
        "The activity was not good"  # This should trigger feedback_response
    ]
    
    print("\n📝 Simulating conversation with feedback:\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Message {i} ---")
        print(f"👨‍🏫 Teacher: {query}")
        
        response = await orch.run({
            "query": query,
            "session_id": session_id
        })
        
        print(f"🤖 Chanakya: {response.get('response', 'No response')[:200]}...")
        
        if i == len(queries):
            # Check if feedback was stored
            print("\n" + "=" * 60)
            print("📊 Checking Feedback Storage:\n")
            
            storage = ConversationStorage()
            feedback_history = await storage.get_feedback_history(session_id=session_id)
            
            if feedback_history:
                print(f"✅ Feedback stored successfully!")
                print(f"\nFeedback Details:")
                for fb in feedback_history:
                    print(f"  - Feedback: {fb['feedback_content']}")
                    print(f"  - Sentiment: {fb['sentiment']}")
                    print(f"  - Response: {fb['response'][:100]}...")
                    print(f"  - Context Messages Stored: {len(fb['context_messages'])}")
                    
                    if fb['context_messages']:
                        print(f"\n  Last 3 messages before feedback:")
                        for idx, msg in enumerate(fb['context_messages'], 1):
                            print(f"    {idx}. [{msg['role']}]: {msg['content'][:60]}...")
            else:
                print("❌ No feedback stored")
    
    print("\n" + "=" * 60)
    print("\n✅ Test completed!\n")


async def test_feedback_variations():
    """Test different types of feedback."""
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    print("\n🔄 Testing Different Feedback Types\n")
    print("=" * 60)
    
    orch = Orchestrator(api_key=api_key)
    
    feedback_examples = [
        ("positive", "Students loved the hands-on activity!"),
        ("negative", "The lesson was too confusing for my students"),
        ("mixed", "Some parts worked but the timing was off"),
        ("vague", "It was okay")
    ]
    
    for feedback_type, feedback_text in feedback_examples:
        print(f"\n📋 Testing {feedback_type.upper()} feedback:")
        print(f"👨‍🏫 Teacher: {feedback_text}")
        
        session_id = f"test_feedback_{feedback_type}"
        
        response = await orch.run({
            "query": feedback_text,
            "session_id": session_id
        })
        
        print(f"🤖 Response: {response.get('response', 'No response')[:150]}...")
        
        if response.get('tool_name') == 'feedback_response':
            print("✅ Correctly routed to feedback_response tool")
        else:
            print(f"⚠️  Routed to: {response.get('tool_name')}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎯 FEEDBACK RESPONSE TOOL TEST")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_feedback_response())
    asyncio.run(test_feedback_variations())
    
    print("\n🎉 All tests completed!\n")
