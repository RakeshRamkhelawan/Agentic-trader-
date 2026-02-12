
import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy import text
from backend.api.auth_api import hash_password
from backend.core.database import SessionManager

@pytest.mark.asyncio
async def test_08_register_duplicate_email(async_client, unique_email):
    """Verify 400 error when registering an already registered email."""
    # Register first user
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Original User"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    # Try to register same email again
    response_duplicate = await async_client.post("/api/v1/auth/register", json=payload)
    assert response_duplicate.status_code == 400
    assert "Already registered" in response_duplicate.json()["detail"] or "Email already registered" in response_duplicate.json()["detail"]

@pytest.mark.asyncio
async def test_09_register_weak_password(async_client):
    """Verify 422 validation error for weak/short passwords."""
    payload = {
        "email": f"weak_pass_{uuid4().hex[:8]}@example.com",
        "password": "123",  # Too short
        "full_name": "Weak Password User"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    # Fastapi/Pydantic returns 422 for validation errors
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_10_protected_endpoint_with_valid_token(async_client, system_db):
    """Verify access to /me with a valid token."""
    # Create user and get token via login
    email = f"me_test_{uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    tenant_id = f"tenant-{uuid4().hex[:12]}"
    
    await system_db.execute(text(f"""
        INSERT INTO users (id, email, password_hash, tenant_id, role, is_active, created_at)
        VALUES ('{uuid4()}', '{email}', '{hash_password(password)}', '{tenant_id}', 'user', true, now())
    """))
    await system_db.commit()
    
    # Login
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    
    # Access /me
    response = await async_client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["tenant_id"] == tenant_id

@pytest.mark.asyncio
async def test_11_invalid_jwt_token(async_client):
    """Verify 401 response for malformed JWT token."""
    response = await async_client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer invalid.token.structure"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_12_expired_jwt_token(async_client):
    """Verify 401 response for expired JWT token (simulated)."""
    # Create an expired token manually
    from jose import jwt
    from datetime import datetime, timedelta, timezone
    
    # We need the secret key. In tests it might be the default dev key.
    try:
        from backend.core.config.settings import settings
        secret = settings.SECRET_KEY
    except:
        secret = "dev-secret-key"
        
    expired_payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "iss": "agentic-trader"
    }
    token = jwt.encode(expired_payload, secret, algorithm="HS256")
    
    response = await async_client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 401
