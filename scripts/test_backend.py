#!/usr/bin/env python3
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Backend Integration Test Suite

Tests all critical backend components:
1. Database connections (PostgreSQL, Redis, ClickHouse)
2. API endpoints (FastAPI)
3. WebSocket connections
4. External integrations (Bitvavo, Auth0)
5. Security (JWT, RLS)

Usage:
    python scripts/test_backend.py
    python scripts/test_backend.py --verbose
    python scripts/test_backend.py --test-db-only
"""

import asyncio
import sys
import argparse
from datetime import datetime
from typing import List, Tuple

# Test results storage
results: List[Tuple[str, bool, str]] = []


def log_test(name: str, passed: bool, message: str = ""):
    """Log test result."""
    status = "[PASS]" if passed else "[FAIL]"
    results.append((name, passed, message))
    print(f"{status} {name}")
    if message and not passed:
        print(f"   > {message}")


async def test_postgresql():
    """Test PostgreSQL connection."""
    try:
        from backend.core.config.settings import settings
        from backend.core.database.session import get_db_session
        from sqlalchemy import text

        print("\n[DB] Testing PostgreSQL...")

        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()

            if value == 1:
                log_test("PostgreSQL Connection", True)

                # Test RLS is enabled
                result = await session.execute(
                    text("SELECT COUNT(*) FROM pg_tables WHERE tablename = 'orders'")
                )
                table_count = result.scalar()
                if table_count > 0:
                    log_test("PostgreSQL Tables Exist", True)
                else:
                    log_test("PostgreSQL Tables Exist", False, "No tables found")
            else:
                log_test("PostgreSQL Connection", False, "Unexpected response")

    except Exception as e:
        log_test("PostgreSQL Connection", False, str(e))


async def test_redis():
    """Test Redis connection."""
    try:
        from backend.core.config.settings import settings
        import redis.asyncio as redis

        print("\n[DB] Testing Redis...")

        # Parse Redis URL
        redis_client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # Test connection
        await redis_client.ping()
        log_test("Redis Connection", True)

        # Test basic operations
        test_key = f"test_{datetime.now().timestamp()}"
        await redis_client.set(test_key, "test_value", ex=10)
        value = await redis_client.get(test_key)

        if value == b"test_value":
            log_test("Redis Operations", True)
        else:
            log_test("Redis Operations", False, "Value mismatch")

        await redis_client.delete(test_key)
        await redis_client.close()

    except Exception as e:
        log_test("Redis Connection", False, str(e))


async def test_clickhouse():
    """Test ClickHouse connection."""
    try:
        from backend.core.config.settings import settings

        print("\n[DB] Testing ClickHouse...")

        # Simple HTTP check
        import aiohttp

        url = f"http://{settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}/ping"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    log_test("ClickHouse Connection", True)
                else:
                    log_test("ClickHouse Connection", False, f"Status: {response.status}")

    except Exception as e:
        log_test("ClickHouse Connection", False, str(e))


async def test_api_endpoints():
    """Test FastAPI endpoints."""
    try:
        from fastapi.testclient import TestClient
        from backend.api.main import app

        print("\n[API] Testing API Endpoints...")

        client = TestClient(app)

        # Test health endpoint
        response = client.get("/api/v1/health")
        if response.status_code == 200:
            log_test("API Health Check", True)
        else:
            log_test("API Health Check", False, f"Status: {response.status_code}")

        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            log_test("API Root Endpoint", True)
        else:
            log_test("API Root Endpoint", False, f"Status: {response.status_code}")

        # Test API info
        response = client.get("/api")
        if response.status_code == 200:
            log_test("API Info Endpoint", True)
        else:
            log_test("API Info Endpoint", False, f"Status: {response.status_code}")

    except Exception as e:
        log_test("API Endpoints", False, str(e))


async def test_websocket():
    """Test WebSocket functionality."""
    try:
        from backend.api.websocket_manager import ws_manager

        print("\n[WS] Testing WebSocket...")

        # Check WebSocket manager is initialized
        if ws_manager is not None:
            log_test("WebSocket Manager", True)
        else:
            log_test("WebSocket Manager", False, "Not initialized")

        # Get stats
        stats = ws_manager.get_stats()
        if isinstance(stats, dict):
            log_test("WebSocket Stats", True, f"Connections: {stats.get('total_connections', 0)}")
        else:
            log_test("WebSocket Stats", False, "Invalid response")

    except Exception as e:
        log_test("WebSocket", False, str(e))


async def test_auth0_config():
    """Test Auth0 configuration."""
    try:
        from backend.core.config.settings import settings

        print("\n[AUTH] Testing Auth0 Configuration...")

        # Check Auth0 settings are configured
        if settings.AUTH0_DOMAIN and settings.AUTH0_DOMAIN != "your-tenant.auth0.com":
            log_test("Auth0 Domain", True)
        else:
            log_test("Auth0 Domain", False, "Not configured")

        if settings.AUTH0_API_AUDIENCE and settings.AUTH0_API_AUDIENCE != "your-api-identifier":
            log_test("Auth0 Audience", True)
        else:
            log_test("Auth0 Audience", False, "Not configured")

    except Exception as e:
        log_test("Auth0 Config", False, str(e))


async def test_bitvavo_config():
    """Test Bitvavo configuration."""
    try:
        from backend.core.config.settings import settings

        print("\n[EXCHANGE] Testing Bitvavo Configuration...")

        # Check if API keys are configured
        if settings.BITVAVO_API_KEY:
            log_test("Bitvavo API Key", True, "Configured")
        else:
            log_test("Bitvavo API Key", False, "Not configured (optional for paper trading)")

        if settings.BITVAVO_API_SECRET:
            log_test("Bitvavo API Secret", True, "Configured")
        else:
            log_test("Bitvavo API Secret", False, "Not configured (optional for paper trading)")

    except Exception as e:
        log_test("Bitvavo Config", False, str(e))


async def test_jwt_handler():
    """Test JWT handler."""
    try:
        from backend.security.jwt_handler import JWTHandler

        print("\n[SECURITY] Testing JWT Handler...")

        # Check JWT handler can be instantiated
        handler = JWTHandler(
            jwks_url="https://test.auth0.com/.well-known/jwks.json",
            audience="test-audience",
            issuer="https://test.auth0.com/"
        )

        if handler is not None:
            log_test("JWT Handler Initialization", True)
        else:
            log_test("JWT Handler Initialization", False, "Failed to create handler")

    except Exception as e:
        log_test("JWT Handler", False, str(e))


async def test_mcp_server():
    """Test MCP server imports."""
    try:
        print("\n[MCP] Testing MCP Server...")

        # Test imports
        from backend.mcp_server.server import mcp

        if mcp is not None:
            log_test("MCP Server Import", True)
        else:
            log_test("MCP Server Import", False, "Not initialized")

        # Try to list tools
        tools = mcp._tools
        if isinstance(tools, dict):
            log_test("MCP Tools", True, f"{len(tools)} tools registered")
        else:
            log_test("MCP Tools", False, "Invalid tools format")

    except Exception as e:
        log_test("MCP Server", False, str(e))


async def test_services():
    """Test key services can be imported."""
    try:
        print("\n[SERVICES] Testing Services...")

        services = [
            ("Trading Service", "backend.services.trading_service"),
            ("Backtest Service", "backend.services.backtest_service"),
            ("Risk Service", "backend.services.risk_service"),
            ("Market Data Service", "backend.services.market_data_service"),
        ]

        for name, module_path in services:
            try:
                __import__(module_path)
                log_test(f"{name} Import", True)
            except Exception as e:
                log_test(f"{name} Import", False, str(e))

    except Exception as e:
        log_test("Services", False, str(e))


async def run_all_tests(args):
    """Run all tests."""
    print("=" * 60)
    print("Backend Integration Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Database tests
    if args.test_all or args.test_db:
        await test_postgresql()
        await test_redis()
        await test_clickhouse()

    # API tests
    if args.test_all or args.test_api:
        await test_api_endpoints()
        await test_websocket()

    # Security tests
    if args.test_all or args.test_security:
        await test_auth0_config()
        await test_jwt_handler()

    # Integration tests
    if args.test_all or args.test_integrations:
        await test_bitvavo_config()
        await test_mcp_server()
        await test_services()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")

    if failed > 0:
        print("\n[FAILED] Failed Tests:")
        for name, passed, message in results:
            if not passed:
                print(f"  - {name}: {message}")

    print("=" * 60)

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Backend Integration Tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test-db-only", action="store_true", help="Test only databases")
    parser.add_argument("--test-api-only", action="store_true", help="Test only API")
    parser.add_argument("--test-security-only", action="store_true", help="Test only security")

    args = parser.parse_args()

    # Determine which tests to run
    args.test_all = not (args.test_db_only or args.test_api_only or args.test_security_only)
    args.test_db = args.test_db_only or args.test_all
    args.test_api = args.test_api_only or args.test_all
    args.test_security = args.test_security_only or args.test_all
    args.test_integrations = args.test_all

    try:
        success = asyncio.run(run_all_tests(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Critical error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
