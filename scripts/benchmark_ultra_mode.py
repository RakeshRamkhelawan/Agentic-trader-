"""
Ultra Mode Benchmark - Test all optimization levels.

⚠️  CRITICAL: ALL output goes to stderr (stdout reserved for MCP JSON-RPC)
"""

import argparse
import asyncio
import time
import sys
from datetime import datetime, timedelta

# CRITICAL: All output to stderr for MCP compatibility
sys.path.insert(0, "c:\\Users\\rsram\\Downloads\\agentic_trader_platform_1734_20260109_210621")

def log(message):
    """Log to stderr (stdout reserved for MCP JSON-RPC)."""
    print(message, file=sys.stderr)


class UltraBenchmark:
    """Benchmark for SaaS-friendly optimizations."""

    def __init__(self):
        self.results = []

    async def run(self, n_symbols: int, n_days: int, iterations: int = 3):
        """Run benchmark."""
        symbols = [f"SYM{i:04d}" for i in range(n_symbols)]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=n_days)

        log("\n" + "="*60)
        log(" "*15 + "ULTRA MODE BENCHMARK (SaaS)")
        log("="*60)
        log(f"Configuration:")
        log(f"  Symbols: {n_symbols}")
        log(f"  Days: {n_days}")
        log(f"  Iterations: {iterations}")
        log("="*60)

        # Check capabilities
        log("\nChecking capabilities...")
        try:
            from backend.mcp_broker.performance.ultra_mode import UltraPerformanceMode
            ultra = UltraPerformanceMode()
            caps = ultra.get_capabilities()
            log(f"  NumPy: {'OK' if caps['numpy'] else 'MISSING'}")
            log(f"  Asyncio: {'OK' if caps['asyncio'] else 'MISSING'}")
        except Exception as e:
            log(f"  Error: {e}")

        # Run benchmarks
        benchmarks = [
            ("Sequential", self._benchmark_sequential),
            ("Parallel", self._benchmark_parallel),
        ]

        results = []
        baseline_time = None

        for i, (name, bench_func) in enumerate(benchmarks, 1):
            log(f"\n[{i}/{len(benchmarks)}] Benchmarking {name}...")
            try:
                times = []
                for j in range(iterations):
                    t = await bench_func(symbols, start_date, end_date)
                    times.append(t)
                    log(f"  Iteration {j+1}/{iterations}: {t:.2f}s")

                avg_time = sum(times) / len(times)
                if baseline_time is None:
                    baseline_time = avg_time

                speedup = baseline_time / avg_time if avg_time > 0 else 0
                results.append({"name": name, "avg_time": avg_time, "speedup": speedup})
                log(f"  Average: {avg_time:.2f}s (speedup: {speedup:.2f}x)")

            except Exception as e:
                log(f"  ERROR: {e}")
                import traceback
                traceback.print_exc(file=sys.stderr)

        # Summary
        log("\n" + "="*60)
        log("BENCHMARK SUMMARY")
        log("="*60)
        for r in results:
            log(f"{r['name']:<15} {r['avg_time']:>8.2f}s    {r['speedup']:>5.2f}x")
        log("="*60)

        return results

    async def _benchmark_sequential(self, symbols, start, end):
        """Benchmark sequential processing."""
        from backend.mcp_broker.backtest_engine_v18_optimized import (
            OptimizedBacktestEngineV18,
            OptimizedBacktestConfig
        )

        config = OptimizedBacktestConfig(
            enable_caching=True,
            enable_parallel_processing=False,
        )

        engine = OptimizedBacktestEngineV18(config)
        t0 = time.time()
        await engine.run_backtest(symbols[:5], start, end)  # Limit for sequential
        return time.time() - t0

    async def _benchmark_parallel(self, symbols, start, end):
        """Benchmark parallel processing."""
        from backend.mcp_broker.backtest_engine_v18_ultra import run_ultra_backtest

        t0 = time.time()
        await run_ultra_backtest(
            symbols=symbols,
            start_date=start,
            end_date=end,
            enable_parallel=True,
            max_workers=4
        )
        return time.time() - t0


def main():
    parser = argparse.ArgumentParser(description="Ultra Mode Benchmark")
    parser.add_argument("--symbols", type=int, default=20, help="Number of symbols")
    parser.add_argument("--days", type=int, default=7, help="Number of days")
    parser.add_argument("--iterations", type=int, default=2, help="Iterations")

    args = parser.parse_args()

    benchmark = UltraBenchmark()
    asyncio.run(benchmark.run(args.symbols, args.days, args.iterations))


if __name__ == "__main__":
    main()
