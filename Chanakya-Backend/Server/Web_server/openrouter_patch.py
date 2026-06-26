import sys
import os
import json
import logging
import requests
import asyncio
from types import ModuleType

logger = logging.getLogger("openrouter_patch")
logging.basicConfig(level=logging.INFO)

# Retrieve OpenRouter API Key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "openrouter_api_key_here":
    # Fallback to GEMINI_API_KEY if needed
    OPENROUTER_API_KEY = os.getenv("GEMINI_API_KEY")

class Part:
    def __init__(self, text=""):
        self.text = text

class Content:
    def __init__(self, role="user", parts=None):
        self.role = role
        self.parts = parts or []

class GenerateContentConfig:
    def __init__(self, temperature=None, max_output_tokens=None, response_mime_type=None, response_schema=None, system_instruction=None, **kwargs):
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.response_mime_type = response_mime_type
        self.response_schema = response_schema
        self.system_instruction = system_instruction

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

def make_openrouter_call(model: str, contents, config: GenerateContentConfig) -> str:
    # 1. Format the messages for OpenAI / OpenRouter format
    messages = []
    
    if isinstance(contents, str):
        messages.append({"role": "user", "content": contents})
    elif isinstance(contents, list):
        for item in contents:
            if isinstance(item, str):
                messages.append({"role": "user", "content": item})
            elif hasattr(item, "parts"):
                content_text = "".join(part.text for part in item.parts if hasattr(part, "text"))
                messages.append({"role": item.role or "user", "content": content_text})
            elif isinstance(item, dict):
                messages.append(item)
    elif hasattr(contents, "parts"):
        content_text = "".join(part.text for part in contents.parts if hasattr(part, "text"))
        messages.append({"role": contents.role or "user", "content": content_text})
    
    # Extract system instruction if present in config
    system_instruction_text = None
    if config and hasattr(config, "system_instruction") and config.system_instruction:
        inst = config.system_instruction
        if isinstance(inst, str):
            system_instruction_text = inst
        elif hasattr(inst, "parts"):
            system_instruction_text = "".join(part.text for part in inst.parts if hasattr(part, "text"))
        elif isinstance(inst, list):
            system_instruction_text = ""
            for item in inst:
                if isinstance(item, str):
                    system_instruction_text += item
                elif hasattr(item, "parts"):
                    system_instruction_text += "".join(part.text for part in item.parts if hasattr(part, "text"))
                    
    if system_instruction_text:
        messages.insert(0, {"role": "system", "content": system_instruction_text})

    # 2. Build the OpenRouter payload
    mapped_model = map_model_name(model)
    payload = {
        "model": mapped_model,
        "messages": messages,
    }
    
    if config:
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.max_output_tokens is not None:
            payload["max_tokens"] = config.max_output_tokens
        if config.response_mime_type == "application/json" or config.response_schema is not None:
            payload["response_format"] = {"type": "json_object"}
            
            # If there's a response schema, we can append it to the last message to enforce structure!
            if config.response_schema and messages:
                schema_instructions = f"\n\nYou must return a JSON object conforming exactly to this JSON schema:\n{json.dumps(config.response_schema)}"
                messages[-1]["content"] += schema_instructions
 
    # 3. Headers
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Kautilya03/teacher-app",
        "X-Title": "Chanakya Teacher App",
    }
    
    # 4. Request
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
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

class ModelsMock:
    def generate_content(self, model: str, contents, config=None, **kwargs) -> GenerateContentResponse:
        ans = make_openrouter_call(model, contents, config)
        return GenerateContentResponse(text=ans)

class AioModelsMock:
    async def generate_content(self, model: str, contents, config=None, **kwargs) -> GenerateContentResponse:
        ans = await asyncio.to_thread(make_openrouter_call, model, contents, config)
        return GenerateContentResponse(text=ans)

class AioMock:
    def __init__(self):
        self.models = AioModelsMock()

class ClientMock:
    def __init__(self, api_key=None, **kwargs):
        self.models = ModelsMock()
        self.aio = AioMock()

# Create dynamic modules
genai_module = ModuleType("google.genai")
genai_module.Client = ClientMock

types_module = ModuleType("google.genai.types")
types_module.Part = Part
types_module.Content = Content
types_module.GenerateContentConfig = GenerateContentConfig

# Bind submodules
genai_module.types = types_module

# Override sys.modules
sys.modules["google.genai"] = genai_module
sys.modules["google.genai.types"] = types_module

# Ensure any existing google module is aware of genai
try:
    import google
    setattr(google, "genai", genai_module)
except ImportError:
    pass

logger.info("google.genai has been patched to route queries to OpenRouter")
