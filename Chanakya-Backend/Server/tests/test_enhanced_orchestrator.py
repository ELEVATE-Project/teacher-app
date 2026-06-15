"""
Test the enhanced orchestrator with all LangGraph features.
"""

import asyncio
import os
from dotenv import load_dotenv
from orchestrator.schemas import OrchestratorInput
from orchestrator.orchestrator import ChanakyaOrchestrator

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# async def test_basic_activity():
#     """Test basic activity generation."""
#     print("=== Test 1: Basic Activity Generation ===")
#     orchestrator = ChanakyaOrchestrator(api_key=api_key)
#     
#     query = "I want an activity about plants for class 4"
#     print(f"Question: {query}")
#     
#     input_data = OrchestratorInput(
#         query=query,
#         context={"grade": 4, "subject": "science"}
#     )
    
#     result = await orchestrator.process(input_data)
#     
#     print(f"Tool Used: {result.tool_used}")
#     print(f"Confidence: {result.confidence}")
#     print(f"Processing Time: {result.processing_time_ms:.2f}ms")
#     print(f"Reasoning: {result.reasoning}")
#     
#     if result.error:
#         print(f"Error: {result.error}")
#     else:
#         print(f"Activity: {result.result.activity_name if hasattr(result.result, 'activity_name') else result.result}")
#     
#     print("\n")

# async def test_crisis_with_followup():
#     """Test crisis handling with automatic activity follow-up."""
#     print("=== Test 2: Crisis Handling with Follow-up ===")
#     orchestrator = ChanakyaOrchestrator(api_key=api_key)
#     
#     query = "My students are making too much noise and not focusing"
#     print(f"Question: {query}")
#     
#     input_data = OrchestratorInput(
#         query=query,
#         context={"grade": 5, "class_size": 50}
#     )
    
#     result = await orchestrator.process(input_data)
#     
#     print(f"Tool Used: {result.tool_used}")
#     print(f"Confidence: {result.confidence}")
#     print(f"Processing Time: {result.processing_time_ms:.2f}ms")
#     print(f"Reasoning: {result.reasoning}")
#     if result.error:
#         print(f"Error: {result.error}")
#     else:
#         print(f"Result: {result.result}")
#         
#         # Check for follow-up
#         if hasattr(result.result, 'get') and result.result.get('follow_up'):
#             print(f"\n[+] Follow-up activity suggested!")
#             print(f"Follow-up: {result.result['follow_up']}")
#     
#     print("\n")

# async def test_ambiguous_query():
#     """Test handling of ambiguous query (should trigger confidence routing)."""
#     print("=== Test 3: Ambiguous Query (Low Confidence) ===")
#     orchestrator = ChanakyaOrchestrator(api_key=api_key)
#     
#     query = "kids"
#     print(f"Question: {query}")
#     
#     input_data = OrchestratorInput(
#         query=query,
#         context={"grade": 3}
#     )
    
#     result = await orchestrator.process(input_data)
#     
#     print(f"Tool Used: {result.tool_used}")
#     print(f"Confidence: {result.confidence}")
#     print(f"Processing Time: {result.processing_time_ms:.2f}ms")
#     print(f"Reasoning: {result.reasoning}")
#     
#     if result.error:
#         print(f"Error: {result.error}")
#     else:
#         print(f"Result: {result.result}")
#     
#     print("\n")

# #     """Test Hindi language query."""
#     print("=== Test 4: Hindi Language Query ===")
#     orchestrator = ChanakyaOrchestrator(api_key=api_key)
#     
#     query = "मुझे कक्षा 3 के लिए गणित की गतिविधि चाहिए"
#     print(f"Question: {query}")
#     
#     input_data = OrchestratorInput(
#         query=query,
#         context={"grade": 3, "subject": "math"}
#     )
    
#     result = await orchestrator.process(input_data)
#     
#     print(f"Tool Used: {result.tool_used}")
#     print(f"Confidence: {result.confidence}")
#     print(f"Processing Time: {result.processing_time_ms:.2f}ms")
#     
#     if result.error:
#         print(f"Error: {result.error}")
#     else:
#         print(f"Activity: {result.result.activity_name if hasattr(result.result, 'activity_name') else result.result}")
#     
#     print("\n")

async def test_checkpointing():
    """Test conversation context persistence."""
    print("=== Test 5: Checkpointing & Context ===")
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    
    session_id = "test_session_123"
    
    # First query
    query1 = "activity for radius for circle"
    print(f"Question 1: {query1}")
    
    input1 = OrchestratorInput(
        query=query1,
        context={"grade": 5},
        session_id=session_id
    )
    
    result1 = await orchestrator.process(input1)
    print(f"\nQuery 1 - Tool: {result1.tool_used}, Confidence: {result1.confidence}")
    print(f"Processing Time: {result1.processing_time_ms:.2f}ms")
    if result1.error:
        print(f"Error: {result1.error}")
    else:
        if hasattr(result1.result, 'activity_name'):
            print(f"\n[+] Activity: {result1.result.activity_name}")
            print(f"Description: {result1.result.description}")
            print(f"Duration: {result1.result.duration_minutes} minutes")
            print(f"Materials: {', '.join(result1.result.materials_needed)}")
            print(f"Steps: {len(result1.result.steps)} steps")
        else:
            print(f"Result: {result1.result}")
    
    # Check context
    ctx = orchestrator.get_context(session_id)
    if ctx:
        print(f"\nContext preserved: {len(ctx.messages)} messages in history")
    
    print("\n" + "="*50 + "\n")
    
    # Second query in same session
    query2 = "now for diameter"
    print(f"Question 2: {query2}")
    
    input2 = OrchestratorInput(
        query=query2,
        context={"grade": 5},
        session_id=session_id
    )
    
    result2 = await orchestrator.process(input2)
    print(f"\nQuery 2 - Tool: {result2.tool_used}, Confidence: {result2.confidence}")
    print(f"Processing Time: {result2.processing_time_ms:.2f}ms")
    if result2.error:
        print(f"Error: {result2.error}")
    else:
        if hasattr(result2.result, 'activity_name'):
            print(f"\n[+] Activity: {result2.result.activity_name}")
            print(f"Description: {result2.result.description}")
            print(f"Duration: {result2.result.duration_minutes} minutes")
            print(f"Materials: {', '.join(result2.result.materials_needed)}")
            print(f"Steps: {len(result2.result.steps)} steps")
        else:
            print(f"Result: {result2.result}")
    
    # Check context again
    ctx = orchestrator.get_context(session_id)
    if ctx:
        print(f"Context updated: {len(ctx.messages)} messages total")
    
    print("\n")

async def main():
    """Run all tests."""
    print("=== Testing Enhanced Orchestrator with LangGraph ===\n")
    print("Features being tested:")
    print("[*] Confidence-based routing")
    print("[*] Retry logic with max attempts")
    print("[*] Output validation")
    print("[*] Follow-up actions (crisis -> activity)")
    print("[*] Checkpointing & conversation context")
    print("[*] Multilingual support\n")
    
    # await test_basic_activity()
    # await test_crisis_with_followup()
    # await test_ambiguous_query()
    # await test_hindi_query()
    await test_checkpointing()
    
    print("[+] All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
