"""
Sarvam AI API test routes.
"""
import os
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

try:
    from sarvamai import SarvamAI
    SARVAM_AVAILABLE = True
except ImportError:
    SARVAM_AVAILABLE = False


class TTSRequest(BaseModel):
    """Text-to-Speech request model."""
    text: str
    target_language_code: str = "hi-IN"
    speaker: str = "manisha"
    pitch: int = 0
    pace: float = 1.0
    loudness: float = 1.0
    speech_sample_rate: int = 22050
    enable_preprocessing: bool = True
    model: str = "bulbul:v2"


@router.get("/test")
async def test_sarvam_connection():
    """
    Test if Sarvam AI is properly configured.
    """
    if not SARVAM_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sarvam AI SDK not installed. Install with: pip install sarvamai"
        )
    
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key or api_key == "YOUR_API_SUBSCRIPTION_KEY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SARVAM_API_KEY not configured. Please set it in your environment variables."
        )
    
    return {
        "status": "ok",
        "message": "Sarvam AI is configured",
        "api_key_set": bool(api_key)
    }


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using Sarvam AI.
    
    Args:
        request: TTS request with text and parameters
        
    Returns:
        Audio file (WAV format)
    """
    if not SARVAM_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sarvam AI SDK not installed"
        )
    
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key or api_key == "YOUR_API_SUBSCRIPTION_KEY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SARVAM_API_KEY not configured"
        )
    
    try:
        import base64
        client = SarvamAI(api_subscription_key=api_key)
        
        response = client.text_to_speech.convert(
            text=request.text,
            target_language_code=request.target_language_code,
            speaker=request.speaker,
            pitch=request.pitch,
            pace=request.pace,
            loudness=request.loudness,
            speech_sample_rate=request.speech_sample_rate,
            enable_preprocessing=request.enable_preprocessing,
            model=request.model
        )
        
        # Handle response like in Python test file - decode base64 audio
        audio_data = None
        if hasattr(response, 'audios') and response.audios:
            # Decode base64 audio (matching Python test file approach)
            audio_data = base64.b64decode(response.audios[0])
        elif isinstance(response, bytes):
            audio_data = response
        elif hasattr(response, 'audio'):
            audio_data = response.audio
        elif hasattr(response, 'content'):
            audio_data = response.content
        else:
            # Try to get the audio from response object
            audio_data = response
        
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No audio data received from Sarvam AI"
            )
        
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sarvam AI TTS error: {str(e)}"
        )


@router.post("/tts/test")
async def test_tts_default():
    """
    Test TTS with default Hindi text (dummy test).
    """
    test_request = TTSRequest(
        text="एडोब फोटोशॉपउद्योग में प्रचलित, शक्तिशाली सॉफ्टवेयर है जिसका उपयोग रास्टर (पिक्सेल-आधारित) छवियों को संपादित करने, उनमें बदलाव करने और बनाने के लिए किया जाता है। इसका उपयोग फोटो रिटचिंग, डिजिटल आर्ट, ग्राफिक डिजाइन और विभिन्न रचनात्मक क्षेत्रों में कंपोजिटिंग के लिए किया जाता है।"
    )
    return await text_to_speech(test_request)


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Convert speech to text using Sarvam AI.
    
    Args:
        audio: Audio file (WAV format)
        
    Returns:
        JSON with transcript
    """
    if not SARVAM_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sarvam AI SDK not installed"
        )
    
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key or api_key == "YOUR_API_SUBSCRIPTION_KEY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SARVAM_API_KEY not configured"
        )
    
    try:
        import tempfile
        client = SarvamAI(api_subscription_key=api_key)
        
        # Read audio file
        audio_content = await audio.read()
        
        # Save to temp file as Sarvam API requires file path
        temp_audio_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_content)
                temp_audio_path = temp_file.name
            
            # Use Sarvam AI STT with correct parameters
            response = client.speech_to_text.transcribe(
                file=temp_audio_path,
                model="saaras:v3"  # Latest Saaras model
            )
        
            # Extract transcript from response
            transcript = ""
            if hasattr(response, 'transcript'):
                transcript = response.transcript
            elif hasattr(response, 'text'):
                transcript = response.text
            elif isinstance(response, dict):
                transcript = response.get('transcript', response.get('text', ''))
            elif isinstance(response, str):
                transcript = response
            
            return {
                "transcript": transcript,
                "text": transcript
            }
        finally:
            # Clean up temp file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sarvam AI STT error: {str(e)}"
        )
