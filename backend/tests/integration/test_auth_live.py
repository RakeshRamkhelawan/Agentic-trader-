import os

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

# Create a TestClient using the real app instance (no overrides)
client = TestClient(app)


def test_live_missing_auth_header():
    """
    Verify that accessing a protected endpoint without an Authorization header
    returns 401 Unauthorized in the real application.
    """
    response = client.get("/api/v1/trading/orders/active")
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing authorization token"}


def test_live_invalid_bearer_format():
    """
    Verify that using 'Basic' instead of 'Bearer' is rejected.
    """
    response = client.get(
        "/api/v1/trading/orders/active", headers={"Authorization": "Basic somecreds"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing authorization token"}


def test_live_malformed_token():
    """
    Verify that a visibly malformed token string is rejected.
    """
    response = client.get(
        "/api/v1/trading/orders/active", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert response.status_code == 401
    # The exact error detail depends on python-jose parsing
    assert "detail" in response.json()


def test_live_forged_token():
    """
    Verify that a JWT signed with a different key (self-signed) is rejected.
    This confirms that the backend is checking against the real Auth0 JWKS.
    """
    try:
        from jose import jwt
    except ImportError:
        pytest.skip("python-jose not installed")

    # Create a self-signed token
    payload = {
        "sub": "hacker",
        "iss": "https://malicious.com/",
        "aud": "https://api.agentic-trader.com",
        "exp": 9999999999,
    }
    # Sign with a random key, not Auth0's private key
    fake_token = jwt.encode(payload, "secret-key", algorithm="HS256")

    response = client.get(
        "/api/v1/trading/orders/active",
        headers={"Authorization": f"Bearer {fake_token}"},
    )

    # Should get 401 because signature verification fails (or alg mismatch)
    # The middleware connects to Auth0 JWKS, finds no matching key ID, or fails signature.
    assert response.status_code == 401
    # Assuming the middleware catches the error and returns 401
    print(f"DEBUG: Forged token response: {response.json()}")


# Optional Happy Path
@pytest.mark.skipif(
    not any(
        os.getenv(k)
        for k in ["AUTH0_TEST_TOKEN", "BEARER_TOKEN", "ACCESS_TOKEN", "AUTH_TOKEN"]
    ),
    reason="Define AUTH0_TEST_TOKEN, BEARER_TOKEN, ACCESS_TOKEN or AUTH_TOKEN in .env to test valid access",
)
def test_live_valid_access():
    """
    Verify access with a real, valid Auth0 token provided by user.
    """
    # Try to load .env explicitly for local testing
    try:
        from dotenv import load_dotenv

        load_dotenv()
        load_dotenv("frontend/.env.local")
    except ImportError:
        pass

    token = (
        os.getenv("AUTH0_TEST_TOKEN")
        or os.getenv("BEARER_TOKEN")
        or os.getenv("ACCESS_TOKEN")
        or os.getenv("AUTH_TOKEN")
    )

    if not token:
        pytest.skip("No token found in environment variables")

    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    response = client.get(
        "/api/v1/trading/orders/active", headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 401:
        pytest.fail(f"Token rejected: {response.json()}")

    # Expect 200 OK (assuming the user has permissions, or 403 if valid but unauthorized)
    # But for a valid token generally, 401 means authentication failed.
    assert response.status_code in [200, 403]
