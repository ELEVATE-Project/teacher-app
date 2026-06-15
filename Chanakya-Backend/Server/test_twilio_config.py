"""
Quick test script to verify Twilio configuration
Run this from the Server directory with venv activated
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("TWILIO CONFIGURATION CHECK")
print("=" * 60)

# Check Twilio credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
phone_number = os.getenv("TWILIO_PHONE_NUMBER")
webhook_url = os.getenv("TWILIO_WEBHOOK_URL")

print("\n1. Environment Variables:")
print(f"   ✓ TWILIO_ACCOUNT_SID: {account_sid[:10]}..." if account_sid else "   ✗ TWILIO_ACCOUNT_SID: Not set")
print(f"   ✓ TWILIO_AUTH_TOKEN: {auth_token[:10]}..." if auth_token else "   ✗ TWILIO_AUTH_TOKEN: Not set")
print(f"   ✓ TWILIO_PHONE_NUMBER: {phone_number}" if phone_number else "   ✗ TWILIO_PHONE_NUMBER: Not set")
print(f"   ⚠ TWILIO_WEBHOOK_URL: {webhook_url}" if webhook_url else "   ✗ TWILIO_WEBHOOK_URL: Not set")

# Check Twilio SDK
print("\n2. Twilio SDK:")
try:
    from twilio.rest import Client
    print("   ✓ Twilio SDK installed")
    
    # Try to create client
    if account_sid and auth_token:
        try:
            client = Client(account_sid, auth_token)
            print("   ✓ Twilio client created successfully")
            
            # Try to fetch account info
            try:
                account = client.api.accounts(account_sid).fetch()
                print(f"   ✓ Account verified: {account.friendly_name}")
                print(f"   ✓ Account status: {account.status}")
            except Exception as e:
                print(f"   ✗ Could not verify account: {str(e)}")
        except Exception as e:
            print(f"   ✗ Failed to create client: {str(e)}")
    else:
        print("   ⚠ Cannot test client - credentials missing")
        
except ImportError:
    print("   ✗ Twilio SDK not installed")

# Check Sarvam AI (for transcription)
print("\n3. Sarvam AI (Speech-to-Text):")
try:
    from sarvamai import SarvamAI
    print("   ✓ Sarvam AI SDK installed")
    
    sarvam_key = os.getenv("SARVAM_API_KEY")
    if sarvam_key and sarvam_key != "YOUR_API_SUBSCRIPTION_KEY":
        print(f"   ✓ SARVAM_API_KEY configured")
    else:
        print("   ⚠ SARVAM_API_KEY not configured (will affect transcription)")
except ImportError:
    print("   ✗ Sarvam AI SDK not installed")

# Check Gemini (for orchestrator)
print("\n4. Gemini API (Orchestrator):")
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key and gemini_key != "YOUR_API_SUBSCRIPTION_KEY":
    print(f"   ✓ GEMINI_API_KEY configured: {gemini_key[:10]}...")
else:
    print("   ✗ GEMINI_API_KEY not configured (orchestrator won't work)")

print("\n" + "=" * 60)
print("SETUP STATUS")
print("=" * 60)

# Overall status
issues = []
warnings = []

if not account_sid or not auth_token or not phone_number:
    issues.append("Twilio credentials incomplete")

if not webhook_url or webhook_url == "https://your-domain.com":
    warnings.append("TWILIO_WEBHOOK_URL needs to be updated with your ngrok/deployment URL")

if not gemini_key:
    issues.append("GEMINI_API_KEY not configured")

if issues:
    print("\n❌ CRITICAL ISSUES:")
    for issue in issues:
        print(f"   - {issue}")

if warnings:
    print("\n⚠️  WARNINGS:")
    for warning in warnings:
        print(f"   - {warning}")

if not issues:
    print("\n✅ All critical components configured!")
    print("\nNEXT STEPS:")
    print("1. Start your server: python Web_server/main.py")
    print("2. If testing locally, start ngrok: ngrok http 3000")
    print("3. Update TWILIO_WEBHOOK_URL in .env with your ngrok URL")
    print("4. Configure Twilio dashboard:")
    print(f"   - Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
    print(f"   - Click on: {phone_number}")
    print("   - Under 'Voice Configuration', set:")
    print("     * A CALL COMES IN: Webhook")
    print("     * URL: [YOUR_WEBHOOK_URL]/api/twilio/voice")
    print("     * Method: POST")
    print("5. Call your number and test!")

print("\n" + "=" * 60)
