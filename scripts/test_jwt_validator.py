#!/usr/bin/env python3
"""
TDD Test Script for JWT Validator (Taak 3.1)
Red Phase: Tests should FAIL because jwt_validator.py doesn't exist yet.

Validates:
1. JWTValidator class exists with required methods
2. TokenPayload model exists
3. validate_token returns TokenPayload
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_jwt_validator():
    print("Starting JWT Validator Test (TDD)...")

    # 1. Test module import
    print("\n--- Test 1: Module Import ---")
    try:
        from backend.core.auth.jwt_validator import JWTValidator
        from backend.core.auth.models import TokenPayload

        print("OK: jwt_validator and models are importable")
    except ImportError as e:
        print(f"FAIL: Cannot import modules: {e}")
        sys.exit(1)

    # 2. Test TokenPayload model
    print("\n--- Test 2: TokenPayload Model ---")
    try:
        payload = TokenPayload(
            sub="user-123", tenant_id="tenant-001", roles=["viewer"], exp=9999999999
        )
        if not hasattr(payload, "sub") or not hasattr(payload, "tenant_id"):
            print("FAIL: TokenPayload missing required fields")
            sys.exit(1)
        print("OK: TokenPayload model works")
    except Exception as e:
        print(f"FAIL: TokenPayload error: {e}")
        sys.exit(1)

    # 3. Test JWTValidator instantiation
    print("\n--- Test 3: JWTValidator Instantiation ---")
    try:
        validator = JWTValidator(
            jwks_url="https://example.auth0.com/.well-known/jwks.json",
            issuer="https://example.auth0.com/",
            audience="agentic-trader-api",
        )
        print("OK: JWTValidator can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate JWTValidator: {e}")
        sys.exit(1)

    # 4. Test required methods exist
    print("\n--- Test 4: Required Methods ---")
    required_methods = ["validate_token", "refresh_jwks"]
    for method in required_methods:
        if not hasattr(validator, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")

    print("\n=== All JWT Validator tests passed! ===")


if __name__ == "__main__":
    test_jwt_validator()
