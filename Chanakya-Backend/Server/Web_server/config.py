"""
Configuration for the Chanakya Web Server.
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from root directory (Chanakya/)
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    """Application settings."""
    
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL", 
        "mongodb+srv://kautilyasrivastava07:4V16P4rd7cBDrbaF@cluster0.5leoy.mongodb.net/Chanakya?retryWrites=true&w=majority"
    )
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "Chanakya")
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS Configuration
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:5173,http://localhost:5174,http://localhost:3000,https://*.vercel.app,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:3000,"
        "https://svelter-nonautomatically-anthony.ngrok-free.dev"
    ).split(",")
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # RAGFlow Configuration
    RAGFLOW_BASE_URL: str = os.getenv("RAGFLOW_BASE_URL", "http://localhost:5001")
    RAGFLOW_API_KEY: str = os.getenv("RAGFLOW_API_KEY", "")
    RAGFLOW_CHAT_ID: str = os.getenv("RAGFLOW_CHAT_ID", "")
    RAGFLOW_CLIENT_ID: str = os.getenv("RAGFLOW_CLIENT_ID", "")
    RAGFLOW_CLIENT_SECRET: str = os.getenv("RAGFLOW_CLIENT_SECRET", "")
    RAGFLOW_GRANT_TYPE: str = os.getenv("RAGFLOW_GRANT_TYPE", "client_credentials")
    RAGFLOW_DEFAULT_SCOPE: str = os.getenv("RAGFLOW_DEFAULT_SCOPE", "student_textbooks")
    RAGFLOW_DATASET_ID: str = os.getenv("RAGFLOW_DATASET_ID", "")
    RAGFLOW_DATASET_NAME: str = os.getenv("RAGFLOW_DATASET_NAME", "student_textbooks")
    RAGFLOW_TIMEOUT_SECONDS: float = float(os.getenv("RAGFLOW_TIMEOUT_SECONDS", "60"))
    RAGFLOW_TOKEN_TTL_SECONDS: int = int(os.getenv("RAGFLOW_TOKEN_TTL_SECONDS", "3300"))
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_WEBHOOK_URL: str = os.getenv("TWILIO_WEBHOOK_URL", "")

    # Query cache (repeated identical queries return cached response, no LLM call)
    QUERY_CACHE_ENABLED: bool = os.getenv("QUERY_CACHE_ENABLED", "true").lower() == "true"
    QUERY_CACHE_MAX_SIZE: int = int(os.getenv("QUERY_CACHE_MAX_SIZE", "500"))
    QUERY_CACHE_TTL_SECONDS: int = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "3600"))

settings = Settings()
