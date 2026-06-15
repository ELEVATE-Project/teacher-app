"""
Test Teacher Motivation Tool
=============================

Tests the teacher motivation tool with various burnout/stress scenarios.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import ChanakyaOrchestrator
from orchestrator.schemas import OrchestratorInput


async def test_teacher_motivation():
    """Test teacher motivation with different scenarios."""
    
    # Load API key
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in environment")
        return
    
    print("\n" + "="*80)
    print("TEACHER MOTIVATION TOOL - TEST SUITE")
    print("="*80)
    
    # Create orchestrator
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    
    # Test scenarios
    test_cases = [
        {
            "name": "General Burnout",
            "query": "I'm feeling completely exhausted and burnt out from teaching. I don't have energy anymore.",
            "description": "Teacher expressing general burnout and exhaustion"
        },
        {
            "name": "Feeling Unappreciated",
            "query": "Nobody appreciates my work. I work so hard but get no recognition or thanks.",
            "description": "Teacher feeling undervalued and unrecognized"
        },
        {
            "name": "Difficult Students",
            "query": "My students are so disrespectful and difficult. I feel like giving up.",
            "description": "Teacher struggling with student behavior"
        },
        {
            "name": "Work-Life Balance",
            "query": "Teaching has taken over my entire life. I have no time for family or myself.",
            "description": "Teacher struggling with work-life balance"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_cases)}: {test['name']}")
        print(f"{'='*80}")
        print(f"Description: {test['description']}")
        print(f"Query: \"{test['query']}\"")
        print("-" * 80)
        
        try:
            # Process the query
            input_data = OrchestratorInput(
                query=test['query'],
                session_id=f"test_motivation_{i}"
            )
            result = await orchestrator.process(input_data)
            
            # Display results
            print(f"\n[SELECTED TOOL]: {result.tool_used}")
            print(f"[CONFIDENCE]: {result.confidence:.2f}")
            print(f"[REASONING]: {result.reasoning}")
            
            if result.result and isinstance(result.result, dict):
                output = result.result
                
                print(f"\n[TITLE]: {output.get('motivation_title', 'N/A')}")
                
                print(f"\n[ACKNOWLEDGMENT]:")
                print(f"  {output.get('acknowledgment', 'N/A')}")
                
                print(f"\n[IMMEDIATE TIPS]:")
                for tip in output.get('immediate_tips', []):
                    print(f"  - {tip}")
                
                print(f"\n[LONG-TERM STRATEGIES]:")
                for strategy in output.get('long_term_strategies', []):
                    print(f"  - {strategy}")
                
                print(f"\n[INSPIRATION]:")
                print(f"  {output.get('inspiration', 'N/A')}")
                
                print(f"\n[SELF-CARE PRACTICES]:")
                for practice in output.get('self_care_practices', []):
                    print(f"  - {practice}")
                
                print(f"\n[PERSPECTIVE SHIFTS]:")
                for shift in output.get('perspective_shifts', []):
                    print(f"  - {shift}")
                
                print(f"\n[SUCCESS] Test passed!")
            else:
                print(f"\n[ERROR] No output generated")
                
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_teacher_motivation())
