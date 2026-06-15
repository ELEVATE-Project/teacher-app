"""
Test Kannada language detection and translation in Chanakya Orchestrator
"""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator import ChanakyaOrchestrator, OrchestratorInput


async def test_kannada_detection():
    """Test Kannada language detection."""
    print("\n" + "="*60)
    print("Testing Kannada Language Detection")
    print("="*60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    
    # Test Kannada query
    kannada_query = "ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆ ಎಂದರೇನು?"  # "What is photosynthesis?" in Kannada
    
    detected_lang = await orchestrator._detect_language(kannada_query)
    print(f"\n📝 Query: {kannada_query}")
    print(f"🔍 Detected Language: {detected_lang}")
    
    if detected_lang == "Kannada":
        print("✅ Kannada detection successful!")
    else:
        print(f"❌ Expected 'Kannada', but got '{detected_lang}'")


async def test_kannada_translation():
    """Test translation to Kannada."""
    print("\n" + "="*60)
    print("Testing Translation to Kannada")
    print("="*60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    
    # Test English text translation
    english_text = "Photosynthesis is the process by which plants make their food using sunlight."
    
    translated = await orchestrator._translate_text(english_text, "Kannada")
    print(f"\n📝 English: {english_text}")
    print(f"🌐 Kannada: {translated}")
    print("✅ Translation completed!")


async def test_kannada_end_to_end():
    """Test end-to-end Kannada query with translated response."""
    print("\n" + "="*60)
    print("Testing End-to-End Kannada Query & Response")
    print("="*60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    orchestrator = ChanakyaOrchestrator(api_key=api_key)
    
    # Test with a simple Kannada greeting
    kannada_query = "ನಮಸ್ಕಾರ"  # "Hello" in Kannada
    
    print(f"\n📝 Query: {kannada_query}")
    
    input_data = OrchestratorInput(
        query=kannada_query,
        session_id="test_kannada_session"
    )
    
    result = await orchestrator.process(input_data)
    
    print(f"\n🔧 Tool Used: {result.tool_used}")
    print(f"📊 Confidence: {result.confidence:.2f}")
    print(f"⏱️  Processing Time: {result.processing_time_ms:.0f}ms")
    
    if result.error:
        print(f"❌ Error: {result.error}")
    else:
        print(f"✅ Success!")
        print(f"\n📤 Response:")
        if isinstance(result.result, dict):
            for key, value in result.result.items():
                print(f"  {key}: {value[:100] if isinstance(value, str) else value}...")
        else:
            print(f"  {result.result}")


async def main():
    """Run all tests."""
    print("\n🚀 Starting Kannada Translation Tests")
    print("="*60)
    
    await test_kannada_detection()
    await test_kannada_translation()
    await test_kannada_end_to_end()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
