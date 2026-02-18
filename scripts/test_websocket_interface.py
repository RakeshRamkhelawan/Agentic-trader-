#!/usr/bin/env python3
"""
TDD Test Script for WebSocket Interface (Taak 5.1)
Red Phase: Tests should FAIL because WebSocket interface doesn't exist yet.

Validates:
1. ExecutionInterface has streaming methods
2. Market data models exist (TickerUpdate, OrderBook, OrderUpdate)
3. WebSocket connection management
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_websocket_interface():
    print("Starting WebSocket Interface Test (TDD)...")

    # 1. Test market data models
    print("\n--- Test 1: Market Data Models ---")
    try:
        from backend.schemas.market_data import (OrderBook, OrderUpdate,
                                                 TickerUpdate)

        print("OK: Market data models are importable")
    except ImportError as e:
        print(f"FAIL: Cannot import market_data models: {e}")
        sys.exit(1)

    # 2. Test TickerUpdate model
    print("\n--- Test 2: TickerUpdate Model ---")
    try:
        from datetime import datetime

        ticker = TickerUpdate(
            symbol="BTC/EUR",
            bid=45000.0,
            ask=45010.0,
            last=45005.0,
            volume_24h=1000000.0,
            timestamp=datetime.utcnow(),
        )
        if not hasattr(ticker, "symbol") or not hasattr(ticker, "bid"):
            print("FAIL: TickerUpdate missing required fields")
            sys.exit(1)
        print("OK: TickerUpdate model works")
    except Exception as e:
        print(f"FAIL: TickerUpdate error: {e}")
        sys.exit(1)

    # 3. Test OrderBook model
    print("\n--- Test 3: OrderBook Model ---")
    try:
        orderbook = OrderBook(
            symbol="BTC/EUR",
            bids=[(45000.0, 1.5), (44990.0, 2.0)],
            asks=[(45010.0, 1.0), (45020.0, 3.0)],
            timestamp=datetime.utcnow(),
        )
        if not hasattr(orderbook, "bids") or not hasattr(orderbook, "asks"):
            print("FAIL: OrderBook missing required fields")
            sys.exit(1)
        print("OK: OrderBook model works")
    except Exception as e:
        print(f"FAIL: OrderBook error: {e}")
        sys.exit(1)

    # 4. Test ExecutionInterface abstract methods
    print("\n--- Test 4: ExecutionInterface Abstract Methods ---")
    try:
        from backend.execution.broker_interface import ExecutionInterface

        required_methods = [
            "subscribe_ticker",
            "subscribe_orderbook",
            "subscribe_orders",
        ]
        for method in required_methods:
            if not hasattr(ExecutionInterface, method):
                print(f"FAIL: Missing method: {method}")
                sys.exit(1)
            print(f"OK: Method '{method}' exists")
    except ImportError as e:
        print(f"FAIL: Cannot import ExecutionInterface: {e}")
        sys.exit(1)

    print("\n=== All WebSocket Interface tests passed! ===")


if __name__ == "__main__":
    test_websocket_interface()
