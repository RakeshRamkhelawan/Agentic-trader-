#!/usr/bin/env python3
"""
TDD Test Script for CCXT Exchange Adapter (Taak 5.2)
Red Phase: Tests should FAIL because CCXTAdapter doesn't exist yet.

Validates:
1. CCXTAdapter class exists and implements ExecutionInterface
2. CCXT Pro support for WebSocket streaming
3. Exchange connection management
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_ccxt_adapter():
    print("Starting CCXT Exchange Adapter Test (TDD)...")

    # 1. Test module import
    print("\n--- Test 1: Module Import ---")
    try:
        from backend.execution.ccxt_adapter import CCXTAdapter

        print("OK: CCXTAdapter is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import CCXTAdapter: {e}")
        sys.exit(1)

    # 2. Test ExecutionInterface inheritance
    print("\n--- Test 2: ExecutionInterface Inheritance ---")
    try:
        from backend.execution.broker_interface import ExecutionInterface

        if not issubclass(CCXTAdapter, ExecutionInterface):
            print("FAIL: CCXTAdapter does not inherit from ExecutionInterface")
            sys.exit(1)
        print("OK: CCXTAdapter inherits from ExecutionInterface")
    except Exception as e:
        print(f"FAIL: Inheritance check error: {e}")
        sys.exit(1)

    # 3. Test class instantiation (mock mode)
    print("\n--- Test 3: Class Instantiation ---")
    try:
        adapter = CCXTAdapter(
            exchange_id="binance",
            api_key="test_key",
            secret="test_secret",
            sandbox=True,
        )
        print("OK: CCXTAdapter can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate adapter: {e}")
        sys.exit(1)

    # 4. Test required methods
    print("\n--- Test 4: Required Methods ---")
    required_methods = [
        "submit_order",
        "get_balance",
        "get_ticker",
        "subscribe_ticker",
        "subscribe_orderbook",
        "subscribe_orders",
    ]
    for method in required_methods:
        if not hasattr(adapter, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")

    print("\n=== All CCXT Adapter tests passed! ===")


if __name__ == "__main__":
    test_ccxt_adapter()
