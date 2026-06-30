"""
Test the Resource Finder Tool with Tavily
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables searching dynamically
load_dotenv(find_dotenv())

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.tools.resource_finder import ResourceFinderTool


async def test_resource_finder():
    """Test the resource finder tool."""
    
    print("=" * 60)
    print("Testing Resource Finder Tool")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("❌ TAVILY_API_KEY not set!")
        return
    
    print(f"✅ Tavily API key found: {api_key[:10]}...")
    
    # Initialize the tool
    try:
        tool = ResourceFinderTool()
        print("✅ ResourceFinderTool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test topic extraction
    print("\n📝 Testing topic extraction:")
    test_queries = [
        "Give me YouTube videos about photosynthesis",
        "Explain gravity and find me some resources",
        "I need lesson plans for teaching fractions",
    ]
    
    for query in test_queries:
        topic = ResourceFinderTool.extract_topic(query)
        print(f"  Query: '{query}'")
        print(f"  Topic: '{topic}'")
        print()
    
    # Test actual search
    print("\n🔍 Testing resource search for 'photosynthesis':")
    try:
        result = await tool.execute("photosynthesis", None)
        
        print(f"\nQuery: {result.query}")
        print(f"Summary: {result.summary[:200]}..." if result.summary else "No summary")
        print(f"Total results: {result.total_results}")
        
        if result.video_resources:
            print("\n🎥 Videos:")
            for i, video in enumerate(result.video_resources, 1):
                print(f"  {i}. {video.title}")
                print(f"     {video.url}")
        
        if result.educational_resources:
            print("\n📚 Educational Resources:")
            for i, res in enumerate(result.educational_resources, 1):
                print(f"  {i}. {res.title}")
                print(f"     {res.url}")
        
        if result.web_resources:
            print("\n🔗 Web Articles:")
            for i, web in enumerate(result.web_resources, 1):
                print(f"  {i}. {web.title}")
                print(f"     {web.url}")
        
        print("\n✅ Test successful!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_orchestrator_with_resources():
    """Test the full orchestrator with resource finding."""
    
    print("\n" + "=" * 60)
    print("Testing Orchestrator with Resource Finder")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set!")
        return
    
    from orchestrator.orchestrator import ChanakyaOrchestrator
    from orchestrator.schemas import OrchestratorInput
    
    try:
        orchestrator = ChanakyaOrchestrator(api_key=api_key)
        print("✅ Orchestrator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test query that should trigger resources
    query = "Explain photosynthesis and give me some YouTube videos"
    print(f"\n📝 Query: '{query}'")
    
    try:
        input_data = OrchestratorInput(query=query)
        result = await orchestrator.process(input_data)
        
        print(f"\n✅ Tool used: {result.tool_used}")
        print(f"Reasoning: {result.reasoning}")
        
        if result.result:
            if isinstance(result.result, dict):
                # Check for resources in result
                if "resources" in result.result:
                    resources = result.result["resources"]
                    print(f"\n📚 Resources found: {resources.get('total_results', 0)}")
                    
                    videos = resources.get("video_resources", [])
                    if videos:
                        print(f"\n🎥 Videos ({len(videos)}):")
                        for v in videos[:3]:
                            print(f"  - {v.get('title', 'Unknown')}")
                else:
                    print("\n⚠️ No resources in result (needs_resources might be False)")
                
                # Print main explanation (truncated)
                if "explanation" in result.result:
                    expl = result.result["explanation"]
                    print(f"\n📖 Explanation: {expl[:200]}...")
            else:
                print(f"Result: {str(result.result)[:200]}...")
        
        print("\n✅ Orchestrator test successful!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run basic resource finder test
    asyncio.run(test_resource_finder())
    
    # Optionally run full orchestrator test
    print("\n" + "-" * 60)
    print("Do you want to test the full orchestrator? (y/n)")
    response = input().strip().lower()
    if response == 'y':
        asyncio.run(test_orchestrator_with_resources())
