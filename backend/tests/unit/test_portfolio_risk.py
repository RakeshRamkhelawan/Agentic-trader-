"""
Step 1A — RED Phase: Tests for PortfolioRiskCalculator.
TDD: All tests written FIRST, expected to FAIL until Step 1B implements production code.

Tests cover:
- RiskState creation and validation
- Risk capacity calculation
- Guna-based thresholds and size multipliers
- Kelly Criterion sizing with risk capacity modulation
- evaluate() accept/hold decisions
- Unhappy paths: negative exposure, zero margin, NaN, negative expectancy, missing guna
"""

import math

import pytest

from backend.core.risk.guna_sizing import GunaType
from backend.core.risk.portfolio_risk import PortfolioRiskCalculator, RiskState


class TestRiskStateCreation:
    """Happy path: RiskState model creation and validation."""

    def test_risk_state_creation_with_valid_data(self):
        """RiskState with 8 dimensions returns valid object."""
        state = RiskState(
            exposure=5000.0,
            margin=10000.0,
            var_95=250.0,
            beta=1.1,
            max_drawdown=0.05,
            correlation=0.3,
            liquidity=0.8,
            volatility_percentile=0.6,
        )
        assert state.exposure == 5000.0
        assert state.margin == 10000.0
        assert state.var_95 == 250.0
        assert state.beta == 1.1
        assert state.max_drawdown == 0.05
        assert state.correlation == 0.3
        assert state.liquidity == 0.8
        assert state.volatility_percentile == 0.6


class TestRiskCapacity:
    """Happy path: Risk capacity calculation from exposure and margin."""

    def test_risk_capacity_full_margin_available(self):
        """exposure=0, margin=10000 → capacity=1.0"""
        calc = PortfolioRiskCalculator()
        state = RiskState(
            exposure=0.0,
            margin=10000.0,
            var_95=0.0,
            beta=1.0,
            max_drawdown=0.0,
            correlation=0.0,
            liquidity=1.0,
            volatility_percentile=0.5,
        )
        capacity = calc.get_risk_capacity(state)
        assert capacity == pytest.approx(1.0, abs=0.01)

    def test_risk_capacity_half_used(self):
        """exposure=5000, margin=10000 → capacity=0.5"""
        calc = PortfolioRiskCalculator()
        state = RiskState(
            exposure=5000.0,
            margin=10000.0,
            var_95=125.0,
            beta=1.0,
            max_drawdown=0.02,
            correlation=0.2,
            liquidity=0.9,
            volatility_percentile=0.5,
        )
        capacity = calc.get_risk_capacity(state)
        assert capacity == pytest.approx(0.5, abs=0.01)


class TestGunaThresholds:
    """Happy path: Guna-based risk threshold and size multiplier mapping."""

    def test_guna_sattva_threshold_conservative(self):
        """Sattva guna → risk_threshold=0.3, size_multiplier=0.5"""
        calc = PortfolioRiskCalculator()
        threshold, multiplier = calc.get_guna_risk_params(GunaType.SATTVA)
        assert threshold == pytest.approx(0.3, abs=0.01)
        assert multiplier == pytest.approx(0.5, abs=0.01)

    def test_guna_rajas_threshold_normal(self):
        """Rajas guna → risk_threshold=0.6, size_multiplier=1.0"""
        calc = PortfolioRiskCalculator()
        threshold, multiplier = calc.get_guna_risk_params(GunaType.RAJAS)
        assert threshold == pytest.approx(0.6, abs=0.01)
        assert multiplier == pytest.approx(1.0, abs=0.01)

    def test_guna_tamas_threshold_defensive(self):
        """Tamas guna → risk_threshold=0.8, size_multiplier=0.2"""
        calc = PortfolioRiskCalculator()
        threshold, multiplier = calc.get_guna_risk_params(GunaType.TAMAS)
        assert threshold == pytest.approx(0.8, abs=0.01)
        assert multiplier == pytest.approx(0.2, abs=0.01)


class TestKellySizing:
    """Happy path: Kelly Criterion sizing with modulation."""

    def test_kelly_sizing_positive_expectancy(self):
        """win_rate=0.55, avg_win=1.5, avg_loss=1.0 → positive size"""
        calc = PortfolioRiskCalculator()
        size = calc.calculate_kelly_size(win_rate=0.55, avg_win=1.5, avg_loss=1.0)
        assert size > 0.0

    def test_kelly_sizing_with_risk_capacity_modulation(self):
        """kelly_size × guna_mult × risk_capacity = final_size"""
        calc = PortfolioRiskCalculator()

        # Get raw Kelly size
        kelly_size = calc.calculate_kelly_size(win_rate=0.55, avg_win=1.5, avg_loss=1.0)

        # Get guna multiplier (Rajas = 1.0)
        _, guna_mult = calc.get_guna_risk_params(GunaType.RAJAS)

        # Capacity = 0.9
        risk_capacity = 0.9

        final_size = calc.modulated_size(
            kelly_size=kelly_size,
            guna_multiplier=guna_mult,
            risk_capacity=risk_capacity,
        )

        expected = kelly_size * guna_mult * risk_capacity
        assert final_size == pytest.approx(expected, rel=0.01)


class TestEvaluateDecision:
    """Happy path: evaluate() accept/hold decisions."""

    def test_evaluate_returns_accept_when_capacity_above_threshold(self):
        """capacity=0.7, threshold=0.6 → action="accept" """
        calc = PortfolioRiskCalculator()
        state = RiskState(
            exposure=3000.0,
            margin=10000.0,
            var_95=75.0,
            beta=0.9,
            max_drawdown=0.01,
            correlation=0.1,
            liquidity=0.95,
            volatility_percentile=0.4,
        )
        decision = calc.evaluate(state, guna=GunaType.RAJAS)
        assert decision.action == "accept"

    def test_evaluate_returns_hold_with_reason_when_below_threshold(self):
        """capacity=0.2, threshold=0.6 → action="hold", reason="insufficient_risk_capacity" """
        calc = PortfolioRiskCalculator()
        state = RiskState(
            exposure=8000.0,
            margin=10000.0,
            var_95=400.0,
            beta=1.5,
            max_drawdown=0.08,
            correlation=0.7,
            liquidity=0.3,
            volatility_percentile=0.9,
        )
        decision = calc.evaluate(state, guna=GunaType.RAJAS)
        assert decision.action == "hold"
        assert "insufficient_risk_capacity" in decision.reason


# ── Unhappy Path Tests ──


class TestRiskStateUnhappy:
    """Unhappy path: edge cases and error handling."""

    def test_risk_state_negative_exposure_clamped_to_zero(self):
        """exposure=-100 → clamped to 0.0"""
        state = RiskState(
            exposure=-100.0,
            margin=10000.0,
            var_95=0.0,
            beta=1.0,
            max_drawdown=0.0,
            correlation=0.0,
            liquidity=1.0,
            volatility_percentile=0.5,
        )
        assert state.exposure >= 0.0

    def test_risk_capacity_zero_margin_returns_zero(self):
        """margin=0 → capacity=0.0 (no division by zero)"""
        calc = PortfolioRiskCalculator()
        state = RiskState(
            exposure=0.0,
            margin=0.0,
            var_95=0.0,
            beta=1.0,
            max_drawdown=0.0,
            correlation=0.0,
            liquidity=0.0,
            volatility_percentile=0.5,
        )
        capacity = calc.get_risk_capacity(state)
        assert capacity == 0.0

    def test_kelly_negative_expectancy_returns_zero_size(self):
        """win_rate=0.3, avg_loss > avg_win → size=0.0"""
        calc = PortfolioRiskCalculator()
        size = calc.calculate_kelly_size(win_rate=0.3, avg_win=0.8, avg_loss=1.2)
        assert size == 0.0

    def test_risk_state_nan_values_handled(self):
        """NaN inputs → fallback to defensive defaults."""
        calc = PortfolioRiskCalculator()
        state = RiskState(
            exposure=float("nan"),
            margin=float("nan"),
            var_95=0.0,
            beta=1.0,
            max_drawdown=0.0,
            correlation=0.0,
            liquidity=0.0,
            volatility_percentile=0.5,
        )
        capacity = calc.get_risk_capacity(state)
        assert capacity == 0.0
        assert not math.isnan(capacity)

    def test_evaluate_with_missing_guna_defaults_to_sattva(self):
        """guna=None → conservative threshold (0.3)"""
        calc = PortfolioRiskCalculator()
        state = RiskState(
            exposure=3000.0,
            margin=10000.0,
            var_95=75.0,
            beta=0.9,
            max_drawdown=0.01,
            correlation=0.1,
            liquidity=0.95,
            volatility_percentile=0.4,
        )
        decision = calc.evaluate(state, guna=None)
        # With Sattva defaults (threshold=0.3), capacity=0.7 > 0.3 → accept
        assert decision.action == "accept"
