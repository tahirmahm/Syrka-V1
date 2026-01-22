"""
Syrka Configuration Module

This module defines all application configuration settings using Pydantic Settings.
All configuration is loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Syrka - National Workforce Mobility OS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM API (OpenAI-compatible: OpenAI, DeepSeek, etc.)
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str = "https://api.openai.com/v1"  # Change to https://api.deepseek.com for DeepSeek
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # Or deepseek-chat for DeepSeek
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # HuggingFace
    HF_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    HF_CACHE_DIR: Optional[str] = None

    # Gmail API
    GMAIL_CREDENTIALS_PATH: str = "credentials.json"
    GMAIL_TOKEN_PATH: str = "token.json"
    GMAIL_SCOPES: list[str] = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly"
    ]

    # External Job APIs
    ADZUNA_API_KEY: str = ""
    ADZUNA_APP_ID: str = ""
    REED_API_KEY: str = ""

    # Vector Store
    FAISS_INDEX_PATH: str = "data/faiss_index"
    EMBEDDING_DIMENSION: int = 384  # for all-MiniLM-L6-v2

    # File Upload
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set[str] = {"pdf", "doc", "docx", "txt"}

    # Scraping
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    SCRAPER_RATE_LIMIT: int = 2  # seconds between requests
    SCRAPER_MAX_RETRIES: int = 3

    # Matching Engine
    MATCH_TOP_K: int = 20
    MATCH_SIMILARITY_WEIGHT: float = 0.5
    MATCH_HEURISTIC_WEIGHT: float = 0.3
    MATCH_SKILL_OVERLAP_WEIGHT: float = 0.2

    # RAG
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5

    # Curriculum
    CURRICULUM_MAX_MODULES: int = 10
    CURRICULUM_MAX_UNITS_PER_MODULE: int = 8

    # Dashboard
    DASHBOARD_DEFAULT_REGIONS: list[str] = [
        "North", "South", "East", "West", "Central"
    ]
    DASHBOARD_DEFAULT_SECTORS: list[str] = [
        "Technology", "Healthcare", "Finance", "Education",
        "Manufacturing", "Construction", "Retail"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
