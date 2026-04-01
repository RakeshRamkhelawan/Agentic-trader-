"""
Backtest Engine V18 - ULTRA MODE (SaaS Friendly).

Practical performance WITHOUT heavy dependencies:
- Pure NumPy (no CuPy)
- Asyncio parallel (no Ray)
- Redis caching
- Incremental processing

NO GPU required - runs on any standard cloud instance.
"""

import asyncio
import logging
import sys
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

# Configure logging to stderr (CRITICAL for MCP)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# SaaS-friendly imports
from backend.mcp_broker.performance.cache import BacktestCache, CacheConfig
from backend.mcp_broker.performance.distributed import ParallelProcessor, SimpleBacktestRunner
from backend.mcp_broker.performance.metrics import BacktestProfiler
from backend.mcp_broker.performance.ultra_mode import IncrementalBacktest, UltraPerformanceMode

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class UltraBacktestConfig:
    """Configuration for Ultra Mode (SaaS friendly)."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        # Core optimizations (always enabled)
        enable_caching: bool = True,
        enable_parallel: bool = True,
        max_workers: int = 4,
        # SaaS-friendly (no GPU/distributed)
        enable_batching: bool = True,
        enable_incremental: bool = True,
    ):
        self.initial_capital = initial_capital
        self.enable_caching = enable_caching
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.enable_batching = enable_batching
        self.enable_incremental = enable_incremental


class BacktestEngineV18Ultra:
    """
    Ultra backtest engine - SaaS optimized.

    Uses only:
    - NumPy (CPU vectorization)
    - Asyncio (lightweight parallelism)
    - Redis (caching)

    NO GPU, NO Ray, NO complex infrastructure.
    """

    def __init__(self, config: UltraBacktestConfig | None = None):
        self.config = config or UltraBacktestConfig()
        self.ultra = UltraPerformanceMode()
        self.cache: BacktestCache | None = None
        self.parallel = ParallelProcessor(max_workers=self.config.max_workers)
        self.profiler = BacktestProfiler()

    async def initialize(self):
        """Initialize components."""
        logger.info("Initializing Ultra Backtest Engine (SaaS mode)...")

        if self.config.enable_caching:
            self.cache = BacktestCache(CacheConfig())
            await self.cache.connect()
            logger.info("Cache initialized")

        caps = self.ultra.get_capabilities()
        logger.info(f"Capabilities: {caps}")

    async def run_ultra_backtest(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        progress_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """
        Run optimized backtest (SaaS friendly).

        Automatically uses best strategy for symbol count.
        """
        start_time = time.time()

        await self.initialize()

        # Choose strategy based on symbol count
        if len(symbols) <= 2 or not self.config.enable_parallel:
            results = await self._run_sequential(symbols, start_date, end_date)
        else:
            results = await self._run_parallel(symbols, start_date, end_date)

        total_time = time.time() - start_time

        results["ultra_performance"] = {
            "strategy": "parallel" if len(symbols) > 2 else "sequential",
            "total_time_seconds": total_time,
            "symbols": len(symbols),
            "throughput": len(symbols) / total_time if total_time > 0 else 0,
        }

        return results

    async def _run_sequential(
        self, symbols: list[str], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Run sequential backtest (for small symbol sets)."""
        from backend.mcp_broker.backtest_engine_v18_optimized import (
            OptimizedBacktestConfig,
            OptimizedBacktestEngineV18,
        )

        config = OptimizedBacktestConfig(
            enable_caching=self.config.enable_caching,
            enable_parallel_processing=False,
        )

        engine = OptimizedBacktestEngineV18(config)
        return await engine.run_backtest(symbols, start_date, end_date)

    async def _run_parallel(
        self, symbols: list[str], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Run parallel backtest using asyncio."""
        runner = SimpleBacktestRunner(max_workers=self.config.max_workers)

        # Use the optimized backtest function for each symbol
        from backend.mcp_broker.backtest_engine_v18_optimized import run_optimized_backtest

        async def process_symbol(symbol, start, end, capital):
            return await run_optimized_backtest(
                symbols=[symbol],
                start_date=start,
                end_date=end,
                initial_capital=capital,
                enable_parallel=False,
            )

        return await runner.run_backtest(
            symbols, start_date, end_date, process_symbol, self.config.initial_capital
        )

    async def run_incremental_backtest(
        self, symbols: list[str], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Run incremental backtest - only process new dates."""
        if not self.config.enable_incremental:
            return await self.run_ultra_backtest(symbols, start_date, end_date)

        incremental = IncrementalBacktest()
        unprocessed = incremental.get_unprocessed_dates(start_date, end_date)

        if not unprocessed:
            logger.info("All dates already processed")
            return {"status": "cached", "message": "All dates already processed"}

        logger.info(f"Processing {len(unprocessed)} new dates")

        results = await self.run_ultra_backtest(symbols, unprocessed[0], unprocessed[-1])

        for date in unprocessed:
            incremental.mark_processed(date)

        return results


# Convenience function
async def run_ultra_backtest(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100000.0,
    enable_parallel: bool = True,
    max_workers: int = 4,
) -> dict[str, Any]:
    """
    Run ultra-optimized backtest (SaaS friendly).

    Automatically selects best strategy based on workload.
    NO GPU required - runs on standard cloud instances.

    Example:
        results = await run_ultra_backtest(
            symbols=["AAPL", "MSFT"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
    """
    config = UltraBacktestConfig(
        initial_capital=initial_capital,
        enable_parallel=enable_parallel,
        max_workers=max_workers,
    )

    engine = BacktestEngineV18Ultra(config)
    return await engine.run_ultra_backtest(symbols, start_date, end_date)


# Benchmark function (lightweight)
async def benchmark_ultra_mode():
    """Benchmark all optimization levels."""
    symbols = [f"SYM{i}" for i in range(20)]
    end = datetime.now()
    start = end - timedelta(days=7)

    print("\n" + "=" * 60, file=sys.stderr)
    print(" " * 15 + "ULTRA MODE BENCHMARK (SaaS)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Symbols: {len(symbols)} | Days: 7", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Sequential
    print("\n[1/2] Sequential...", file=sys.stderr)
    t0 = time.time()
    await run_ultra_backtest(symbols[:3], start, end, enable_parallel=False)
    seq_time = time.time() - t0
    print(f"  Time: {seq_time:.2f}s", file=sys.stderr)

    # Parallel
    print("\n[2/2] Parallel...", file=sys.stderr)
    t0 = time.time()
    await run_ultra_backtest(symbols, start, end, enable_parallel=True, max_workers=4)
    par_time = time.time() - t0
    print(f"  Time: {par_time:.2f}s", file=sys.stderr)

    # Summary
    print("\n" + "=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Sequential: {seq_time:.2f}s", file=sys.stderr)
    print(
        f"Parallel:   {par_time:.2f}s (speedup: {seq_time/par_time:.2f}x)",
        file=sys.stderr,
    )
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(benchmark_ultra_mode())
