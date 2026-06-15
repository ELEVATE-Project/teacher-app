#!/usr/bin/env python3
"""
Script to check if API keys are properly configured
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_llama_api_key():
    """Check LlamaParse API key"""
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    
    if not api_key:
        print("❌ LLAMA_CLOUD_API_KEY not found in .env file")
        print("   Get your API key from: https://cloud.llamaindex.ai/")
        return False
    
    if api_key.strip() in ["", "your_llama_parse_api_key_here", "your_api_key_here"]:
        print("❌ LLAMA_CLOUD_API_KEY is set to placeholder value")
        print("   Please update .env file with your actual API key")
        print("   Get your API key from: https://cloud.llamaindex.ai/")
        return False
    
    # Check key format (LlamaParse keys usually start with certain patterns)
    if len(api_key) < 20:
        print("⚠️  LLAMA_CLOUD_API_KEY seems too short (might be invalid)")
        print("   Please verify your API key from: https://cloud.llamaindex.ai/")
        return False
    
    print(f"✅ LLAMA_CLOUD_API_KEY found (length: {len(api_key)})")
    return True

def check_gemini_api_key():
    """Check Gemini API key"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        return False
    
    if api_key.strip() in ["", "your_gemini_api_key_here", "your_api_key_here"]:
        print("❌ GEMINI_API_KEY is set to placeholder value")
        print("   Please update .env file with your actual API key")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        return False
    
    print(f"✅ GEMINI_API_KEY found (length: {len(api_key)})")
    return True

def main():
    print("=" * 60)
    print("API Key Configuration Check")
    print("=" * 60)
    print()
    
    llama_ok = check_llama_api_key()
    print()
    gemini_ok = check_gemini_api_key()
    print()
    
    print("=" * 60)
    if llama_ok and gemini_ok:
        print("✅ All API keys are configured!")
        print()
        print("You can now run:")
        print("  python embedding/generate_embeddings.py")
    else:
        print("❌ Some API keys are missing or invalid")
        print()
        print("Please update your .env file with valid API keys:")
        print("  1. LLAMA_CLOUD_API_KEY - from https://cloud.llamaindex.ai/")
        print("  2. GEMINI_API_KEY - from https://makersuite.google.com/app/apikey")
    print("=" * 60)

if __name__ == "__main__":
    main()
