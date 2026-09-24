"""Unit tests for configuration management."""

import pytest
from aletheia.config.settings import Settings
from simulator.services.checkout_api.config import CheckoutSettings


@pytest.mark.unit
def test_aletheia_settings_defaults():
    """Verify default values for Aletheia platform settings."""
    settings = Settings()
    assert settings.app_name == "Aletheia Investigation Platform"
    assert settings.app_version == "0.1.0"
    assert settings.aletheia_port == 8000
    assert settings.aletheia_env in ["development", "production", "test"]


@pytest.mark.unit
def test_checkout_settings_defaults():
    """Verify default values for Checkout API settings."""
    settings = CheckoutSettings()
    assert settings.service_name == "checkout-api"
    assert settings.service_version == "1.0.0"
    assert settings.port == 8001
    assert "checkout_db" in settings.database_url or "sqlite" in settings.database_url
