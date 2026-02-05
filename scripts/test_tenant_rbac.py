#!/usr/bin/env python3
"""
TDD Test Script for RBAC & Tenant Isolation (Taak 3.2 & 3.3)
Tests tenant context management and role-based access control.
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

def test_tenant_context():
    print("Starting Tenant Context & RBAC Test (TDD)...")
    
    # 1. Test context module import
    print("\n--- Test 1: Context Module Import ---")
    try:
        from backend.core.auth.context import (
            set_current_tenant, get_current_tenant,
            set_current_user, get_current_user,
            clear_context, UnauthorizedError
        )
        print("OK: context module is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import context: {e}")
        sys.exit(1)
    
    # 2. Test set/get tenant
    print("\n--- Test 2: Tenant Context ---")
    try:
        clear_context()
        set_current_tenant("tenant-001")
        tenant = get_current_tenant()
        if tenant != "tenant-001":
            print(f"FAIL: Expected 'tenant-001', got '{tenant}'")
            sys.exit(1)
        print("OK: Tenant context works")
    except Exception as e:
        print(f"FAIL: Tenant context error: {e}")
        sys.exit(1)
    
    # 3. Test unauthorized error
    print("\n--- Test 3: UnauthorizedError ---")
    try:
        clear_context()
        try:
            get_current_tenant()
            print("FAIL: Should have raised UnauthorizedError")
            sys.exit(1)
        except UnauthorizedError:
            print("OK: UnauthorizedError raised correctly")
    except Exception as e:
        print(f"FAIL: Unexpected error: {e}")
        sys.exit(1)
    
    # 4. Test middleware existence
    print("\n--- Test 4: Auth Middleware ---")
    try:
        from backend.core.auth.middleware import AuthMiddleware
        print("OK: AuthMiddleware is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import AuthMiddleware: {e}")
        sys.exit(1)
    
    # 5. Test RBAC decorator
    print("\n--- Test 5: RBAC Decorator ---")
    try:
        from backend.core.auth.rbac import require_role, require_any_role
        print("OK: RBAC decorators are importable")
    except ImportError as e:
        print(f"FAIL: Cannot import RBAC: {e}")
        sys.exit(1)
    
    print("\n=== All Tenant Context & RBAC tests passed! ===")

if __name__ == "__main__":
    test_tenant_context()
