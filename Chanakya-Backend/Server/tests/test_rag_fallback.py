"""
Test RAG Fallback to Expert Teacher
====================================

Tests that when RAG (content_explainer) can't find content,
it automatically falls back to expert_teacher.
"""

import asyncio
import os
from dotenv import load_dotenv
from orchestrator import ChanakyaOrchestrator
from orchestrator.schemas import OrchestratorInput

load_dotenv()


async def test_rag_fallback():
    """Test RAG fallback mechanism."""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    
    test_cases = [
        {
            "query": "What is photosynthesis?",
            "expected_behavior": "RAG should find this in NCERT",
            "should_fallback": False
        },
        {
            "query": "What is quantum entanglement?",
            "expected_behavior": "RAG should NOT find this, fallback to expert",
            "should_fallback": True
        },
        {
            "query": "Explain blockchain technology",
            "expected_behavior": "RAG should NOT find this, fallback to expert",
            "should_fallback": True
        },
        {
            "query": "What is the water cycle?",
            "expected_behavior": "RAG should find this in NCERT",
            "should_fallback": False
        }
    ]
    
    print("=" * 80)
    print("RAG FALLBACK MECHANISM TEST")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'=' * 80}")
        print(f"TEST {i}: {test['query']}")
        print(f"Expected: {test['expected_behavior']}")
        print("=" * 80)
        
        try:
            result = await orchestrator.process(
                OrchestratorInput(
                    query=test['query'],
                    context={"grade": "10", "subject": "science"},
                    session_id=f"test_{i}"
                )
            )
            
            print(f"\n🎯 Selected Tool: {result.tool_used}")
            print(f"📊 Confidence: {result.confidence:.2f}")
            print(f"💭 Reasoning: {result.reasoning}")
            
            # Check if fallback worked as expected
            if test['should_fallback']:
                if 'expert' in result.tool_used.lower() or 'fallback' in result.reasoning.lower():
                    print(f"✅ CORRECT: Fallback to expert teacher worked!")
                else:
                    print(f"⚠️ UNEXPECTED: Expected fallback but tool was {result.tool_used}")
            else:
                if 'content_explainer' in result.tool_used:
                    print(f"✅ CORRECT: RAG found content in NCERT")
                else:
                    print(f"⚠️ UNEXPECTED: Expected RAG but got {result.tool_used}")
            
            # Show response preview
            if isinstance(result.result, dict):
                explanation = result.result.get('explanation', '')
                if explanation:
                    response_preview = explanation[:300] + "..." if len(explanation) > 300 else explanation
                    print(f"\n📝 Response Preview:")
                    print(f"{response_preview}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(2)
    
    print(f"\n\n{'=' * 80}")
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rag_fallback())
