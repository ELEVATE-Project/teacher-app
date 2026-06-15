"""
Test ContentExplainerTool with RAG Integration
==============================================

This script tests the newly integrated ContentExplainerTool that uses
RAG embeddings to retrieve and answer questions from NCERT content.
"""

import asyncio
import os
from dotenv import load_dotenv
from orchestrator.tools.content_explainer import ContentExplainerTool

# Load environment variables from .env file
load_dotenv()


async def test_content_explainer():
    """Test the content explainer tool with sample queries."""
    
    # Ensure API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ERROR: GEMINI_API_KEY environment variable not set!")
        print("   Set it with: $env:GEMINI_API_KEY='your-api-key-here'")
        return
    
    print("=" * 70)
    print("Testing ContentExplainerTool with RAG Integration")
    print("=" * 70)
    
    try:
        # Initialize the tool
        print("\n1️⃣  Initializing ContentExplainerTool...")
        tool = ContentExplainerTool(
            db_path="Server/orchestrator/tools/RAG/ncert_books.db",
            top_k=3  # Retrieve top 3 relevant passages
        )
        print(f"✅ Tool initialized successfully!")
        print(f"   Database contains {tool.db.get_document_count()} documents")
        
        # Test queries
        test_queries = [
            {
                "query": "What is rectilinear motion?",
                "context": {"class": "10", "subject": "Science"}
            },
            {
                "query": "Explain how a pinhole camera works",
                "context": {"class": "10", "subject": "Science"}
            },
            {
                "query": "What are the standard units of measurement for length?",
                "context": None  # No filters
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n{'-' * 70}")
            print(f"Test {i}: {test['query']}")
            if test['context']:
                print(f"Filters: {test['context']}")
            print(f"{'-' * 70}")
            
            # Run the tool
            result = await tool.run(test['query'], test['context'])
            
            # Display results
            print(f"\n📊 Results:")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"   Coverage: {result.get('coverage', 'unknown')}")
            print(f"   Retrieved Passages: {result.get('retrieved_passages', 0)}")
            
            if result.get('sources'):
                print(f"\n📚 Sources:")
                for source in result['sources'][:3]:  # Show first 3
                    print(f"   - {source}")
            
            print(f"\n💡 Explanation:")
            explanation = result.get('explanation', 'No explanation provided')
            print(f"   {explanation[:300]}...")  # Show first 300 chars
            
            if result.get('key_points'):
                print(f"\n🔑 Key Points:")
                for point in result['key_points'][:3]:  # Show first 3
                    print(f"   - {point}")
            
            if result.get('error'):
                print(f"\n⚠️  Error: {result['error']}")
        
        # Close the tool
        tool.close()
        print(f"\n{'=' * 70}")
        print("✅ All tests completed successfully!")
        print(f"{'=' * 70}")
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: Database file not found!")
        print(f"   {e}")
        print(f"   Make sure ncert_books.db exists at: orchestrator/tools/RAG/ncert_books.db")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   {e}")
        import traceback
        traceback.print_exc()


async def test_orchestrator_integration():
    """Test the full orchestrator with content queries."""
    
    print("\n" + "=" * 70)
    print("Testing Full Orchestrator Integration")
    print("=" * 70)
    
    try:
        from orchestrator.orchestrator import ChanakyaOrchestrator
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ ERROR: GEMINI_API_KEY not set!")
            return
        
        print("\n1️⃣  Initializing ChanakyaOrchestrator...")
        orchestrator = ChanakyaOrchestrator(api_key=api_key)
        print(f"✅ Orchestrator initialized!")
        print(f"   Available tools: {list(orchestrator.tools.keys())}")
        
        # Test routing to content_explainer
        test_query = "What is rectilinear motion?"
        
        print(f"\n2️⃣  Testing query: '{test_query}'")
        print(f"   Expected tool: content_explainer")
        
        from orchestrator.schemas import OrchestratorInput
        
        result = await orchestrator.process(
            input_data=OrchestratorInput(
                query=test_query,
                session_id="test_session_rag"
            )
        )
        
        print(f"\n📊 Results:")
        print(f"   Tool Used: {result.tool_used}")
        print(f"   Confidence: {result.confidence:.2f}")
        
        if result.result:
            tool_result = result.result
            print(f"\n💡 Explanation Preview:")
            explanation = tool_result.get('explanation', 'No explanation') if isinstance(tool_result, dict) else getattr(tool_result, 'explanation', 'No explanation')
            print(f"   {explanation[:200]}...")
        
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
    print("\n🚀 Starting RAG Integration Tests\n")
    
    # Run tests
    asyncio.run(test_content_explainer())
    
    print("\n" + "=" * 70)
    input("Press Enter to continue with orchestrator integration test...")
    
    asyncio.run(test_orchestrator_integration())
    
    print("\n✅ All tests completed!")
