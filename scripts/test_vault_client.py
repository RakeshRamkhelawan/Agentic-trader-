#!/usr/bin/env python3
"""
TDD Test Script for Vault Client (Taak 2.1)
Red Phase: Tests should FAIL because vault_manager.py doesn't exist yet.

Validates:
1. Module exists and is importable
2. VaultManager class exists with required methods
3. get_secret, list_secrets, rotate_key methods work
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_vault_client():
    print("Starting Vault Client Test (TDD)...")

    # 1. Test module exists
    print("\n--- Test 1: Module Import ---")
    try:
        from backend.core.security.vault_manager import VaultManager

        print("OK: vault_manager module is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import vault_manager: {e}")
        sys.exit(1)

    # 2. Test class instantiation
    print("\n--- Test 2: Class Instantiation ---")
    try:
        manager = VaultManager()
        print("OK: VaultManager can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate VaultManager: {e}")
        sys.exit(1)

    # 3. Test required methods exist
    print("\n--- Test 3: Required Methods ---")
    required_methods = ["get_secret", "list_secrets", "rotate_key"]
    for method in required_methods:
        if not hasattr(manager, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")

    # 4. Test get_secret returns string
    print("\n--- Test 4: get_secret Functionality ---")
    try:
        result = manager.get_secret("test/path", "test_key")
        if not isinstance(result, str):
            print(f"FAIL: get_secret should return str, got {type(result)}")
            sys.exit(1)
        print("OK: get_secret returns string")
    except Exception as e:
        print(f"FAIL: get_secret raised exception: {e}")
        sys.exit(1)

    # 5. Test list_secrets returns list
    print("\n--- Test 5: list_secrets Functionality ---")
    try:
        result = manager.list_secrets("test/path")
        if not isinstance(result, list):
            print(f"FAIL: list_secrets should return list, got {type(result)}")
            sys.exit(1)
        print("OK: list_secrets returns list")
    except Exception as e:
        print(f"FAIL: list_secrets raised exception: {e}")
        sys.exit(1)

    print("\n=== All Vault Client tests passed! ===")


if __name__ == "__main__":
    test_vault_client()
