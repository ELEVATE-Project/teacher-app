"""Test Hindi translation in orchestrator"""
import asyncio
import os
from dotenv import load_dotenv
from orchestrator.orchestrator import ChanakyaOrchestrator
from orchestrator.schemas import OrchestratorInput

# Load environment variables
load_dotenv()

async def test():
    orch = ChanakyaOrchestrator(api_key=os.getenv('GEMINI_API_KEY'))
    
    inp = OrchestratorInput(
        query='मेरी क्लास के बच्चे बहुत ज्यादा शेतानी कर रहे हैं, मैं क्या करूं बताओ।',
        session_id='test123'
    )
    
    result = await orch.process(inp)
    
    print(f"\n{'='*60}")
    print(f"Tool Used: {result.tool_used}")
    print(f"Confidence: {result.confidence}")
    print(f"{'='*60}\n")
    
    if hasattr(result.result, 'activity_name'):
        print(f"Activity Name: {result.result.activity_name}")
        print(f"\nDescription: {result.result.description}")
        print(f"\nSteps:")
        for i, step in enumerate(result.result.steps, 1):
            print(f"  {i}. {step}")
        print(f"\nLearning Outcome: {result.result.learning_outcome}")
    else:
        print(f"Result: {result.result}")

if __name__ == "__main__":
    asyncio.run(test())
