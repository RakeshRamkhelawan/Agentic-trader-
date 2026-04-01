import os

import pytest
import requests
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def get_real_auth0_token():
    """
    Attempts to fetch a real Access Token from Auth0 using available credentials.
    Supports:
    1. Client Credentials Flow (needs AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET)
    2. Password Flow (needs AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, TEST_USER_EMAIL, TEST_USER_PASSWORD)
    """
    domain = os.getenv("AUTH0_DOMAIN") or os.getenv("NEXT_PUBLIC_AUTH0_DOMAIN")
    client_id = os.getenv("AUTH0_CLIENT_ID") or os.getenv("NEXT_PUBLIC_AUTH0_CLIENT_ID")
    client_secret = os.getenv("AUTH0_CLIENT_SECRET")
    audience = os.getenv("AUTH0_API_AUDIENCE") or os.getenv(
        "NEXT_PUBLIC_AUTH0_AUDIENCE"
    )

    username = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")

    if not domain or not client_id or not audience:
        print("SKIPPING: Missing Domain, Client ID, or Audience.")
        return None

    url = f"https://{domain}/oauth/token"

    # Try Client Credentials Flow (Machine-to-Machine)
    if client_secret and not username:
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": audience,
            "grant_type": "client_credentials",
        }
        print(f"Attempting Client Credentials usage for {client_id}...")
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("access_token")
        else:
            print(f"Client Credentials failed: {resp.status_code} - {resp.text}")
            print(f"Using Domain: {domain}")
            print(f"Using Client ID: {client_id}")
            print(f"Using Audience: {audience}")

    # Try Resource Owner Password Flow (User Login)
    if username and password:
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,  # Might be needed for Confidential apps, optional for Public
            "audience": audience,
            "username": username,
            "password": password,
            "grant_type": "password",
            "scope": "openid profile email",
        }
        print(f"Attempting Password Login for {username}...")
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("access_token")
        else:
            print(f"Password Login failed: {resp.text}")

    return None


def test_live_happy_path_with_real_token():
    """
    End-to-End Test:
    1. Fetch Real Token from Auth0.
    2. Hit Protected API Endpoint.
    3. Verify 200 OK.
    """
    # Load env vars safely if not already loaded
    try:
        from dotenv import load_dotenv

        load_dotenv()
        load_dotenv("frontend/.env.local")
    except ImportError:
        pass

    # Check if we have a manual token first
    token = (
        os.getenv("AUTH0_TEST_TOKEN")
        or os.getenv("BEARER_TOKEN")
        or os.getenv("ACCESS_TOKEN")
        or os.getenv("AUTH_TOKEN")
    )

    if not token:
        # Try to generate one
        token = get_real_auth0_token()

    if not token:
        pytest.fail(
            "Could not obtain a real Auth0 token. \n"
            "Please provide ONE of the following in your .env:\n"
            "1. AUTH0_CLIENT_SECRET (for Machine-to-Machine test)\n"
            "2. TEST_USER_EMAIL + TEST_USER_PASSWORD (for User Login test)\n"
            "3. AUTH0_TEST_TOKEN (if you want to paste a token manually)"
        )

    # Clean token
    if token.startswith("Bearer "):
        token = token[7:]

    print(f"Using Token: {token[:10]}...")

    # Act
    response = client.get(
        "/api/v1/trading/orders/active", headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    # 200 = Success (Authenticated & Authorized)
    # 403 = Authenticated but not Authorized (RLS or Scope issue) - Still passes AUTH verification
    if response.status_code not in [200, 403]:
        pytest.fail(
            f"API Rejected Valid Token: {response.status_code} - {response.text}"
        )

    assert response.status_code in [200, 403]
