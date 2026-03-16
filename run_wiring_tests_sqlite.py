#!/usr/bin/env python3
"""
Run wiring integration tests with SQLite backend.
No PostgreSQL required!
"""

import os
import sys
import subprocess

# Set SQLite for testing BEFORE anything else
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-integration-tests-12345-minimum-32-chars"
os.environ["AUTH_DISABLED"] = "true"
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["POSTGRES_USER"] = "test"
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["POSTGRES_DB"] = "test"

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

TEST_FILES = [
    "backend/tests/integration/test_auth_api_integration.py",
    "backend/tests/integration/test_kyc_api_integration.py",
    "backend/tests/integration/test_settings_api_integration.py",
    "backend/tests/integration/test_competitions_api_integration.py",
    "backend/tests/integration/test_wiring_e2e_integration.py",
]


def main():
    print("=" * 70)
    print("FRONTEND-BACKEND WIRING INTEGRATION TESTS (SQLite)")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  Database: SQLite (in-memory)")
    print("  Auth: Disabled (test mode)")
    print("  JWT Secret: Set")
    print()
    print("Testing:")
    print("  1. Auth API (register, login, me, token)")
    print("  2. KYC API (status, submit, documents)")
    print("  3. Settings API (profile, notifications, security, preferences)")
    print("  4. Competitions API (tournaments, leagues, leaderboard)")
    print("  5. E2E Integration (complete user journey)")
    print()
    print("=" * 70)
    print()

    cmd = [
        sys.executable, "-m", "pytest",
        *TEST_FILES,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=project_root, env=os.environ.copy())

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("ALL TESTS PASSED!")
    else:
        print(f"TESTS FAILED (exit code: {result.returncode})")
    print("=" * 70)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
