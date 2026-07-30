"""
Test Orchestrator with Expert Teacher
======================================

Tests how the orchestrator routes between content_explainer (RAG) 
and expert_teacher based on query type.
"""

import asyncio
import os
from dotenv import load_dotenv, find_dotenv
from orchestrator import ChanakyaOrchestrator
from orchestrator.schemas import OrchestratorInput

# Load environment variables
load_dotenv(find_dotenv())


async def test_orchestrator_routing():
    """Test orchestrator routing to appropriate tools."""
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Neither OPENROUTER_API_KEY nor GEMINI_API_KEY set")
        return
    
    # Initialize orchestrator
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    
    # Test cases
    test_cases = [
        {
            "query": "What is photosynthesis?",
            "expected_tool": "content_explainer",
            "reason": "NCERT curriculum topic - should use RAG"
        },
        {
            "query": "What is quantum mechanics?",
            "expected_tool": "expert_teacher",
            "reason": "Advanced topic not in NCERT - should use expert"
        },
        {
            "query": "Explain the Pythagoras theorem",
            "expected_tool": "content_explainer",
            "reason": "Standard NCERT mathematics - should use RAG"
        },
        {
            "query": "How does artificial intelligence work?",
            "expected_tool": "expert_teacher",
            "reason": "Modern topic beyond NCERT - should use expert"
        },
        {
            "query": "What are fractals?",
            "expected_tool": "expert_teacher",
            "reason": "Advanced math concept - should use expert"
        },
        {
            "query": "Explain the water cycle",
            "expected_tool": "content_explainer",
            "reason": "Basic NCERT science - should use RAG"
        }
    ]
    
    print("=" * 80)
    print("ORCHESTRATOR ROUTING TEST")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'=' * 80}")
        print(f"TEST {i}: {test['query']}")
        print(f"Expected Tool: {test['expected_tool']}")
        print(f"Reason: {test['reason']}")
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
            
            # Check if routing was correct
            if result.tool_used == test['expected_tool']:
                print(f"✅ CORRECT ROUTING")
            else:
                print(f"⚠️ UNEXPECTED ROUTING (expected {test['expected_tool']})")
            
            # Show a snippet of the response
            explanation = ""
            if isinstance(result.result, dict):
                explanation = result.result.get('explanation') or result.result.get('response') or ''
            elif hasattr(result.result, 'explanation'):
                explanation = result.result.explanation
            elif hasattr(result.result, 'model_dump'):
                explanation = str(result.result.model_dump())
            else:
                explanation = str(result.result)
                
            if explanation:
                response_preview = explanation[:200] + "..." if len(explanation) > 200 else explanation
                print(f"\n📝 Response Preview:")
                print(f"{response_preview}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print(f"\n\n{'=' * 80}")
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_orchestrator_routing())
