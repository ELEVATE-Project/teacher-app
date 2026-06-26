import sys
import os
import json
import logging
import requests
from types import ModuleType

logger = logging.getLogger("openrouter_generativeai_patch")
logging.basicConfig(level=logging.INFO)

# Retrieve OpenRouter API Key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "openrouter_api_key_here":
    OPENROUTER_API_KEY = os.getenv("GEMINI_API_KEY")

class GenerateContentResponse:
    def __init__(self, text=""):
        self._text = text

    @property
    def text(self) -> str:
        return self._text

# Map model names to OpenRouter model names
def map_model_name(model_name: str) -> str:
    name = model_name
    if name.startswith("models/"):
        name = name[7:]
    
    # Map to OpenRouter slugs
    if "gemini-2.5-flash" in name:
        return "google/gemini-2.5-flash"
    if "gemini-2.5-pro" in name:
        return "google/gemini-2.5-pro"
    if "gemini-1.5-flash" in name:
        return "google/gemini-1.5-flash"
    if "gemini-1.5-pro" in name:
        return "google/gemini-1.5-pro"
    
    return "google/gemini-2.5-flash"  # default fallback

def make_openrouter_call(model: str, contents, generation_config=None) -> str:
    messages = [{"role": "user", "content": contents}]
    mapped_model = map_model_name(model)
    payload = {
        "model": mapped_model,
        "messages": messages,
    }
    
    if generation_config:
        if isinstance(generation_config, dict):
            temp = generation_config.get("temperature")
            if temp is not None:
                payload["temperature"] = temp
            max_tokens = generation_config.get("max_output_tokens")
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            response_mime = generation_config.get("response_mime_type")
            if response_mime == "application/json":
                payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Kautilya03/teacher-app",
        "X-Title": "Chanakya Teacher App",
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        resp_json = response.json()
        
        choices = resp_json.get("choices") or []
        if not choices:
            error_info = resp_json.get("error") or {}
            error_msg = error_info.get("message") or "Empty response from OpenRouter"
            raise Exception(error_msg)
            
        answer = choices[0].get("message", {}).get("content", "")
        return answer
    except Exception as e:
        logger.error(f"OpenRouter call failed: {e}")
        raise

class GenerativeModel:
    def __init__(self, model_name, generation_config=None, **kwargs):
        self.model_name = model_name
        self.generation_config = generation_config

    def generate_content(self, contents, **kwargs) -> GenerateContentResponse:
        ans = make_openrouter_call(self.model_name, contents, self.generation_config)
        return GenerateContentResponse(text=ans)

def configure(api_key=None, **kwargs):
    pass

# Create dynamic modules
generativeai_module = ModuleType("google.generativeai")
generativeai_module.GenerativeModel = GenerativeModel
generativeai_module.configure = configure

# Override sys.modules
sys.modules["google.generativeai"] = generativeai_module

# Ensure any existing google module is aware of generativeai
try:
    import google
    setattr(google, "generativeai", generativeai_module)
except ImportError:
    pass

logger.info("google.generativeai has been patched to route queries to OpenRouter")
