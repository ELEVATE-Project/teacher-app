"""
Diagnostic script for Twilio 502 Bad Gateway errors
Run this to identify the root cause of the issue
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("TWILIO 502 BAD GATEWAY DIAGNOSTIC")
print("=" * 70)

issues = []
warnings = []

# 1. Check Twilio SDK
print("\n[1] Checking Twilio SDK...")
try:
    from twilio.twiml.voice_response import VoiceResponse
    from twilio.rest import Client as TwilioClient
    print("    ✓ Twilio SDK installed")
except ImportError as e:
    print(f"    ✗ Twilio SDK not installed: {e}")
    issues.append("Install Twilio: pip install twilio")

# 2. Check environment variables
print("\n[2] Checking Environment Variables...")
env_vars = {
    "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
    "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
    "TWILIO_PHONE_NUMBER": os.getenv("TWILIO_PHONE_NUMBER"),
    "TWILIO_WEBHOOK_URL": os.getenv("TWILIO_WEBHOOK_URL"),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
}

for key, value in env_vars.items():
    if value and value not in ["YOUR_API_SUBSCRIPTION_KEY", "YOUR_TWILIO_ACCOUNT_SID", "YOUR_TWILIO_AUTH_TOKEN"]:
        if "KEY" in key or "TOKEN" in key or "SID" in key:
            print(f"    ✓ {key}: {value[:10]}...")
        else:
            print(f"    ✓ {key}: {value}")
    else:
        print(f"    ✗ {key}: NOT CONFIGURED")
        issues.append(f"Set {key} in .env file")

# 3. Check Gemini API (critical for transcription)
print("\n[3] Checking Gemini API...")
try:
    from google import genai
    print("    ✓ Google Generative AI SDK installed")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "YOUR_API_SUBSCRIPTION_KEY":
        print("    ✓ GEMINI_API_KEY configured")
        try:
            client = genai.Client(api_key=api_key)
            print("    ✓ Gemini client initialized")
        except Exception as e:
            print(f"    ✗ Failed to initialize Gemini client: {e}")
            issues.append("Check GEMINI_API_KEY validity")
    else:
        print("    ✗ GEMINI_API_KEY not configured")
        issues.append("Set GEMINI_API_KEY in .env (required for audio transcription)")
except ImportError as e:
    print(f"    ✗ Google Generative AI SDK not installed: {e}")
    issues.append("Install google-generativeai: pip install google-generativeai")

# 4. Check orchestrator service
print("\n[4] Checking Orchestrator Service...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Web_server"))
    from services.orchestrator_service import orchestrator_service
    
    if orchestrator_service.is_ready():
        print("    ✓ Orchestrator service is ready")
    else:
        print("    ✗ Orchestrator service not ready")
        warnings.append("Orchestrator needs to be initialized (might happen during server startup)")
except Exception as e:
    print(f"    ⚠ Cannot check orchestrator: {e}")
    warnings.append("Orchestrator check failed - this is OK if server isn't running")

# 5. Check server status
print("\n[5] Checking Server Status...")
try:
    import requests
    try:
        response = requests.get("http://localhost:8000/api/twilio/status", timeout=3)
        if response.status_code == 200:
            status_data = response.json()
            print(f"    ✓ Server is running")
            print(f"    - Twilio SDK: {'Available' if status_data.get('sdk_available') else 'Not Available'}")
            print(f"    - Orchestrator: {'Ready' if status_data.get('orchestrator_ready') else 'Not Ready'}")
            if not status_data.get('orchestrator_ready'):
                issues.append("Orchestrator not ready - restart server to initialize")
        else:
            print(f"    ⚠ Server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("    ✗ Server not running on localhost:8000")
        warnings.append("Start the server: cd Server/Web_server && uvicorn main:app")
    except Exception as e:
        print(f"    ⚠ Cannot connect to server: {e}")
except ImportError:
    print("    ⚠ requests library not installed (optional check)")

# 6. Common 502 causes
print("\n[6] Common 502 Bad Gateway Causes:")
print("    - Server not running or crashed")
print("    - Orchestrator not initialized (check server startup logs)")
print("    - Missing dependencies (google-generativeai, twilio)")
print("    - Invalid API keys (Gemini, Twilio)")
print("    - Timeout in async operations")
print("    - Uncaught exceptions in endpoint handlers")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if issues:
    print("\n🔴 CRITICAL ISSUES (must fix):")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")

if warnings:
    print("\n🟡 WARNINGS:")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")

if not issues and not warnings:
    print("\n✅ All checks passed!")
    print("\nIf you're still getting 502 errors:")
    print("   1. Check server logs for detailed error messages")
    print("   2. Restart the server completely")
    print("   3. Verify your ngrok URL matches TWILIO_WEBHOOK_URL")
    print("   4. Test with: curl -X POST http://localhost:8000/api/twilio/voice")

# Quick fixes
print("\n" + "=" * 70)
print("QUICK FIXES")
print("=" * 70)
print("\n1. Install missing packages:")
print("   pip install twilio google-generativeai")
print("\n2. Restart server:")
print("   cd Server/Web_server")
print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
print("\n3. Test Twilio endpoint:")
print("   curl -X POST http://localhost:8000/api/twilio/voice")
print("\n4. Check server logs for detailed errors")
