"""
Fase 2: Auth, Rate Limiting & Security Middleware - Integration Tests

Tests run against real services (no mocks).
Verifies the full auth and security flow end-to-end.

Requirements: docker-compose up db redis
Run with: pytest backend/tests/security/test_auth_integration.py -v -m integration
"""

import pytest


@pytest.mark.integration
class TestAuthIntegration:
    """Full auth flow against real services."""

    @pytest.mark.asyncio
    async def test_full_jwt_lifecycle(self):
        """Create, verify, refresh, and validate JWT tokens."""
        from backend.auth.jwt_handler import JWTHandler

        handler = JWTHandler()

        # Create access token
        access_token = handler.create_access_token(
            user_id="integration-test-user",
            tenant_id="integration-test-tenant",
            role="admin",
        )
        assert access_token is not None
        assert len(access_token) > 50

        # Verify access token
        payload = handler.verify_access_token(access_token)
        assert payload is not None
        assert payload["sub"] == "integration-test-user"
        assert payload["tenant_id"] == "integration-test-tenant"
        assert payload["role"] == "admin"

        # Create refresh token
        refresh_token = handler.create_refresh_token(
            user_id="integration-test-user",
            tenant_id="integration-test-tenant",
        )
        assert refresh_token is not None

        # Refresh token must not be accepted as access token
        wrong_result = handler.verify_access_token(refresh_token)
        assert wrong_result is None, "Refresh token accepted as access token"

    @pytest.mark.asyncio
    async def test_security_headers_on_all_endpoints(self, async_client):
        """All endpoints must return security headers."""
        endpoints = ["/", "/api", "/api/v1/health"]
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            assert (
                response.headers.get("x-content-type-options") == "nosniff"
            ), f"{endpoint} missing X-Content-Type-Options"
            assert (
                response.headers.get("x-frame-options") == "DENY"
            ), f"{endpoint} missing X-Frame-Options"
            csp = response.headers.get("content-security-policy", "")
            assert "default-src" in csp, f"{endpoint} missing Content-Security-Policy"

    @pytest.mark.asyncio
    async def test_rate_limiter_returns_headers(self, async_client):
        """Responses must include rate limit information headers."""
        response = await async_client.get("/api/v1/health")
        # slowapi adds X-RateLimit-Limit and X-RateLimit-Remaining
        header_keys = [k.lower() for k in response.headers.keys()]
        has_ratelimit = any("ratelimit" in k for k in header_keys)
        # Note: slowapi may not add headers on all endpoints
        # unless decorated. Check on decorated endpoint instead.
        response2 = await async_client.get("/api/v1/config")
        if response2.status_code != 404:
            header_keys2 = [k.lower() for k in response2.headers.keys()]
            has_ratelimit = has_ratelimit or any("ratelimit" in k for k in header_keys2)
        assert has_ratelimit, (
            "No rate limit headers found on any endpoint. "
            "slowapi may not be properly configured."
        )

    @pytest.mark.asyncio
    async def test_config_endpoint_safe_response(self, async_client):
        """Config endpoint must return safe, non-sensitive data."""
        response = await async_client.get("/api/v1/config")
        if response.status_code == 404:
            pytest.skip("/api/v1/config not found")
        assert response.status_code == 200
        data = response.json()
        # Must have expected structure
        assert "auth" in data
        assert "features" in data
        assert "environment" in data
        # Must NOT have sensitive fields
        auth = data["auth"]
        assert "domain" not in auth
        assert "audience" not in auth
        assert "client_secret" not in str(data).lower()
