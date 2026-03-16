"""
Test Runner for Frontend-Backend Wiring Integration Tests

Run all integration tests for the newly registered APIs:
- Auth API
- KYC API
- Settings API
- Competitions API

Usage:
    python backend/tests/integration/run_wiring_tests.py

Or with pytest directly:
    pytest backend/tests/integration/test_auth_api_integration.py -v
    pytest backend/tests/integration/test_kyc_api_integration.py -v
    pytest backend/tests/integration/test_settings_api_integration.py -v
    pytest backend/tests/integration/test_competitions_api_integration.py -v
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

TEST_FILES = [
    "backend/tests/integration/test_auth_api_integration.py",
    "backend/tests/integration/test_kyc_api_integration.py",
    "backend/tests/integration/test_settings_api_integration.py",
    "backend/tests/integration/test_competitions_api_integration.py",
]


def run_tests(verbose: bool = True, fail_fast: bool = False):
    """Run all wiring integration tests."""

    print("=" * 70)
    print("FRONTEND-BACKEND WIRING INTEGRATION TESTS")
    print("=" * 70)
    print()
    print("Testing the following APIs:")
    print("  1. Auth API (/api/v1/auth)")
    print("  2. KYC API (/api/v1/kyc)")
    print("  3. Settings API (/api/v1/settings)")
    print("  4. Competitions API (/api/v1/competitions)")
    print()
    print("All tests use REAL backend integration - NO MOCKS")
    print("=" * 70)
    print()

    cmd = [
        sys.executable, "-m", "pytest",
        *TEST_FILES,
        "-v" if verbose else "",
        "--tb=short",
        "-x" if fail_fast else "",
    ]

    # Remove empty strings
    cmd = [c for c in cmd if c]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=project_root)

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {result.returncode})")
    print("=" * 70)

    return result.returncode


def run_single_test(test_file: str, verbose: bool = True):
    """Run a single test file."""
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v" if verbose else "",
        "--tb=short",
    ]

    cmd = [c for c in cmd if c]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Frontend-Backend Wiring Integration Tests")
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Less verbose output"
    )
    parser.add_argument(
        "--auth-only",
        action="store_true",
        help="Run only Auth API tests"
    )
    parser.add_argument(
        "--kyc-only",
        action="store_true",
        help="Run only KYC API tests"
    )
    parser.add_argument(
        "--settings-only",
        action="store_true",
        help="Run only Settings API tests"
    )
    parser.add_argument(
        "--competitions-only",
        action="store_true",
        help="Run only Competitions API tests"
    )

    args = parser.parse_args()

    # Determine which tests to run
    if args.auth_only:
        sys.exit(run_single_test("backend/tests/integration/test_auth_api_integration.py", verbose=not args.quiet))
    elif args.kyc_only:
        sys.exit(run_single_test("backend/tests/integration/test_kyc_api_integration.py", verbose=not args.quiet))
    elif args.settings_only:
        sys.exit(run_single_test("backend/tests/integration/test_settings_api_integration.py", verbose=not args.quiet))
    elif args.competitions_only:
        sys.exit(run_single_test("backend/tests/integration/test_competitions_api_integration.py", verbose=not args.quiet))
    else:
        sys.exit(run_tests(verbose=not args.quiet, fail_fast=args.fail_fast))
