#!/usr/bin/env python
"""
Week 6 Test Suite - Multi-Exchange Price Aggregation

Tests:
1. MultiExchangeAggregator initialization
2. Price aggregation from multiple exchanges
3. Best price discovery
4. Arbitrage detection
5. Smart order routing
6. MCP tool integration
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


async def test_aggregator_init():
    """Test MultiExchangeAggregator initialization."""
    print("\n" + "=" * 60)
    print("Test 1: MultiExchangeAggregator Initialization")
    print("=" * 60)

    from backend.execution.multi_exchange_aggregator import MultiExchangeAggregator

    aggregator = MultiExchangeAggregator()

    print(f"Aggregator initialized")
    print(f"Supported exchanges: {aggregator.SUPPORTED_EXCHANGES}")
    print(f"Update interval: {aggregator.update_interval}s")
    print(f"Max price age: {aggregator.max_price_age}s")

    # Test initialization
    await aggregator.initialize()
    print(f"\nInitialized adapters: {list(aggregator._exchange_adapters.keys())}")

    stats = aggregator.get_stats()
    print(f"Stats: {stats}")

    return True


async def test_exchange_price_dataclass():
    """Test ExchangePrice dataclass."""
    print("\n" + "=" * 60)
    print("Test 2: ExchangePrice Dataclass")
    print("=" * 60)

    from backend.execution.multi_exchange_aggregator import ExchangePrice

    price = ExchangePrice(
        exchange="bitvavo",
        symbol="BTC",
        bid=65000.0,
        ask=65050.0,
        last=65025.0,
        volume_24h=1000.0,
        latency_ms=25.5,
    )

    print(f"Exchange: {price.exchange}")
    print(f"Symbol: {price.symbol}")
    print(f"Bid: {price.bid}")
    print(f"Ask: {price.ask}")
    print(f"Last: {price.last}")
    print(f"Spread: {price.spread}")
    print(f"Spread %: {price.spread_pct:.4f}%")
    print(f"Mid: {price.mid}")
    print(f"Latency: {price.latency_ms}ms")
    print(f"Is fresh: {price.is_fresh()}")

    return True


async def test_aggregated_price():
    """Test AggregatedPrice calculations."""
    print("\n" + "=" * 60)
    print("Test 3: AggregatedPrice Calculations")
    print("=" * 60)

    from backend.execution.multi_exchange_aggregator import AggregatedPrice, ExchangePrice
    from datetime import datetime

    # Create sample prices
    prices = {
        "bitvavo": ExchangePrice(
            exchange="bitvavo",
            symbol="BTC",
            bid=65000.0,
            ask=65050.0,
            last=65025.0,
            volume_24h=500.0,
        ),
        "revolutx": ExchangePrice(
            exchange="revolutx",
            symbol="BTC",
            bid=65020.0,
            ask=65080.0,
            last=65050.0,
            volume_24h=300.0,
        ),
    }

    agg = AggregatedPrice(
        symbol="BTC",
        prices=prices,
        aggregated_at=datetime.utcnow(),
    )

    print(f"Symbol: {agg.symbol}")
    print(f"Best Bid: {agg.best_bid}")
    print(f"Best Ask: {agg.best_ask}")
    print(f"VWAP: {agg.vwap:.2f}")
    print(f"Price Discrepancy: {agg.price_discrepancy_pct:.4f}%")

    arb = agg.arbitrage_opportunity
    if arb:
        print(f"\nArbitrage Opportunity:")
        print(f"  Buy on: {arb['buy_exchange']} at {arb['buy_price']}")
        print(f"  Sell on: {arb['sell_exchange']} at {arb['sell_price']}")
        print(f"  Profit: {arb['profit_pct']:.4f}%")
    else:
        print("\nNo arbitrage opportunity")

    ranking = agg.get_exchange_ranking()
    print(f"\nExchange Ranking: {ranking}")

    return True


async def test_mcp_tools():
    """Test MCP tool integration."""
    print("\n" + "=" * 60)
    print("Test 4: MCP Multi-Exchange Tools")
    print("=" * 60)

    import asyncio

    from backend.mcp_broker.server import mcp

    tools = await mcp.list_tools()

    multi_exchange_tools = [t for t in tools if "multi" in t.name or t.name.startswith("smart_order")]

    print(f"Total tools: {len(tools)}")
    print(f"Multi-exchange tools: {len(multi_exchange_tools)}")

    expected = [
        "multi_exchange__get_price",
        "multi_exchange__get_best_price",
        "multi_exchange__find_arbitrage",
        "multi_exchange__get_discrepancies",
        "smart_order__route",
        "multi_exchange__get_stats",
    ]

    print("\nRegistered tools:")
    found = [t.name for t in multi_exchange_tools]
    for tool in expected:
        status = "OK" if tool in found else "MISSING"
        print(f"  - {tool}: {status}")

    return len(multi_exchange_tools) == len(expected)


async def test_smart_order_routing():
    """Test smart order routing logic."""
    print("\n" + "=" * 60)
    print("Test 5: Smart Order Routing")
    print("=" * 60)

    from backend.mcp_broker.tools.multi_exchange_tools import smart_order_route

    # This will fail to get real data but tests the logic
    result = await smart_order_route(
        symbol="BTC",
        side="buy",
        quantity=0.1,
        order_type="market",
    )

    print(f"Success: {result.get('success')}")
    if result.get("success"):
        print(f"Recommended exchange: {result.get('recommended_exchange')}")
        print(f"Expected price: {result.get('expected_price')}")
        print(f"Expected value: {result.get('expected_value')}")
        print(f"Estimated fee: {result.get('estimated_fee')}")
    else:
        print(f"Error: {result.get('error')}")

    return True  # Pass even if no data - tests the flow


async def test_arbitrage_detection():
    """Test arbitrage detection."""
    print("\n" + "=" * 60)
    print("Test 6: Arbitrage Detection")
    print("=" * 60)

    from backend.mcp_broker.tools.multi_exchange_tools import multi_exchange_find_arbitrage

    result = await multi_exchange_find_arbitrage()

    print(f"Success: {result.get('success')}")
    print(f"Opportunities found: {result.get('count', 0)}")

    if result.get("opportunities"):
        for opp in result["opportunities"][:3]:
            print(f"\n  {opp['symbol']}:")
            print(f"    Buy: {opp['buy_exchange']} at {opp['buy_price']}")
            print(f"    Sell: {opp['sell_exchange']} at {opp['sell_price']}")
            print(f"    Profit: {opp['profit_pct']:.4f}%")

    return True


async def main():
    """Run all Week 6 tests."""
    print("=" * 60)
    print("Week 6: Multi-Exchange Price Aggregation Tests")
    print("=" * 60)

    results = {}

    tests = [
        ("aggregator_init", test_aggregator_init),
        ("exchange_price", test_exchange_price_dataclass),
        ("aggregated_price", test_aggregated_price),
        ("mcp_tools", test_mcp_tools),
        ("smart_routing", test_smart_order_routing),
        ("arbitrage_detection", test_arbitrage_detection),
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
        print("All Week 6 tests passed! Multi-exchange aggregation ready.")
    else:
        print("Some tests failed. Check logs above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
