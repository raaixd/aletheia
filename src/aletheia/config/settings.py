"""Settings and configuration management for Aletheia."""

from functools import lru_cache
from typing import Optional
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


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
