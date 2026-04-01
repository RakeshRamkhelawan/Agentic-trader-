import os

import pytest
from pydantic import ValidationError

from backend.core.config.settings import Settings


@pytest.mark.unit
def test_auth0_settings_missing():
    """Test that missing Auth0 settings raise an error when auth is enabled."""
    env_vars = {
        "AUTH_DISABLED": "false",
        "JWT_SECRET_KEY": "a_very_secure_random_key_min_32_chars_long",
        # Intentionally missing AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET
    }

    with pytest.MonkeyPatch.context() as m:
        for k, v in env_vars.items():
            m.setenv(k, v)

        # Remove existing Auth0 env vars if they exist
        m.delenv("AUTH0_DOMAIN", raising=False)
        m.delenv("AUTH0_CLIENT_ID", raising=False)
        m.delenv("AUTH0_CLIENT_SECRET", raising=False)

        # When auth is enabled, missing Auth0 settings should raise a validation error
        # Assuming the Settings model validates this, or we will implement it.
        with pytest.raises(ValidationError):
            Settings(_env_file=None)


@pytest.mark.unit
def test_auth0_settings_happy_path():
    """Test that valid Auth0 settings allow successful initialization."""
    env_vars = {
        "AUTH_DISABLED": "false",
        "JWT_SECRET_KEY": "a_very_secure_random_key_min_32_chars_long",
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_CLIENT_ID": "test_client_id",
        "AUTH0_CLIENT_SECRET": "test_client_secret",
        "AUTH0_AUDIENCE": "https://test.auth0.com/api/v2/",
    }

    with pytest.MonkeyPatch.context() as m:
        for k, v in env_vars.items():
            m.setenv(k, v)

        settings = Settings(_env_file=None)
        assert settings.AUTH0_DOMAIN == "test.auth0.com"
        assert settings.AUTH0_CLIENT_ID == "test_client_id"
        assert settings.AUTH0_CLIENT_SECRET == "test_client_secret"
