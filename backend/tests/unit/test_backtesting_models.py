"""
Unit Tests for Advanced Backtesting Models.

Tests for Slippage, Fill, and Position Sizing models.
"""

import pytest

from backend.backtesting.fill_models import (
    FullFillModel,
    ProportionalFillModel,
    RealisticFillModel,
)
from backend.backtesting.position_sizing import (
    FixedQuantitySizer,
    KellyCriterionSizer,
    PercentOfEquitySizer,
    RiskBasedSizer,
    VolatilityScaledSizer,
)
from backend.backtesting.slippage_models import (
    FixedSlippageModel,
    OrderSide,
    VolumeSlippageModel,
)


class TestSlippageModels:
    """Test slippage model implementations."""

    def test_fixed_slippage_buy(self):
        """Test fixed slippage on BUY order."""
        model = FixedSlippageModel(basis_points=5.0)
        price = 100.0
        quantity = 1.0
        adjusted_price, slippage_amount = model.apply(price, quantity, OrderSide.BUY)

        # 5 bps = 0.05% = 0.0005
        expected_adjusted = 100.0 * 1.0005
        expected_slippage = 100.0 * 1.0 * 0.0005

        assert abs(adjusted_price - expected_adjusted) < 0.001
        assert abs(slippage_amount - expected_slippage) < 0.001

    def test_fixed_slippage_sell(self):
        """Test fixed slippage on SELL order."""
        model = FixedSlippageModel(basis_points=5.0)
        price = 100.0
        quantity = 1.0
        adjusted_price, slippage_amount = model.apply(price, quantity, OrderSide.SELL)

        # SELL = adverse slippage (price goes down)
        expected_adjusted = 100.0 * 0.9995
        expected_slippage = 100.0 * 1.0 * 0.0005

        assert abs(adjusted_price - expected_adjusted) < 0.001
        assert abs(slippage_amount - expected_slippage) < 0.001

    def test_volume_slippage_large_order(self):
        """Test volume slippage with large order."""
        model = VolumeSlippageModel(impact_factor=0.1, base_bps=2.0)
        price = 100.0
        quantity = 100.0  # Large order
        avg_volume = 1000.0

        adjusted_price, slippage_amount = model.apply(
            price, quantity, OrderSide.BUY, avg_volume
        )

        # Should have more slippage than fixed model
        assert adjusted_price > 100.0 * 1.0005
        assert slippage_amount > 0.05  # > 0.05 USD

    def test_volume_slippage_zero_volume(self):
        """Test volume slippage with zero volume."""
        model = VolumeSlippageModel(impact_factor=0.1, base_bps=2.0)
        price = 100.0
        quantity = 1.0

        adjusted_price, slippage_amount = model.apply(
            price, quantity, OrderSide.BUY, avg_bar_volume=0.0
        )

        # Should use base bps only
        assert adjusted_price > price
        assert slippage_amount > 0.0


class TestFillModels:
    """Test fill model implementations."""

    def test_full_fill_complete(self):
        """Test full fill when volume is sufficient."""
        model = FullFillModel()
        filled, unfilled = model.compute_fill(order_quantity=1.0, available_volume=10.0)

        assert filled == 1.0
        assert unfilled == 0.0

    def test_full_fill_insufficient_volume(self):
        """Test full fill when volume is insufficient."""
        model = FullFillModel()
        filled, unfilled = model.compute_fill(order_quantity=10.0, available_volume=5.0)

        assert filled == 0.0
        assert unfilled == 10.0

    def test_realistic_fill_small_order(self):
        """Test realistic fill with small order."""
        model = RealisticFillModel(max_participation_rate=0.1)
        filled, unfilled = model.compute_fill(
            order_quantity=1.0, available_volume=100.0
        )

        # Max fillable = 100 * 0.1 = 10.0, so 1.0 fills completely
        assert filled == 1.0
        assert unfilled == 0.0

    def test_realistic_fill_large_order(self):
        """Test realistic fill with large order (partial)."""
        model = RealisticFillModel(max_participation_rate=0.1)
        filled, unfilled = model.compute_fill(
            order_quantity=20.0, available_volume=100.0
        )

        # Max fillable = 100 * 0.1 = 10.0
        assert filled == 10.0
        assert unfilled == 10.0

    def test_proportional_fill(self):
        """Test proportional fill model."""
        model = ProportionalFillModel(max_participation_rate=0.5)
        filled, unfilled = model.compute_fill(
            order_quantity=50.0, available_volume=100.0
        )

        # Fill ratio = min(50/100, 0.5) = 0.5
        # Filled = 50 * 0.5 = 25.0
        assert filled == 25.0
        assert unfilled == 25.0


class TestPositionSizers:
    """Test position sizing models."""

    def test_fixed_quantity_sizer(self):
        """Test fixed quantity sizer."""
        sizer = FixedQuantitySizer(base_quantity=1.0)
        quantity = sizer.calculate_quantity(
            signal_strength=1.0, price=100.0, portfolio_value=10000.0
        )

        assert quantity == 1.0

    def test_fixed_quantity_sizer_with_signal(self):
        """Test fixed quantity sizer scaled by signal."""
        sizer = FixedQuantitySizer(base_quantity=1.0)
        quantity = sizer.calculate_quantity(
            signal_strength=0.5, price=100.0, portfolio_value=10000.0
        )

        assert quantity == 0.5

    def test_percent_of_equity_sizer(self):
        """Test percent of equity sizer."""
        sizer = PercentOfEquitySizer(percent_per_trade=0.02)
        quantity = sizer.calculate_quantity(
            signal_strength=1.0, price=100.0, portfolio_value=10000.0
        )

        # 2% of 10000 = 200, /100 = 2.0 shares
        assert quantity == 2.0

    def test_percent_of_equity_sizer_scales_with_portfolio(self):
        """Test percent sizer scales with portfolio value."""
        sizer = PercentOfEquitySizer(percent_per_trade=0.02)
        quantity = sizer.calculate_quantity(
            signal_strength=1.0, price=100.0, portfolio_value=20000.0
        )

        # 2% of 20000 = 400, /100 = 4.0 shares
        assert quantity == 4.0

    def test_risk_based_sizer(self):
        """Test risk-based position sizer."""
        sizer = RiskBasedSizer(risk_per_trade_pct=0.01)
        quantity = sizer.calculate_quantity(
            signal_strength=1.0,
            price=100.0,
            portfolio_value=10000.0,
            stop_loss_pct=0.02,
        )

        # Max loss = 10000 * 0.01 = 100
        # Loss per unit = 100 * 0.02 = 2
        # Quantity = 100 / 2 = 50
        assert quantity == 50.0

    def test_kelly_criterion_basic(self):
        """Test Kelly Criterion sizer (should be non-zero for positive expectancy)."""
        sizer = KellyCriterionSizer(
            win_rate=0.55, avg_win=1.0, avg_loss=1.0, fractional_kelly=0.25
        )
        quantity = sizer.calculate_quantity(
            signal_strength=1.0, price=100.0, portfolio_value=10000.0
        )

        # Kelly = (1.0 * 0.55 - 0.45) / 1.0 = 0.1
        # Fractional (0.25x) = 0.025 of portfolio
        # 10000 * 0.025 / 100 = 2.5
        assert quantity > 0.0
        assert quantity < 3.0

    def test_kelly_criterion_zero_expectancy(self):
        """Test Kelly Criterion with negative expectancy."""
        sizer = KellyCriterionSizer(
            win_rate=0.40,  # 40% win rate, likely negative expectancy
            avg_win=1.0,
            avg_loss=1.0,
            fractional_kelly=0.25,
        )
        quantity = sizer.calculate_quantity(
            signal_strength=1.0, price=100.0, portfolio_value=10000.0
        )

        # Should be zero or very small (negative expectancy)
        assert quantity >= 0.0
        assert quantity < 1.0

    def test_volatility_scaled_sizer(self):
        """Test volatility-scaled position sizer."""
        sizer = VolatilityScaledSizer(target_vol=0.02, base_pct=0.02)

        # Normal volatility = target
        quantity_normal = sizer.calculate_quantity(
            signal_strength=1.0,
            price=100.0,
            portfolio_value=10000.0,
            current_volatility=0.02,
        )

        # High volatility = smaller position
        quantity_high_vol = sizer.calculate_quantity(
            signal_strength=1.0,
            price=100.0,
            portfolio_value=10000.0,
            current_volatility=0.04,
        )

        assert quantity_normal > quantity_high_vol
        assert quantity_normal == 2.0  # baseline 2%
        assert quantity_high_vol == 1.0  # halved due to 2x vol


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
