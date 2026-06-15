"""
Test script for Chanakya Orchestrator
=====================================

Run: python test_orchestrator.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from orchestrator import ChanakyaOrchestrator, OrchestratorInput


async def test_orchestrator():
    """Test the orchestrator with sample queries."""
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: Please set GEMINI_API_KEYor GEMINI_API_KEY environment variable")
        return
    
    print("🚀 Initializing Chanakya Orchestrator...")
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    print("✅ Orchestrator initialized!\n")
    
    # Test queries
    test_queries = [
        {
            "query": "How do I teach Pythagoras theorem to my students?",
            "context": {"grade": "Class 8", "subject": "Mathematics"}
        },
        {
            "query": "Students are making too much noise and not listening to me",
            "context": {"grade": "Class 6", "class_size": 50}
        },
        {
            "query": "My class is completely out of control, everyone is talking and I can't teach",
            "context": {"grade": "Class 7", "class_size": 45}
        },
    ]
    
    session_id = "test-session-001"
    
    for i, test in enumerate(test_queries, 1):
        print(f"{'='*60}")
        print(f"📝 Test {i}: {test['query']}")
        print(f"📚 Context: {test.get('context', {})}")
        print(f"{'='*60}\n")
        
        # Create input
        input_data = OrchestratorInput(
            query=test["query"],
            context=test.get("context"),
            session_id=session_id
        )
        
        # Process
        result = await orchestrator.process(input_data)
        
        # Display result
        print(f"🔧 Tool Used: {result.tool_used}")
        print(f"💭 Reasoning: {result.reasoning}")
        print(f"⏱️  Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"📊 Confidence: {result.confidence}")
        
        if result.error:
            print(f"❌ Error: {result.error}")
        else:
            activity = result.result
            print(f"\n🎯 Activity: {activity.activity_name}")
            print(f"📋 Description: {activity.description}")
            print(f"⏰ Duration: {activity.duration_minutes} minutes")
            print(f"\n📦 Materials Needed:")
            for material in activity.materials_needed:
                print(f"   • {material}")
            print(f"\n📝 Steps:")
            for step in activity.steps:
                print(f"   {step}")
            print(f"\n🎓 Learning Outcome: {activity.learning_outcome}")
            if activity.tips:
                print(f"\n💡 Tips:")
                for tip in activity.tips:
                    print(f"   • {tip}")
        
        print("\n")
    
    # Show conversation context
    print(f"{'='*60}")
    print("📜 Conversation History:")
    print(f"{'='*60}")
    ctx = orchestrator.get_context(session_id)
    if ctx:
        for msg in ctx.messages:
            print(f"[{msg.role.upper()}] {msg.content}")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
