"""
Test multi-language support with circle-related queries.
Tests Hindi, Hinglish, and English queries about the same topic.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import ChanakyaOrchestrator
from orchestrator.schemas import OrchestratorInput
from dotenv import load_dotenv

load_dotenv()


async def test_multilang_circle():
    """Test 3 queries about circles in different languages."""
    
    try:
        print("=" * 80)
        print("MULTI-LANGUAGE CIRCLE ACTIVITY TEST")
        print("=" * 80)
        print("\nTesting orchestrator with Hindi, Hinglish, and English queries")
        print("Topic: Circle (गोला/round shape)\n")
        print("=" * 80)
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("\n[ERROR] GEMINI_API_KEY not found in environment variables!")
            print("Please set GEMINI_API_KEY in your .env file")
            return
        
        orchestrator = ChanakyaOrchestrator(api_key=api_key)
        
        # Test queries - all about circles
        test_cases = [
            {
                "language": "Hindi",
                "query": "गोले के बारे में बच्चों को सिखाने के लिए एक गतिविधि बताइए",
                "session_id": "test_hindi_circle"
            },
            {
                "language": "Hinglish",
                "query": "bacchon ko gol shape samjhane ke liye koi activity batao",
                "session_id": "test_hinglish_circle"
            },
            {
                "language": "English",
                "query": "activity for teaching round shapes to kindergarten students",
                "session_id": "test_english_circle"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'=' * 80}")
            print(f"TEST {i}: {test_case['language']} Query")
            print(f"{'=' * 80}")
            print(f"\nQuery: {test_case['query']}")
            print(f"Language: {test_case['language']}")
            print("\nProcessing...")
            print("-" * 80)
            
            input_data = OrchestratorInput(
                query=test_case['query'],
                session_id=test_case['session_id']
            )
            
            result = await orchestrator.process(input_data)
            results.append(result)
            
            print(f"\n[RESULT]")
            print(f"Tool Used: {result.tool_used}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Processing Time: {result.processing_time_ms:.2f}ms")
            print(f"Success: {'Yes' if not result.error else 'No'}")
            
            if result.error:
                print(f"Error: {result.error}")
            elif hasattr(result.result, 'activity_name'):
                activity = result.result
                print(f"\n[ACTIVITY DETAILS]")
                print(f"Name: {activity.activity_name}")
                print(f"Description: {activity.description}")
                print(f"Duration: {activity.duration_minutes} minutes")
                print(f"\nMaterials Needed:")
                for material in activity.materials_needed[:5]:  # Show first 5
                    print(f"  - {material}")
                if len(activity.materials_needed) > 5:
                    print(f"  ... and {len(activity.materials_needed) - 5} more")
                
                print(f"\nSteps:")
                for idx, step in enumerate(activity.steps[:3], 1):  # Show first 3 steps
                    print(f"  {idx}. {step}")
                if len(activity.steps) > 3:
                    print(f"  ... and {len(activity.steps) - 3} more steps")
                
                print(f"\nLearning Outcome: {activity.learning_outcome}")
                
                if activity.tips:
                    print(f"\nTips:")
                    for tip in activity.tips[:2]:  # Show first 2 tips
                        print(f"  - {tip}")
                    if len(activity.tips) > 2:
                        print(f"  ... and {len(activity.tips) - 2} more tips")
            
            # Cleanup
            if orchestrator.storage:
                await orchestrator.storage.delete_session(test_case['session_id'])
            
            # Small delay between requests
            if i < len(test_cases):
                await asyncio.sleep(1)
        
        # Summary
        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")
        
        success_count = sum(1 for r in results if not r.error)
        print(f"\nTotal Queries: {len(test_cases)}")
        print(f"Successful: {success_count}/{len(test_cases)}")
        print(f"Failed: {len(test_cases) - success_count}/{len(test_cases)}")
        
        print(f"\nLanguages Tested:")
        for test_case in test_cases:
            status = "[OK]" if results[test_cases.index(test_case)].error is None else "[FAILED]"
            print(f"  {status} {test_case['language']}")
        
        if success_count == len(test_cases):
            print(f"\n[OK] All multi-language tests passed!")
            print("Multi-language support is working correctly for:")
            print("  - Native script (Hindi/Devanagari)")
            print("  - Romanized transliteration (Hinglish)")
            print("  - English")
        else:
            print(f"\n[WARNING] {len(test_cases) - success_count} test(s) failed")
        
        print(f"\n{'=' * 80}")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_multilang_circle())
