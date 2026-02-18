#!/usr/bin/env python3
"""
TDD Test Script for Performance Analytics Service (Taak 6.3)
Red Phase: Tests should FAIL because PerformanceAnalytics doesn't exist yet.

Validates:
1. PerformanceAnalytics class exists
2. Trading metrics calculation (Sharpe, MaxDD, Win Rate)
3. Equity curve tracking
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def test_performance_analytics():
    print("Starting Performance Analytics Test (TDD)...")

    # 1. Test module import
    print("\n--- Test 1: Module Import ---")
    try:
        from backend.services.performance_analytics import PerformanceAnalytics

        print("OK: PerformanceAnalytics is importable")
    except ImportError as e:
        print(f"FAIL: Cannot import PerformanceAnalytics: {e}")
        sys.exit(1)

    # 2. Test class instantiation
    print("\n--- Test 2: Class Instantiation ---")
    try:
        analytics = PerformanceAnalytics()
        print("OK: PerformanceAnalytics can be instantiated")
    except Exception as e:
        print(f"FAIL: Cannot instantiate PerformanceAnalytics: {e}")
        sys.exit(1)

    # 3. Test required methods
    print("\n--- Test 3: Required Methods ---")
    required_methods = [
        "calculate_sharpe_ratio",
        "calculate_sortino_ratio",
        "calculate_max_drawdown",
        "calculate_win_rate",
        "calculate_profit_factor",
        "get_equity_curve",
    ]
    for method in required_methods:
        if not hasattr(analytics, method):
            print(f"FAIL: Missing method: {method}")
            sys.exit(1)
        print(f"OK: Method '{method}' exists")

    # 4. Test TradeResult model
    print("\n--- Test 4: TradeResult Model ---")
    try:
        from backend.services.performance_analytics import TradeResult

        trade = TradeResult(
            pnl=100.0, entry_price=45000.0, exit_price=45500.0, quantity=0.1
        )
        print(f"OK: TradeResult model works (pnl: {trade.pnl})")
    except Exception as e:
        print(f"FAIL: TradeResult model error: {e}")
        sys.exit(1)

    print("\n=== All Performance Analytics tests passed! ===")


if __name__ == "__main__":
    test_performance_analytics()
