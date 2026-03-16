"""
Simple route verification tests.
Checks that all wired API routes exist and respond.
"""

import os
import sys

# Set minimal env
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-wiring-tests-32-chars-long"
os.environ["AUTH_DISABLED"] = "true"
os.environ["ENV"] = "development"

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_routes():
    """Test that all API routes are registered."""
    print("=" * 70)
    print("API ROUTE VERIFICATION")
    print("=" * 70)
    print()

    try:
        from backend.api.main import app

        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                # Skip internal routes
                if route.path.startswith('/api'):
                    for method in route.methods:
                        if method != 'HEAD':
                            routes.append((method, route.path))

        print(f"Found {len(routes)} API routes")
        print()

        # Check for our new routes
        checks = [
            ("POST", "/api/v1/auth/register"),
            ("POST", "/api/v1/auth/login"),
            ("GET", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/token"),
            ("GET", "/api/v1/kyc/status"),
            ("GET", "/api/v1/kyc/required"),
            ("POST", "/api/v1/kyc/submit"),
            ("POST", "/api/v1/kyc/documents"),
            ("GET", "/api/v1/settings/all"),
            ("GET", "/api/v1/settings/profile"),
            ("PUT", "/api/v1/settings/profile"),
            ("GET", "/api/v1/settings/notifications"),
            ("PUT", "/api/v1/settings/notifications"),
            ("GET", "/api/v1/settings/security"),
            ("POST", "/api/v1/settings/security/2fa"),
            ("POST", "/api/v1/settings/security/password"),
            ("GET", "/api/v1/settings/appearance"),
            ("PUT", "/api/v1/settings/appearance"),
            ("GET", "/api/v1/settings/preferences"),
            ("PUT", "/api/v1/settings/preferences"),
            ("GET", "/api/v1/settings/api-keys"),
            ("POST", "/api/v1/settings/api-keys"),
            ("GET", "/api/v1/competitions/tournaments"),
            ("GET", "/api/v1/competitions/league-info"),
            ("POST", "/api/v1/competitions/enter"),
            ("GET", "/api/v1/competitions/leaderboard"),
            ("GET", "/api/v1/competitions/badges/{competitor_id}"),
            ("GET", "/api/v1/competitions/available-badges"),
        ]

        passed = 0
        failed = 0

        for method, path in checks:
            found = (method, path) in routes
            status = "OK" if found else "MISSING"
            symbol = "[x]" if found else "[ ]"
            print(f"  {symbol} {method:6} {path:45} {status}")
            if found:
                passed += 1
            else:
                failed += 1

        print()
        print("=" * 70)
        print(f"RESULT: {passed}/{len(checks)} routes verified")

        if failed == 0:
            print("SUCCESS: All API routes are registered!")
        else:
            print(f"WARNING: {failed} routes not found")

        print("=" * 70)

        # Show all registered auth/kyc/settings/competitions routes
        print()
        print("All Auth/KYC/Settings/Competitions routes:")
        relevant = [r for r in routes if any(x in r[1] for x in ['/auth', '/kyc', '/settings', '/competitions'])]
        for method, path in sorted(relevant):
            print(f"  {method:6} {path}")

        return failed == 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_routes()
    sys.exit(0 if success else 1)
