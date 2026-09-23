"""
Application Configuration using pydantic-settings.
Loads environment variables from .env file or system environment.
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TrustAI - AI Security Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # API Routes
    API_PREFIX: str = "/api/v1"

    # Vector Database & Embeddings
    # Computes absolute path relative to project root if relative path is given
    VECTOR_STORE_PATH: str = os.getenv(
        "VECTOR_STORE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "vector_store")
    )
    COLLECTION_NAME: str = "trustai_compliance_docs"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Retrieval Tuning
    TOP_K: int = 3
    RELEVANCE_THRESHOLD: float = 0.35

    # Local Ollama LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT_SECONDS: float = 35.0
    OLLAMA_TEMPERATURE: float = 0.15

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
