"""
TDD Tests for User Registration & Login System.

RED PHASE: These tests should FAIL initially because:
- User model lacks password_hash field
- /register and /login endpoints don't exist yet

Tests cover:
- Happy path: Successful registration and login
- Unhappy paths: Duplicate email, invalid input, wrong password
"""
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta, timezone

# Import the app
from backend.api.main import app

# ============================================================================
# TEST DATA
# ============================================================================

TEST_USER = {
    "email": "testuser@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
}

ADMIN_USER = {
    "email": "admin@agentic-trader.com",
    "password": "admin@123"
}

DEMO_USER = {
    "email": "demo@agentic-trader.com",
    "password": "demo@123"
}


# ============================================================================
# REGISTRATION TESTS - HAPPY PATH
# ============================================================================

@pytest.mark.asyncio
async def test_register_new_user_returns_jwt():
    """
    Happy Path: Registering a new user should return JWT token.
    
    Expected: 
    - 201 Created
    - Response contains access_token
    - Response contains user info
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"newuser_{datetime.now().timestamp()}@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"].endswith("@example.com")


@pytest.mark.asyncio
async def test_register_creates_user_with_correct_tenant():
    """
    Happy Path: Registered user should have unique tenant_id.
    """
    unique_email = f"tenant_test_{datetime.now().timestamp()}@example.com"
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "Tenant Test User"
            }
        )
    
    assert response.status_code == 201
    data = response.json()
    # Tenant ID should be in the JWT claims or user object
    assert "user" in data
    assert data["user"].get("tenant_id") is not None


# ============================================================================
# REGISTRATION TESTS - UNHAPPY PATH
# ============================================================================

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_400():
    """
    Unhappy Path: Registering with existing email should fail.
    """
    unique_email = f"duplicate_{datetime.now().timestamp()}@example.com"
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        # First registration
        response1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "First User"
            }
        )
        assert response1.status_code == 201
        
        # Second registration with same email
        response2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "DifferentPass456!",
                "full_name": "Second User"
            }
        )
    
    assert response2.status_code == 400, f"Expected 400, got {response2.status_code}"
    assert "email" in response2.text.lower() or "exists" in response2.text.lower()


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422():
    """
    Unhappy Path: Invalid email format should fail validation.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Invalid Email User"
            }
        )
    
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_register_weak_password_returns_400():
    """
    Unhappy Path: Weak password should be rejected.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"weakpass_{datetime.now().timestamp()}@example.com",
                "password": "123",  # Too short/weak
                "full_name": "Weak Password User"
            }
        )
    
    # Either 400 (business rule) or 422 (validation)
    assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"


@pytest.mark.asyncio
async def test_register_missing_fields_returns_422():
    """
    Unhappy Path: Missing required fields should fail.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "missing@example.com"
                # Missing password and full_name
            }
        )
    
    assert response.status_code == 422


# ============================================================================
# LOGIN TESTS - HAPPY PATH
# ============================================================================

@pytest.mark.asyncio
async def test_login_valid_credentials_returns_jwt():
    """
    Happy Path: Login with valid credentials returns JWT.
    """
    unique_email = f"login_test_{datetime.now().timestamp()}@example.com"
    password = "LoginTestPass123!"
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        # First register
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "Login Test User"
            }
        )
        assert reg_response.status_code == 201
        
        # Then login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": password
            }
        )
    
    assert login_response.status_code == 200, f"Expected 200, got {login_response.status_code}"
    data = login_response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_returns_user_info():
    """
    Happy Path: Login response includes user information.
    """
    unique_email = f"userinfo_{datetime.now().timestamp()}@example.com"
    password = "UserInfoPass123!"
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        # Register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "User Info Test"
            }
        )
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == unique_email


# ============================================================================
# LOGIN TESTS - UNHAPPY PATH
# ============================================================================

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401():
    """
    Unhappy Path: Wrong password should return 401.
    """
    unique_email = f"wrongpass_{datetime.now().timestamp()}@example.com"
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        # Register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "CorrectPassword123!",
                "full_name": "Wrong Pass Test"
            }
        )
        
        # Login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "WrongPassword456!"
            }
        )
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
async def test_login_nonexistent_user_returns_401():
    """
    Unhappy Path: Login with non-existent email should return 401.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@nowhere.com",
                "password": "SomePassword123!"
            }
        )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_password_returns_422():
    """
    Unhappy Path: Missing password field should fail.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com"
                # Missing password
            }
        )
    
    assert response.status_code == 422


# ============================================================================
# SEED USER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_admin_user_can_login():
    """
    Seed User Test: Admin user should be able to login.
    
    This will fail until seed users are created.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json=ADMIN_USER
        )
    
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data.get("user", {}).get("role") == "admin"


@pytest.mark.asyncio
async def test_demo_user_can_login():
    """
    Seed User Test: Demo user should be able to login.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json=DEMO_USER
        )
    
    assert response.status_code == 200, f"Demo login failed: {response.text}"
    data = response.json()
    assert "access_token" in data


# ============================================================================
# TOKEN VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_token_from_login_works_for_protected_route():
    """
    Integration Test: Token from login should work for protected routes.
    """
    unique_email = f"token_test_{datetime.now().timestamp()}@example.com"
    password = "TokenTestPass123!"
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        # Register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "full_name": "Token Test User"
            }
        )
        
        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password}
        )
        token = login_response.json().get("access_token")
        
        # Use token for protected route
        protected_response = await client.get(
            "/api/v1/trading/markets",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert protected_response.status_code == 200, f"Protected route failed: {protected_response.text}"
