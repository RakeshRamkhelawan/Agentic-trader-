"""
Unit tests for Optimized VaR Calculator with Numba JIT (Sprint 2).
"""

import time

import numpy as np
import pandas as pd
import pytest

from backend.risk.var_calculator_optimized import (
    VaRCalculatorOptimized,
    VaRCalculationError,
    _warmup_jit_functions,
)


@pytest.fixture
def var_calculator():
    """Create a VaR calculator with warmup."""
    return VaRCalculatorOptimized(warmup=True)


@pytest.fixture
def sample_returns():
    """Create sample returns data."""
    np.random.seed(42)
    return pd.Series(np.random.randn(1000) * 0.02)  # 2% volatility


@pytest.fixture
def large_returns():
    """Create large returns dataset for performance testing."""
    np.random.seed(42)
    return pd.Series(np.random.randn(10000) * 0.02)


class TestJITAvailability:
    """Test cases for JIT availability check."""

    def test_numba_availability(self):
        """Test that Numba is available in test environment."""
        from backend.risk.var_calculator_optimized import NUMBA_AVAILABLE

        # This test documents whether Numba is installed
        # In production, we expect NUMBA_AVAILABLE to be True
        print(f"\nNumba available: {NUMBA_AVAILABLE}")


class TestVaRCalculation:
    """Test cases for VaR calculation."""

    def test_var_95_percent(self, var_calculator, sample_returns):
        """Test 95% VaR calculation."""
        var = var_calculator.calculate_historical_var(sample_returns, 0.95)

        # VaR should be negative (loss)
        assert var < 0

        # For normal distribution with 2% vol, 95% VaR should be around -3.3%
        assert -0.05 < var < -0.01

    def test_var_99_percent(self, var_calculator, sample_returns):
        """Test 99% VaR calculation."""
        var_95 = var_calculator.calculate_historical_var(sample_returns, 0.95)
        var_99 = var_calculator.calculate_historical_var(sample_returns, 0.99)

        # 99% VaR should be worse (more negative) than 95%
        assert var_99 < var_95

    def test_var_invalid_confidence(self, var_calculator, sample_returns):
        """Test that invalid confidence raises error."""
        with pytest.raises(VaRCalculationError, match="Confidence level"):
            var_calculator.calculate_historical_var(sample_returns, 1.5)

        with pytest.raises(VaRCalculationError, match="Confidence level"):
            var_calculator.calculate_historical_var(sample_returns, 0)

    def test_var_empty_series(self, var_calculator):
        """Test that empty series raises error."""
        with pytest.raises(VaRCalculationError, match="empty"):
            var_calculator.calculate_historical_var(pd.Series([]))

    def test_var_with_nan(self, var_calculator):
        """Test that NaN values are handled."""
        returns = pd.Series([0.01, np.nan, -0.02, 0.015, np.nan, -0.01])
        var = var_calculator.calculate_historical_var(returns, 0.95)

        # Should calculate VaR on non-NaN values
        assert var < 0

    def test_var_numerical_parity(self, var_calculator):
        """Test that JIT result matches pure Python implementation."""
        np.random.seed(42)
        returns = pd.Series(np.random.randn(100) * 0.02)

        # Calculate with JIT
        var_jit = var_calculator.calculate_historical_var(returns, 0.95)

        # Calculate with pure Python (sort + index)
        sorted_returns = np.sort(returns.dropna().values)
        var_index = int(np.floor((1 - 0.95) * len(sorted_returns)))
        var_python = sorted_returns[var_index]

        # Results should be identical (or very close)
        assert abs(var_jit - var_python) < 1e-10


class TestCVaRCalculation:
    """Test cases for CVaR calculation."""

    def test_cvar_calculation(self, var_calculator, sample_returns):
        """Test CVaR calculation."""
        var = var_calculator.calculate_cvar(sample_returns, 0.95)

        # CVaR should be negative (average of tail losses)
        assert var < 0

    def test_cvar_worse_than_var(self, var_calculator, sample_returns):
        """Test that CVaR is worse than VaR."""
        var = var_calculator.calculate_historical_var(sample_returns, 0.95)
        cvar = var_calculator.calculate_cvar(sample_returns, 0.95)

        # CVaR (average of tail) should be worse (more negative) than VaR
        assert cvar <= var


class TestKellyCalculation:
    """Test cases for Kelly Criterion calculation."""

    def test_kelly_calculation(self, var_calculator):
        """Test Kelly fraction calculation."""
        kelly = var_calculator.calculate_kelly_fraction(
            win_probability=0.6, win_loss_ratio=1.5, conservative_factor=0.25
        )

        # Kelly should be positive
        assert kelly > 0

        # Should be conservative (0.25 of full Kelly)
        assert kelly < 0.25

    def test_kelly_invalid_probability(self, var_calculator):
        """Test that invalid probability raises error."""
        with pytest.raises(VaRCalculationError):
            var_calculator.calculate_kelly_fraction(1.5, 1.0)

        with pytest.raises(VaRCalculationError):
            var_calculator.calculate_kelly_fraction(-0.1, 1.0)

    def test_kelly_invalid_ratio(self, var_calculator):
        """Test that invalid ratio raises error."""
        with pytest.raises(VaRCalculationError):
            var_calculator.calculate_kelly_fraction(0.6, -1.0)


class TestVolatilityCalculation:
    """Test cases for volatility calculation."""

    def test_volatility_daily(self, var_calculator, sample_returns):
        """Test daily volatility calculation."""
        vol = var_calculator.calculate_volatility(sample_returns, annualize=False)

        # Should be around 2% (from test data generation)
        assert 0.015 < vol < 0.025

    def test_volatility_annualized(self, var_calculator, sample_returns):
        """Test annualized volatility calculation."""
        vol_daily = var_calculator.calculate_volatility(sample_returns, annualize=False)
        vol_annual = var_calculator.calculate_volatility(sample_returns, annualize=True)

        # Annual vol should be daily * sqrt(252)
        expected_annual = vol_daily * np.sqrt(252)
        assert abs(vol_annual - expected_annual) < 1e-10


class TestSharpeRatioCalculation:
    """Test cases for Sharpe ratio calculation."""

    def test_sharpe_calculation(self, var_calculator, sample_returns):
        """Test Sharpe ratio calculation."""
        sharpe = var_calculator.calculate_sharpe_ratio(sample_returns, risk_free_rate=0.0)

        # For random returns centered at 0, Sharpe should be near 0
        assert abs(sharpe) < 1.0

    def test_sharpe_with_risk_free_rate(self, var_calculator):
        """Test Sharpe with risk-free rate."""
        # Create returns with positive mean
        returns = pd.Series(np.ones(100) * 0.001)  # 0.1% daily return

        sharpe = var_calculator.calculate_sharpe_ratio(returns, risk_free_rate=0.02)

        # Should be positive
        assert sharpe > 0


class TestMaxDrawdownCalculation:
    """Test cases for max drawdown calculation."""

    def test_max_drawdown(self, var_calculator):
        """Test max drawdown calculation."""
        # Create a series with a clear drawdown
        returns = pd.Series(
            [
                0.10,
                0.05,
                -0.15,
                -0.10,
                -0.05,  # Peak to trough
                0.20,
                0.10,
                -0.30,
                0.05,
                0.05,  # Another drawdown
            ]
        )

        dd = var_calculator.calculate_max_drawdown(returns)

        assert dd["max_drawdown"] > 0
        assert dd["start_index"] >= 0
        assert dd["end_index"] > dd["start_index"]


class TestComprehensiveAnalysis:
    """Test cases for comprehensive risk analysis."""

    def test_comprehensive_analysis(self, var_calculator, sample_returns):
        """Test comprehensive risk analysis."""
        result = var_calculator.comprehensive_risk_analysis(sample_returns)

        # Should include all metrics
        assert "volatility" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert "var" in result
        assert "cvar" in result
        assert "data_points" in result

        # VaR and CVaR should have 95 and 99 levels
        assert "var_95" in result["var"]
        assert "var_99" in result["var"]
        assert "cvar_95" in result["cvar"]
        assert "cvar_99" in result["cvar"]


class TestPerformanceTargets:
    """Test cases for performance targets."""

    def test_var_performance_10k(self, var_calculator, large_returns):
        """Test VaR calculation performance for 10k datapoints."""
        # Warm up
        for _ in range(5):
            var_calculator.calculate_historical_var(large_returns, 0.95)

        # Measure
        latencies = []
        for _ in range(100):
            start = time.perf_counter_ns()
            var_calculator.calculate_historical_var(large_returns, 0.95)
            end = time.perf_counter_ns()
            latencies.append((end - start) / 1000.0)  # μs

        p99 = np.percentile(latencies, 99)
        mean = np.mean(latencies)

        print(f"\nVaR 10k datapoints - Mean: {mean:.2f}μs, P99: {p99:.2f}μs")

        # Target: < 100μs for 10k datapoints
        assert p99 < 100, f"VaR P99 {p99:.2f}μs exceeds 100μs target"

    def test_kelly_performance(self, var_calculator):
        """Test Kelly calculation performance."""
        latencies = []
        for _ in range(1000):
            start = time.perf_counter_ns()
            var_calculator.calculate_kelly_fraction(0.6, 1.5, 0.25)
            end = time.perf_counter_ns()
            latencies.append((end - start) / 1000.0)

        p99 = np.percentile(latencies, 99)
        mean = np.mean(latencies)

        print(f"\nKelly calculation - Mean: {mean:.3f}μs, P99: {p99:.3f}μs")

        # Target: < 10μs
        assert p99 < 10, f"Kelly P99 {p99:.3f}μs exceeds 10μs target"


class TestJITWarmup:
    """Test cases for JIT warmup."""

    def test_warmup_function(self):
        """Test that warmup function runs without error."""
        # Should not raise
        _warmup_jit_functions()

    def test_cold_start_vs_warm(self, large_returns):
        """Compare cold start vs warm performance."""
        # Create fresh calculator without warmup
        cold_calc = VaRCalculatorOptimized(warmup=False)

        # First call (cold)
        start = time.perf_counter_ns()
        cold_calc.calculate_historical_var(large_returns, 0.95)
        cold_time = (time.perf_counter_ns() - start) / 1000.0

        # Second call (warm)
        start = time.perf_counter_ns()
        cold_calc.calculate_historical_var(large_returns, 0.95)
        warm_time = (time.perf_counter_ns() - start) / 1000.0

        print(f"\nCold start: {cold_time:.2f}μs, Warm: {warm_time:.2f}μs")

        # Warm should be much faster
        assert warm_time < cold_time * 0.5  # At least 2x faster


class TestInputValidation:
    """Test cases for input validation."""

    def test_validate_returns_series(self, var_calculator, sample_returns):
        """Test validation of Pandas Series."""
        arr = var_calculator._validate_returns(sample_returns)
        assert isinstance(arr, np.ndarray)
        assert arr.dtype == np.float64

    def test_validate_returns_array(self, var_calculator):
        """Test validation of NumPy array."""
        arr_input = np.array([0.01, -0.02, 0.015], dtype=np.float32)
        arr = var_calculator._validate_returns(arr_input)
        assert isinstance(arr, np.ndarray)
        assert arr.dtype == np.float64

    def test_validate_returns_invalid_type(self, var_calculator):
        """Test that invalid type raises error."""
        with pytest.raises(VaRCalculationError, match="must be pd.Series or np.ndarray"):
            var_calculator._validate_returns([0.01, -0.02, 0.015])

    def test_validate_returns_none(self, var_calculator):
        """Test that None raises error."""
        with pytest.raises(VaRCalculationError, match="cannot be None"):
            var_calculator._validate_returns(None)


class TestBackwardCompatibility:
    """Test that public interface remains compatible."""

    def test_import_alias(self):
        """Test that VaRCalculator alias works."""
        from backend.risk.var_calculator_optimized import VaRCalculator

        # Should be able to instantiate
        calc = VaRCalculator(warmup=False)
        assert isinstance(calc, VaRCalculatorOptimized)

    def test_same_method_signatures(self, var_calculator, sample_returns):
        """Test that method signatures are compatible."""
        # All these should work without errors
        var_calculator.calculate_historical_var(sample_returns, 0.95)
        var_calculator.calculate_cvar(sample_returns, 0.95)
        var_calculator.calculate_kelly_fraction(0.6, 1.5)
        var_calculator.calculate_volatility(sample_returns)
        var_calculator.calculate_sharpe_ratio(sample_returns)
        var_calculator.calculate_max_drawdown(sample_returns)
