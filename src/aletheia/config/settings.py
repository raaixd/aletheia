"""Settings and configuration management for Aletheia."""

from functools import lru_cache
from typing import Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Aletheia Investigation Platform"
    app_version: str = "0.1.0"
    aletheia_env: str = "development"
    aletheia_port: int = 8000
    aletheia_log_level: str = "INFO"

    # Simulated Environment Target
    checkout_api_url: str = "http://localhost:8001"

    # Database URL (optional for Aletheia platform storage in later phases)
    database_url: Optional[str] = None

    # LLM & Evaluation Configuration
    llm_provider: str = "mock"  # "mock", "openai", "openai-compatible"
    llm_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY"),
        description="API key for LLM provider, read from LLM_API_KEY or OPENAI_API_KEY",
    )
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_mock_mode: str = "accurate"  # "accurate", "hallucinated", "partial", "invalid_json"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
