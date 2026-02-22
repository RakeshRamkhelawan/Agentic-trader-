"""
Performance Benchmark for Backtest Engine V18.

Compares performance between:
1. V17 baseline (if available)
2. V18 sequential with caching
3. V18 parallel processing
4. V18 with all optimizations

Usage:
    python scripts/benchmark_backtest_performance.py --symbols AAPL,MSFT,GOOGL --days 30
"""

import argparse
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
import json
import sys

# Add project root to path
sys.path.insert(0, "c:\\Users\\rsram\\Downloads\\agentic_trader_platform_1734_20260109_210621")


class PerformanceBenchmark:
    """Benchmark suite for backtest performance."""
    
    def __init__(self):
        self.results = []
    
    async def run_benchmark(
        self,
        symbols: List[str],
        days: int,
        iterations: int = 3
    ) -> Dict[str, Any]:
        """Run comprehensive benchmark."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"\n{'='*60}")
        print(f"BACKTEST PERFORMANCE BENCHMARK")
        print(f"{'='*60}")
        print(f"Symbols: {symbols}")
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        print(f"Iterations per test: {iterations}")
        print(f"{'='*60}\n")
        
        benchmark_results = {
            "config": {
                "symbols": symbols,
                "days": days,
                "iterations": iterations,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "tests": []
        }
        
        # Test 1: V18 Sequential with caching disabled
        print("\n[1/4] Testing V18 Sequential (no cache)...")
        seq_result = await self._benchmark_sequential(
            symbols, start_date, end_date, iterations, enable_cache=False
        )
        benchmark_results["tests"].append(seq_result)
        self._print_result(seq_result)
        
        # Test 2: V18 Sequential with caching enabled
        print("\n[2/4] Testing V18 Sequential (with cache)...")
        seq_cached_result = await self._benchmark_sequential(
            symbols, start_date, end_date, iterations, enable_cache=True
        )
        benchmark_results["tests"].append(seq_cached_result)
        self._print_result(seq_cached_result)
        
        # Test 3: V18 Parallel processing
        print("\n[3/4] Testing V18 Parallel...")
        parallel_result = await self._benchmark_parallel(
            symbols, start_date, end_date, iterations
        )
        benchmark_results["tests"].append(parallel_result)
        self._print_result(parallel_result)
        
        # Test 4: V18 Full optimizations
        print("\n[4/4] Testing V18 Full Optimizations...")
        optimized_result = await self._benchmark_optimized(
            symbols, start_date, end_date, iterations
        )
        benchmark_results["tests"].append(optimized_result)
        self._print_result(optimized_result)
        
        # Calculate speedups
        baseline_time = seq_result["avg_time_seconds"]
        benchmark_results["speedups"] = {
            "cache_vs_no_cache": baseline_time / seq_cached_result["avg_time_seconds"],
            "parallel_vs_sequential": baseline_time / parallel_result["avg_time_seconds"],
            "optimized_vs_baseline": baseline_time / optimized_result["avg_time_seconds"]
        }
        
        # Summary
        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*60}")
        print(f"Cache speedup: {benchmark_results['speedups']['cache_vs_no_cache']:.2f}x")
        print(f"Parallel speedup: {benchmark_results['speedups']['parallel_vs_sequential']:.2f}x")
        print(f"Full optimization speedup: {benchmark_results['speedups']['optimized_vs_baseline']:.2f}x")
        print(f"{'='*60}\n")
        
        return benchmark_results
    
    async def _benchmark_sequential(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        iterations: int,
        enable_cache: bool
    ) -> Dict[str, Any]:
        """Benchmark sequential processing."""
        from backend.mcp_broker.backtest_engine_v18_optimized import (
            OptimizedBacktestEngineV18, 
            OptimizedBacktestConfig
        )
        
        times = []
        
        for i in range(iterations):
            config = OptimizedBacktestConfig(
                enable_caching=enable_cache,
                enable_parallel_processing=False,
                enable_batch_processing=False,
                enable_vectorization=False
            )
            engine = OptimizedBacktestEngineV18(config)
            
            start = time.perf_counter()
            result = await engine.run_backtest(symbols, start_date, end_date)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
            print(f"  Iteration {i+1}/{iterations}: {elapsed:.2f}s")
        
        return {
            "name": f"Sequential {'(cached)' if enable_cache else '(no cache)'}",
            "avg_time_seconds": sum(times) / len(times),
            "min_time_seconds": min(times),
            "max_time_seconds": max(times),
            "trades": result.get("trades", []),
            "iterations": iterations
        }
    
    async def _benchmark_parallel(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        iterations: int
    ) -> Dict[str, Any]:
        """Benchmark parallel processing."""
        from backend.mcp_broker.backtest_engine_v18_optimized import (
            OptimizedBacktestEngineV18, 
            OptimizedBacktestConfig
        )
        
        times = []
        
        for i in range(iterations):
            config = OptimizedBacktestConfig(
                enable_caching=True,
                enable_parallel_processing=True,
                enable_batch_processing=True,
                max_workers=min(4, len(symbols))
            )
            engine = OptimizedBacktestEngineV18(config)
            
            start = time.perf_counter()
            result = await engine.run_backtest(symbols, start_date, end_date)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
            print(f"  Iteration {i+1}/{iterations}: {elapsed:.2f}s")
        
        return {
            "name": "Parallel",
            "avg_time_seconds": sum(times) / len(times),
            "min_time_seconds": min(times),
            "max_time_seconds": max(times),
            "trades": result.get("trades", []),
            "iterations": iterations
        }
    
    async def _benchmark_optimized(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        iterations: int
    ) -> Dict[str, Any]:
        """Benchmark fully optimized processing."""
        from backend.mcp_broker.backtest_engine_v18_optimized import (
            run_optimized_backtest
        )
        
        times = []
        
        for i in range(iterations):
            start = time.perf_counter()
            result = await run_optimized_backtest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                enable_parallel=True,
                max_workers=min(4, len(symbols))
            )
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
            print(f"  Iteration {i+1}/{iterations}: {elapsed:.2f}s")
        
        return {
            "name": "Full Optimizations",
            "avg_time_seconds": sum(times) / len(times),
            "min_time_seconds": min(times),
            "max_time_seconds": max(times),
            "trades": result.get("trades", []),
            "iterations": iterations,
            "performance": result.get("performance", {})
        }
    
    def _print_result(self, result: Dict[str, Any]) -> None:
        """Print benchmark result."""
        print(f"  Average: {result['avg_time_seconds']:.2f}s")
        print(f"  Min: {result['min_time_seconds']:.2f}s")
        print(f"  Max: {result['max_time_seconds']:.2f}s")
        if 'trades' in result:
            print(f"  Trades: {len(result['trades'])}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Backtest Engine V18 Performance"
    )
    parser.add_argument(
        "--symbols",
        default="AAPL,MSFT,GOOGL",
        help="Comma-separated list of symbols to test"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to backtest"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations per test"
    )
    parser.add_argument(
        "--output",
        default="benchmark_results.json",
        help="Output file for results"
    )
    
    args = parser.parse_args()
    
    symbols = args.symbols.split(",")
    
    benchmark = PerformanceBenchmark()
    results = asyncio.run(benchmark.run_benchmark(
        symbols=symbols,
        days=args.days,
        iterations=args.iterations
    ))
    
    # Save results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
