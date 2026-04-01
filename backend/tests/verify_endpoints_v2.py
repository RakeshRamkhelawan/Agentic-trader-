import sys

import requests

BASE_URL = "http://localhost:8003/api/v1"


def print_result(name, success, data=None):
    if success:
        print(f"✅ {name}: SUCCESS")
    else:
        print(f"❌ {name}: FAILED")
        if data:
            print(f"   Reason: {data}")


def verify_system():
    print("🚀 Starting API Verification...")

    # 1. Health Check
    try:
        r = requests.get("http://localhost:8003/health", timeout=10)
        if r.status_code == 200:
            print_result("Health Check", True)
        else:
            print_result("Health Check", False, r.text)
            sys.exit(1)
    except Exception as e:
        print_result("Health Check", False, str(e))
        sys.exit(1)

    # 2. Authentication (Get Token)
    # The current auth_api.py uses /api/v1/auth/token endpoint
    token = None
    try:
        # Assuming a standard OAuth2 password flow or similar, but the current mock
        # implementation in auth_api.py (as viewed earlier) creates a token.
        # Let's check the endpoint shape. From main.py: app.include_router(auth_router, prefix="/api/v1/auth"...)
        # From auth_api.py: @router.post("/token")

        # We need to send form data or json? Standard OAuth2 is form data.
        # But let's assume the mock implementation might be simple.
        # Let's try sending standard password flow data.

        payload = {"tenant_id": "tenant-123", "account_id": "acc-123"}

        # Try JSON first as it's common in modern APIs, fallback to form if 422
        r = requests.post(f"{BASE_URL}/auth/token", json=payload, timeout=30)

        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            print_result("Auth Login", True)
        elif r.status_code == 422:
            # Retry with form data
            r = requests.post(f"{BASE_URL}/auth/token", data=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                token = data.get("access_token")
                print_result("Auth Login (Form)", True)
            else:
                print_result("Auth Login", False, r.text)
        else:
            print_result("Auth Login", False, r.text)

    except Exception as e:
        print_result("Auth Login", False, str(e))

    if not token:
        print("⚠️ Skipping authenticated tests due to login failure.")
        return

    # 3. Protected Resource (Trading Markets)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BASE_URL}/trading/markets", headers=headers, timeout=10)
        if r.status_code == 200:
            markets = r.json()
            print_result("Get Markets", True, f"Found {len(markets)} markets")
        else:
            print_result("Get Markets", False, r.text)
    except Exception as e:
        print_result("Get Markets", False, str(e))

    # 4. Protected Resource (User Settings)
    try:
        r = requests.get(f"{BASE_URL}/settings/profile", headers=headers, timeout=10)
        if r.status_code == 200:
            print_result("Get Profile", True)
        elif r.status_code == 404:
            print("⚠️ Profile not found. Attempting to create one...")
            profile_data = {
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@example.com",
            }
            r = requests.put(
                f"{BASE_URL}/settings/profile",
                headers=headers,
                json=profile_data,
                timeout=10,
            )
            if r.status_code == 200:
                print_result("Create Profile", True)
                # Verify it exists now
                r = requests.get(f"{BASE_URL}/settings/profile", headers=headers, timeout=10)
                if r.status_code == 200:
                    print_result("Get Profile (After Create)", True)
                else:
                    print_result("Get Profile (After Create)", False, r.text)
            else:
                print_result("Create Profile", False, r.text)
        else:
            print_result("Get Profile", False, r.text)
    except Exception as e:
        print_result("Get Profile", False, str(e))


if __name__ == "__main__":
    verify_system()
