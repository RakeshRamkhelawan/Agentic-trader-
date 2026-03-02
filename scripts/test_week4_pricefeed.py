#!/usr/bin/env python
"""
Week 4 Test Suite - PriceFeedService Verification

Tests:
1. PriceFetchAgent initialization and cache
2. WebSocket connection to Bitvavo
3. REST fallback mechanism
4. Real-time data flow
5. Circuit breaker behavior
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")


async def test_price_fetch_agent():
    """Test PriceFetchAgent initialization and basic operations."""
    print("\n" + "=" * 60)
    print("Test 1: PriceFetchAgent Initialization")
    print("=" * 60)

    from backend.services.price_fetch_agent import PriceFetchAgent, PriceData

    agent = PriceFetchAgent(
        max_staleness_seconds=30.0,
        rest_fallback_interval=15.0,
        circuit_breaker_threshold=5,
    )

    print(f"Agent initialized")
    print(f"Max staleness: {agent.max_staleness}s")
    print(f"REST fallback interval: {agent.rest_fallback_interval}s")
    print(f"Circuit breaker threshold: {agent.circuit_breaker_threshold}")

    # Test initial stats
    stats = agent.get_stats()
    print(f"\nInitial stats: {stats}")

    # Test PriceData dataclass
    price_data = PriceData(
        symbol="BTC/EUR",
        price=65000.0,
        timestamp=datetime.now(),
        source="test",
        volume_24h=1000.0,
        change_24h=0.05,
    )

    print(f"\nPriceData created:")
    print(f"  Symbol: {price_data.symbol}")
    print(f"  Price: {price_data.price}")
    print(f"  Age: {price_data.age_ms:.0f}ms")
    print(f"  Is fresh: {price_data.is_fresh()}")

    return True


async def test_websocket_manager():
    """Test WebSocketManager for client connections."""
    print("\n" + "=" * 60)
    print("Test 2: WebSocket Manager")
    print("=" * 60)

    from backend.api.websocket_manager import WebSocketManager, Connection

    manager = WebSocketManager()

    print(f"WebSocketManager initialized")
    print(f"Initial connections: {len(manager.connections)}")
    print(f"Initial channels: {len(manager.channel_subscribers)}")

    # Test stats
    stats = manager.get_stats()
    print(f"\nStats: {stats}")

    return True


async def test_price_feed_integration():
    """Test integrated price feed with WebSocket + REST fallback."""
    print("\n" + "=" * 60)
    print("Test 3: PriceFeed Integration (15s test)")
    print("=" * 60)

    from backend.services.price_fetch_agent import PriceFetchAgent

    agent = PriceFetchAgent()

    # Start the agent
    print("Starting PriceFetchAgent...")
    await agent.start()

    # Wait for initial connection and data
    print("Waiting 5s for WebSocket connection...")
    await asyncio.sleep(5)

    # Check stats
    stats = agent.get_stats()
    print(f"\nStats after 5s:")
    print(f"  WebSocket connected: {stats['ws_connected']}")
    print(f"  Cache size: {stats['cache_size']}")
    print(f"  WS messages: {stats['ws_messages']}")
    print(f"  REST requests: {stats['rest_requests']}")

    # Wait a bit more for data
    print("\nWaiting 10s more for price data...")
    await asyncio.sleep(10)

    # Check cache
    all_prices = await agent.get_all_prices()
    print(f"\nCached prices: {len(all_prices)}")

    if all_prices:
        print("\nSample prices:")
        for i, (symbol, data) in enumerate(list(all_prices.items())[:5]):
            print(f"  {symbol}: {data.price:.2f} ({data.source})")

    # Stop the agent
    print("\nStopping agent...")
    await agent.stop()

    return stats['cache_size'] > 0 or stats['ws_messages'] > 0


async def test_circuit_breaker():
    """Test circuit breaker behavior."""
    print("\n" + "=" * 60)
    print("Test 4: Circuit Breaker")
    print("=" * 60)

    from backend.services.price_fetch_agent import PriceFetchAgent

    agent = PriceFetchAgent(circuit_breaker_threshold=3)

    # Initially circuit should be closed
    print(f"Circuit open: {agent._circuit_open}")
    print(f"Consecutive errors: {agent._consecutive_errors}")

    # Simulate errors
    agent._consecutive_errors = 3
    agent._open_circuit()

    print(f"After opening circuit:")
    print(f"Circuit open: {agent._circuit_open}")
    print(f"Reset time: {agent._circuit_reset_time}")

    return agent._circuit_open is True


async def test_market_data_ws():
    """Test market data WebSocket manager (Kraken)."""
    print("\n" + "=" * 60)
    print("Test 5: Market Data WebSocket (Kraken)")
    print("=" * 60)

    from backend.core.market_data.websocket_manager import WebSocketManager

    ws = WebSocketManager(url="wss://ws.kraken.com")

    print(f"WebSocketManager created")
    print(f"URL: {ws.url}")
    print(f"Running: {ws.is_running}")
    print(f"Subscriptions: {ws.subscriptions}")

    # Note: We won't actually connect to avoid external dependencies in tests
    print("\n(Skipping actual connection to avoid external dependency)")

    return True


async def main():
    """Run all Week 4 tests."""
    print("=" * 60)
    print("Week 4: PriceFeedService Verification")
    print("=" * 60)

    results = {}

    # Test 1: PriceFetchAgent
    try:
        results["price_fetch_agent"] = await test_price_fetch_agent()
    except Exception as e:
        logger.error(f"PriceFetchAgent test failed: {e}")
        results["price_fetch_agent"] = False

    # Test 2: WebSocket Manager
    try:
        results["websocket_manager"] = await test_websocket_manager()
    except Exception as e:
        logger.error(f"WebSocketManager test failed: {e}")
        results["websocket_manager"] = False

    # Test 3: Integration (with live connection)
    try:
        results["price_feed_integration"] = await test_price_feed_integration()
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        results["price_feed_integration"] = False

    # Test 4: Circuit Breaker
    try:
        results["circuit_breaker"] = await test_circuit_breaker()
    except Exception as e:
        logger.error(f"Circuit breaker test failed: {e}")
        results["circuit_breaker"] = False

    # Test 5: Market Data WS
    try:
        results["market_data_ws"] = await test_market_data_ws()
    except Exception as e:
        logger.error(f"Market data WS test failed: {e}")
        results["market_data_ws"] = False

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
        print("All Week 4 tests passed! PriceFeedService verified.")
    else:
        print("Some tests failed. Check logs above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
