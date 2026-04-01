"""
Integration Tests for Auth API - Real Backend Integration

Tests use the actual FastAPI app and real database.
No mocks are used for the API layer - all requests are real HTTP calls.
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestAuthAPIIntegration:
    """Full integration tests for Authentication API with real backend."""

    async def test_register_new_user_success(
        self, async_client: AsyncClient, unique_email: str
    ):
        """Test successful user registration with real database insert."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == unique_email
        assert data["user"]["full_name"] == "Test User"
        assert "tenant_id" in data["user"]
        assert "id" in data["user"]

        # Verify JWT token is valid format (3 parts separated by dots)
        token_parts = data["access_token"].split(".")
        assert len(token_parts) == 3

    async def test_register_duplicate_email_fails(
        self, async_client: AsyncClient, unique_email: str
    ):
        """Test that registering with duplicate email returns proper error."""
        # First registration
        response1 = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "First User",
            },
        )
        assert response1.status_code == 201

        # Second registration with same email should fail
        response2 = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "DifferentPass456!",
                "full_name": "Second User",
            },
        )

        assert response2.status_code == 400
        data = response2.json()
        assert "detail" in data
        assert "already registered" in data["detail"].lower()

    async def test_login_success(self, async_client: AsyncClient, unique_email: str):
        """Test successful login with real credentials."""
        password = "SecurePass123!"

        # Register first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "Test User",
            },
        )

        # Login
        response = await async_client.post(
            "/api/v1/auth/login", json={"email": unique_email, "password": password}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == unique_email

    async def test_login_wrong_password_fails(
        self, async_client: AsyncClient, unique_email: str
    ):
        """Test login with wrong password returns 401."""
        # Register first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "CorrectPass123!",
                "full_name": "Test User",
            },
        )

        # Login with wrong password
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "WrongPass456!"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_nonexistent_user_fails(self, async_client: AsyncClient):
        """Test login with non-existent user returns 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent_user_12345@test.com",
                "password": "SomePass123!",
            },
        )

        assert response.status_code == 401

    async def test_get_me_with_valid_token(
        self, async_client: AsyncClient, unique_email: str
    ):
        """Test /me endpoint with valid JWT token."""
        # Register and get token
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "Test User",
            },
        )

        token = register_response.json()["access_token"]

        # Get current user
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == unique_email
        assert "id" in data
        assert "tenant_id" in data
        assert "role" in data

    async def test_get_me_without_token_fails(self, async_client: AsyncClient):
        """Test /me endpoint without token returns 401."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_get_me_with_invalid_token_fails(self, async_client: AsyncClient):
        """Test /me endpoint with invalid token returns 401."""
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    async def test_legacy_token_endpoint(self, async_client: AsyncClient):
        """Test legacy token endpoint for backward compatibility."""
        response = await async_client.post(
            "/api/v1/auth/token",
            json={"tenant_id": "test-tenant-123", "account_id": "test-account-456"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_validation_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password fails validation."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"test_{__import__('uuid').uuid4().hex[:8]}@example.com",
                "password": "123",  # Too short
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_register_validation_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email fails validation."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_complete_auth_flow(
        self, async_client: AsyncClient, unique_email: str
    ):
        """Test complete authentication flow: register -> login -> me -> token reuse."""
        password = "SecurePass123!"

        # Step 1: Register
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "Integration Test User",
            },
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        user_id = register_data["user"]["id"]
        tenant_id = register_data["user"]["tenant_id"]

        # Step 2: Login
        login_response = await async_client.post(
            "/api/v1/auth/login", json={"email": unique_email, "password": password}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]

        # Step 3: Get current user with token
        me_response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()

        # Verify consistency
        assert me_data["id"] == user_id
        assert me_data["tenant_id"] == tenant_id
        assert me_data["email"] == unique_email

        # Step 4: Verify token works multiple times
        for _ in range(3):
            check_response = await async_client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert check_response.status_code == 200
