"""Test content explainer directly"""
import asyncio
import os
from dotenv import load_dotenv
from orchestrator.tools.content_explainer import ContentExplainerTool

load_dotenv()

async def test():
    print("Initializing tool...")
    tool = ContentExplainerTool()
    
    print("\nTesting: What is photosynthesis?")
    result = await tool.run("What is photosynthesis?", {})
    
    print(f"\nConfidence: {result.get('confidence')}")
    print(f"Coverage: {result.get('coverage')}")
    print(f"Retrieved passages: {result.get('retrieved_passages')}")
    print(f"\nExplanation preview:")
    print(result.get('explanation', '')[:200])

if __name__ == "__main__":
    asyncio.run(test())
