#!/usr/bin/env python3
"""
TDD Test Script for Backtest Engine (Taak 6.1)
Red Phase: Tests should FAIL because BacktestEngine doesn't exist yet.

Validates:
1. BacktestEngine class exists
2. SimulatedClock for time control
3. Historical data streaming capability
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_backtest_engine():
    print("Starting Backtest Engine Test (TDD)...")

    # 1. Test module import - BacktestEngine
    print("\n--- Test 1: BacktestEngine Import ---")
    try:
        from backend.execution.backtest_engine import BacktestEngine

        print("OK: BacktestEngine is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import BacktestEngine: {e}")
        sys.exit(1)

    # 2. Test SimulatedClock import
    print("\n--- Test 2: SimulatedClock Import ---")
    try:
        from backend.execution.simulated_clock import SimulatedClock

        print("OK: SimulatedClock is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import SimulatedClock: {e}")
        sys.exit(1)

    # 3. Test SimulatedClock instantiation
    print("\n--- Test 3: SimulatedClock Instantiation ---")
    try:
        from datetime import datetime

        clock = SimulatedClock(start_time=datetime(2025, 1, 1), speed=100.0)
        print("OK: SimulatedClock can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate SimulatedClock: {e}")
        sys.exit(1)

    # 4. Test clock attributes
    print("\n--- Test 4: SimulatedClock Attributes ---")
    required_attrs = ["current_time", "speed", "now"]
    for attr in required_attrs:
        if not hasattr(clock, attr):
            print(f"FAIL: Missing attribute: {attr}")
            sys.exit(1)
        print(f"OK: Attribute '{attr}' exists")

    # 5. Test BacktestEngine instantiation
    print("\n--- Test 5: BacktestEngine Instantiation ---")
    try:
        from datetime import datetime

        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)
        engine = BacktestEngine(start_date=start, end_date=end, speed=100.0)
        print("OK: BacktestEngine can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate BacktestEngine: {e}")
        sys.exit(1)

    # 6. Test required methods
    print("\n--- Test 6: Required Methods ---")
    required_methods = ["stream_ticks", "get_current_tick"]
    for method in required_methods:
        if not hasattr(engine, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")

    print("\n=== All Backtest Engine tests passed! ===")


if __name__ == "__main__":
    test_backtest_engine()
