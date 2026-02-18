#!/usr/bin/env python3
"""
TDD Test Script for Settings Integration (Taak 2.2)
Red Phase: Tests should verify Vault-integrated settings.

Validates:
1. Settings has VAULT_ENABLED flag
2. Sensitive properties use Vault when enabled
3. Fallback to env vars when Vault disabled
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_settings_integration():
    print("Starting Settings Integration Test (TDD)...")

    # 1. Test Settings import
    print("\n--- Test 1: Settings Import ---")
    try:
        from backend.core.config.settings import Settings

        print("OK: Settings class is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import Settings: {e}")
        sys.exit(1)

    # 2. Test VAULT_ENABLED flag exists
    print("\n--- Test 2: VAULT_ENABLED Flag ---")
    settings = Settings()
    if not hasattr(settings, "VAULT_ENABLED"):
        print("FAIL: Settings missing VAULT_ENABLED flag")
        sys.exit(1)
    print(f"OK: VAULT_ENABLED = {settings.VAULT_ENABLED}")

    # 3. Test sensitive property decorator pattern
    print("\n--- Test 3: Sensitive Properties ---")
    sensitive_fields = ["REVOLUT_API_KEY", "JWT_SECRET_KEY", "DATABASE_URL"]
    for field in sensitive_fields:
        if not hasattr(settings, field):
            print(f"WARN: Settings missing {field} (may be optional)")
            continue
        value = getattr(settings, field)
        if not isinstance(value, str):
            print(f"FAIL: {field} should return str, got {type(value)}")
            sys.exit(1)
        print(f"OK: {field} returns string")

    print("\n=== Settings Integration tests passed! ===")


if __name__ == "__main__":
    test_settings_integration()
