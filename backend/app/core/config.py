from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Grounded Advisory Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # Security & JWT
    JWT_SECRET_KEY: str = "dev-secret-key-grounded-advisory-assistant-team02-super-secure"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Vector DB
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    SIMILARITY_THRESHOLD: float = 0.68

    # LLM & Embeddings
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Upload Limits
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    DISABLE_RATE_LIMITS: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.ENVIRONMENT == "production" and "*" in origins:
            raise ValueError("Wildcard CORS origin '*' is strictly prohibited in production.")
        return origins

    def validate_production_configuration(self):
        """Validates critical enterprise security settings for production deployments."""
        if self.ENVIRONMENT == "production":
            if not self.JWT_SECRET_KEY or "dev-secret-key" in self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "Production configuration error: JWT_SECRET_KEY must be set to a secure, "
                    "randomly generated key of at least 32 characters. Default dev keys are prohibited."
                )
            if "*" in self.cors_origins_list:
                raise ValueError("Production configuration error: Wildcard CORS origin is prohibited.")
            if self.LLM_PROVIDER == "groq" and (not self.GROQ_API_KEY or self.GROQ_API_KEY.startswith("gsk_mock")):
                raise ValueError("Production configuration error: Valid GROQ_API_KEY is required for Groq provider.")
            if self.LLM_PROVIDER == "openai" and (not self.OPENAI_API_KEY or self.OPENAI_API_KEY.startswith("sk-mock")):
                raise ValueError("Production configuration error: Valid OPENAI_API_KEY is required for OpenAI provider.")

    model_config = SettingsConfigDict(
        env_file=[
            str(BASE_DIR.parent / ".env"),
            str(BASE_DIR / ".env"),
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

