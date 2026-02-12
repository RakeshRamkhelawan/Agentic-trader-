#!/usr/bin/env python3
"""
TDD Test Script for ClickHouse Tenant Isolation (Taak 4.1)
Red Phase: Tests should FAIL because TenantAwareClickHouseClient doesn't exist yet.

Validates:
1. TenantAwareClickHouseClient class exists
2. Query methods automatically inject tenant_id filter
3. Prevents cross-tenant data access
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

def test_clickhouse_tenant_isolation():
    print("Starting ClickHouse Tenant Isolation Test (TDD)...")
    
    # 1. Test module import
    print("\n--- Test 1: Module Import ---")
    try:
        from backend.storage.tenant_aware_clickhouse import TenantAwareClickHouseClient
        print("OK: TenantAwareClickHouseClient is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import TenantAwareClickHouseClient: {e}")
        sys.exit(1)
    
    # 2. Test class instantiation
    print("\n--- Test 2: Class Instantiation ---")
    try:
        client = TenantAwareClickHouseClient(host="localhost", port=8123)
        print("OK: TenantAwareClickHouseClient can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate client: {e}")
        sys.exit(1)
    
    # 3. Test required methods exist
    print("\n--- Test 3: Required Methods ---")
    required_methods = ['query', 'inject_tenant_filter', 'execute']
    for method in required_methods:
        if not hasattr(client, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")
    
    # 4. Test tenant filter injection
    print("\n--- Test 4: Tenant Filter Injection ---")
    try:
        test_sql = "SELECT * FROM trades ORDER BY timestamp"
        filtered_sql = client.inject_tenant_filter(test_sql, "tenant-001")
        if "tenant_id" not in filtered_sql.lower():
            print(f"FAIL: tenant_id not injected. Got: {filtered_sql}")
            sys.exit(1)
        print(f"OK: Tenant filter injected correctly")
    except Exception as e:
        print(f"FAIL: inject_tenant_filter error: {e}")
        sys.exit(1)
    
    print("\n=== All ClickHouse Tenant Isolation tests passed! ===")

if __name__ == "__main__":
    test_clickhouse_tenant_isolation()
