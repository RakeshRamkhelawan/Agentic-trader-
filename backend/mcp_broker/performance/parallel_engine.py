"""
Parallel backtest execution engine for maximum performance.

Provides:
- Multi-symbol parallel processing
- Workload partitioning strategies
- Result aggregation
- Resource monitoring
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from backend.mcp_broker.client import MCPClientWrapper
from backend.mcp_broker.performance.batch_processor import BatchProcessor
from backend.mcp_broker.performance.cache import BacktestCache


@dataclass
class ParallelConfig:
    """Configuration for parallel execution."""

    max_workers: int = 4  # Number of parallel workers
    symbols_per_worker: int = 10  # Symbols assigned to each worker
    chunk_size_days: int = 30  # Days to process per chunk
    enable_work_stealing: bool = True  # Load balancing
    result_aggregation: str = "immediate"  # or "deferred"
    progress_interval_seconds: int = 10


@dataclass
class WorkerResult:
    """Result from a single worker."""

    worker_id: int
    symbols: list[str]
    trades: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0


class SymbolPartitioner:
    """
    Intelligent symbol partitioning for parallel processing.

    Strategies:
    - Round-robin: Distribute evenly
    - By volatility: Group similar volatility symbols
    - By sector: Keep related symbols together
    """

    @staticmethod
    def round_robin(symbols: list[str], num_partitions: int) -> list[list[str]]:
        """Distribute symbols evenly across partitions."""
        partitions = [[] for _ in range(num_partitions)]
        for i, symbol in enumerate(symbols):
            partitions[i % num_partitions].append(symbol)
        return partitions

    @staticmethod
    def by_volatility(
        symbols: list[str], volatility_data: dict[str, float], num_partitions: int
    ) -> list[list[str]]:
        """Partition by volatility to balance computational load."""
        # Sort by volatility
        sorted_symbols = sorted(symbols, key=lambda s: volatility_data.get(s, 0.5), reverse=True)

        # Distribute high/low volatility evenly
        partitions = [[] for _ in range(num_partitions)]
        for i, symbol in enumerate(sorted_symbols):
            # Alternate direction for better balance
            partition_idx = (
                i % num_partitions
                if (i // num_partitions) % 2 == 0
                else (num_partitions - 1 - i % num_partitions)
            )
            partitions[partition_idx].append(symbol)

        return partitions

    @staticmethod
    def by_sector(
        symbols: list[str], sector_data: dict[str, str], num_partitions: int
    ) -> list[list[str]]:
        """Partition by sector to keep related symbols together."""
        # Group by sector
        sectors: dict[str, list[str]] = {}
        for symbol in symbols:
            sector = sector_data.get(symbol, "unknown")
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(symbol)

        # Distribute sectors across partitions
        partitions = [[] for _ in range(num_partitions)]
        partition_idx = 0
        for sector_symbols in sectors.values():
            for symbol in sector_symbols:
                partitions[partition_idx].append(symbol)
                partition_idx = (partition_idx + 1) % num_partitions

        return partitions

    @staticmethod
    def adaptive(
        symbols: list[str],
        historical_performance: dict[str, float],
        num_partitions: int,
    ) -> list[list[str]]:
        """
        Adaptive partitioning based on historical processing times.

        Uses greedy bin-packing to balance expected workload.
        """
        # Sort by expected processing time (descending)
        sorted_symbols = sorted(
            symbols, key=lambda s: historical_performance.get(s, 1.0), reverse=True
        )

        # Greedy assignment to least-loaded partition
        partitions: list[list[str]] = [[] for _ in range(num_partitions)]
        partition_loads = [0.0] * num_partitions

        for symbol in sorted_symbols:
            load = historical_performance.get(symbol, 1.0)
            # Find partition with minimum load
            min_idx = partition_loads.index(min(partition_loads))
            partitions[min_idx].append(symbol)
            partition_loads[min_idx] += load

        return partitions


class ParallelBacktestEngine:
    """
    High-performance parallel backtest engine.

    Executes backtests across multiple symbols in parallel,
    with intelligent partitioning and result aggregation.
    """

    def __init__(
        self,
        mcp_client: MCPClientWrapper,
        cache: BacktestCache | None = None,
        config: ParallelConfig | None = None,
    ):
        self.client = mcp_client
        self.cache = cache
        self.config = config or ParallelConfig()
        self.batch_processor = BatchProcessor(mcp_client)
        self._workers: list[asyncio.Task] = []
        self._progress_callbacks: list[Callable] = []

    def on_progress(self, callback: Callable[[int, int, dict], None]) -> None:
        """Register a progress callback."""
        self._progress_callbacks.append(callback)

    async def _notify_progress(self, completed: int, total: int, details: dict) -> None:
        """Notify all progress callbacks."""
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(completed, total, details)
                else:
                    callback(completed, total, details)
            except Exception:
                pass  # Don't let callbacks break execution

    async def _worker_loop(
        self,
        worker_id: int,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        result_queue: asyncio.Queue,
    ) -> None:
        """
        Worker process for a subset of symbols.
        """
        start_time = time.time()
        worker_result = WorkerResult(worker_id=worker_id, symbols=symbols)

        try:
            # Process each symbol
            for symbol in symbols:
                try:
                    # Run backtest for single symbol
                    symbol_result = await self._run_symbol_backtest(
                        symbol, start_date, end_date, initial_capital / len(symbols)
                    )

                    worker_result.trades.extend(symbol_result.get("trades", []))
                    worker_result.metrics[symbol] = symbol_result.get("metrics", {})

                except Exception as e:
                    worker_result.errors.append(f"{symbol}: {str(e)}")

        except Exception as e:
            worker_result.errors.append(f"Worker {worker_id} failed: {str(e)}")

        finally:
            worker_result.processing_time_seconds = time.time() - start_time
            await result_queue.put(worker_result)

    async def _run_symbol_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        allocated_capital: float,
    ) -> dict[str, Any]:
        """Run backtest for a single symbol."""
        trades = []
        current_date = start_date
        capital = allocated_capital

        # Generate date range
        while current_date <= end_date:
            try:
                # Get market data
                market_data = await self.client.call_tool(
                    "data__get_historical_prices",
                    {
                        "symbol": symbol,
                        "start_date": current_date.isoformat(),
                        "end_date": current_date.isoformat(),
                    },
                )

                if not market_data or "error" in market_data:
                    current_date += timedelta(days=1)
                    continue

                price = market_data.get("close", 100.0)

                # Get VedAstro signal
                signal = await self.client.call_tool(
                    "vedastro__generate_signal",
                    {"symbol": symbol, "current_price": price},
                )

                vedastro_score = signal.get("score", 50)

                # Get Elemental consensus
                consensus = await self.client.call_tool(
                    "elemental__ether_consensus",
                    {
                        "fire_vote": signal.get("fire", 0.5),
                        "earth_vote": signal.get("earth", 0.5),
                        "water_vote": signal.get("water", 0.5),
                        "air_vote": signal.get("air", 0.5),
                        "symbol": symbol,
                    },
                )

                if consensus.get("should_enter") and capital > 1000:
                    # Get position size
                    position = await self.client.call_tool(
                        "elemental__fire_position_size",
                        {
                            "symbol": symbol,
                            "portfolio_value": capital,
                            "vedastro_score": vedastro_score,
                            "price_history": market_data.get("prices", [price] * 20),
                        },
                    )

                    position_size = position.get("position_size_eur", 1000)

                    if position_size > 100:
                        # Execute trade
                        trade_result = await self.client.call_tool(
                            "execution__execute_paper_trade",
                            {
                                "symbol": symbol,
                                "action": "buy",
                                "quantity": position_size / price,
                                "current_price": price,
                            },
                        )

                        if "error" not in trade_result:
                            trades.append(
                                {
                                    "date": current_date.isoformat(),
                                    "symbol": symbol,
                                    "action": "buy",
                                    "price": price,
                                    "size": position_size,
                                    "pnl": trade_result.get("pnl", 0),
                                }
                            )
                            capital -= position_size

            except Exception:
                pass  # Continue to next date

            current_date += timedelta(days=1)

        return {
            "trades": trades,
            "metrics": {
                "total_trades": len(trades),
                "final_capital": capital,
                "allocated_capital": allocated_capital,
            },
        }

    async def run_parallel_backtest(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
        partition_strategy: str = "round_robin",
    ) -> dict[str, Any]:
        """
        Run parallel backtest across multiple symbols.

        Args:
            symbols: List of symbols to backtest
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Starting capital
            partition_strategy: "round_robin", "volatility", "sector", "adaptive"

        Returns:
            Combined backtest results
        """
        total_start_time = time.time()

        # Partition symbols
        if partition_strategy == "round_robin":
            partitions = SymbolPartitioner.round_robin(symbols, self.config.max_workers)
        else:
            # Default to round-robin for other strategies
            partitions = SymbolPartitioner.round_robin(symbols, self.config.max_workers)

        # Remove empty partitions
        partitions = [p for p in partitions if p]

        # Result queue
        result_queue: asyncio.Queue = asyncio.Queue()

        # Start workers
        workers = []
        for worker_id, partition in enumerate(partitions):
            worker = asyncio.create_task(
                self._worker_loop(
                    worker_id,
                    partition,
                    start_date,
                    end_date,
                    initial_capital,
                    result_queue,
                )
            )
            workers.append(worker)

        # Wait for all workers with progress reporting
        completed_workers = 0
        total_workers = len(workers)

        while completed_workers < total_workers:
            try:
                # Wait for next result with timeout for progress updates
                result = await asyncio.wait_for(
                    result_queue.get(), timeout=self.config.progress_interval_seconds
                )
                completed_workers += 1

                await self._notify_progress(
                    completed_workers,
                    total_workers,
                    {
                        "worker_id": result.worker_id,
                        "symbols_processed": len(result.symbols),
                        "trades": len(result.trades),
                        "errors": len(result.errors),
                        "time": result.processing_time_seconds,
                    },
                )

            except TimeoutError:
                # Progress update
                await self._notify_progress(
                    completed_workers, total_workers, {"status": "in_progress"}
                )

        # Collect all results
        all_results = []
        while not result_queue.empty():
            all_results.append(await result_queue.get())

        # Aggregate results
        all_trades = []
        all_metrics = {}
        all_errors = []
        total_worker_time = 0.0

        for result in all_results:
            all_trades.extend(result.trades)
            all_metrics.update(result.metrics)
            all_errors.extend(result.errors)
            total_worker_time += result.processing_time_seconds

        total_time = time.time() - total_start_time

        return {
            "status": "completed",
            "symbols": symbols,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "initial_capital": initial_capital,
            "total_trades": len(all_trades),
            "trades": all_trades,
            "symbol_metrics": all_metrics,
            "errors": all_errors,
            "performance": {
                "total_time_seconds": total_time,
                "worker_time_seconds": total_worker_time,
                "parallel_efficiency": (total_worker_time / total_time if total_time > 0 else 0),
                "symbols_per_second": (len(symbols) / total_time if total_time > 0 else 0),
                "trades_per_second": (len(all_trades) / total_time if total_time > 0 else 0),
            },
        }

    async def run_chunked_backtest(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
    ) -> dict[str, Any]:
        """
        Run backtest in time chunks for memory efficiency.

        Processes data in chunks (e.g., monthly) to limit memory usage.
        """
        chunk_results = []
        current_start = start_date

        while current_start < end_date:
            current_end = min(current_start + timedelta(days=self.config.chunk_size_days), end_date)

            # Run backtest for this chunk
            chunk_result = await self.run_parallel_backtest(
                symbols,
                current_start,
                current_end,
                initial_capital / ((end_date - start_date).days / self.config.chunk_size_days),
                "round_robin",
            )

            chunk_results.append(chunk_result)
            current_start = current_end + timedelta(days=1)

        # Aggregate chunk results
        all_trades = []
        for chunk in chunk_results:
            all_trades.extend(chunk.get("trades", []))

        return {
            "status": "completed",
            "chunks_processed": len(chunk_results),
            "total_trades": len(all_trades),
            "trades": all_trades,
            "chunk_details": chunk_results,
        }
