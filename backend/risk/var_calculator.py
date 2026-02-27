"""Value at Risk (VaR) calculation."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np
from scipy import stats


class VaRMethod(Enum):
    """VaR calculation methods."""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


@dataclass
class VaRResult:
    """VaR calculation result."""
    value: float  # VaR value (positive = loss)
    confidence_level: float  # e.g., 0.95 for 95%
    time_horizon_days: int
    method: VaRMethod
    portfolio_value: float
    var_percentage: float  # VaR as % of portfolio

    # Additional metrics
    expected_shortfall: float  # CVaR / Expected Shortfall
    max_loss: float

    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "var": round(self.value, 2),
            "confidence_level": f"{self.confidence_level * 100:.0f}%",
            "time_horizon": f"{self.time_horizon_days}d",
            "method": self.method.value,
            "portfolio_value": round(self.portfolio_value, 2),
            "var_percentage": f"{self.var_percentage * 100:.2f}%",
            "expected_shortfall": round(self.expected_shortfall, 2),
            "max_loss": round(self.max_loss, 2),
            "timestamp": self.timestamp.isoformat(),
        }


class VaRCalculator:
    """
    Value at Risk calculator using multiple methods.

    VaR estimates the maximum potential loss over a specific time
    period at a given confidence level.
    """

    def __init__(self):
        self.calculation_history: list[VaRResult] = []

    def calculate(
        self,
        returns: list[float],
        portfolio_value: float,
        confidence_level: float = 0.95,
        time_horizon_days: int = 1,
        method: VaRMethod = VaRMethod.HISTORICAL,
    ) -> VaRResult:
        """
        Calculate VaR for a portfolio.

        Args:
            returns: Historical return series (daily)
            portfolio_value: Current portfolio value
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            time_horizon_days: VaR time horizon
            method: Calculation method

        Returns:
            VaR calculation result
        """
        if not returns or len(returns) < 30:
            raise ValueError("Need at least 30 returns for VaR calculation")

        if method == VaRMethod.HISTORICAL:
            var_value, es_value = self._historical_var(returns, confidence_level)
        elif method == VaRMethod.PARAMETRIC:
            var_value, es_value = self._parametric_var(returns, confidence_level)
        elif method == VaRMethod.MONTE_CARLO:
            var_value, es_value = self._monte_carlo_var(returns, confidence_level)
        else:
            raise ValueError(f"Unknown VaR method: {method}")

        # Scale to time horizon (square root rule)
        if time_horizon_days > 1:
            scaling_factor = np.sqrt(time_horizon_days)
            var_value *= scaling_factor
            es_value *= scaling_factor

        # Scale to portfolio value
        var_value *= portfolio_value
        es_value *= portfolio_value

        # Calculate percentage
        var_percentage = abs(var_value) / portfolio_value if portfolio_value > 0 else 0

        # Max loss (absolute historical maximum)
        max_loss = abs(min(returns)) * portfolio_value

        result = VaRResult(
            value=abs(var_value),  # Always positive for VaR
            confidence_level=confidence_level,
            time_horizon_days=time_horizon_days,
            method=method,
            portfolio_value=portfolio_value,
            var_percentage=var_percentage,
            expected_shortfall=abs(es_value),
            max_loss=max_loss,
            timestamp=datetime.utcnow(),
        )

        self.calculation_history.append(result)
        return result

    def _historical_var(
        self,
        returns: list[float],
        confidence_level: float,
    ) -> tuple[float, float]:
        """
        Historical VaR using empirical quantile.
        """
        returns_array = np.array(returns)

        # VaR is the quantile at (1 - confidence) level
        var_quantile = 1 - confidence_level
        var = np.percentile(returns_array, var_quantile * 100)

        # Expected Shortfall (CVaR) - average of returns beyond VaR
        shortfall_returns = returns_array[returns_array <= var]
        es = np.mean(shortfall_returns) if len(shortfall_returns) > 0 else var

        return var, es

    def _parametric_var(
        self,
        returns: list[float],
        confidence_level: float,
    ) -> tuple[float, float]:
        """
        Parametric VaR assuming normal distribution.
        """
        mean = np.mean(returns)
        std = np.std(returns)

        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)

        # VaR = mean + z_score * std (z_score is negative)
        var = mean + z_score * std

        # Expected Shortfall for normal distribution
        # ES = mean - std * phi(z) / (1 - confidence)
        # where phi is PDF of standard normal
        pdf_z = stats.norm.pdf(z_score)
        es = mean - std * (pdf_z / (1 - confidence_level))

        return var, es

    def _monte_carlo_var(
        self,
        returns: list[float],
        confidence_level: float,
        simulations: int = 10000,
    ) -> tuple[float, float]:
        """
        Monte Carlo VaR simulation.
        """
        mean = np.mean(returns)
        std = np.std(returns)

        # Generate simulated returns
        simulated_returns = np.random.normal(mean, std, simulations)

        # Calculate VaR from simulations
        var_quantile = 1 - confidence_level
        var = np.percentile(simulated_returns, var_quantile * 100)

        # Expected Shortfall
        shortfall_returns = simulated_returns[simulated_returns <= var]
        es = np.mean(shortfall_returns) if len(shortfall_returns) > 0 else var

        return var, es

    def compare_methods(
        self,
        returns: list[float],
        portfolio_value: float,
        confidence_level: float = 0.95,
    ) -> dict[str, VaRResult]:
        """Compare VaR across all methods."""
        results = {}

        for method in VaRMethod:
            try:
                results[method.value] = self.calculate(
                    returns=returns,
                    portfolio_value=portfolio_value,
                    confidence_level=confidence_level,
                    method=method,
                )
            except Exception as e:
                results[method.value] = {"error": str(e)}

        return results

    def get_var_breach_history(
        self,
        returns: list[float],
        var_results: list[VaRResult],
    ) -> dict:
        """Analyze historical VaR breaches."""
        breaches = 0
        breach_details = []

        for i, ret in enumerate(returns):
            if i < len(var_results):
                var = var_results[i].var_percentage
                if ret < -var:  # Loss exceeds VaR
                    breaches += 1
                    breach_details.append({
                        "index": i,
                        "return": ret,
                        "var": var,
                        "excess_loss": abs(ret) - var,
                    })

        total_observations = len(returns)
        breach_rate = breaches / total_observations if total_observations > 0 else 0

        return {
            "total_observations": total_observations,
            "breaches": breaches,
            "breach_rate": breach_rate,
            "expected_breach_rate": 1 - var_results[0].confidence_level if var_results else 0.05,
            "breach_details": breach_details[:10],  # Top 10 breaches
        }


# Global VaR calculator
var_calculator = VaRCalculator()
