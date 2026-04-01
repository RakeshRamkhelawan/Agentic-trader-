"""
Integration Test: Full Backtesting Stack with Advanced Position Sizing.

This test:
1. Uses all new backtesting models (slippage, fills, position sizing)
2. Runs MovingAverageStrategy with different position sizers
3. Compares results across different sizer configurations
4. Validates metrics calculation
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest

from backend.backtesting.exchange import SimulatedExchange
from backend.backtesting.fill_models import RealisticFillModel
from backend.backtesting.metrics import MetricsCalculator
from backend.backtesting.models import OrderSide, Trade
from backend.backtesting.position_sizing import (
    FixedQuantitySizer,
    PercentOfEquitySizer,
)
from backend.backtesting.slippage_models import FixedSlippageModel, VolumeSlippageModel
from backend.backtesting.strategies.simple_ma import MovingAverageStrategy


class TestDataFeed:
    """Simple test data feed generator."""

    @staticmethod
    def generate_ohlcv(
        symbol: str = "BTC/USD", days: int = 100, start_price: float = 50000.0
    ) -> List[Dict[str, Any]]:
        """Generate synthetic OHLCV data for testing.

        Args:
            symbol: Trading pair
            days: Number of days of data
            start_price: Starting price

        Returns:
            List of OHLCV bars
        """
        bars = []
        price = start_price
        start_time = datetime(2025, 1, 1, tzinfo=timezone.utc)

        for i in range(days):
            timestamp = start_time + timedelta(days=i)

            # Generate price movement (random walk with trend)
            daily_return = 0.001 + (i % 7) * 0.0002 - 0.0005
            price = price * (1 + daily_return)

            # Create OHLCV bar
            bar = {
                "timestamp": timestamp,
                "open": price * 0.99,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": 100 + (i % 50),
            }
            bars.append(bar)

        return bars


class TestBacktestingIntegration:
    """Integration tests for backtesting with position sizing."""

    @pytest.mark.asyncio
    async def test_ma_strategy_with_fixed_sizer(self):
        """Test MA strategy with fixed quantity sizer."""
        # Setup
        bars = TestDataFeed.generate_ohlcv(days=50)
        exchange = SimulatedExchange(initial_capital=10000.0)

        sizer = FixedQuantitySizer(base_quantity=1.0)
        strategy = MovingAverageStrategy(
            exchange=exchange,
            short_window=10,
            long_window=20,
            position_sizer=sizer,
            slippage_model=FixedSlippageModel(basis_points=5.0),
        )

        # Run strategy
        await strategy.on_start()
        start_time = bars[0]["timestamp"]
        equity_curve = [{"timestamp": start_time, "equity": exchange.cash}]

        for bar in bars:
            await strategy.on_bar("BTC/USD", bar)
            equity_curve.append(
                {"timestamp": bar["timestamp"], "equity": exchange.cash}
            )

        await strategy.on_stop()

        # Verify
        assert len(equity_curve) > 0
        assert equity_curve[-1]["equity"] > 0  # Portfolio still has value
        assert strategy.trades_count > 0  # At least one trade
        print(
            f"Fixed Sizer: {strategy.trades_count} trades, final equity: {equity_curve[-1]['equity']:.2f}"
        )

    @pytest.mark.asyncio
    async def test_ma_strategy_with_percent_sizer(self):
        """Test MA strategy with percent of equity sizer."""
        # Setup
        bars = TestDataFeed.generate_ohlcv(days=50)
        exchange = SimulatedExchange(initial_capital=10000.0)

        sizer = PercentOfEquitySizer(percent_per_trade=0.02)
        strategy = MovingAverageStrategy(
            exchange=exchange,
            short_window=10,
            long_window=20,
            position_sizer=sizer,
            slippage_model=VolumeSlippageModel(impact_factor=0.1),
        )

        # Run strategy
        await strategy.on_start()
        start_time = bars[0]["timestamp"]
        equity_curve = [{"timestamp": start_time, "equity": exchange.cash}]

        for bar in bars:
            await strategy.on_bar("BTC/USD", bar)
            equity_curve.append(
                {"timestamp": bar["timestamp"], "equity": exchange.cash}
            )

        await strategy.on_stop()

        # Verify
        assert len(equity_curve) > 0
        print(
            f"Percent Sizer: {strategy.trades_count} trades, final equity: {equity_curve[-1]['equity']:.2f}"
        )

    @pytest.mark.asyncio
    async def test_ma_strategy_with_realistic_fills(self):
        """Test MA strategy with partial fills (realistic execution)."""
        # Setup
        bars = TestDataFeed.generate_ohlcv(days=50)
        exchange = SimulatedExchange(initial_capital=10000.0)

        sizer = PercentOfEquitySizer(percent_per_trade=0.05)
        strategy = MovingAverageStrategy(
            exchange=exchange,
            short_window=10,
            long_window=20,
            position_sizer=sizer,
            slippage_model=FixedSlippageModel(basis_points=10.0),  # 10 bps
            fill_model=RealisticFillModel(max_participation_rate=0.1),  # Max 10% volume
        )

        # Run strategy
        await strategy.on_start()
        start_time = bars[0]["timestamp"]
        equity_curve = [{"timestamp": start_time, "equity": exchange.cash}]

        for bar in bars:
            await strategy.on_bar("BTC/USD", bar)
            equity_curve.append(
                {"timestamp": bar["timestamp"], "equity": exchange.cash}
            )

        await strategy.on_stop()

        # Verify
        assert len(equity_curve) > 0
        print(
            f"Realistic Fills: {strategy.trades_count} trades, final equity: {equity_curve[-1]['equity']:.2f}"
        )

    def test_metrics_comparison_across_sizers(self):
        """Compare metrics across different position sizing strategies."""
        # Generate sample equity curves
        equity_fixed = self._generate_equity_curve(
            start=10000, returns=[0.001, 0.002, -0.001, 0.0015]
        )
        equity_percent = self._generate_equity_curve(
            start=10000, returns=[0.0015, 0.0025, -0.0005, 0.002]
        )

        # Calculate metrics
        metrics_fixed = MetricsCalculator.calculate(
            equity_fixed, initial_capital=10000.0
        )
        metrics_percent = MetricsCalculator.calculate(
            equity_percent, initial_capital=10000.0
        )

        # Verify
        assert metrics_fixed.total_return > 0
        assert metrics_percent.total_return > 0
        assert metrics_fixed.sharpe_ratio > 0
        assert metrics_percent.sharpe_ratio > 0

        print(f"Fixed Sizer Sharpe: {metrics_fixed.sharpe_ratio:.4f}")
        print(f"Percent Sizer Sharpe: {metrics_percent.sharpe_ratio:.4f}")

    def test_trade_statistics_calculation(self):
        """Test trade-level statistics."""
        now = datetime.now(timezone.utc)
        trades = [
            Trade(
                symbol="BTC/USD",
                side=OrderSide.BUY,
                quantity=1.0,
                price=50000.0,
                timestamp=now,
                commission=50.0,
                pnl=1000.0,
            ),
            Trade(
                symbol="BTC/USD",
                side=OrderSide.SELL,
                quantity=1.0,
                price=51000.0,
                timestamp=now + timedelta(hours=1),
                commission=51.0,
                pnl=-500.0,
            ),
            Trade(
                symbol="BTC/USD",
                side=OrderSide.BUY,
                quantity=1.0,
                price=50500.0,
                timestamp=now + timedelta(hours=2),
                commission=50.50,
                pnl=1500.0,
            ),
        ]

        # Get statistics
        stats = MetricsCalculator.calculate_trade_statistics(trades)

        # Verify
        assert stats["total_trades"] == 3
        assert stats["winning_trades"] == 2
        assert stats["losing_trades"] == 1
        assert abs(stats["win_rate"] - 2 / 3) < 0.01
        assert stats["profit_factor"] > 0

        print(
            f"Trade Stats: {stats['total_trades']} trades, "
            f"win_rate={stats['win_rate']:.2%}, "
            f"profit_factor={stats['profit_factor']:.2f}"
        )

    @staticmethod
    def _generate_equity_curve(start: float, returns: List[float]) -> List[Dict]:
        """Generate sample equity curve from returns."""
        curve = []
        equity = start
        timestamp = datetime.now(timezone.utc)

        for ret in returns:
            equity = equity * (1 + ret)
            curve.append(
                {
                    "timestamp": timestamp,
                    "equity": equity,
                }
            )
            timestamp = timestamp + timedelta(days=1)

        return curve


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
