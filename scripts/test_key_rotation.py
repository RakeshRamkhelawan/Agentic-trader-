#!/usr/bin/env python3
"""
TDD Test Script for Key Rotation Service (Taak 2.3)
Red Phase: Tests should FAIL because key_rotator.py doesn't exist yet.

Validates:
1. Module exists and is importable
2. KeyRotator class exists with required methods
3. generate_key_pair, rotate_key methods work
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_key_rotation():
    print("Starting Key Rotation Test (TDD)...")

    # 1. Test module import
    print("\n--- Test 1: Module Import ---")
    try:
        from backend.core.security.key_rotator import KeyRotator

        print("OK: key_rotator module is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import key_rotator: {e}")
        sys.exit(1)

    # 2. Test class instantiation
    print("\n--- Test 2: Class Instantiation ---")
    try:
        rotator = KeyRotator()
        print("OK: KeyRotator can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate KeyRotator: {e}")
        sys.exit(1)

    # 3. Test required methods exist
    print("\n--- Test 3: Required Methods ---")
    required_methods = ["generate_key_pair", "rotate_key", "get_current_public_key"]
    for method in required_methods:
        if not hasattr(rotator, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")

    # 4. Test generate_key_pair returns tuple of bytes
    print("\n--- Test 4: generate_key_pair Functionality ---")
    try:
        private_key, public_key = rotator.generate_key_pair()
        if not isinstance(private_key, bytes) or not isinstance(public_key, bytes):
            print("FAIL: generate_key_pair should return (bytes, bytes)")
            sys.exit(1)
        print("OK: generate_key_pair returns (bytes, bytes)")
    except Exception as e:
        print(f"FAIL: generate_key_pair raised exception: {e}")
        sys.exit(1)

    print("\n=== All Key Rotation tests passed! ===")


if __name__ == "__main__":
    test_key_rotation()
