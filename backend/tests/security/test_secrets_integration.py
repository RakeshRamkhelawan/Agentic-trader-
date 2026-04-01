"""
Fase 1: Secrets & Credential Hardening - Integration Tests

Tests run against real services (no mocks, no placeholders).
Verifies the full startup chain with proper secrets configuration.

Requirements: docker-compose up db redis
Run with: pytest backend/tests/security/test_secrets_integration.py -v -m integration
"""

import pytest


@pytest.mark.integration
class TestSecretsIntegration:
    """Integration tests verifying the full secrets lifecycle."""

    @pytest.mark.asyncio
    async def test_app_starts_with_valid_secrets(self, async_client):
        """FastAPI app must start successfully when all secrets are valid."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in (
            "healthy",
            "ok",
            "operational",
            "running",
        ), f"Unexpected health status: {data}"

    @pytest.mark.asyncio
    async def test_config_endpoint_hides_secrets(self, async_client):
        """The /api/v1/config endpoint must not expose any secrets."""
        response = await async_client.get("/api/v1/config")
        if response.status_code == 404:
            pytest.skip("/api/v1/config endpoint not found")
        assert response.status_code == 200
        data_str = str(response.json()).lower()
        # Must not contain any secret-like values
        secret_keywords = [
            "client_secret",
            "api_secret",
            "private_key",
        ]
        for keyword in secret_keywords:
            assert keyword not in data_str, f"/api/v1/config leaks '{keyword}' in response"

    @pytest.mark.asyncio
    async def test_jwt_token_full_lifecycle(self):
        """Create, verify, and validate a JWT token against real settings."""
        from backend.auth.jwt_handler import JWTHandler

        handler = JWTHandler()

        # Create access token
        access_token = handler.create_access_token(
            user_id="integration-test-user",
            tenant_id="integration-test-tenant",
            role="user",
        )
        assert access_token is not None
        assert len(access_token) > 50, "JWT token is suspiciously short"

        # Verify token decodes correctly
        payload = handler.verify_access_token(access_token)
        assert payload is not None, "Token verification failed"
        assert payload["sub"] == "integration-test-user"
        assert payload["tenant_id"] == "integration-test-tenant"
        assert payload["role"] == "user"

    @pytest.mark.asyncio
    async def test_jwt_tampered_token_rejected(self):
        """A tampered JWT token must be rejected."""
        from backend.auth.jwt_handler import JWTHandler

        handler = JWTHandler()

        token = handler.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            role="user",
        )
        # Tamper with the token by modifying the last character
        if token[-1] == "A":
            tampered = token[:-1] + "B"
        else:
            tampered = token[:-1] + "A"

        result = handler.verify_access_token(tampered)
        assert result is None, "Tampered token was accepted -- signature validation broken"

    @pytest.mark.asyncio
    async def test_settings_loads_without_insecure_defaults(self):
        """Settings singleton must load without any insecure default values."""
        from backend.core.config.settings import _INSECURE_DEFAULTS, settings

        jwt_key = settings.JWT_SECRET_KEY
        assert (
            jwt_key not in _INSECURE_DEFAULTS
        ), f"Settings loaded with insecure JWT default: {jwt_key[:10]}..."
        assert len(jwt_key) >= 32, f"JWT_SECRET_KEY is only {len(jwt_key)} chars (minimum 32)"

    @pytest.mark.asyncio
    async def test_get_jwt_secret_returns_same_as_field(self):
        """get_jwt_secret() must return the same value as the Field when Vault is disabled."""
        from backend.core.config.settings import settings

        if settings.VAULT_ENABLED:
            pytest.skip("Vault is enabled -- get_jwt_secret may differ")

        field_value = settings.JWT_SECRET_KEY
        method_value = settings.get_jwt_secret()
        assert (
            field_value == method_value
        ), "get_jwt_secret() returns a different value than JWT_SECRET_KEY field"
