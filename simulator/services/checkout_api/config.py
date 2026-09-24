"""Configuration for simulated Checkout API service."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class CheckoutSettings(BaseSettings):
    """Checkout service settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "checkout-api"
    service_version: str = "1.0.0"
    service_environment: str = "production-sim"
    host: str = "0.0.0.0"
    port: int = 8001

    # Database connection URL - checks DATABASE_URL, SIMULATOR_DATABASE_URL or fallback
    database_url: str = os.getenv(
        "DATABASE_URL",
        os.getenv(
            "SIMULATOR_DATABASE_URL",
            "postgresql://aletheia:aletheia_secret@localhost:5432/checkout_db",
        ),
    )


@lru_cache
def get_checkout_settings() -> CheckoutSettings:
    """Return cached checkout settings."""
    return CheckoutSettings()
