"""
Configuration settings for the chatbot API.
"""

import os
from typing import Optional


class Config:
    """Application configuration."""

    # Server settings
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))

    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]

    # Session settings
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "1800"))  # 30 minutes
    MAX_SESSION_HISTORY: int = 100

    # Message settings
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "10000"))
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "20"))  # messages per minute

    # Gemini settings
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    API_KEY: Optional[str] = os.getenv("GOOGLE_AI_STUDIO_KEY") or os.getenv("GOOGLE_API_KEY")

    # ChromaDB settings (for semantic search tools)
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))

    # File storage
    GENERATED_FILES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")

    # Development mode
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


config = Config()
