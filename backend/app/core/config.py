"""
Centralized application configuration.

All configuration is read from environment variables (see .env.example at the
repo root). Nothing here should contain real secrets — this module only
defines *how* config is loaded and validated, never the values themselves.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    ENV: Literal["development", "staging", "production"] = "development"
    SECRET_KEY: str = Field(..., description="Used to sign auth tokens. Must be set in .env")
    API_PREFIX: str = "/api"
    # Comma-separated CORS origins (Todo T4.3) — parsed in app/main.py.
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # --- Database ---
    DATABASE_URL: str = Field(..., description="postgresql+psycopg2://user:pass@host:port/dbname")

    # --- Redis / background jobs ---
    REDIS_URL: str = Field(..., description="redis://host:port/0")

    # --- AI provider abstraction ---
    # The app must not be hard-wired to one vendor. AI_PROVIDER selects the
    # adapter implementation in app/ai/providers/.
    # Default is "ollama": fully local, no API key, no cost — matches the
    # project's no-paid-tools constraint. "gemini" and "groq" are cloud
    # options with a free tier (still require a free-signup API key).
    # "anthropic"/"openai" are supported by the abstraction but require a
    # paid key, so they are not the default here.
    AI_PROVIDER: Literal["ollama", "gemini", "groq", "anthropic", "openai"] = "ollama"
    AI_API_KEY: str | None = None
    AI_MODEL: str = "llama3.1"
    # Model used for embeddings (pgvector matching, Todo T1.3).
    # Default 768 dims matches nomic-embed-text — change both together.
    AI_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # --- Browser automation ---
    BROWSER_HEADLESS: bool = True

    # --- Job sources ---
    # JSON-encoded config describing which JobSource adapters are enabled.
    # Kept as a raw string here; parsed by app/sources/registry.py.
    JOB_SOURCE_CONFIG: str = "{}"

    # --- Uploads ---
    MAX_UPLOAD_MB: int = 10
    UPLOAD_DIR: str = "./uploads"


@lru_cache
def get_settings() -> Settings:
    """Settings are cached so the .env file is parsed once per process."""
    return Settings()
