"""
Test backend by importing and running tests directly.
"""
import os
import sys

# MUST set these BEFORE importing backend
os.environ["JWT_SECRET_KEY"] = "65a2ed0b53625014a011b6882a2ed5df15d36d6843a61904c68102660bb3b744"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://trader:pIu4r4xm8wel5_vBkKYi_mjelL4Hp35E@localhost:5432/trading_db"
os.environ["AUTH_DISABLED"] = "true"
os.environ["ENV"] = "development"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from uuid import uuid4


async def test_backend():
    """Test backend endpoints."""
    print("=" * 70)
    print("DIRECT BACKEND INTEGRATION TESTS")
    print("=" * 70)
    print()

    # Import app
    print("Loading FastAPI app...")
    from backend.api.main import app
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)

    passed = 0
    failed = 0
    token = None

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("[OK] App loaded\n")

        # Test 1: Health
        print("TEST 1: Health Check")
        try:
            resp = await client.get("/api/v1/health")
            if resp.status_code == 200:
                print(f"  [OK] /api/v1/health - {resp.json().get('status', 'OK')}")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/health - HTTP {resp.status_code}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/health - {e}")
            failed += 1

        # Test 2: KYC Status
        print("\nTEST 2: KYC Status")
        try:
            resp = await client.get("/api/v1/kyc/status")
            if resp.status_code == 200:
                print(f"  [OK] /api/v1/kyc/status - Status: {resp.json().get('status')}")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/kyc/status - HTTP {resp.status_code}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/kyc/status - {e}")
            failed += 1

        # Test 3: KYC Required
        print("\nTEST 3: KYC Required")
        try:
            resp = await client.get("/api/v1/kyc/required")
            if resp.status_code == 200:
                print(f"  [OK] /api/v1/kyc/required - Required: {resp.json().get('required')}")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/kyc/required - HTTP {resp.status_code}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/kyc/required - {e}")
            failed += 1

        # Test 4: Competitions Tournaments
        print("\nTEST 4: Competitions Tournaments")
        try:
            resp = await client.get("/api/v1/competitions/tournaments?status=active")
            if resp.status_code == 200:
                print(f"  [OK] /api/v1/competitions/tournaments - Count: {resp.json().get('count')}")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/competitions/tournaments - HTTP {resp.status_code}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/competitions/tournaments - {e}")
            failed += 1

        # Test 5: Competitions League Info
        print("\nTEST 5: Competitions League Info")
        try:
            resp = await client.get("/api/v1/competitions/league-info")
            if resp.status_code == 200:
                tiers = list(resp.json().keys())[:3]
                print(f"  [OK] /api/v1/competitions/league-info - Tiers: {tiers}")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/competitions/league-info - HTTP {resp.status_code}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/competitions/league-info - {e}")
            failed += 1

        # Test 6: Competitions Leaderboard
        print("\nTEST 6: Competitions Leaderboard")
        try:
            resp = await client.get("/api/v1/competitions/leaderboard")
            if resp.status_code == 200:
                print(f"  [OK] /api/v1/competitions/leaderboard - Total: {resp.json().get('total')}")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/competitions/leaderboard - HTTP {resp.status_code}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/competitions/leaderboard - {e}")
            failed += 1

        # Test 7: Auth Register
        print("\nTEST 7: Auth Register")
        test_email = f"test_{uuid4().hex[:8]}@example.com"
        try:
            resp = await client.post("/api/v1/auth/register", json={
                "email": test_email,
                "password": "SecurePass123!",
                "full_name": "Test User"
            })
            if resp.status_code == 201:
                token = resp.json().get('access_token')
                print(f"  [OK] /api/v1/auth/register - Token received")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/auth/register - HTTP {resp.status_code}: {resp.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/auth/register - {e}")
            failed += 1

        # Test 8: Auth Login
        print("\nTEST 8: Auth Login")
        try:
            resp = await client.post("/api/v1/auth/login", json={
                "email": test_email,
                "password": "SecurePass123!"
            })
            if resp.status_code == 200:
                token = resp.json().get('access_token')
                print(f"  [OK] /api/v1/auth/login - Token received")
                passed += 1
            else:
                print(f"  [FAIL] /api/v1/auth/login - HTTP {resp.status_code}: {resp.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"  [FAIL] /api/v1/auth/login - {e}")
            failed += 1

        # Test 9: Auth Me
        print("\nTEST 9: Auth Me")
        if token:
            try:
                resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200:
                    print(f"  [OK] /api/v1/auth/me - User: {resp.json().get('email')}")
                    passed += 1
                else:
                    print(f"  [FAIL] /api/v1/auth/me - HTTP {resp.status_code}")
                    failed += 1
            except Exception as e:
                print(f"  [FAIL] /api/v1/auth/me - {e}")
                failed += 1
        else:
            print("  [SKIP] Skipped (no token)")

        # Test 10: Settings All
        print("\nTEST 10: Settings All")
        if token:
            try:
                resp = await client.get("/api/v1/settings/all", headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200:
                    sections = list(resp.json().keys())
                    print(f"  [OK] /api/v1/settings/all - Sections: {sections}")
                    passed += 1
                else:
                    print(f"  [FAIL] /api/v1/settings/all - HTTP {resp.status_code}: {resp.text[:200]}")
                    failed += 1
            except Exception as e:
                print(f"  [FAIL] /api/v1/settings/all - {e}")
                failed += 1
        else:
            print("  ⊘ Skipped (no token)")

        # Test 11: Settings Profile Update
        print("\nTEST 11: Settings Profile Update")
        if token:
            try:
                resp = await client.put("/api/v1/settings/profile",
                    json={"first_name": "Test", "last_name": "User", "email": test_email},
                    headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200:
                    print(f"  [OK] /api/v1/settings/profile - Updated")
                    passed += 1
                else:
                    print(f"  [FAIL] /api/v1/settings/profile - HTTP {resp.status_code}: {resp.text[:200]}")
                    failed += 1
            except Exception as e:
                print(f"  [FAIL] /api/v1/settings/profile - {e}")
                failed += 1
        else:
            print("  ⊘ Skipped (no token)")

    # Summary
    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    if failed == 0:
        print("[SUCCESS] ALL TESTS PASSED!")
    else:
        print(f"[WARNING] {failed} TEST(S) FAILED")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_backend())
    sys.exit(exit_code)
