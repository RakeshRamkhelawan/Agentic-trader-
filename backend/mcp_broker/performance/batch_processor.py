"""
Batch processing and vectorized calculations for backtest performance.

Provides:
- Batch MCP tool calls for multiple symbols
- Vectorized Elemental calculations using numpy/pandas
- Parallel preprocessing of market data
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

# Optional pandas import
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from backend.mcp_broker.client import MCPClientWrapper


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    max_batch_size: int = 50  # Max symbols per batch
    max_concurrent_calls: int = 10  # Max parallel MCP calls
    use_vectorization: bool = True
    prefetch_lookahead_days: int = 5  # Prefetch data N days ahead


class BatchProcessor:
    """
    High-performance batch processor for backtest operations.

    Optimizes MCP tool calls by:
    - Grouping similar operations
    - Parallel execution with semaphore control
    - Intelligent prefetching
    """

    def __init__(self, mcp_client: MCPClientWrapper, config: BatchConfig | None = None):
        self.client = mcp_client
        self.config = config or BatchConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_calls)
        self._prefetch_queue: asyncio.Queue = asyncio.Queue()
        self._cache: dict[str, Any] = {}

    async def batch_call_tool(self, tool_name: str, params_list: list[dict[str, Any]]) -> list[Any]:
        """
        Execute multiple MCP tool calls in parallel with concurrency control.

        Args:
            tool_name: Name of the MCP tool to call
            params_list: List of parameter dictionaries

        Returns:
            List of results in same order as params_list
        """

        async def _call_single(params: dict) -> Any:
            async with self._semaphore:
                try:
                    return await self.client.call_tool(tool_name, params)
                except Exception as e:
                    return {"error": str(e), "params": params}

        # Create tasks for all calls
        tasks = [_call_single(params) for params in params_list]

        # Execute all with gather
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({"error": str(result), "params": params_list[i]})
            else:
                processed_results.append(result)

        return processed_results

    async def batch_elemental_consensus(
        self, symbol_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Batch process Elemental consensus for multiple symbols.

        Args:
            symbol_data: List of dicts with 'symbol', 'fire_vote', etc.

        Returns:
            List of consensus results
        """
        params_list = [
            {
                "fire_vote": data.get("fire_vote", 0.5),
                "earth_vote": data.get("earth_vote", 0.5),
                "water_vote": data.get("water_vote", 0.5),
                "air_vote": data.get("air_vote", 0.5),
                "symbol": data["symbol"],
            }
            for data in symbol_data
        ]

        return await self.batch_call_tool("elemental__ether_consensus", params_list)

    async def batch_position_sizes(self, symbol_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Batch calculate position sizes for multiple symbols.

        Args:
            symbol_data: List of dicts with portfolio and VedAstro data

        Returns:
            List of position size results
        """
        params_list = [
            {
                "symbol": data["symbol"],
                "portfolio_value": data["portfolio_value"],
                "vedastro_score": data.get("vedastro_score", 50),
                "price_history": data.get("price_history", [100.0] * 20),
            }
            for data in symbol_data
        ]

        return await self.batch_call_tool("elemental__fire_position_size", params_list)

    async def batch_vedastro_signals(
        self, symbol_date_pairs: list[tuple[str, datetime]]
    ) -> list[dict[str, Any]]:
        """
        Batch fetch VedAstro signals for multiple symbol/date pairs.

        Args:
            symbol_date_pairs: List of (symbol, date) tuples

        Returns:
            List of signal results
        """
        params_list = [
            {
                "symbol": symbol,
                "current_price": 100.0,  # Will be updated with actual price
                "date": date.isoformat(),
            }
            for symbol, date in symbol_date_pairs
        ]

        return await self.batch_call_tool("vedastro__generate_signal", params_list)

    async def prefetch_market_data(
        self, symbols: list[str], current_date: datetime, days_ahead: int | None = None
    ) -> None:
        """
        Prefetch market data for upcoming dates.

        This runs in background to warm the cache.
        """
        days = days_ahead or self.config.prefetch_lookahead_days

        async def _prefetch_symbol(symbol: str) -> None:
            for offset in range(1, days + 1):
                target_date = current_date + timedelta(days=offset)
                try:
                    await self.client.call_tool(
                        "data__get_historical_prices",
                        {
                            "symbol": symbol,
                            "start_date": target_date.isoformat(),
                            "end_date": target_date.isoformat(),
                        },
                    )
                except Exception:
                    pass  # Prefetch errors are non-critical

        # Start prefetch tasks in background
        tasks = [_prefetch_symbol(s) for s in symbols]
        asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))


class VectorizedElementalCalculator:
    """
    Vectorized calculations for Elemental agents using numpy.

    Performs batch calculations without MCP calls for simple operations.
    """

    def __init__(self):
        self.max_position_eur = 2000.0
        self.commission_pct = 0.0005
        self.slippage_pct = 0.001

    def vectorized_position_sizes(
        self,
        portfolio_values: np.ndarray,
        vedastro_scores: np.ndarray,
        confidences: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Calculate position sizes for multiple symbols vectorized.

        Args:
            portfolio_values: Array of portfolio values
            vedastro_scores: Array of VedAstro scores (0-100)
            confidences: Optional array of confidence values

        Returns:
            Array of position sizes respecting €2k cap
        """
        if confidences is None:
            confidences = np.ones_like(vedastro_scores) * 0.7

        # Base position: 10% of portfolio * confidence
        base_sizes = portfolio_values * 0.10 * confidences

        # Scale by VedAstro score (linear interpolation)
        score_multipliers = 0.5 + (vedastro_scores / 100.0) * 0.5
        scaled_sizes = base_sizes * score_multipliers

        # Apply 2% portfolio limit
        max_by_portfolio = portfolio_values * 0.02

        # Apply €2k absolute cap
        absolute_cap = self.max_position_eur

        # Final size: min of all constraints
        position_sizes = np.minimum(np.minimum(scaled_sizes, max_by_portfolio), absolute_cap)

        return position_sizes

    def vectorized_trailing_stops(
        self, entry_prices: np.ndarray, current_prices: np.ndarray, highest_prices: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Vectorized trailing stop calculation.

        Returns:
            Tuple of (should_exit, exit_prices)
        """
        # Calculate returns from entry
        total_returns = (current_prices - entry_prices) / entry_prices

        # Calculate drawdown from peak
        peak_returns = (highest_prices - entry_prices) / entry_prices
        current_from_peak = (current_prices - highest_prices) / highest_prices

        # Trailing stop triggered if:
        # 1. Up 40% from entry AND down 15% from peak
        trailing_triggered = (peak_returns >= 0.40) & (current_from_peak <= -0.15)

        # Or 2. Down 20% from entry (hard stop)
        hard_stop = total_returns <= -0.20

        should_exit = trailing_triggered | hard_stop

        # Exit price is current price minus slippage
        exit_prices = current_prices * (1 - self.slippage_pct)

        return should_exit, exit_prices

    def vectorized_commission_slippage(
        self, quantities: np.ndarray, prices: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate commission and slippage for multiple trades.

        Returns:
            Tuple of (commissions, slippage_costs, net_values)
        """
        gross_values = quantities * prices

        commissions = gross_values * self.commission_pct
        slippage_costs = gross_values * self.slippage_pct

        net_values = gross_values - commissions - slippage_costs

        return commissions, slippage_costs, net_values

    def vectorized_kelly_sizing(
        self,
        win_rates: np.ndarray,
        avg_wins: np.ndarray,
        avg_losses: np.ndarray,
        portfolio_values: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate Kelly criterion position sizes vectorized.

        Kelly % = W - (1-W)/R
        where W = win rate, R = win/loss ratio
        """
        # Avoid division by zero
        avg_losses_safe = np.maximum(avg_losses, 0.001)
        win_loss_ratios = avg_wins / avg_losses_safe

        # Kelly percentage
        kelly_pcts = win_rates - (1 - win_rates) / win_loss_ratios

        # Half-Kelly for safety
        half_kelly_pcts = np.maximum(kelly_pcts * 0.5, 0)

        # Apply to portfolio
        position_sizes = portfolio_values * half_kelly_pcts

        # Cap at €2k
        return np.minimum(position_sizes, self.max_position_eur)

    def batch_elemental_scores(
        self, price_histories: list[list[float]], lookback: int = 20
    ) -> dict[str, np.ndarray]:
        """
        Calculate Elemental scores for multiple symbols from price history.

        Returns:
            Dict with arrays for each element
        """
        n = len(price_histories)

        fire_scores = np.zeros(n)
        earth_scores = np.zeros(n)
        water_scores = np.zeros(n)
        air_scores = np.zeros(n)

        for i, prices in enumerate(price_histories):
            if len(prices) < lookback:
                continue

            prices_arr = np.array(prices[-lookback:])

            # Fire: Momentum (price change velocity)
            if len(prices_arr) > 1:
                returns = np.diff(prices_arr) / prices_arr[:-1]
                fire_scores[i] = np.mean(returns) * 100 + 50  # Center at 50

            # Earth: Volatility stability (inverse of volatility)
            volatility = np.std(returns) if len(returns) > 0 else 0
            earth_scores[i] = max(0, 100 - volatility * 100)

            # Water: Trend strength (RSI-like)
            gains = np.sum(returns[returns > 0]) if len(returns) > 0 else 0
            losses = abs(np.sum(returns[returns < 0])) if len(returns) > 0 else 0.001
            water_scores[i] = 100 - (100 / (1 + gains / losses))

            # Air: Volume/momentum oscillation
            if len(returns) >= 5:
                air_scores[i] = 50 + (returns[-1] - np.mean(returns[-5:])) * 100

        # Normalize to 0-100
        fire_scores = np.clip(fire_scores, 0, 100)
        earth_scores = np.clip(earth_scores, 0, 100)
        water_scores = np.clip(water_scores, 0, 100)
        air_scores = np.clip(air_scores, 0, 100)

        return {
            "fire": fire_scores,
            "earth": earth_scores,
            "water": water_scores,
            "air": air_scores,
        }


# Convenience function for batch processing
async def process_symbols_batch(
    mcp_client: MCPClientWrapper,
    symbols: list[str],
    portfolio_value: float,
    vedastro_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Process a batch of symbols efficiently.

    Returns combined results for entry decisions and position sizing.
    """
    processor = BatchProcessor(mcp_client)
    calculator = VectorizedElementalCalculator()

    # Prepare symbol data
    symbol_data = []
    for symbol in symbols:
        symbol_data.append(
            {
                "symbol": symbol,
                "portfolio_value": portfolio_value,
                "vedastro_score": vedastro_scores.get(symbol, 50) if vedastro_scores else 50,
                "price_history": [100.0] * 20,  # Placeholder, should be actual data
            }
        )

    # Batch get consensus and position sizes
    consensus_results = await processor.batch_elemental_consensus(symbol_data)
    position_results = await processor.batch_position_sizes(symbol_data)

    # Combine results
    combined = {}
    for i, symbol in enumerate(symbols):
        combined[symbol] = {
            "consensus": consensus_results[i] if i < len(consensus_results) else None,
            "position_size": position_results[i] if i < len(position_results) else None,
        }

    return combined
