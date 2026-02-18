from uuid import uuid4

import pytest
from sqlalchemy import text

from backend.api.auth_api import hash_password
from backend.core.database import SessionManager

# ============================================================================
# TEST SUITE
# ============================================================================


@pytest.mark.asyncio
async def test_01_health_check(async_client):
    """Verify API is up and running."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_02_register_happy_path(async_client, unique_email):
    """
    Verify a new user can register.
    This implicitly tests:
    1. public route access
    2. get_admin_db RLS bypass in /register
    """
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Integration Tester",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["tenant_id"].startswith("tenant-")


@pytest.mark.asyncio
async def test_03_login_happy_path(async_client, system_db):
    """
    Verify registered user can login.
    Tests get_admin_db RLS bypass in /login.
    """
    # Setup: Create user manually via system session to ensure control
    email = f"login_test_{uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    tenant_id = f"tenant-{uuid4().hex[:12]}"

    # We use raw SQL for speed and independance from Model changes in this fixture setup
    await system_db.execute(
        text(
            f"""
        INSERT INTO users (id, email, password_hash, tenant_id, role, is_active, created_at)
        VALUES ('{uuid4()}', '{email}', '{hash_password(password)}', '{tenant_id}', 'user', true, now())
    """
        )
    )
    await system_db.commit()

    # Test Login
    response = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] is not None
    assert data["user"]["tenant_id"] == tenant_id

    return data["access_token"], tenant_id


@pytest.mark.asyncio
async def test_04_login_unhappy_path(async_client):
    """Verify login fails with wrong credentials."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_05_auth_middleware_enforcement(async_client):
    """Verify protected routes block unauthenticated access."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_06_rls_isolation_enforcement(system_db):
    """
    CRITICAL ARCHITECTURE TEST:
    Verify that tenant_session CANNOT see data from another tenant.
    """
    # 1. Setup: Create Users in different tenats
    tenant_a = f"tenant-A-{uuid4().hex[:8]}"
    tenant_b = f"tenant-B-{uuid4().hex[:8]}"

    # Insert Data using System Session (Global Access)
    email_a = f"user_a_{uuid4().hex[:8]}@test.com"
    email_b = f"user_b_{uuid4().hex[:8]}@test.com"

    await system_db.execute(
        text(
            f"""
        INSERT INTO users (id, email, tenant_id, role, is_active)
        VALUES ('{uuid4()}', '{email_a}', '{tenant_a}', 'user', true)
    """
        )
    )
    await system_db.execute(
        text(
            f"""
        INSERT INTO users (id, email, tenant_id, role, is_active)
        VALUES ('{uuid4()}', '{email_b}', '{tenant_b}', 'user', true)
    """
        )
    )
    await system_db.commit()

    # 2. Verify: Tenant A Session should ONLY see Tenant A users
    # Note: 'users' table MIGHT be exempt from strict RLS if we moved to 'auth' schema,
    # but based on current audit, policies are generally ON.
    # Actually, RLS on users table IS the issue we fixed for login.
    # BUT, let's test a table that DEFINITELY has RLS, like 'orders' or 'user_preferences' request.

    # Let's use user_preferences as they are strictly RLS'd
    user_a_id = str(uuid4())
    user_b_id = str(uuid4())

    # Create users first
    email_pref_a = f"pref_a_{uuid4().hex[:8]}@test.com"
    email_pref_b = f"pref_b_{uuid4().hex[:8]}@test.com"

    await system_db.execute(
        text(
            f"""
        INSERT INTO users (id, email, tenant_id) VALUES ('{user_a_id}', '{email_pref_a}', '{tenant_a}')
    """
        )
    )
    await system_db.execute(
        text(
            f"""
        INSERT INTO users (id, email, tenant_id) VALUES ('{user_b_id}', '{email_pref_b}', '{tenant_b}')
    """
        )
    )

    # Create preferences
    await system_db.execute(
        text(
            f"""
        INSERT INTO user_preferences (id, user_id, theme) VALUES ('{uuid4()}', '{user_a_id}', 'dark')
    """
        )
    )
    await system_db.execute(
        text(
            f"""
        INSERT INTO user_preferences (id, user_id, theme) VALUES ('{uuid4()}', '{user_b_id}', 'light')
    """
        )
    )
    await system_db.commit()

    # TEST: Access as Tenant A
    async with SessionManager.tenant_session(tenant_a) as session_a:
        # Should see A's preference
        res_a = await session_a.execute(
            text(f"SELECT COUNT(*) FROM user_preferences WHERE user_id = '{user_a_id}'")
        )
        assert res_a.scalar() == 1

        # Should NOT see B's preference (even if we query for it specifically, RLS filters it)
        res_b = await session_a.execute(
            text(f"SELECT COUNT(*) FROM user_preferences WHERE user_id = '{user_b_id}'")
        )
        assert res_b.scalar() == 0


@pytest.mark.asyncio
async def test_07_background_task_context_access(system_db):
    """
    Verify that system_admin_session can access data across tenants.
    This simulates the Market Data Publisher or Admin Dashboard.
    """
    # Create a random tenant and data
    tenant_bg = f"tenant-BG-{uuid4().hex[:8]}"
    user_id = str(uuid4())
    email_bg = f"bg_task_{uuid4().hex[:8]}@test.com"

    await system_db.execute(
        text(
            f"""
        INSERT INTO users (id, email, tenant_id) VALUES ('{user_id}', '{email_bg}', '{tenant_bg}')
    """
        )
    )
    await system_db.execute(
        text(
            f"""
        INSERT INTO user_preferences (id, user_id, theme) VALUES ('{uuid4()}', '{user_id}', 'system')
    """
        )
    )
    await system_db.commit()

    # Verify System Admin can see it
    async with SessionManager.system_admin_session() as admin_session:
        res = await admin_session.execute(
            text(f"SELECT COUNT(*) FROM user_preferences WHERE user_id = '{user_id}'")
        )
        assert res.scalar() == 1
