#!/usr/bin/env python3
"""
Standalone wiring integration tests with SQLite.
No conftest.py dependencies - runs completely standalone.
"""

import os
import sys
import asyncio
from uuid import uuid4

# CRITICAL: Set environment BEFORE any backend imports
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-integration-tests-12345-minimum-32-chars"
os.environ["AUTH_DISABLED"] = "true"
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DISABLE_RLS"] = "true"  # Try to disable RLS

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def setup_database():
    """Setup SQLite database with tables."""
    from backend.db_models.user_settings import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine


async def run_tests():
    """Run all wiring tests."""
    print("=" * 70)
    print("STANDALONE WIRING INTEGRATION TESTS")
    print("=" * 70)
    print()

    # Setup database
    print("Setting up SQLite database...")
    try:
        engine = await setup_database()
        print("✓ Database setup complete")
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return 1

    # Import app
    print("Loading FastAPI app...")
    try:
        from backend.api.main import app
        print("✓ App loaded")
    except Exception as e:
        print(f"✗ App load failed: {e}")
        return 1

    # Create test client
    print("Creating test client...")
    transport = ASGITransport(app=app)

    passed = 0
    failed = 0

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("✓ Test client ready")
        print()
        print("=" * 70)
        print()

        # TEST 1: Health check
        print("TEST 1: API Health Check")
        try:
            response = await client.get("/api/v1/health")
            if response.status_code == 200:
                print(f"  ✓ Health endpoint OK (HTTP {response.status_code})")
                passed += 1
            else:
                print(f"  ✗ Health endpoint failed (HTTP {response.status_code})")
                failed += 1
        except Exception as e:
            print(f"  ✗ Health endpoint error: {e}")
            failed += 1

        # TEST 2: Auth Register
        print("\nTEST 2: Auth Register")
        test_email = f"test_{uuid4().hex[:8]}@example.com"
        try:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": test_email,
                    "password": "SecurePass123!",
                    "full_name": "Test User"
                }
            )
            if response.status_code == 201:
                data = response.json()
                if "access_token" in data and "user" in data:
                    print(f"  ✓ Register OK (HTTP {response.status_code})")
                    print(f"    User ID: {data['user']['id'][:8]}...")
                    print(f"    Tenant ID: {data['user']['tenant_id'][:8]}...")
                    passed += 1
                    token = data["access_token"]
                else:
                    print(f"  ✗ Register response missing fields")
                    failed += 1
            else:
                print(f"  ✗ Register failed (HTTP {response.status_code})")
                print(f"    Response: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  ✗ Register error: {e}")
            failed += 1
            token = None

        # TEST 3: Auth Login
        print("\nTEST 3: Auth Login")
        try:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_email,
                    "password": "SecurePass123!"
                }
            )
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    print(f"  ✓ Login OK (HTTP {response.status_code})")
                    token = data["access_token"]
                    passed += 1
                else:
                    print(f"  ✗ Login response missing token")
                    failed += 1
            else:
                print(f"  ✗ Login failed (HTTP {response.status_code})")
                print(f"    Response: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  ✗ Login error: {e}")
            failed += 1

        # TEST 4: Auth Me (with token)
        print("\nTEST 4: Auth Me")
        if token:
            try:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ Me OK (HTTP {response.status_code})")
                    print(f"    Email: {data.get('email', 'N/A')}")
                    passed += 1
                else:
                    print(f"  ✗ Me failed (HTTP {response.status_code})")
                    print(f"    Response: {response.text[:200]}")
                    failed += 1
            except Exception as e:
                print(f"  ✗ Me error: {e}")
                failed += 1
        else:
            print("  ⊘ Skipped (no token)")

        # TEST 5: KYC Status
        print("\nTEST 5: KYC Status")
        try:
            response = await client.get("/api/v1/kyc/status")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ KYC Status OK (HTTP {response.status_code})")
                print(f"    Status: {data.get('status', 'N/A')}")
                print(f"    Enabled: {data.get('enabled', 'N/A')}")
                passed += 1
            else:
                print(f"  ✗ KYC Status failed (HTTP {response.status_code})")
                print(f"    Response: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  ✗ KYC Status error: {e}")
            failed += 1

        # TEST 6: KYC Required
        print("\nTEST 6: KYC Required")
        try:
            response = await client.get("/api/v1/kyc/required")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ KYC Required OK (HTTP {response.status_code})")
                print(f"    Required: {data.get('required', 'N/A')}")
                passed += 1
            else:
                print(f"  ✗ KYC Required failed (HTTP {response.status_code})")
                failed += 1
        except Exception as e:
            print(f"  ✗ KYC Required error: {e}")
            failed += 1

        # TEST 7: Competitions Tournaments
        print("\nTEST 7: Competitions Tournaments")
        try:
            response = await client.get("/api/v1/competitions/tournaments?status=active")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Competitions Tournaments OK (HTTP {response.status_code})")
                print(f"    Count: {data.get('count', 'N/A')}")
                passed += 1
            else:
                print(f"  ✗ Competitions Tournaments failed (HTTP {response.status_code})")
                print(f"    Response: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  ✗ Competitions Tournaments error: {e}")
            failed += 1

        # TEST 8: Competitions League Info
        print("\nTEST 8: Competitions League Info")
        try:
            response = await client.get("/api/v1/competitions/league-info")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Competitions League Info OK (HTTP {response.status_code})")
                print(f"    Tiers: {list(data.keys())[:3]}...")
                passed += 1
            else:
                print(f"  ✗ Competitions League Info failed (HTTP {response.status_code})")
                print(f"    Response: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  ✗ Competitions League Info error: {e}")
            failed += 1

        # TEST 9: Competitions Leaderboard
        print("\nTEST 9: Competitions Leaderboard")
        try:
            response = await client.get("/api/v1/competitions/leaderboard")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Competitions Leaderboard OK (HTTP {response.status_code})")
                print(f"    Total entries: {data.get('total', 'N/A')}")
                passed += 1
            else:
                print(f"  ✗ Competitions Leaderboard failed (HTTP {response.status_code})")
                print(f"    Response: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  ✗ Competitions Leaderboard error: {e}")
            failed += 1

        # TEST 10: Settings All (requires auth)
        print("\nTEST 10: Settings All")
        if token:
            try:
                response = await client.get(
                    "/api/v1/settings/all",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ Settings All OK (HTTP {response.status_code})")
                    print(f"    Sections: {list(data.keys())}")
                    passed += 1
                else:
                    print(f"  ✗ Settings All failed (HTTP {response.status_code})")
                    print(f"    Response: {response.text[:200]}")
                    failed += 1
            except Exception as e:
                print(f"  ✗ Settings All error: {e}")
                failed += 1
        else:
            print("  ⊘ Skipped (no token)")

    # Summary
    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)

    await engine.dispose()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
