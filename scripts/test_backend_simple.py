#!/usr/bin/env python3
"""
Simplified Backend Test Suite

Tests basic backend connectivity without complex imports.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
import redis.asyncio as redis
import aiohttp
from datetime import datetime


async def test_postgresql():
    """Test PostgreSQL connection."""
    print("[TEST] PostgreSQL Connection")
    try:
        # Get connection string from environment
        db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/trading_db")

        # Try to connect
        conn = await asyncpg.connect(db_url)

        # Run simple query
        result = await conn.fetchval("SELECT 1")

        if result == 1:
            print("  [PASS] Connected successfully")

            # Check if tables exist
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' LIMIT 5"
            )
            print(f"  [INFO] Found {len(tables)} tables")
            for t in tables:
                print(f"         - {t['tablename']}")

        await conn.close()
        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


async def test_redis():
    """Test Redis connection."""
    print("\n[TEST] Redis Connection")
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        # Connect
        r = redis.from_url(redis_url, socket_connect_timeout=5)

        # Test ping
        await r.ping()
        print("  [PASS] Connected successfully")

        # Test operations
        test_key = f"test:{datetime.now().timestamp()}"
        await r.set(test_key, "test_value", ex=10)
        value = await r.get(test_key)

        if value == b"test_value":
            print("  [PASS] Read/Write operations work")
        else:
            print("  [FAIL] Value mismatch")

        await r.delete(test_key)
        await r.aclose()
        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


async def test_clickhouse():
    """Test ClickHouse connection."""
    print("\n[TEST] ClickHouse Connection")
    try:
        host = os.getenv("CLICKHOUSE_HOST", "localhost")
        port = os.getenv("CLICKHOUSE_PORT", "8123")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{host}:{port}/ping", timeout=5) as resp:
                if resp.status == 200:
                    print("  [PASS] ClickHouse is responding")
                    return True
                else:
                    print(f"  [FAIL] Status: {resp.status}")
                    return False

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


async def test_backend_api():
    """Test backend API."""
    print("\n[TEST] Backend API")
    try:
        api_url = os.getenv("API_URL", "http://localhost:8000")

        async with aiohttp.ClientSession() as session:
            # Test health
            try:
                async with session.get(f"{api_url}/api/v1/health", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"  [PASS] Health check OK: {data}")
                    else:
                        print(f"  [WARN] Health check returned {resp.status}")
            except Exception as e:
                print(f"  [WARN] Health check failed: {e}")

            # Test root
            try:
                async with session.get(f"{api_url}/", timeout=5) as resp:
                    if resp.status == 200:
                        print("  [PASS] Root endpoint OK")
                    else:
                        print(f"  [WARN] Root returned {resp.status}")
            except Exception as e:
                print(f"  [WARN] Root check failed: {e}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("BACKEND INTEGRATION TEST SUITE")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("PostgreSQL", await test_postgresql()))
    results.append(("Redis", await test_redis()))
    results.append(("ClickHouse", await test_clickhouse()))
    results.append(("Backend API", await test_backend_api()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print()
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
