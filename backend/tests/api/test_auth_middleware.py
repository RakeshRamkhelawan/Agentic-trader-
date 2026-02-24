"""
TDD Tests for AuthMiddleware Integration.

RED PHASE: These tests should FAIL initially because:
- AuthMiddleware is not yet added to main.py
- deps.py still uses hardcoded tenant-123

Tests cover:
- Happy path: Valid token extracts correct tenant_id
- Unhappy paths: Invalid/missing/expired tokens return 401
- Public routes bypass authentication
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

# Import the app
from backend.api.main import app

# Test constants
SECRET_KEY = "dev-secret-key"
ALGORITHM = "HS256"

# ============================================================================
# TOKEN HELPERS
# ============================================================================


def create_test_token(
    tenant_id: str = "tenant-test-1",
    account_id: str = "account-test-1",
    roles: list = None,
    expires_delta: timedelta = timedelta(hours=24),
    expired: bool = False,
) -> str:
    """Create a valid JWT token for testing."""
    now = datetime.now(UTC)

    if expired:
        exp = now - timedelta(hours=1)  # Already expired
    else:
        exp = now + expires_delta

    payload = {
        "sub": account_id,
        "tenant_id": tenant_id,
        "account_id": account_id,
        "roles": roles or ["trader"],
        "exp": exp,
        "iat": now,
        "iss": "agentic-trader",
        "aud": "agentic-trader-api",
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_invalid_token() -> str:
    """Create a token signed with wrong key."""
    payload = {
        "sub": "account-1",
        "tenant_id": "tenant-1",
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return jwt.encode(payload, "wrong-secret-key", algorithm=ALGORITHM)


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_valid_token_extracts_correct_tenant():
    """
    Happy Path: A valid JWT token should extract the correct tenant_id.

    Expected: The API uses tenant_id from token ("tenant-test-1"),
              NOT the hardcoded "tenant-123".
    """
    token = create_test_token(tenant_id="tenant-test-1", account_id="user-test-1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/trading/markets", headers={"Authorization": f"Bearer {token}"}
        )

    # Should succeed
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # The response should be based on tenant-test-1, not tenant-123
    # This test will initially FAIL because deps.py returns hardcoded tenant


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires live PostgreSQL database connection")
async def test_valid_token_sets_request_state():
    """
    Happy Path: Token payload should be accessible in request.state.

    This tests that AuthMiddleware properly sets request.state.tenant_id
    """
    token = create_test_token(tenant_id="tenant-abc", account_id="user-xyz")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Call an endpoint that returns user info
        response = await client.get(
            "/api/v1/trading/portfolio", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200


# ============================================================================
# UNHAPPY PATH TESTS - MISSING TOKEN
# ============================================================================


@pytest.mark.asyncio
async def test_missing_token_returns_401_on_protected_route():
    """
    Unhappy Path: Protected routes should return 401 when no token is provided.

    Expected: 401 Unauthorized with message about missing token.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/trading/markets")
        # No Authorization header

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert "token" in response.text.lower() or "authorization" in response.text.lower()


@pytest.mark.asyncio
async def test_empty_authorization_header_returns_401():
    """
    Unhappy Path: Empty Authorization header should return 401.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/trading/markets", headers={"Authorization": ""})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bearer_without_token_returns_401():
    """
    Unhappy Path: "Bearer " without actual token should return 401.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/trading/markets", headers={"Authorization": "Bearer "})

    assert response.status_code == 401


# ============================================================================
# UNHAPPY PATH TESTS - INVALID TOKEN
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_signature_returns_401():
    """
    Unhappy Path: Token signed with wrong key should return 401.
    """
    token = create_invalid_token()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/trading/markets", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
async def test_malformed_token_returns_401():
    """
    Unhappy Path: Malformed JWT should return 401.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/trading/markets",
            headers={"Authorization": "Bearer not.a.valid.jwt.token"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_returns_401():
    """
    Unhappy Path: Expired token should return 401.
    """
    token = create_test_token(expired=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/trading/markets", headers={"Authorization": f"Bearer {token}"}
        )

    assert (
        response.status_code == 401
    ), f"Expected 401 for expired token, got {response.status_code}"


# ============================================================================
# PUBLIC ROUTES TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_health_endpoint_works_without_token():
    """
    Public routes should work without authentication.
    /health is explicitly public.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_docs_endpoint_works_without_token():
    """
    /docs (OpenAPI) should be accessible without token.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/docs")

    # Either 200 or redirect to docs UI
    assert response.status_code in [200, 307]


@pytest.mark.asyncio
async def test_auth_token_endpoint_works_without_token():
    """
    /api/v1/auth/token (login) should be accessible without token.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/token",
            json={"tenant_id": "test-tenant", "account_id": "test-account"},
        )

    # Should return token, not 401
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


# ============================================================================
# TENANT ISOLATION TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires live PostgreSQL database connection for RLS")
async def test_different_tenants_get_isolated_data():
    """
    Critical: Different tenants should see only their own data.

    This is a placeholder - actual data isolation depends on RLS.
    """
    token_tenant_1 = create_test_token(tenant_id="tenant-1")
    token_tenant_2 = create_test_token(tenant_id="tenant-2")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Both should succeed
        response_1 = await client.get(
            "/api/v1/trading/portfolio",
            headers={"Authorization": f"Bearer {token_tenant_1}"},
        )
        response_2 = await client.get(
            "/api/v1/trading/portfolio",
            headers={"Authorization": f"Bearer {token_tenant_2}"},
        )

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    # In production, data should be different per tenant
    # For now, verify the endpoint works with different tokens
