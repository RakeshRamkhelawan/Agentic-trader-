import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from backend.backtesting.data_feed import DataFeed
from backend.backtesting.exchange import SimulatedExchange
from backend.backtesting.metrics import MetricsCalculator
from backend.backtesting.models import (BacktestConfig, BacktestMetrics,
                                        BacktestResult)
from backend.backtesting.strategy import Strategy

_logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Orchestrates the backtest simulation.
    """

    def __init__(self, data_feed: DataFeed, initial_capital: float = 10000.0):
        self.data_feed = data_feed
        self.exchange = SimulatedExchange(initial_capital)
        self.equity_curve = []

    async def run(self, strategy: Strategy, config: BacktestConfig) -> BacktestResult:
        """Run the backtest loop."""
        _logger.info(f"Starting backtest for {config.strategy_name}")

        await strategy.on_start()

        # Main Loop
        while self.data_feed.next():
            current_time = self.data_feed.current_time()
            if current_time > config.end_date:
                break

            # Update Exchange Prices
            current_prices = {}
            for symbol in config.symbols:
                bar = self.data_feed.get_latest_bar(symbol)
                if bar:
                    close_price = bar["close"]
                    current_prices[symbol] = close_price

                    # Notify Strategy
                    await strategy.on_bar(symbol, bar)

            # Helper: Force exchange to execute pending orders (if we were modeling limits/stops)
            # For now, SimulatedExchange executes market orders immediately in strategy.

            # Track Equity
            equity = self.exchange.get_equity(current_prices)
            self.equity_curve.append({"timestamp": current_time, "equity": equity})

        await strategy.on_stop()

        # Calculate Metrics
        metrics = MetricsCalculator.calculate(
            self.equity_curve, self.exchange.initial_capital
        )
        metrics.total_trades = len(self.exchange.trades)

        # Calculate Win Rate
        winning_trades = [t for t in self.exchange.trades if (t.pnl or 0) > 0]
        if metrics.total_trades > 0:
            metrics.win_rate = len(winning_trades) / metrics.total_trades

        return BacktestResult(
            config=config,
            metrics=metrics,
            equity_curve=self.equity_curve,
            trades=self.exchange.trades,
            logs=[],
        )
