"""
Quick performance test for Backtest Engine V18.

Usage:
    python scripts/quick_performance_test.py
"""

import asyncio
import time
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "c:\\Users\\rsram\\Downloads\\agentic_trader_platform_1734_20260109_210621")


async def test_performance():
    """Run quick performance test."""
    from backend.mcp_broker.backtest_engine_v18_optimized import (
        run_optimized_backtest,
        OptimizedBacktestEngineV18,
        OptimizedBacktestConfig
    )
    
    symbols = ["AAPL", "MSFT"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # 1 week
    
    print("\n" + "="*60)
    print("QUICK PERFORMANCE TEST - Backtest Engine V18")
    print("="*60)
    print(f"Symbols: {symbols}")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print("="*60 + "\n")
    
    # Test 1: Sequential
    print("[1/3] Testing Sequential...")
    config = OptimizedBacktestConfig(
        enable_caching=True,
        enable_parallel_processing=False,
        enable_batch_processing=True
    )
    engine = OptimizedBacktestEngineV18(config)
    
    start = time.perf_counter()
    result1 = await engine.run_backtest(symbols, start_date, end_date)
    seq_time = time.perf_counter() - start
    
    print(f"  Time: {seq_time:.2f}s")
    print(f"  Trades: {len(result1.get('trades', []))}")
    
    # Test 2: Parallel
    print("\n[2/3] Testing Parallel...")
    config = OptimizedBacktestConfig(
        enable_caching=True,
        enable_parallel_processing=True,
        max_workers=2
    )
    engine = OptimizedBacktestEngineV18(config)
    
    start = time.perf_counter()
    result2 = await engine.run_backtest(symbols, start_date, end_date)
    par_time = time.perf_counter() - start
    
    print(f"  Time: {par_time:.2f}s")
    print(f"  Trades: {len(result2.get('trades', []))}")
    
    # Test 3: Full optimizations
    print("\n[3/3] Testing Full Optimizations...")
    
    start = time.perf_counter()
    result3 = await run_optimized_backtest(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        enable_parallel=True,
        max_workers=2
    )
    opt_time = time.perf_counter() - start
    
    print(f"  Time: {opt_time:.2f}s")
    print(f"  Trades: {len(result3.get('trades', []))}")
    
    # Summary
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Sequential:     {seq_time:.2f}s")
    print(f"Parallel:       {par_time:.2f}s (speedup: {seq_time/par_time:.2f}x)")
    print(f"Full Optimized: {opt_time:.2f}s (speedup: {seq_time/opt_time:.2f}x)")
    print("="*60)
    
    # Performance details
    if "performance" in result3:
        perf = result3["performance"]
        print("\nDetailed Metrics:")
        print(f"  Cache hit rate: {perf.get('metrics', {}).get('cache', {}).get('hit_rate', 0):.1%}")
        print(f"  Total signals: {perf.get('metrics', {}).get('total_signals_generated', 0)}")
        print(f"  Days processed: {perf.get('metrics', {}).get('total_days_processed', 0)}")
    
    print("\n✅ Performance test completed!")


if __name__ == "__main__":
    asyncio.run(test_performance())
