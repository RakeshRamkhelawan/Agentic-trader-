#!/usr/bin/env python3
"""
Run integration tests against the actual backend with real database.
This script runs tests directly against the FastAPI app.
"""

import os
import sys
import subprocess

# Set environment variables
os.environ["JWT_SECRET_KEY"] = "65a2ed0b53625014a011b6882a2ed5df15d36d6843a61904c68102660bb3b744"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://trader:pIu4r4xm8wel5_vBkKYi_mjelL4Hp35E@localhost:5432/trading_db"
os.environ["AUTH_DISABLED"] = "true"
os.environ["ENV"] = "test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def check_backend():
    """Check if backend is accessible."""
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8000/api/v1/health", timeout=5)
        return True
    except:
        return False


def main():
    print("=" * 70)
    print("INTEGRATION TESTS - Frontend-Backend Wiring")
    print("=" * 70)
    print()

    # Check backend
    print("Checking backend availability...")
    if check_backend():
        print("✅ Backend is running on http://localhost:8000")
    else:
        print("⚠️  Backend not accessible on http://localhost:8000")
        print("   Tests will run against FastAPI app directly via ASGI transport")
    print()

    # Test files to run
    test_files = [
        "backend/tests/integration/test_auth_api_integration.py",
        "backend/tests/integration/test_kyc_api_integration.py",
        "backend/tests/integration/test_settings_api_integration.py",
        "backend/tests/integration/test_competitions_api_integration.py",
        "backend/tests/integration/test_wiring_e2e_integration.py",
    ]

    print("Running tests:")
    for f in test_files:
        print(f"  - {f}")
    print()

    # Run tests
    cmd = [
        sys.executable, "-m", "pytest",
        *test_files,
        "-v",
        "--tb=short",
        "--timeout=300",
    ]

    # Filter out problematic conftest.py by running from different location
    env = os.environ.copy()

    result = subprocess.run(cmd, cwd=project_root, env=env)

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {result.returncode})")
    print("=" * 70)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
