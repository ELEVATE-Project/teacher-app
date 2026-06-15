"""
Configuration for the Chanakya orchestrator.
"""

import os
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseConfig:
    """Database configuration management."""
    
    def __init__(self):
        self.env = os.getenv("ENV", Environment.DEVELOPMENT)
        
    @property
    def use_sqlite(self) -> bool:
        """Check if SQLite should be used for checkpointing (default)."""
        return os.getenv("USE_SQLITE", "true").lower() == "true"
    
    @property
    def sqlite_path(self) -> str:
        """Get SQLite database path."""
        import os.path as path
        db_path = os.getenv("SQLITE_PATH", "data/checkpoints.db")
        # Ensure absolute path
        if not path.isabs(db_path):
            # Make relative to Server directory
            base_dir = path.dirname(path.dirname(path.abspath(__file__)))
            db_path = path.join(base_dir, db_path)
        return db_path


class Config:
    """Main configuration class."""
    
    db = DatabaseConfig()
    
    # Model settings
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "32768"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Retry settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    
    # Conversation settings
    MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "10"))
    CONTEXT_EXPIRY_HOURS = int(os.getenv("CONTEXT_EXPIRY_HOURS", "24"))
    
    # Summarization settings
    SUMMARIZATION_THRESHOLD = int(os.getenv("SUMMARIZATION_THRESHOLD", "20"))  # Trigger summarization after 20 messages
    SUMMARIZATION_KEEP_RECENT = int(os.getenv("SUMMARIZATION_KEEP_RECENT", "5"))  # Keep last 5 messages
    
    # Hallucination detection settings
    HALLUCINATION_THRESHOLD = float(os.getenv("HALLUCINATION_THRESHOLD", "0.7"))  # Minimum acceptable score (0-1)
    MAX_HALLUCINATION_CHECKS = int(os.getenv("MAX_HALLUCINATION_CHECKS", "2"))  # Max retries for hallucination
