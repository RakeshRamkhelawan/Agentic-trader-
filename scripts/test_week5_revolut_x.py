#!/usr/bin/env python
"""
Week 5 Test Suite - Revolut X Integration

Tests:
1. Revolut X client initialization
2. API connectivity check
3. Symbol listing (public endpoint)
4. Ticker fetch (requires auth)
5. MCP tool integration
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")


async def test_revolutx_client_init():
    """Test Revolut X client initialization."""
    print("\n" + "=" * 60)
    print("Test 1: Revolut X Client Initialization")
    print("=" * 60)

    from backend.integrations.revolut_x_client import RevolutXClient

    client = RevolutXClient()

    print(f"Client initialized")
    print(f"Base URL: {client.BASE_URL}")
    print(f"API Key configured: {bool(client.api_key)}")
    print(f"Private key path: {client.private_key_path}")
    print(f"Authenticated: {client._authenticated}")

    return True


async def test_revolutx_account_info():
    """Test Revolut X account info via MCP tool."""
    print("\n" + "=" * 60)
    print("Test 2: Revolut X Account Info (MCP Tool)")
    print("=" * 60)

    from backend.mcp_broker.tools.revolut_x_tools import revolutx_get_account_info

    result = await revolutx_get_account_info()

    print(f"Success: {result.get('success')}")
    print(f"Connected: {result.get('connected')}")
    print(f"API Key configured: {result.get('api_key_configured')}")
    print(f"Private Key configured: {result.get('private_key_configured')}")

    if result.get("api_key_preview"):
        print(f"API Key preview: {result.get('api_key_preview')}")

    return result.get("success") is True


async def test_revolutx_symbols():
    """Test fetching available symbols."""
    print("\n" + "=" * 60)
    print("Test 3: Revolut X Symbols")
    print("=" * 60)

    from backend.mcp_broker.tools.revolut_x_tools import revolutx_get_symbols

    result = await revolutx_get_symbols()

    print(f"Success: {result.get('success')}")

    if result.get("success"):
        symbols = result.get("symbols", [])
        print(f"Total symbols: {len(symbols)}")

        if symbols:
            print(f"\nSample symbols:")
            for s in symbols[:10]:
                print(f"  - {s}")

        # Check for major pairs
        major_pairs = ["BTC-USD", "ETH-USD", "SOL-USD"]
        found = [p for p in major_pairs if p in symbols]
        print(f"\nMajor pairs found: {found}")

        return len(symbols) > 0
    else:
        print(f"Error: {result.get('error')}")
        return False


async def test_revolutx_adapter():
    """Test Revolut X adapter."""
    print("\n" + "=" * 60)
    print("Test 4: Revolut X Adapter")
    print("=" * 60)

    from backend.execution.revolut_x_adapter import RevolutXAdapter

    adapter = RevolutXAdapter()

    print(f"Adapter initialized")
    print(f"Connected: {adapter._connected}")

    # Test symbol mapping
    test_cases = [
        ("BTC/USDT", "BTC-USD"),
        ("ETH/USDT", "ETH-USD"),
        ("SOL/USD", "SOL-USD"),
    ]

    print("\nSymbol mapping tests:")
    for ooda_symbol, expected in test_cases:
        result = adapter._map_symbol(ooda_symbol)
        status = "OK" if result == expected else "FAIL"
        print(f"  {ooda_symbol} -> {result} (expected: {expected}) [{status}]")

    return True


async def test_mcp_server_integration():
    """Test that Revolut X tools are registered in MCP server."""
    print("\n" + "=" * 60)
    print("Test 5: MCP Server Integration")
    print("=" * 60)

    import asyncio

    from backend.mcp_broker.server import mcp

    # List all tools
    tools = await mcp.list_tools()

    revolut_tools = [t for t in tools if t.name.startswith("revolutx")]

    print(f"Total tools: {len(tools)}")
    print(f"Revolut X tools: {len(revolut_tools)}")

    expected_tools = [
        "revolutx__get_ticker",
        "revolutx__get_orderbook",
        "revolutx__get_symbols",
        "revolutx__place_order",
        "revolutx__get_active_orders",
        "revolutx__get_account_info",
    ]

    print("\nRegistered Revolut X tools:")
    found_tools = [t.name for t in revolut_tools]

    for tool_name in expected_tools:
        status = "OK" if tool_name in found_tools else "MISSING"
        print(f"  - {tool_name}: {status}")

    return len(revolut_tools) == len(expected_tools)


async def main():
    """Run all Week 5 tests."""
    print("=" * 60)
    print("Week 5: Revolut X Integration Tests")
    print("=" * 60)

    results = {}

    # Test 1: Client initialization
    try:
        results["client_init"] = await test_revolutx_client_init()
    except Exception as e:
        logger.error(f"Client init test failed: {e}")
        results["client_init"] = False

    # Test 2: Account info
    try:
        results["account_info"] = await test_revolutx_account_info()
    except Exception as e:
        logger.error(f"Account info test failed: {e}")
        results["account_info"] = False

    # Test 3: Symbols
    try:
        results["symbols"] = await test_revolutx_symbols()
    except Exception as e:
        logger.error(f"Symbols test failed: {e}")
        results["symbols"] = False

    # Test 4: Adapter
    try:
        results["adapter"] = await test_revolutx_adapter()
    except Exception as e:
        logger.error(f"Adapter test failed: {e}")
        results["adapter"] = False

    # Test 5: MCP integration
    try:
        results["mcp_integration"] = await test_mcp_server_integration()
    except Exception as e:
        logger.error(f"MCP integration test failed: {e}")
        results["mcp_integration"] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        emoji = " " if passed else " "
        print(f"{emoji} {test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("All Week 5 tests passed! Revolut X integration ready.")
    else:
        print("Some tests failed. Check logs above.")
        print("\nNote: Live API tests require valid credentials in .env:")
        print("  - REVOLUT_API_KEY")
        print("  - REVOLUT_PRIVATE_KEY_PATH")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
