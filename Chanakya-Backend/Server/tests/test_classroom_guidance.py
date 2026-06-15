"""
Test ClassroomGuidanceTool
===========================

Test the new classroom guidance tool with pedagogical challenges.
"""

import asyncio
import os
from dotenv import load_dotenv
from orchestrator.tools.classroom_guidance import ClassroomGuidanceTool

# Load environment variables
load_dotenv()


async def test_classroom_guidance():
    """Test the classroom guidance tool with various teaching challenges."""
    
    # Ensure API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY environment variable not set!")
        return
    
    print("=" * 70)
    print("Testing ClassroomGuidanceTool")
    print("=" * 70)
    
    try:
        # Initialize the tool
        print("\n1️⃣  Initializing ClassroomGuidanceTool...")
        tool = ClassroomGuidanceTool(api_key=api_key)
        print("✅ Tool initialized successfully!")
        
        # Test queries
        test_queries = [
            {
                "query": "Students are unable to interpret maps, data tables and graphs systematically",
                "context": {"class": "8", "subject": "Science"}
            },
            {
                "query": "केवल 2-3 छात्र ही सवालों के जवाब देते हैं",
                "context": None
            },
            {
                "query": "విద్యార్థులు ఫార్ములాలను కంఠస్థం చేస్తారు కానీ వాటిని ఎప్పుడు ఉపయోగించాలో అర్థం చేసుకోలేరు",
                "context": {"subject": "Mathematics"}
            },
            {
                "query": "மாணவர்கள் வரைபடங்கள் மற்றும் தரவு அட்டவணைகளை புரிந்துகொள்ள முடியவில்லை",
                "context": {"class": "9"}
            },
            {
                "query": "My students copy answers during tests. কীভাবে এটি থামাবো?",
                "context": None
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n{'=' * 70}")
            print(f"Test {i}: {test['query']}")
            if test['context']:
                print(f"Context: {test['context']}")
            print(f"{'=' * 70}")
            
            # Run the tool
            result = await tool.run(test['query'], test['context'])
            
            # Display results
            print(f"\n📊 Situation Analysis:")
            print(f"   {result.get('situation_analysis', 'N/A')}")
            
            if result.get('immediate_tips'):
                print(f"\n⚡ Immediate Tips:")
                for tip in result['immediate_tips']:
                    print(f"   • {tip}")
            
            if result.get('step_by_step_strategies'):
                print(f"\n🎯 Strategies:")
                for strategy in result['step_by_step_strategies'][:2]:  # Show first 2
                    print(f"\n   Strategy: {strategy.get('strategy_name', 'N/A')}")
                    if strategy.get('steps'):
                        print(f"   Steps:")
                        for step in strategy['steps'][:3]:  # Show first 3 steps
                            print(f"      - {step}")
                    if strategy.get('why_it_works'):
                        print(f"   Why: {strategy['why_it_works'][:150]}...")
            
            if result.get('long_term_approach'):
                print(f"\n📈 Long-term Approach:")
                print(f"   {result['long_term_approach'][:200]}...")
            
            if result.get('rural_adaptations'):
                print(f"\n🌾 Rural Adaptations:")
                print(f"   {result['rural_adaptations'][:200]}...")
            
            if result.get('encouragement'):
                print(f"\n💪 Encouragement:")
                print(f"   {result['encouragement']}")
            
            if result.get('error'):
                print(f"\n⚠️  Error: {result['error']}")
        
        print(f"\n{'=' * 70}")
        print("✅ All tests completed successfully!")
        print(f"{'=' * 70}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   {e}")
        import traceback
        traceback.print_exc()


async def test_orchestrator_integration():
    """Test the full orchestrator with classroom guidance queries."""
    
    print("\n" + "=" * 70)
    print("Testing Full Orchestrator Integration")
    print("=" * 70)
    
    try:
        from orchestrator.orchestrator import ChanakyaOrchestrator
        from orchestrator.schemas import OrchestratorInput
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ ERROR: GEMINI_API_KEY not set!")
            return
        
        print("\n1️⃣  Initializing ChanakyaOrchestrator...")
        orchestrator = ChanakyaOrchestrator(api_key=api_key)
        print(f"✅ Orchestrator initialized!")
        print(f"   Available tools: {list(orchestrator.tools.keys())}")
        
        # Test routing to classroom_guidance
        test_query = "Only 2-3 students answer questions in my class. How can I increase participation?"
        
        print(f"\n2️⃣  Testing query: '{test_query}'")
        print(f"   Expected tool: classroom_guidance")
        
        result = await orchestrator.process(
            input_data=OrchestratorInput(
                query=test_query,
                session_id="test_session_guidance"
            )
        )
        
        print(f"\n📊 Results:")
        print(f"   Tool Used: {result.tool_used}")
        print(f"   Confidence: {result.confidence:.2f}")
        
        if result.result:
            tool_result = result.result
            print(f"\n💡 Guidance Preview:")
            if isinstance(tool_result, dict):
                situation = tool_result.get('situation_analysis', 'No analysis')
                print(f"   Situation: {situation[:150]}...")
                if tool_result.get('immediate_tips'):
                    print(f"\n   Quick Tip: {tool_result['immediate_tips'][0]}")
            else:
                print(f"   {tool_result}")
        
        print(f"\n{'=' * 70}")
        print("✅ Orchestrator integration test completed!")
        print(f"{'=' * 70}")
        
    except ImportError as e:
        print(f"\n⚠️  Skipping orchestrator test: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting ClassroomGuidanceTool Tests\n")
    
    # Run tests
    asyncio.run(test_classroom_guidance())
    
    print("\n" + "=" * 70)
    input("Press Enter to continue with orchestrator integration test...")
    
    asyncio.run(test_orchestrator_integration())
    
    print("\n✅ All tests completed!")
