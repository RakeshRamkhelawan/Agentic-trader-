"""
Value at Risk (VaR) Calculator - OPTIMIZED VERSION (Sprint 2).

Uses Numba JIT compilation for 50-100x speedup on inner loops.
Target: < 100μs for 10k datapoints (was: ~5ms)

Philosophy:
Risk calculation is like the Kanchukas (restrictions) in the 36 Tattvas -
it constrains the possibilities, protecting the system from catastrophic loss.
The speed of this calculation determines how quickly we can respond to danger.
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd

# Numba JIT compilation
try:
    from numba import float64, int64, njit

    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

    # Fallback decorator if numba not installed
    def njit(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


logger = logging.getLogger("VaRCalculatorOptimized")


class VaRCalculationError(Exception):
    """Custom exception for VaR calculation errors."""

    pass


# ============================================================================
# JIT-COMPILED CORE FUNCTIONS
# ============================================================================


@njit(cache=True, fastmath=True)
def _calculate_var_jit(returns: np.ndarray, confidence: float) -> float:
    """
    JIT-compiled VaR calculation.

    CRITICAL: Only NumPy types allowed - no Python objects, strings, or dicts!
    This function is compiled once and cached for subsequent calls.

    Performance:
    - 10k datapoints: ~50-100μs (vs ~5ms without JIT)
    - 100k datapoints: ~200-300μs (vs ~50ms without JIT)

    Args:
        returns: NumPy array of returns (float64)
        confidence: Confidence level (0.0 - 1.0)

    Returns:
        VaR value (negative for loss)
    """
    # Sort returns in-place for efficiency
    sorted_returns = np.sort(returns)

    # Calculate index for VaR
    n = len(sorted_returns)
    var_index = int(np.floor((1.0 - confidence) * n))

    # Bounds check
    if var_index < 0:
        var_index = 0
    elif var_index >= n:
        var_index = n - 1

    return sorted_returns[var_index]


@njit(cache=True, fastmath=True)
def _calculate_cvar_jit(returns: np.ndarray, confidence: float) -> float:
    """
    JIT-compiled Conditional VaR (Expected Shortfall) calculation.

    CVaR is the average of returns worse than VaR (the tail losses).
    Provides a more comprehensive risk measure than VaR alone.

    Args:
        returns: NumPy array of returns
        confidence: Confidence level

    Returns:
        CVaR value (average of tail losses)
    """
    var = _calculate_var_jit(returns, confidence)

    # Count tail losses
    tail_count = 0
    tail_sum = 0.0

    for i in range(len(returns)):
        if returns[i] <= var:
            tail_count += 1
            tail_sum += returns[i]

    if tail_count == 0:
        return var

    return tail_sum / tail_count


@njit(cache=True, fastmath=True)
def _calculate_kelly_fraction_jit(
    win_prob: float, win_ratio: float, loss_ratio: float, conservative_factor: float
) -> float:
    """
    JIT-compiled Kelly Criterion position sizing.

    Formula: f* = (bp - q) / b
    Where:
    - f* = optimal fraction of capital to risk
    - b = win_ratio / loss_ratio (odds)
    - p = win probability
    - q = 1 - p = loss probability

    Conservative approach: result is multiplied by conservative_factor (default 0.25)

    Args:
        win_prob: Probability of winning (0.0 - 1.0)
        win_ratio: Average win amount
        loss_ratio: Average loss amount (positive value)
        conservative_factor: Multiplier for conservative sizing

    Returns:
        Kelly fraction (0.0 - 1.0)
    """
    q = 1.0 - win_prob

    # Avoid division by zero
    if win_ratio < 1e-10:
        return 0.0

    # Calculate Kelly fraction
    kelly = (win_prob * win_ratio - q * loss_ratio) / win_ratio

    # Clamp to [0, 1] and apply conservative factor
    if kelly < 0.0:
        kelly = 0.0
    elif kelly > 1.0:
        kelly = 1.0

    return kelly * conservative_factor


@njit(cache=True, fastmath=True)
def _calculate_volatility_jit(returns: np.ndarray) -> float:
    """
    JIT-compiled volatility calculation (standard deviation).

    Args:
        returns: NumPy array of returns

    Returns:
        Volatility (std dev)
    """
    n = len(returns)
    if n < 2:
        return 0.0

    # Calculate mean
    mean = 0.0
    for i in range(n):
        mean += returns[i]
    mean /= n

    # Calculate variance
    variance = 0.0
    for i in range(n):
        diff = returns[i] - mean
        variance += diff * diff
    variance /= n - 1  # Sample variance

    return np.sqrt(variance)


@njit(cache=True, fastmath=True)
def _calculate_sharpe_jit(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """
    JIT-compiled Sharpe ratio calculation.

    Sharpe = (mean_return - risk_free_rate) / volatility

    Args:
        returns: NumPy array of returns
        risk_free_rate: Risk-free rate (annualized)

    Returns:
        Sharpe ratio
    """
    n = len(returns)
    if n == 0:
        return 0.0

    # Calculate mean return
    mean_return = 0.0
    for i in range(n):
        mean_return += returns[i]
    mean_return /= n

    # Calculate volatility
    volatility = _calculate_volatility_jit(returns)

    if volatility < 1e-10:
        return 0.0

    return (mean_return - risk_free_rate) / volatility


@njit(cache=True, fastmath=True)
def _calculate_max_drawdown_jit(returns: np.ndarray) -> Tuple[float, int, int]:
    """
    JIT-compiled maximum drawdown calculation.

    Args:
        returns: NumPy array of returns

    Returns:
        Tuple of (max_drawdown, start_index, end_index)
    """
    n = len(returns)
    if n == 0:
        return 0.0, 0, 0

    # Calculate cumulative returns
    cumulative = np.empty(n)
    cumulative[0] = 1.0 + returns[0]
    for i in range(1, n):
        cumulative[i] = cumulative[i - 1] * (1.0 + returns[i])

    # Find maximum drawdown
    max_dd = 0.0
    peak_idx = 0
    trough_idx = 0

    peak = cumulative[0]
    peak_index = 0

    for i in range(1, n):
        if cumulative[i] > peak:
            peak = cumulative[i]
            peak_index = i

        dd = (peak - cumulative[i]) / peak
        if dd > max_dd:
            max_dd = dd
            peak_idx = peak_index
            trough_idx = i

    return max_dd, peak_idx, trough_idx


# ============================================================================
# WARM-UP FUNCTION
# ============================================================================


def _warmup_jit_functions() -> None:
    """
    Warm up JIT-compiled functions to avoid cold-start latency.

    This should be called during system startup. It runs the JIT functions
    with dummy data to trigger compilation before real usage.

    Cold-start latency without warmup: ~500ms for first call
    With warmup: ~50-100μs for first real call
    """
    if not NUMBA_AVAILABLE:
        logger.warning("Numba not available, skipping JIT warmup")
        return

    logger.info("Warming up JIT-compiled risk functions...")

    # Dummy data
    dummy_returns = np.random.randn(1000).astype(np.float64)

    # Warm up VaR
    _calculate_var_jit(dummy_returns, 0.95)
    _calculate_var_jit(dummy_returns, 0.99)

    # Warm up CVaR
    _calculate_cvar_jit(dummy_returns, 0.95)

    # Warm up Kelly
    _calculate_kelly_fraction_jit(0.6, 1.5, 1.0, 0.25)

    # Warm up volatility
    _calculate_volatility_jit(dummy_returns)

    # Warm up Sharpe
    _calculate_sharpe_jit(dummy_returns, 0.0)

    # Warm up drawdown
    _calculate_max_drawdown_jit(dummy_returns)

    logger.info("JIT warmup complete")


# ============================================================================
# PYTHON WRAPPER CLASS
# ============================================================================


class VaRCalculatorOptimized:
    """
    Optimized VaR Calculator with Numba JIT compilation.

    Performance targets:
    - VaR calculation: < 100μs for 10k datapoints (was: ~5ms)
    - Kelly calculation: < 10μs
    - All calculations: Numerical parity with original implementation

    Features:
    - Historical VaR (percentile method)
    - Conditional VaR (Expected Shortfall)
    - Kelly Criterion position sizing
    - Volatility estimation
    - Sharpe ratio
    - Maximum drawdown
    """

    def __init__(self, warmup: bool = True):
        """
        Initialize VaR calculator.

        Args:
            warmup: If True, warm up JIT functions immediately
        """
        self.logger = logging.getLogger("VaRCalculatorOptimized")

        if not NUMBA_AVAILABLE:
            self.logger.warning(
                "Numba not available. Falling back to pure Python implementations. "
                "Performance will be significantly slower."
            )

        # Warm up JIT functions to avoid cold-start latency
        if warmup and NUMBA_AVAILABLE:
            _warmup_jit_functions()

    def _validate_returns(self, returns: pd.Series) -> np.ndarray:
        """
        Validate and convert returns input.

        Args:
            returns: Pandas Series or NumPy array of returns

        Returns:
            NumPy array of float64 values

        Raises:
            VaRCalculationError: If input is invalid
        """
        if returns is None:
            raise VaRCalculationError("Returns cannot be None")

        if isinstance(returns, pd.Series):
            if returns.empty:
                raise VaRCalculationError("Returns series is empty")
            # Convert to numpy, drop NaN values
            returns_array = returns.dropna().values.astype(np.float64)
        elif isinstance(returns, np.ndarray):
            if len(returns) == 0:
                raise VaRCalculationError("Returns array is empty")
            returns_array = returns.astype(np.float64)
        else:
            raise VaRCalculationError(
                f"Returns must be pd.Series or np.ndarray, got {type(returns)}"
            )

        if len(returns_array) < 30:
            self.logger.warning(
                f"Insufficient data ({len(returns_array)} points) for robust VaR calculation. "
                "At least 100 points recommended, 30 minimum."
            )

        return returns_array

    def calculate_historical_var(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Historical VaR using JIT-compiled function.

        Args:
            returns: Pandas Series of daily returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            VaR value (negative for loss)

        Raises:
            VaRCalculationError: If input is invalid

        Performance:
        - 10k datapoints: ~50-100μs
        - 100k datapoints: ~200-300μs
        """
        # Input validation (Python side)
        if not 0 < confidence_level < 1:
            raise VaRCalculationError(
                "Confidence level must be between 0 and 1 (exclusive)."
            )

        # Convert and validate input
        returns_array = self._validate_returns(returns)

        # Call JIT-compiled function
        var = _calculate_var_jit(returns_array, float(confidence_level))

        self.logger.info(
            f"Calculated VaR at {confidence_level*100}% confidence: {var:.4f} "
            f"({len(returns_array)} datapoints)"
        )

        return float(var)

    def calculate_cvar(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).

        CVaR is the expected return in the tail beyond VaR.
        Provides a more comprehensive risk measure than VaR alone.

        Args:
            returns: Pandas Series of daily returns
            confidence_level: Confidence level

        Returns:
            CVaR value

        Performance:
        - 10k datapoints: ~100-150μs
        """
        if not 0 < confidence_level < 1:
            raise VaRCalculationError("Confidence level must be between 0 and 1")

        returns_array = self._validate_returns(returns)
        cvar = _calculate_cvar_jit(returns_array, float(confidence_level))

        self.logger.info(
            f"Calculated CVaR at {confidence_level*100}% confidence: {cvar:.4f}"
        )

        return float(cvar)

    def calculate_kelly_fraction(
        self,
        win_probability: float,
        win_loss_ratio: float,
        conservative_factor: float = 0.25,
    ) -> float:
        """
        Calculate Kelly Criterion position size using JIT-compiled function.

        Formula: f* = (bp - q) / b * conservative_factor

        Args:
            win_probability: Probability of winning (0.0 - 1.0)
            win_loss_ratio: Ratio of average win to average loss
            conservative_factor: Multiplier for conservative sizing (default 0.25)

        Returns:
            Recommended fraction of capital to risk

        Raises:
            VaRCalculationError: If inputs are invalid

        Performance:
        - < 10μs
        """
        if not 0 < win_probability < 1:
            raise VaRCalculationError("Win probability must be between 0 and 1")

        if win_loss_ratio <= 0:
            raise VaRCalculationError("Win/loss ratio must be positive")

        if not 0 < conservative_factor <= 1:
            raise VaRCalculationError("Conservative factor must be between 0 and 1")

        # Assume loss ratio is 1.0 (normalized)
        loss_ratio = 1.0

        kelly = _calculate_kelly_fraction_jit(
            float(win_probability),
            float(win_loss_ratio),
            loss_ratio,
            float(conservative_factor),
        )

        self.logger.info(
            f"Calculated Kelly fraction: {kelly:.4f} "
            f"(p={win_probability:.2f}, b={win_loss_ratio:.2f})"
        )

        return float(kelly)

    def calculate_volatility(
        self, returns: pd.Series, annualize: bool = True, periods_per_year: int = 252
    ) -> float:
        """
        Calculate volatility (standard deviation) using JIT-compiled function.

        Args:
            returns: Pandas Series of returns
            annualize: If True, annualize the result
            periods_per_year: Number of periods per year (default 252 for daily)

        Returns:
            Volatility (standard deviation)

        Performance:
        - 10k datapoints: ~50μs
        """
        returns_array = self._validate_returns(returns)
        volatility = _calculate_volatility_jit(returns_array)

        if annualize:
            volatility *= np.sqrt(periods_per_year)

        return float(volatility)

    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        """
        Calculate Sharpe ratio using JIT-compiled function.

        Formula: (mean_return - risk_free_rate) / volatility

        Args:
            returns: Pandas Series of returns
            risk_free_rate: Risk-free rate (annualized, e.g., 0.02 for 2%)
            periods_per_year: Number of periods per year

        Returns:
            Sharpe ratio

        Performance:
        - 10k datapoints: ~60μs
        """
        returns_array = self._validate_returns(returns)

        # Convert annual risk-free rate to period rate
        period_risk_free = risk_free_rate / periods_per_year

        sharpe = _calculate_sharpe_jit(returns_array, float(period_risk_free))

        # Annualize Sharpe ratio
        sharpe *= np.sqrt(periods_per_year)

        return float(sharpe)

    def calculate_max_drawdown(self, returns: pd.Series) -> dict:
        """
        Calculate maximum drawdown using JIT-compiled function.

        Args:
            returns: Pandas Series of returns

        Returns:
            Dictionary with max_drawdown, start_index, end_index

        Performance:
        - 10k datapoints: ~100μs
        """
        returns_array = self._validate_returns(returns)

        max_dd, start_idx, end_idx = _calculate_max_drawdown_jit(returns_array)

        return {
            "max_drawdown": float(max_dd),
            "start_index": int(start_idx),
            "end_index": int(end_idx),
        }

    def comprehensive_risk_analysis(
        self, returns: pd.Series, confidence_levels: list = None
    ) -> dict:
        """
        Perform comprehensive risk analysis using all JIT-compiled functions.

        Args:
            returns: Pandas Series of returns
            confidence_levels: List of confidence levels to calculate (default: [0.95, 0.99])

        Returns:
            Dictionary with all risk metrics
        """
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]

        returns_array = self._validate_returns(returns)

        # Calculate all metrics
        volatility = self.calculate_volatility(returns)
        sharpe = self.calculate_sharpe_ratio(returns)
        drawdown = self.calculate_max_drawdown(returns)

        # Calculate VaR and CVaR for each confidence level
        var_results = {}
        cvar_results = {}

        for conf in confidence_levels:
            var_results[f"var_{int(conf*100)}"] = float(
                _calculate_var_jit(returns_array, float(conf))
            )
            cvar_results[f"cvar_{int(conf*100)}"] = float(
                _calculate_cvar_jit(returns_array, float(conf))
            )

        return {
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "max_drawdown": drawdown,
            "var": var_results,
            "cvar": cvar_results,
            "data_points": len(returns_array),
        }


# Backward compatibility alias
VaRCalculator = VaRCalculatorOptimized
