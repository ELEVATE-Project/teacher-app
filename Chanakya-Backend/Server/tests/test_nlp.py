"""
Chanakya NLP - Test Runner (Simplified)
=======================================

Simple test for the NLP pipeline.
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from nlp.pipeline import NLPPipeline
from nlp.schemas import TeacherUtterance


# Test examples in different Indian languages
TEST_EXAMPLES = [
    # Hindi
    {"text": "Bachche sun nahi rahe hain", "expected_lang": "hi"},
    {"text": "Inko addition samajh nahi aa raha", "expected_lang": "hi"},
    {"text": "Bahut shor ho raha hai class mein", "expected_lang": "hi"},
    
    # Tamil
    {"text": "குழந்தைகள் கவனிக்கவில்லை", "expected_lang": "ta"},
    
    # Bengali
    {"text": "বাচ্চারা বুঝতে পারছে না", "expected_lang": "bn"},
    
    # Telugu
    {"text": "పిల్లలు వినడం లేదు", "expected_lang": "te"},
    
    # Marathi
    {"text": "मुलं लक्ष देत नाहीत", "expected_lang": "mr"},
    
    # Code-mixed
    {"text": "Circle ka radius kaise explain karu?", "expected_lang": "mixed"},
    {"text": "Fraction wala part samajh nahi aa raha inko", "expected_lang": "mixed"},
]


def run_tests(api_key: str):
    """Run test examples."""
    
    pipeline = NLPPipeline(gemini_api_key=api_key)
    
    print("\n" + "=" * 60)
    print("CHANAKYA NLP TEST - Simple English Understanding")
    print("=" * 60)
    
    for i, example in enumerate(TEST_EXAMPLES, 1):
        print(f"\n--- Test {i} ---")
        print(f"Input: {example['text']}")
        print(f"Expected language: {example['expected_lang']}")
        
        utterance = TeacherUtterance(
            text=example["text"],
            timestamp=datetime.now(timezone.utc)
        )
        
        result = pipeline.process_sync(utterance)
        
        print(f"English: {result.english_understanding}")
        print(f"Detected language: {result.detected_language}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Time: {result.processing_time_ms:.0f}ms")
        
        if result.error:
            print(f"Error: {result.error}")


def interactive_mode(api_key: str):
    """Interactive testing mode."""
    
    pipeline = NLPPipeline(gemini_api_key=api_key)
    
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE - Type in any Indian language")
    print("Type 'quit' to exit")
    print("=" * 60)
    
    while True:
        text = input("\nTeacher says: ").strip()
        
        if text.lower() == 'quit':
            break
        
        if not text:
            continue
        
        utterance = TeacherUtterance(
            text=text,
            timestamp=datetime.now(timezone.utc)
        )
        
        result = pipeline.process_sync(utterance)
        
        print(f"\n→ English: {result.english_understanding}")
        print(f"  Language: {result.detected_language} | Confidence: {result.confidence:.2f} | Time: {result.processing_time_ms:.0f}ms")
        
        if result.error:
            print(f"  Error: {result.error}")


if __name__ == "__main__":
    import sys
    
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("Please set GEMINI_API_KEY environment variable or pass as argument")
        print("Usage: python test_nlp.py [api_key]")
        sys.exit(1)
    
    # Run a few tests first
    print("Running sample tests...")
    run_tests(api_key)
    
    # Then interactive mode
    interactive_mode(api_key)
