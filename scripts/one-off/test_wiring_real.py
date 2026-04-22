#!/usr/bin/env python3
"""
Real integration tests with live backend.
Tests actual HTTP endpoints.
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Test configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"


def make_request(method, path, data=None, headers=None):
    """Make HTTP request."""
    url = f"{API_URL}{path}"
    req = urllib.request.Request(url, method=method)

    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    if data and method in ["POST", "PUT"]:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8')) if e.read() else {}
    except Exception as e:
        return None, str(e)


def test_health():
    """Test health endpoint."""
    status, data = make_request("GET", "/health")
    if status == 200:
        print(f"  ✅ Health check: {data.get('status', 'OK')}")
        return True
    else:
        print(f"  ❌ Health check failed: HTTP {status}")
        return False


def test_kyc_endpoints():
    """Test KYC endpoints."""
    print("\n📋 Testing KYC API...")

    # Test KYC status
    status, data = make_request("GET", "/kyc/status")
    if status == 200:
        print(f"  ✅ GET /kyc/status - Status: {data.get('status')}")
    else:
        print(f"  ❌ GET /kyc/status failed: HTTP {status}")
        return False

    # Test KYC required
    status, data = make_request("GET", "/kyc/required")
    if status == 200:
        print(f"  ✅ GET /kyc/required - Required: {data.get('required')}")
    else:
        print(f"  ❌ GET /kyc/required failed: HTTP {status}")
        return False

    return True


def test_competitions_endpoints():
    """Test Competitions endpoints."""
    print("\n🏆 Testing Competitions API...")

    # Test tournaments
    status, data = make_request("GET", "/competitions/tournaments?status=active")
    if status == 200:
        print(f"  ✅ GET /competitions/tournaments - Count: {data.get('count', 0)}")
    else:
        print(f"  ❌ GET /competitions/tournaments failed: HTTP {status}")
        return False

    # Test league info
    status, data = make_request("GET", "/competitions/league-info")
    if status == 200:
        tiers = list(data.keys())[:3]
        print(f"  ✅ GET /competitions/league-info - Tiers: {tiers}")
    else:
        print(f"  ❌ GET /competitions/league-info failed: HTTP {status}")
        return False

    # Test leaderboard
    status, data = make_request("GET", "/competitions/leaderboard")
    if status == 200:
        print(f"  ✅ GET /competitions/leaderboard - Entries: {data.get('total', 0)}")
    else:
        print(f"  ❌ GET /competitions/leaderboard failed: HTTP {status}")
        return False

    # Test badges
    status, data = make_request("GET", "/competitions/available-badges")
    if status == 200:
        print(f"  ✅ GET /competitions/available-badges - Total: {data.get('total', 0)}")
    else:
        print(f"  ❌ GET /competitions/available-badges failed: HTTP {status}")
        return False

    return True


def test_auth_endpoints():
    """Test Auth endpoints."""
    print("\n🔐 Testing Auth API...")

    # Test register
    import uuid
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    status, data = make_request("POST", "/auth/register", {
        "email": test_email,
        "password": "SecurePass123!",
        "full_name": "Test User"
    })

    if status == 201:
        print(f"  ✅ POST /auth/register - User created")
        token = data.get('access_token')
    else:
        print(f"  ❌ POST /auth/register failed: HTTP {status}, {data}")
        return False

    # Test login
    status, data = make_request("POST", "/auth/login", {
        "email": test_email,
        "password": "SecurePass123!"
    })

    if status == 200:
        print(f"  ✅ POST /auth/login - Login successful")
        token = data.get('access_token')
    else:
        print(f"  ❌ POST /auth/login failed: HTTP {status}")
        return False

    # Test me endpoint
    status, data = make_request("GET", "/auth/me", headers={"Authorization": f"Bearer {token}"})
    if status == 200:
        print(f"  ✅ GET /auth/me - User: {data.get('email')}")
    else:
        print(f"  ❌ GET /auth/me failed: HTTP {status}")
        return False

    return token


def test_settings_endpoints(token):
    """Test Settings endpoints."""
    print("\n⚙️  Testing Settings API...")

    if not token:
        print("  ⚠️  Skipping (no auth token)")
        return True

    # Test get all settings
    status, data = make_request("GET", "/settings/all", headers={"Authorization": f"Bearer {token}"})
    if status == 200:
        print(f"  ✅ GET /settings/all - Sections: {list(data.keys())}")
    else:
        print(f"  ❌ GET /settings/all failed: HTTP {status}")
        return False

    # Test update profile
    status, data = make_request("PUT", "/settings/profile", {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com"
    }, headers={"Authorization": f"Bearer {token}"})

    if status == 200:
        print(f"  ✅ PUT /settings/profile - Updated")
    else:
        print(f"  ❌ PUT /settings/profile failed: HTTP {status}")
        return False

    return True


def main():
    print("=" * 70)
    print("LIVE INTEGRATION TESTS - Frontend-Backend Wiring")
    print("=" * 70)
    print(f"\nBase URL: {BASE_URL}")
    print()

    passed = 0
    failed = 0

    # Test 1: Health
    if test_health():
        passed += 1
    else:
        failed += 1
        print("\n⚠️  Backend not accessible, stopping tests")
        print("Make sure backend is running on http://localhost:8000")
        return 1

    # Test 2: KYC
    if test_kyc_endpoints():
        passed += 1
    else:
        failed += 1

    # Test 3: Competitions
    if test_competitions_endpoints():
        passed += 1
    else:
        failed += 1

    # Test 4: Auth
    token = test_auth_endpoints()
    if token:
        passed += 1
    else:
        failed += 1

    # Test 5: Settings
    if test_settings_endpoints(token):
        passed += 1
    else:
        failed += 1

    # Summary
    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
