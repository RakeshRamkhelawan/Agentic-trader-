"""
Integration test - Test all components without full MCP client.
"""

import sys
import asyncio
from datetime import datetime, timedelta


def test_imports():
    """Test all imports."""
    print("="*60, file=sys.stderr)
    print("TEST: Imports", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    try:
        from backend.mcp_broker.performance.cache import BacktestCache
        from backend.mcp_broker.performance.batch_processor import BatchProcessor
        from backend.mcp_broker.performance.parallel_engine import ParallelBacktestEngine
        from backend.mcp_broker.performance.metrics import PerformanceMetricsCollector
        from backend.mcp_broker.performance.ultra_mode import UltraPerformanceMode
        from backend.mcp_broker.performance.distributed import ParallelProcessor
        print("✓ All performance modules imported", file=sys.stderr)
        
        from backend.mcp_broker.backtest_engine_v18 import BacktestEngineV18
        from backend.mcp_broker.backtest_engine_v18_optimized import OptimizedBacktestEngineV18
        from backend.mcp_broker.backtest_engine_v18_ultra import BacktestEngineV18Ultra
        print("✓ All engines imported", file=sys.stderr)
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def test_performance_components():
    """Test performance components directly."""
    print("\n" + "="*60, file=sys.stderr)
    print("TEST: Performance Components", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    try:
        from backend.mcp_broker.performance.ultra_mode import UltraPerformanceMode
        import numpy as np
        
        ultra = UltraPerformanceMode()
        
        # Test vectorized position sizing
        portfolios = np.array([100000.0] * 10)
        scores = np.array([80.0, 70, 90, 60, 85, 75, 95, 50, 65, 88])
        
        sizes = ultra.vectorized_position_sizes(portfolios, scores)
        print(f"✓ Position sizing: {len(sizes)} symbols processed", file=sys.stderr)
        print(f"  Sample sizes: {sizes[:3]}", file=sys.stderr)
        
        # Test trailing stops
        entry = np.array([100.0] * 10)
        current = np.array([120.0, 110, 90, 105, 130, 95, 125, 80, 100, 115])
        peak = np.array([140.0, 120, 95, 110, 145, 100, 130, 85, 105, 120])
        
        should_exit, exit_prices = ultra.calculate_trailing_stops(entry, current, peak)
        print(f"✓ Trailing stops: {sum(should_exit)} exits triggered", file=sys.stderr)
        
        return True
        
    except Exception as e:
        print(f"✗ Performance test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def test_parallel_processor():
    """Test parallel processor."""
    print("\n" + "="*60, file=sys.stderr)
    print("TEST: Parallel Processor", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    try:
        from backend.mcp_broker.performance.distributed import ParallelProcessor
        
        processor = ParallelProcessor(max_workers=4)
        
        async def process_item(item):
            await asyncio.sleep(0.1)  # Simulate work
            return item * 2
        
        async def run_test():
            items = list(range(10))
            results = await processor.process_symbols(
                [str(i) for i in items],
                lambda symbol, **kwargs: process_item(int(symbol))
            )
            return results
        
        results = asyncio.run(run_test())
        print(f"✓ Parallel processing: {len(results)} items processed", file=sys.stderr)
        print(f"  Sample results: {list(results.items())[:3]}", file=sys.stderr)
        
        return True
        
    except Exception as e:
        print(f"✗ Parallel test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def test_cache():
    """Test cache component."""
    print("\n" + "="*60, file=sys.stderr)
    print("TEST: Cache", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    try:
        from backend.mcp_broker.performance.cache import BacktestCache
        
        cache = BacktestCache()
        
        # Test without Redis (memory only)
        result = cache._generate_key("test", {"a": 1, "b": 2})
        print(f"✓ Cache key generation: {result}", file=sys.stderr)
        
        # Test serialization
        data = {"signal": "BUY", "score": 85.5}
        serialized = cache._serialize(data)
        deserialized = cache._deserialize(serialized)
        print(f"✓ Serialization: {deserialized == data}", file=sys.stderr)
        
        return True
        
    except Exception as e:
        print(f"✗ Cache test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70, file=sys.stderr)
    print(" "*20 + "INTEGRATION TEST SUITE", file=sys.stderr)
    print("="*70, file=sys.stderr)
    
    tests = [
        ("Imports", test_imports),
        ("Performance Components", test_performance_components),
        ("Parallel Processor", test_parallel_processor),
        ("Cache", test_cache),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}", file=sys.stderr)
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70, file=sys.stderr)
    print("TEST SUMMARY", file=sys.stderr)
    print("="*70, file=sys.stderr)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name:<30} {status}", file=sys.stderr)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print("="*70, file=sys.stderr)
    print(f"Total: {passed}/{total} tests passed", file=sys.stderr)
    print("="*70, file=sys.stderr)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
