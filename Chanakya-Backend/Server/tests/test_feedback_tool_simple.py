"""
Quick Test: Feedback Response
==============================

Simple test to verify the feedback tool works correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.tools.feedback_response import FeedbackResponseTool


def test_feedback_tool():
    """Test the feedback tool directly."""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  Warning: GEMINI_API_KEY not set")
        print("Set it with: export GEMINI_API_KEY='your-key-here'")
        return
    
    print("\n" + "="*60)
    print("🧪 Testing Feedback Response Tool")
    print("="*60 + "\n")
    
    tool = FeedbackResponseTool(api_key=api_key)
    
    # Test feedback
    feedback = "the activity was not good"
    
    print(f"Teacher Feedback: '{feedback}'\n")
    print("Running feedback tool...")
    
    try:
        import asyncio
        
        # Create context with recent messages
        context = {
            "recent_messages": [
                {
                    "role": "user",
                    "content": "Give me an activity for teaching addition",
                    "timestamp": "2026-02-05T10:00:00"
                },
                {
                    "role": "assistant",
                    "content": "Here's a great activity using blocks...",
                    "timestamp": "2026-02-05T10:00:05"
                },
                {
                    "role": "user",
                    "content": "I tried it",
                    "timestamp": "2026-02-05T10:30:00"
                }
            ]
        }
        
        result = asyncio.run(tool.run(feedback, context))
        
        print("\n" + "="*60)
        print("✅ Response Generated:")
        print("="*60)
        print(f"\n📝 Response: {result['response']}")
        print(f"\n😊 Sentiment: {result['sentiment']}")
        
        if result.get('follow_up_questions'):
            print(f"\n❓ Follow-up Questions:")
            for q in result['follow_up_questions']:
                print(f"   - {q}")
        
        if result.get('quick_suggestions'):
            print(f"\n💡 Quick Suggestions:")
            for s in result['quick_suggestions']:
                print(f"   - {s}")
        
        print("\n" + "="*60)
        print("✅ Test completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_feedback_tool()
