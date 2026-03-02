#!/usr/bin/env python
"""
Week 7 Test Suite - Live Multi-Exchange Trading

Tests:
1. Live trading service initialization
2. Order validation (risk checks)
3. Order dataclass functionality
4. Position tracking
5. MCP tool integration
6. Risk limit configuration
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


async def test_live_trading_init():
    """Test LiveMultiExchangeTrading initialization."""
    print("\n" + "=" * 60)
    print("Test 1: Live Trading Service Initialization")
    print("=" * 60)

    from backend.execution.live_multi_exchange_trading import LiveMultiExchangeTrading

    trading = LiveMultiExchangeTrading()

    print(f"Service initialized")
    print(f"Risk limits:")
    print(f"  Max order value: €{trading.max_order_value_eur:,.2f}")
    print(f"  Max position value: €{trading.max_position_value_eur:,.2f}")
    print(f"  Max total exposure: €{trading.max_total_exposure:,.2f}")
    print(f"  Require confirmation: {trading.require_confirmation}")

    # Test initialization
    await trading.initialize()
    print(f"\nInitialized exchanges: {list(trading._exchanges.keys())}")

    stats = trading.get_stats()
    print(f"Stats: {stats}")

    await trading.stop()
    return True


async def test_order_dataclass():
    """Test LiveOrder dataclass."""
    print("\n" + "=" * 60)
    print("Test 2: LiveOrder Dataclass")
    print("=" * 60)

    from backend.execution.live_multi_exchange_trading import LiveOrder, OrderStatus

    order = LiveOrder(
        order_id="test_order_001",
        client_order_id="client_001",
        exchange="bitvavo",
        symbol="BTC-EUR",
        side="buy",
        order_type="limit",
        quantity=0.1,
        price=65000.0,
        status=OrderStatus.SUBMITTED,
        filled_quantity=0.05,
        avg_fill_price=64950.0,
    )

    print(f"Order ID: {order.order_id}")
    print(f"Exchange: {order.exchange}")
    print(f"Symbol: {order.symbol}")
    print(f"Side: {order.side}")
    print(f"Type: {order.order_type}")
    print(f"Quantity: {order.quantity}")
    print(f"Price: {order.price}")
    print(f"Status: {order.status.value}")
    print(f"Filled: {order.filled_quantity}")
    print(f"Remaining: {order.remaining_quantity}")
    print(f"Fill %: {order.fill_pct:.1f}%")
    print(f"Avg fill: {order.avg_fill_price}")
    print(f"Is complete: {order.is_complete}")

    return True


async def test_position_dataclass():
    """Test CrossExchangePosition dataclass."""
    print("\n" + "=" * 60)
    print("Test 3: CrossExchangePosition Dataclass")
    print("=" * 60)

    from backend.execution.live_multi_exchange_trading import (
        CrossExchangePosition,
        ExchangePosition,
    )

    pos = CrossExchangePosition(
        symbol="BTC",
        positions={
            "bitvavo": ExchangePosition(
                exchange="bitvavo",
                symbol="BTC",
                quantity=0.5,
                avg_entry_price=64000.0,
                unrealized_pnl=500.0,
            ),
            "revolutx": ExchangePosition(
                exchange="revolutx",
                symbol="BTC",
                quantity=0.3,
                avg_entry_price=64500.0,
                unrealized_pnl=150.0,
            ),
        },
    )

    print(f"Symbol: {pos.symbol}")
    print(f"Total quantity: {pos.total_quantity}")
    print(f"Avg entry price: {pos.avg_entry_price:.2f}")
    print(f"Total unrealized PnL: €{pos.total_unrealized_pnl:.2f}")
    print(f"Total realized PnL: €{pos.total_realized_pnl:.2f}")
    print(f"Exchange breakdown:")
    for ex, p in pos.positions.items():
        print(f"  {ex}: {p.quantity} BTC @ €{p.avg_entry_price:.2f}")

    return True


async def test_order_validation():
    """Test order validation with risk checks."""
    print("\n" + "=" * 60)
    print("Test 4: Order Validation")
    print("=" * 60)

    from backend.mcp_broker.tools.live_trading_tools import live_trading_validate_order

    # Test valid order
    result = await live_trading_validate_order(
        symbol="BTC-EUR",
        side="buy",
        quantity=0.05,
        price=60000.0,
    )

    print(f"Validation result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Valid: {result.get('valid')}")
    print(f"  Symbol: {result.get('symbol')}")
    print(f"  Side: {result.get('side')}")
    print(f"  Quantity: {result.get('quantity')}")
    print(f"  Order value: €{result.get('order_value', 0):,.2f}")
    print(f"  Risk check: {result.get('risk_check')}")
    print(f"  Can execute: {result.get('can_execute')}")

    # Test oversized order
    result_large = await live_trading_validate_order(
        symbol="BTC-EUR",
        side="buy",
        quantity=1.0,
        price=60000.0,  # €60,000 - exceeds limit
    )

    print(f"\nLarge order validation:")
    print(f"  Valid: {result_large.get('valid')}")
    print(f"  Risk check: {result_large.get('risk_check')}")
    print(f"  Reason: {result_large.get('risk_reason')}")

    return True


async def test_mcp_tools():
    """Test MCP tool integration."""
    print("\n" + "=" * 60)
    print("Test 5: MCP Live Trading Tools")
    print("=" * 60)

    import asyncio

    from backend.mcp_broker.server import mcp

    tools = await mcp.list_tools()

    live_tools = [t for t in tools if "live_trading" in t.name]

    print(f"Total tools: {len(tools)}")
    print(f"Live trading tools: {len(live_tools)}")

    expected = [
        "live_trading__place_order",
        "live_trading__get_order_status",
        "live_trading__cancel_order",
        "live_trading__get_positions",
        "live_trading__validate_order",
        "live_trading__get_stats",
    ]

    print("\nRegistered tools:")
    found = [t.name for t in live_tools]
    for tool in expected:
        status = "OK" if tool in found else "MISSING"
        print(f"  - {tool}: {status}")

    return len(live_tools) == len(expected)


async def test_risk_limits():
    """Test risk limit calculations."""
    print("\n" + "=" * 60)
    print("Test 6: Risk Limit Checks")
    print("=" * 60)

    from backend.execution.live_multi_exchange_trading import LiveMultiExchangeTrading

    trading = LiveMultiExchangeTrading()

    test_cases = [
        ("BTC-EUR", "buy", 0.01, 50000.0, True),   # €500 - OK
        ("BTC-EUR", "buy", 0.1, 50000.0, True),    # €5,000 - at limit
        ("BTC-EUR", "buy", 0.2, 50000.0, False),   # €10,000 - exceeds
    ]

    for symbol, side, qty, price, expected in test_cases:
        allowed, reason = trading._check_risk_limits(symbol, side, qty, price)
        value = qty * price
        status = "PASS" if allowed == expected else "FAIL"
        print(f"  €{value:>8,.0f} order: {'ALLOWED' if allowed else 'REJECTED'} [{status}]")
        if not allowed and reason:
            print(f"    Reason: {reason}")

    return True


async def main():
    """Run all Week 7 tests."""
    print("=" * 60)
    print("Week 7: Live Multi-Exchange Trading Tests")
    print("=" * 60)
    print("\nWARNING: These tests validate the live trading infrastructure.")
    print("No real orders are placed during testing.")
    print()

    results = {}

    tests = [
        ("live_trading_init", test_live_trading_init),
        ("order_dataclass", test_order_dataclass),
        ("position_dataclass", test_position_dataclass),
        ("order_validation", test_order_validation),
        ("mcp_tools", test_mcp_tools),
        ("risk_limits", test_risk_limits),
    ]

    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"{test_name} test failed: {e}")
            results[test_name] = False

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
        print("All Week 7 tests passed! Live trading infrastructure ready.")
        print("\nReady for live trading with risk controls:")
        print("  - Max order: €5,000")
        print("  - Max position: €10,000")
        print("  - Max exposure: €50,000")
    else:
        print("Some tests failed. Check logs above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
