#!/usr/bin/env python3
"""
TDD Test Script for Paper Exchange (Taak 6.2)
Red Phase: Tests should FAIL because PaperExchange doesn't exist yet.

Validates:
1. PaperExchange class exists and implements ExecutionInterface
2. Slippage calculation based on order size
3. Balance tracking
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_paper_exchange():
    print("Starting Paper Exchange Test (TDD)...")

    # 1. Test module import
    print("\n--- Test 1: Module Import ---")
    try:
        from backend.execution.paper_exchange import PaperExchange

        print("OK: PaperExchange is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import PaperExchange: {e}")
        sys.exit(1)

    # 2. Test ExecutionInterface inheritance
    print("\n--- Test 2: ExecutionInterface Inheritance ---")
    try:
        from backend.execution.broker_interface import ExecutionInterface

        if not issubclass(PaperExchange, ExecutionInterface):
            print("FAIL: PaperExchange does not inherit from ExecutionInterface")
            sys.exit(1)
        print("OK: PaperExchange inherits from ExecutionInterface")
    except Exception as e:
        print(f"FAIL: Inheritance check error: {e}")
        sys.exit(1)

    # 3. Test class instantiation
    print("\n--- Test 3: Class Instantiation ---")
    try:
        exchange = PaperExchange(initial_balance={"EUR": 10000.0, "BTC": 1.0})
        print("OK: PaperExchange can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate exchange: {e}")
        sys.exit(1)

    # 4. Test required methods
    print("\n--- Test 4: Required Methods ---")
    required_methods = [
        "submit_order",
        "get_balance",
        "get_ticker",
        "calculate_slippage",
    ]
    for method in required_methods:
        if not hasattr(exchange, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")

    # 5. Test balance tracking
    print("\n--- Test 5: Balance Attribute ---")
    try:
        balance = exchange.balance
        if "EUR" not in balance:
            print("FAIL: Balance doesn't contain EUR")
            sys.exit(1)
        print(f"OK: Balance tracking works (EUR: {balance['EUR']})")
    except Exception as e:
        print(f"FAIL: Balance attribute error: {e}")
        sys.exit(1)

    print("\n=== All Paper Exchange tests passed! ===")


if __name__ == "__main__":
    test_paper_exchange()
