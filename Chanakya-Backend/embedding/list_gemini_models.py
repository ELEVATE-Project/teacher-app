#!/usr/bin/env python3
"""
Script to list available Gemini models
"""

import os
import warnings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
from google import genai

# Configure API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    exit(1)

client = genai.Client(api_key=api_key)

# List available models
print("=" * 60)
print("Available Gemini Models")
print("=" * 60)
print()

try:
    models = client.models.list()
    for model in models:
        print(f"Model: {model.name}")
        if hasattr(model, 'display_name'):
            print(f"  Display Name: {model.display_name}")
        if hasattr(model, 'description'):
            print(f"  Description: {model.description}")
        print()
except Exception as e:
    print(f"Error listing models: {e}")
    print()
    print("Trying common model names...")
    
    # Try common model names
    common_models = [
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
    ]
    
    for model_name in common_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="test"
            )
            print(f"✓ {model_name} - Available")
        except Exception as err:
            print(f"✗ {model_name} - Not available: {str(err)[:50]}")
