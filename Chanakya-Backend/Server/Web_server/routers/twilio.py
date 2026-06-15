"""
Twilio Integration Router
Handles incoming voice calls and SMS, processes queries through orchestrator
"""
import os
import structlog
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Form
from typing import Optional, Any
import aiohttp

logger = structlog.get_logger(__name__)

# Try to import Twilio SDK
try:
    from twilio.twiml.voice_response import VoiceResponse, Gather
    from twilio.request_validator import RequestValidator
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio SDK not installed. Install with: pip install twilio")
    TwilioClient = Any

from services.orchestrator_service import orchestrator_service
from services.chat_service import ChatService
from utils.jwt import decode_access_token

router = APIRouter()

# Track processed calls to prevent duplicate SMS
processed_calls = set()


def truncate_for_sms(text: str, max_chars: int = 155) -> str:
    """Truncate text to fit in a single SMS segment (160 chars for GSM-7, leaving 5 for '...')"""
    if len(text) <= max_chars:
        return text
    # Find the last space before max_chars to avoid cutting words
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + '...'


def get_twilio_client() -> Optional[TwilioClient]:
    """Get initialized Twilio client or None if not configured"""
    if not TWILIO_AVAILABLE:
        return None
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        return None
    
    return TwilioClient(account_sid, auth_token)


def validate_twilio_signature(request: Request) -> bool:
    """Validate that request came from Twilio"""
    if not TWILIO_AVAILABLE:
        return False
    
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not auth_token:
        return False
    
    # Get signature from headers
    signature = request.headers.get("X-Twilio-Signature", "")
    
    # Build full URL
    url = str(request.url)
    
    # Get form parameters
    params = dict(request.query_params)
    
    # Validate
    validator = RequestValidator(auth_token)
    return validator.validate(url, params, signature)


@router.get("/test")
async def test_twilio_connection():
    """Test Twilio configuration"""
    if not TWILIO_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Twilio SDK not installed. Install with: pip install twilio"
        )
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not account_sid or account_sid == "YOUR_TWILIO_ACCOUNT_SID":
        raise HTTPException(
            status_code=400,
            detail="TWILIO_ACCOUNT_SID not configured"
        )
    
    if not auth_token or auth_token == "YOUR_TWILIO_AUTH_TOKEN":
        raise HTTPException(
            status_code=400,
            detail="TWILIO_AUTH_TOKEN not configured"
        )
    
    if not phone_number or phone_number == "YOUR_TWILIO_PHONE_NUMBER":
        raise HTTPException(
            status_code=400,
            detail="TWILIO_PHONE_NUMBER not configured"
        )
    
    return {
        "status": "ok",
        "account_sid": account_sid[:10] + "...",
        "phone_number": phone_number
    }


@router.post("/voice")
async def handle_incoming_call(request: Request):
    """
    Handle incoming voice call - record the message
    This endpoint is called by Twilio when someone calls your Twilio number
    """
    try:
        if not TWILIO_AVAILABLE:
            logger.error("Twilio SDK not available")
            error_response = VoiceResponse()
            error_response.say("Service is currently unavailable. Please try again later.", voice="woman")
            error_response.hangup()
            return Response(content=str(error_response), media_type="application/xml")
        
        # Note: In production, uncomment signature validation
        # if not validate_twilio_signature(request):
        #     raise HTTPException(status_code=401, detail="Invalid Twilio signature")
        
        # Get form data from Twilio
        form_data = await request.form()
        caller_number = form_data.get("From", "unknown")
        
        logger.info(f"Incoming call from {caller_number}")
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Greet the teacher
        response.say(
            "Welcome to Chanakya, your classroom assistant. "
            "Please ask your question after the beep.",
            voice="woman",
            language="en-IN"
        )
    except Exception as e:
        logger.error(f"Critical error in handle_incoming_call: {str(e)}", exc_info=True)
        # Always return valid TwiML to avoid 502
        error_response = VoiceResponse()
        error_response.say("Sorry, there was an error. Please try again later.", voice="woman")
        error_response.hangup()
        return Response(content=str(error_response), media_type="application/xml")
    
    # Record the message
    # Get webhook URL from environment or construct it
    webhook_url = os.getenv("TWILIO_WEBHOOK_URL", "").rstrip('/')
    if webhook_url:
        recording_callback = f"{webhook_url}/api/twilio/recording"
    else:
        # Fallback to relative URL
        recording_callback = "/api/twilio/recording"
    
    response.record(
        action=recording_callback,
        method="POST",
        max_length=60,  # 60 seconds max
        transcribe=False,  # Use Sarvam STT instead
        play_beep=True,
        finish_on_key="#"
    )
    
    # Return TwiML
    return Response(content=str(response), media_type="application/xml")


@router.post("/recording")
async def handle_recording(request: Request):
    """
    Handle recorded voice message - transcribe and process
    This endpoint is called by Twilio after recording is complete
    """
    try:
        if not TWILIO_AVAILABLE:
            logger.error("Twilio SDK not available")
            return Response(content="<Response><Say>Service unavailable</Say><Hangup/></Response>", media_type="application/xml")
        
        # Get form data from Twilio
        form_data = await request.form()
        recording_url = form_data.get("RecordingUrl")
        caller_number = form_data.get("From", "unknown")
        call_sid = form_data.get("CallSid", "unknown")
        
        logger.info(f"Processing recording from {caller_number}, CallSid: {call_sid}")
    except Exception as e:
        logger.error(f"Error initializing recording handler: {str(e)}", exc_info=True)
        return Response(content="<Response><Hangup/></Response>", media_type="application/xml")
    
    # Check if we already processed this call
    if call_sid in processed_calls:
        logger.info(f"Call {call_sid} already processed, skipping")
        return Response(content="<Response><Hangup/></Response>", media_type="application/xml")
    
    # Mark as processed
    processed_calls.add(call_sid)
    
    if not recording_url:
        logger.error("No recording URL provided")
        return Response(content="<Response><Say>Error: No recording received</Say></Response>", media_type="application/xml")
    
    try:
        # Download audio file from Twilio
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        
        # Download MP3 format
        recording_url_mp3 = f"{recording_url}.mp3"
        logger.info(f"Downloading recording from {recording_url_mp3}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                recording_url_mp3,
                auth=aiohttp.BasicAuth(account_sid, auth_token)
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to download recording: {resp.status}")
                audio_content = await resp.read()
        
        logger.info(f"Downloaded {len(audio_content)} bytes of audio")
        
        # Transcribe using Sarvam STT
        transcript = await transcribe_with_sarvam(audio_content)
        
        if not transcript:
            logger.error("Transcription failed or empty")
            await send_sms(caller_number, "Sorry, I couldn't understand your message. Please try again.")
            return Response(content="<Response><Hangup/></Response>", media_type="application/xml")
        
        logger.info(f"Transcribed: {transcript}")
        
        # Process through orchestrator
        if not orchestrator_service.is_ready():
            logger.error("Orchestrator not ready")
            await send_sms(caller_number, "Sorry, the system is not ready. Please try again later.")
            return Response(content="<Response><Hangup/></Response>", media_type="application/xml")
        
        # Create query request
        from schemas.query import QueryRequest
        query_request = QueryRequest(
            query=transcript,
            context={
                "channel": "twilio_voice",
                "caller": caller_number,
                "call_sid": call_sid
            },
            session_id=f"twilio_{call_sid}"
        )
        
        # Process query
        response = await orchestrator_service.process_query(query_request)
        
        # Extract response text
        response_text = ""
        if response.success:
            if hasattr(response, 'response') and response.response:
                response_text = response.response
            elif hasattr(response, 'content') and response.content:
                response_text = response.content
            else:
                response_text = str(response.result) if hasattr(response, 'result') else "Response received."
        else:
            response_text = "Sorry, I couldn't process your request. Please try again."
        
        # Truncate to fit in single SMS segment (160 chars)
        response_text = truncate_for_sms(response_text, 155)
        
        logger.info(f"Sending SMS response to {caller_number}")
        
        # Send response via SMS
        await send_sms(caller_number, response_text)
        
        # Hang up
        return Response(content="<Response><Hangup/></Response>", media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing recording: {str(e)}", exc_info=True)
        
        # Try to send error SMS
        try:
            await send_sms(
                caller_number,
                "Sorry, there was an error processing your request. Please try again later."
            )
        except:
            pass
        
        # Return simple hangup TwiML (no voice feedback)
        error_response = VoiceResponse()
        error_response.hangup()
        return Response(content=str(error_response), media_type="application/xml")


@router.post("/recording/transcription")
async def handle_transcription_callback(request: Request):
    """
    Handle Twilio transcription callback - processes the transcription when ready
    """
    if not TWILIO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Twilio SDK not available")
    
    # Get form data from Twilio
    form_data = await request.form()
    
    # Log all form fields for debugging
    logger.info(f"Transcription callback form fields: {dict(form_data)}")
    
    # Try different field names that Twilio might use
    transcription_text = (
        form_data.get("TranscriptionText") or 
        form_data.get("transcription_text") or
        form_data.get("Transcript") or 
        ""
    )
    recording_sid = form_data.get("RecordingSid", "")
    call_sid = form_data.get("CallSid", "")
    transcription_status = form_data.get("TranscriptionStatus", "")
    
    logger.info(f"Transcription callback - CallSid: {call_sid}, Status: {transcription_status}, Text length: {len(transcription_text)}")
    
    if not transcription_text or not transcription_text.strip():
        logger.error(f"Empty transcription received. Status: {transcription_status}")
        return Response(content="", status_code=200)
    
    # Get caller number directly from form data (it's included in the callback)
    caller_number = form_data.get("From", form_data.get("Caller", "unknown"))
    
    logger.info(f"Processing transcription for {caller_number}: {transcription_text}")
    
    try:
        
        # Process through orchestrator
        if not orchestrator_service.is_ready():
            logger.error("Orchestrator not ready")
            await send_sms(caller_number, "Sorry, the system is not ready. Please try again later.")
            return Response(content="", status_code=200)
        
        # Create query request
        from schemas.query import QueryRequest
        query_request = QueryRequest(
            query=transcription_text,
            context={
                "channel": "twilio_voice_transcription",
                "caller": caller_number,
                "call_sid": call_sid,
                "recording_sid": recording_sid
            },
            session_id=f"twilio_{call_sid}"
        )
        
        # Process query
        response = await orchestrator_service.process_query(query_request)
        
        # Extract response text
        response_text = ""
        if response.success:
            if hasattr(response, 'response') and response.response:
                response_text = response.response
            elif hasattr(response, 'content') and response.content:
                response_text = response.content
            else:
                response_text = str(response.result) if hasattr(response, 'result') else "Response received."
        else:
            response_text = "Sorry, I couldn't process your request. Please try again."
        
        # Truncate to fit in single SMS segment (160 chars)
        response_text = truncate_for_sms(response_text, 155)
        
        logger.info(f"Sending transcription response to {caller_number}")
        
        # Send response via SMS
        await send_sms(caller_number, response_text)
        
        return Response(content="", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing transcription: {str(e)}", exc_info=True)
        return Response(content="", status_code=500)


@router.post("/sms")
async def handle_incoming_sms(request: Request):
    """
    Handle incoming SMS - process text query
    This endpoint is called by Twilio when someone texts your Twilio number
    """
    if not TWILIO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Twilio SDK not available")
    
    # Get form data from Twilio
    form_data = await request.form()
    message_body = form_data.get("Body", "")
    sender_number = form_data.get("From", "unknown")
    message_sid = form_data.get("MessageSid", "unknown")
    
    logger.info(f"Incoming SMS from {sender_number}: {message_body}")
    
    if not message_body.strip():
        await send_sms(sender_number, "Please send a message with your question.")
        return Response(content="", status_code=200)
    
    try:
        # Process through orchestrator
        if not orchestrator_service.is_ready():
            logger.error("Orchestrator not ready")
            await send_sms(sender_number, "Sorry, the system is not ready. Please try again later.")
            return Response(content="", status_code=200)
        
        # Create query request
        from schemas.query import QueryRequest
        query_request = QueryRequest(
            query=message_body,
            context={
                "channel": "twilio_sms",
                "sender": sender_number,
                "message_sid": message_sid
            },
            session_id=f"twilio_sms_{sender_number.replace('+', '')}"
        )
        
        # Process query
        response = await orchestrator_service.process_query(query_request)
        
        # Extract response text
        response_text = ""
        if response.success:
            if hasattr(response, 'response') and response.response:
                response_text = response.response
            elif hasattr(response, 'content') and response.content:
                response_text = response.content
            else:
                response_text = str(response.result) if hasattr(response, 'result') else "Response received."
        else:
            response_text = "Sorry, I couldn't process your request. Please try again."
        
        # Truncate to fit in single SMS segment (160 chars)
        response_text = truncate_for_sms(response_text, 155)
        
        logger.info(f"Sending SMS response to {sender_number}")
        
        # Send response via SMS
        await send_sms(sender_number, response_text)
        
        return Response(content="", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing SMS: {str(e)}", exc_info=True)
        
        # Try to send error SMS
        try:
            await send_sms(
                sender_number,
                "Sorry, there was an error processing your request. Please try again later."
            )
        except:
            pass
        
        return Response(content="", status_code=500)


async def transcribe_with_sarvam(audio_content: bytes) -> Optional[str]:
    """
    Transcribe audio using Google Gemini API (already configured)
    """
    import tempfile
    from google import genai
    from google.genai import types
    
    temp_audio_path = None
    
    try:
        # Use Gemini API (already configured)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not configured")
            return None
        
        # Configure Gemini client
        client = genai.Client(api_key=api_key)
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_content)
            temp_audio_path = temp_file.name
        
        logger.info(f"Transcribing audio with Gemini: {temp_audio_path}")
        
        # Upload audio file to Gemini (specify mime_type via config dict)
        with open(temp_audio_path, 'rb') as f:
            audio_file = client.files.upload(file=f, config={"mime_type": "audio/mpeg"})
        
        # Use Gemini 2.0 to transcribe
        prompt = "Please transcribe this audio recording accurately. Only output the transcribed text, nothing else."
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, audio_file]
        )
        
        transcript = response.text.strip()
        
        logger.info(f"Gemini transcription: {transcript}")
        
        return transcript if transcript else None
        
    except Exception as e:
        logger.error(f"Gemini transcription error: {str(e)}", exc_info=True)
        return None
    finally:
        # Clean up temp file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass


async def transcribe_audio(audio_content: bytes) -> Optional[str]:
    """
    Transcribe audio using Sarvam STT
    """
    import tempfile
    temp_audio_path = None
    
    try:
        # Check if Sarvam is available
        try:
            from sarvamai import SarvamAI
            sarvam_available = True
        except ImportError:
            sarvam_available = False
            logger.warning("Sarvam AI not available for transcription")
        
        if not sarvam_available:
            # Fallback: return empty or use Twilio transcription
            logger.warning("Using fallback transcription (not implemented)")
            return None
        
        api_key = os.getenv("SARVAM_API_KEY")
        if not api_key or api_key == "YOUR_API_SUBSCRIPTION_KEY":
            logger.warning("SARVAM_API_KEY not configured")
            return None
        
        # Initialize Sarvam client
        client = SarvamAI(api_subscription_key=api_key)
        
        # Save audio to temporary file (Sarvam API requires file path or file object)
        # Use MP3 format as it's more compatible with Sarvam
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_content)
            temp_audio_path = temp_file.name
        
        # Transcribe using file path
        response = client.speech_to_text.transcribe(
            file=temp_audio_path,
            model="saaras:v3"  # Latest Saaras model for speech-to-text
        )
        
        # Extract transcript
        transcript = ""
        if hasattr(response, 'transcript'):
            transcript = response.transcript
        elif hasattr(response, 'text'):
            transcript = response.text
        elif isinstance(response, dict):
            transcript = response.get('transcript', response.get('text', ''))
        
        return transcript.strip() if transcript else None
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        return None
    finally:
        # Clean up temp file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass


async def send_sms(to_number: str, message: str):
    """
    Send SMS message via Twilio
    Handles long messages by splitting into multiple SMS
    """
    try:
        client = get_twilio_client()
        if not client:
            logger.error("Twilio client not available")
            return
        
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        if not from_number:
            logger.error("TWILIO_PHONE_NUMBER not configured")
            return
        
        # SMS character limit (1600 for safety, actual limit is higher)
        max_length = 1500
        
        # If message is too long, split it
        if len(message) > max_length:
            # Split into chunks
            chunks = []
            words = message.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 <= max_length:
                    current_chunk += word + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = word + " "
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Send each chunk
            for i, chunk in enumerate(chunks[:3]):  # Limit to 3 SMS
                if i > 0:
                    chunk = f"(Part {i+1}) {chunk}"
                
                message_obj = client.messages.create(
                    body=chunk,
                    from_=from_number,
                    to=to_number
                )
                logger.info(f"SMS sent (part {i+1}): {message_obj.sid}")
            
            if len(chunks) > 3:
                # Send continuation notice
                client.messages.create(
                    body="Response truncated. Reply 'MORE' for full answer or call for details.",
                    from_=from_number,
                    to=to_number
                )
        else:
            # Send single SMS
            message_obj = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            logger.info(f"SMS sent: {message_obj.sid}")
            
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}", exc_info=True)
        raise


@router.get("/status")
async def twilio_status():
    """
    Check Twilio configuration status (public endpoint for testing)
    """
    if not TWILIO_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Twilio SDK not installed"
        }
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    webhook_url = os.getenv("TWILIO_WEBHOOK_URL")
    
    configured = bool(account_sid and auth_token and phone_number)
    
    return {
        "status": "configured" if configured else "not_configured",
        "sdk_available": TWILIO_AVAILABLE,
        "account_sid_set": bool(account_sid),
        "auth_token_set": bool(auth_token),
        "phone_number": phone_number if phone_number else "not_set",
        "webhook_url": webhook_url if webhook_url else "not_set",
        "orchestrator_ready": orchestrator_service.is_ready()
    }
