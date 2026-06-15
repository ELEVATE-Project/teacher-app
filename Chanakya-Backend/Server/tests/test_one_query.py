"""Simple one-query test"""
import asyncio
import os
from dotenv import load_dotenv
from orchestrator import ChanakyaOrchestrator
from orchestrator.schemas import OrchestratorInput

load_dotenv()

async def test():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("API key not set")
        return
    
    print("Initializing orchestrator...")
    orch = ChanakyaOrchestrator(api_key=api_key)
    
    print("\nQuery: What is photosynthesis?")
    result = await orch.process(
        OrchestratorInput(
            query="What is photosynthesis?",
            context={"grade": "10", "subject": "science"},
            session_id="test1"
        )
    )
    
    print(f"\nTool used: {result.tool_used}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Confidence: {result.confidence}")
    
    if isinstance(result.result, dict):
        print(f"Retrieved passages: {result.result.get('retrieved_passages', 'N/A')}")
        print(f"Coverage: {result.result.get('coverage', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test())
