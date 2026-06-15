import os
import base64
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    print("⚠️  Set SARVAM_API_KEY in .env")
    exit()

client = SarvamAI(api_subscription_key=api_key)

print("Testing Sarvam TTS...")

try:
    response = client.text_to_speech.convert(
        text="नमस्ते, मैं सरवम एआई हूँ।",
        target_language_code="hi-IN",
        speaker="manisha",
        model="bulbul:v2"
    )
    
    # Decode base64 audio and save
    audio_data = base64.b64decode(response.audios[0])
    with open("output.wav", "wb") as f:
        f.write(audio_data)
    
    print("✅ Saved to output.wav")
    os.system("start output.wav")
    
except Exception as e:
    print(f"❌ Error: {e}")