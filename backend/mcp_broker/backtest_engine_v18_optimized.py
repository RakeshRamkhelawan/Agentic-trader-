"""
Optimized Backtest Engine V18 with Performance Enhancements.

Features:
- Intelligent caching (Redis + in-memory)
- Parallel symbol processing
- Batch MCP tool calls
- Vectorized calculations
- Real-time performance metrics
- Progress reporting
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
import time

from backend.mcp_broker.client import MCPClientWrapper, get_client
from backend.mcp_broker.performance.cache import BacktestCache, CacheConfig, get_cache
from backend.mcp_broker.performance.batch_processor import (
    BatchProcessor,
    BatchConfig,
    VectorizedElementalCalculator,
    process_symbols_batch
)
from backend.mcp_broker.performance.parallel_engine import (
    ParallelBacktestEngine,
    ParallelConfig
)
from backend.mcp_broker.performance.metrics import (
    PerformanceMetricsCollector,
    BacktestProfiler
)


@dataclass
class OptimizedBacktestConfig:
    """Configuration for optimized backtest."""
    # Core settings
    initial_capital: float = 100000.0
    max_position_eur: float = 2000.0

    # Performance settings
    enable_caching: bool = True
    enable_parallel_processing: bool = True
    enable_batch_processing: bool = True
    enable_vectorization: bool = True

    # Parallel settings
    max_workers: int = 4
    symbols_per_worker: int = 10

    # Cache settings
    cache_config: Optional[CacheConfig] = None

    # Batch settings
    batch_config: Optional[BatchConfig] = None

    # Progress
    progress_callback: Optional[Callable[[int, int, Dict], None]] = None
    progress_interval_seconds: int = 10


class OptimizedBacktestEngineV18:
    """
    High-performance backtest engine with advanced optimizations.

    This engine combines multiple performance techniques:
    1. Caching: VedAstro signals, market data, consensus results
    2. Parallel Processing: Multiple symbols simultaneously
    3. Batch Processing: Grouped MCP tool calls
    4. Vectorization: NumPy-based calculations where possible
    5. Metrics: Real-time performance monitoring

    Example:
        engine = OptimizedBacktestEngineV18()
        results = await engine.run_backtest(
            symbols=["AAPL", "MSFT", "GOOGL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
    """

    def __init__(self, config: Optional[OptimizedBacktestConfig] = None):
        self.config = config or OptimizedBacktestConfig()
        self._client: Optional[MCPClientWrapper] = None
        self._cache: Optional[BacktestCache] = None
        self._batch_processor: Optional[BatchProcessor] = None
        self._parallel_engine: Optional[ParallelBacktestEngine] = None
        self._vectorized_calc = VectorizedElementalCalculator()
        self._profiler = BacktestProfiler()
        self._metrics_collector: Optional[PerformanceMetricsCollector] = None

    async def _initialize(self) -> None:
        """Initialize all components."""
        # Initialize client
        self._client = await get_client()

        # Initialize cache
        if self.config.enable_caching:
            self._cache = get_cache(self.config.cache_config)
            await self._cache.connect()

        # Initialize batch processor
        if self.config.enable_batch_processing:
            batch_config = self.config.batch_config or BatchConfig()
            self._batch_processor = BatchProcessor(self._client, batch_config)

        # Initialize parallel engine
        if self.config.enable_parallel_processing:
            parallel_config = ParallelConfig(
                max_workers=self.config.max_workers,
                symbols_per_worker=self.config.symbols_per_worker
            )
            self._parallel_engine = ParallelBacktestEngine(
                self._client,
                self._cache,
                parallel_config
            )

            if self.config.progress_callback:
                self._parallel_engine.on_progress(self.config.progress_callback)

        # Initialize metrics
        self._metrics_collector = self._profiler.start_profiling()

    async def run_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Run optimized backtest.

        Args:
            symbols: List of symbols to backtest
            start_date: Start date
            end_date: End date
            interval: Data interval (1d, 1h, etc.)

        Returns:
            Comprehensive backtest results with performance metrics
        """
        start_time = time.time()

        # Initialize
        await self._initialize()

        # Set up metrics
        self._metrics_collector.set_symbols(symbols)
        self._metrics_collector.set_date_range(start_date, end_date)

        # Choose execution strategy based on configuration
        if self.config.enable_parallel_processing and len(symbols) > 1:
            # Use parallel processing
            results = await self._run_parallel(symbols, start_date, end_date)
        else:
            # Use sequential processing with optimizations
            results = await self._run_sequential(symbols, start_date, end_date, interval)

        # Finalize metrics
        metrics = self._profiler.stop_profiling()

        # Add performance data
        results["performance"] = {
            "total_time_seconds": time.time() - start_time,
            "metrics": metrics.to_dict(),
            "profile_report": self._profiler.generate_report()
        }

        return results

    async def _run_sequential(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Dict[str, Any]:
        """Run sequential backtest with batching."""
        all_trades = []
        all_signals = []
        portfolio_values = []

        # Pre-fetch all market data in batches
        market_data_cache = {}
        if self.config.enable_batch_processing and self._batch_processor:
            with self._metrics_collector.time_section("data_fetch"):
                # Batch fetch market data for all symbols
                market_data_tasks = []
                for symbol in symbols:
                    task = self._fetch_market_data_cached(
                        symbol, start_date, end_date, interval
                    )
                    market_data_tasks.append((symbol, task))

                for symbol, task in market_data_tasks:
                    try:
                        data = await task
                        market_data_cache[symbol] = data
                    except Exception as e:
                        market_data_cache[symbol] = {"error": str(e)}

        # Process each symbol
        for symbol in symbols:
            symbol_result = await self._process_symbol_optimized(
                symbol,
                start_date,
                end_date,
                market_data_cache.get(symbol, {})
            )
            all_trades.extend(symbol_result.get("trades", []))
            all_signals.extend(symbol_result.get("signals", []))
            portfolio_values.append(symbol_result.get("final_portfolio_value", 0))

        return {
            "symbols": symbols,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trades": all_trades,
            "signals": all_signals,
            "final_portfolio_value": sum(portfolio_values),
            "strategy": "sequential_optimized"
        }

    async def _run_parallel(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Run parallel backtest."""
        return await self._parallel_engine.run_parallel_backtest(
            symbols,
            start_date,
            end_date,
            self.config.initial_capital
        )

    async def _fetch_market_data_cached(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Dict:
        """Fetch market data with caching."""
        # Try cache first
        if self.config.enable_caching and self._cache:
            cached = await self._cache.get_market_data(symbol, start_date, end_date, interval)
            if cached is not None:
                await self._metrics_collector.record_cache_hit()
                return {"data": cached, "cached": True}
            await self._metrics_collector.record_cache_miss()

        # Fetch from MCP
        with self._metrics_collector.time_tool_call("data__get_historical_prices"):
            result = await self._client.call_tool(
                "data__get_historical_prices",
                {
                    "symbol": symbol,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "interval": interval
                }
            )

        # Cache result
        if self.config.enable_caching and self._cache and "error" not in result:
            await self._cache.set_market_data(
                symbol, start_date, end_date, result.get("data", []), interval
            )

        return result

    async def _process_symbol_optimized(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        market_data: Dict
    ) -> Dict[str, Any]:
        """Process a single symbol with all optimizations."""
        trades = []
        signals = []
        portfolio_value = self.config.initial_capital / 10  # Allocate per symbol

        # Generate date range
        current_date = start_date
        while current_date <= end_date:
            await self._metrics_collector.record_day_processed()

            try:
                # Get VedAstro signal (cached)
                signal = await self._get_vedastro_signal_cached(symbol, current_date)
                signals.append({
                    "date": current_date.isoformat(),
                    "symbol": symbol,
                    **signal
                })

                vedastro_score = signal.get("score", 50)

                # Quick filter: skip if score too low
                if vedastro_score < 30:
                    current_date += timedelta(days=1)
                    continue

                # Get current price from market data
                price = self._get_price_for_date(market_data, current_date)
                if price is None:
                    current_date += timedelta(days=1)
                    continue

                # Get Elemental consensus (cached)
                consensus = await self._get_elemental_consensus_cached(
                    symbol, current_date, signal
                )

                if consensus.get("should_enter") and portfolio_value > 1000:
                    # Calculate position size
                    position = await self._calculate_position_cached(
                        symbol, portfolio_value, vedastro_score, market_data
                    )

                    position_size = min(
                        position.get("position_size_eur", 1000),
                        self.config.max_position_eur
                    )

                    if position_size > 100:
                        # Execute trade
                        trade = await self._execute_trade(
                            symbol, "buy", position_size / price, price
                        )

                        if trade and "error" not in trade:
                            trades.append(trade)
                            portfolio_value -= position_size
                            await self._metrics_collector.record_trade()

            except Exception as e:
                pass  # Continue to next day

            current_date += timedelta(days=1)

        return {
            "symbol": symbol,
            "trades": trades,
            "signals": signals,
            "final_portfolio_value": portfolio_value
        }

    async def _get_vedastro_signal_cached(
        self,
        symbol: str,
        date: datetime
    ) -> Dict:
        """Get VedAstro signal with caching."""
        # Try cache
        if self.config.enable_caching and self._cache:
            cached = await self._cache.get_vedastro_signal(symbol, date)
            if cached is not None:
                await self._metrics_collector.record_cache_hit()
                return cached
            await self._metrics_collector.record_cache_miss()

        # Fetch from MCP
        with self._metrics_collector.time_tool_call("vedastro__generate_signal"):
            result = await self._client.call_tool(
                "vedastro__generate_signal",
                {"symbol": symbol, "date": date.isoformat()}
            )

        await self._metrics_collector.record_signal()

        # Cache result
        if self.config.enable_caching and self._cache:
            await self._cache.set_vedastro_signal(symbol, date, result)

        return result

    async def _get_elemental_consensus_cached(
        self,
        symbol: str,
        date: datetime,
        signal: Dict
    ) -> Dict:
        """Get Elemental consensus with caching."""
        elemental_scores = {
            "fire": signal.get("fire", 0.5),
            "earth": signal.get("earth", 0.5),
            "water": signal.get("water", 0.5),
            "air": signal.get("air", 0.5)
        }

        # Try cache
        if self.config.enable_caching and self._cache:
            cached = await self._cache.get_elemental_consensus(elemental_scores, date)
            if cached is not None:
                await self._metrics_collector.record_cache_hit()
                return cached
            await self._metrics_collector.record_cache_miss()

        # Use vectorized calculation if enabled
        if self.config.enable_vectorization:
            with self._metrics_collector.time_section("elemental"):
                # Quick vectorized consensus calculation
                votes = list(elemental_scores.values())
                avg_vote = sum(votes) / len(votes)
                should_enter = avg_vote > 0.65 and max(votes) > 0.75

                result = {
                    "should_enter": should_enter,
                    "consensus_strength": avg_vote,
                    "votes": elemental_scores
                }
        else:
            # Use MCP tool
            with self._metrics_collector.time_tool_call("elemental__ether_consensus"):
                result = await self._client.call_tool(
                    "elemental__ether_consensus",
                    {
                        **elemental_scores,
                        "symbol": symbol
                    }
                )

        # Cache result
        if self.config.enable_caching and self._cache:
            await self._cache.set_elemental_consensus(elemental_scores, date, result)

        return result

    async def _calculate_position_cached(
        self,
        symbol: str,
        portfolio_value: float,
        vedastro_score: float,
        market_data: Dict
    ) -> Dict:
        """Calculate position size with caching."""
        # Use vectorized calculation if enabled
        if self.config.enable_vectorization:
            with self._metrics_collector.time_section("elemental"):
                # Vectorized position sizing
                sizes = self._vectorized_calc.vectorized_position_sizes(
                    np.array([portfolio_value]),
                    np.array([vedastro_score])
                )

                return {
                    "position_size_eur": float(sizes[0]),
                    "confidence": vedastro_score / 100.0
                }
        else:
            # Use MCP tool
            with self._metrics_collector.time_tool_call("elemental__fire_position_size"):
                return await self._client.call_tool(
                    "elemental__fire_position_size",
                    {
                        "symbol": symbol,
                        "portfolio_value": portfolio_value,
                        "vedastro_score": vedastro_score,
                        "price_history": market_data.get("prices", [100.0] * 20)
                    }
                )

    async def _execute_trade(
        self,
        symbol: str,
        action: str,
        quantity: float,
        price: float
    ) -> Optional[Dict]:
        """Execute a trade."""
        with self._metrics_collector.time_tool_call("execution__execute_paper_trade"):
            result = await self._client.call_tool(
                "execution__execute_paper_trade",
                {
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "current_price": price
                }
            )

        if "error" not in result:
            return {
                "date": datetime.now().isoformat(),
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "price": price,
                **result
            }
        return None

    def _get_price_for_date(
        self,
        market_data: Dict,
        date: datetime
    ) -> Optional[float]:
        """Extract price for specific date from market data."""
        data = market_data.get("data", [])
        date_str = date.strftime("%Y-%m-%d")

        for entry in data:
            if entry.get("date") == date_str:
                return entry.get("close")

        return None

    async def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report."""
        return self._profiler.generate_report()


# Convenience functions

async def run_optimized_backtest(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100000.0,
    enable_parallel: bool = True,
    max_workers: int = 4,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Run an optimized backtest with all performance features enabled.

    This is the recommended entry point for production backtests.

    Example:
        results = await run_optimized_backtest(
            symbols=["AAPL", "MSFT", "GOOGL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            enable_parallel=True,
            max_workers=4
        )

        print(f"Trades: {results['trades']}")
        print(f"Performance: {results['performance']}")
    """
    config = OptimizedBacktestConfig(
        initial_capital=initial_capital,
        enable_caching=True,
        enable_parallel_processing=enable_parallel,
        enable_batch_processing=True,
        enable_vectorization=True,
        max_workers=max_workers,
        progress_callback=progress_callback
    )

    engine = OptimizedBacktestEngineV18(config)
    return await engine.run_backtest(symbols, start_date, end_date)


# Import numpy for vectorized calculations
try:
    import numpy as np
except ImportError:
    np = None
