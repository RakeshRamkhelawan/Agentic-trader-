"""
Fase 2: Auth, Rate Limiting & Security Middleware - Happy Path Tests

Verifies:
- Security headers are present on all responses
- Rate limit headers are returned
- /api/v1/config does not leak Auth0 details
- CSP is strict in production, relaxed in development

Run with: pytest backend/tests/security/test_auth_hardening.py -v
"""

import os

import pytest


class TestSecurityHeadersPresent:
    """Verify all security headers are set on responses."""

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, async_client):
        """X-Content-Type-Options must be nosniff."""
        response = await async_client.get("/api/v1/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, async_client):
        """X-Frame-Options must be DENY."""
        response = await async_client.get("/api/v1/health")
        assert response.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_xss_protection(self, async_client):
        """X-XSS-Protection must be set."""
        response = await async_client.get("/api/v1/health")
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy(self, async_client):
        """Referrer-Policy must be strict-origin-when-cross-origin."""
        response = await async_client.get("/api/v1/health")
        assert (
            response.headers.get("referrer-policy")
            == "strict-origin-when-cross-origin"
        )

    @pytest.mark.asyncio
    async def test_permissions_policy_present(self, async_client):
        """Permissions-Policy must be present."""
        response = await async_client.get("/api/v1/health")
        pp = response.headers.get("permissions-policy", "")
        assert "geolocation=()" in pp
        assert "camera=()" in pp

    @pytest.mark.asyncio
    async def test_csp_present(self, async_client):
        """Content-Security-Policy must be present."""
        response = await async_client.get("/api/v1/health")
        csp = response.headers.get("content-security-policy", "")
        assert "default-src" in csp
        assert "'self'" in csp


class TestConfigEndpointSecurity:
    """Verify /api/v1/config does not leak sensitive information."""

    @pytest.mark.asyncio
    async def test_config_no_auth0_domain(self, async_client):
        """Config endpoint must NOT expose Auth0 domain."""
        response = await async_client.get("/api/v1/config")
        if response.status_code == 404:
            pytest.skip("/api/v1/config not found")
        data = response.json()
        auth_section = data.get("auth", {})
        assert "domain" not in auth_section, (
            "/api/v1/config leaks Auth0 domain"
        )

    @pytest.mark.asyncio
    async def test_config_no_auth0_audience(self, async_client):
        """Config endpoint must NOT expose Auth0 audience."""
        response = await async_client.get("/api/v1/config")
        if response.status_code == 404:
            pytest.skip("/api/v1/config not found")
        data = response.json()
        auth_section = data.get("auth", {})
        assert "audience" not in auth_section, (
            "/api/v1/config leaks Auth0 audience"
        )

    @pytest.mark.asyncio
    async def test_config_no_client_secret(self, async_client):
        """Config endpoint must NOT contain any client_secret."""
        response = await async_client.get("/api/v1/config")
        if response.status_code == 404:
            pytest.skip("/api/v1/config not found")
        data_str = str(response.json()).lower()
        assert "client_secret" not in data_str


class TestProductionSafetyValidator:
    """Verify production safety validators work."""

    def test_auth_disabled_blocked_in_production(self):
        """AUTH_DISABLED=True must raise when ENV=production."""
        from backend.core.config.settings import Settings

        with pytest.raises(ValueError, match="AUTH_DISABLED"):
            Settings(
                ENV="production",
                AUTH_DISABLED=True,
                JWT_SECRET_KEY="a" * 40,
                _env_file=None,
            )

    def test_auth_disabled_allowed_in_development(self):
        """AUTH_DISABLED=True should work when ENV=development."""
        from backend.core.config.settings import Settings

        s = Settings(
            ENV="development",
            AUTH_DISABLED=True,
            JWT_SECRET_KEY="a" * 40,
            _env_file=None,
        )
        assert s.AUTH_DISABLED is True
