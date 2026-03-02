"""
Kelly Criterion Position Sizing - Optimal Capital Allocation.

Calculates optimal position size using Kelly Criterion formula:
f* = (bp - q) / b

Where:
- f* = optimal fraction of capital to risk
- b = odds (win amount / loss amount)
- p = probability of winning
- q = 1 - p = probability of losing
"""

import logging
from dataclasses import dataclass


@dataclass
class KellyResult:
    """Result of Kelly Criterion calculation."""

    optimal_fraction: float  # Percentage of capital to risk (0.0 - 1.0)
    position_size: float  # Position size in EUR
    recommended_size: float  # Conservative (Kelly * 0.25) size in EUR
    kelly_percentage: float  # Kelly as percentage
    win_probability: float
    win_loss_ratio: float


class KellyCriterion:
    """
    Calculate optimal position sizing using Kelly Criterion.

    Conservative approach: Use 25% of Kelly fraction to avoid over-betting.
    """

    def __init__(self, conservative_factor: float = 0.25):
        """
        Args:
            conservative_factor: Multiply Kelly result by this (default: 0.25 = 25% Kelly)
        """
        if not (0 < conservative_factor <= 1.0):
            raise ValueError("Conservative factor must be between 0 and 1")

        self.conservative_factor = conservative_factor
        self.logger = logging.getLogger("KellyCriterion")

    def calculate(
        self, win_probability: float, win_loss_ratio: float, portfolio_value: float
    ) -> KellyResult:
        """
        Calculate Kelly Criterion position size.

        Args:
            win_probability: Probability of winning trade (0.0 - 1.0)
            win_loss_ratio: Ratio of average win to average loss (e.g., 1.5 = win 1.5x to lose 1x)
            portfolio_value: Current portfolio value in EUR

        Returns:
            KellyResult with position size recommendations

        Raises:
            ValueError: If probabilities invalid or ratio negative
        """
        # Validate inputs
        if not (0 < win_probability < 1):
            raise ValueError("Win probability must be between 0 and 1")

        if win_loss_ratio <= 0:
            raise ValueError("Win/loss ratio must be positive")

        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")

        # Kelly Criterion: f* = (bp - q) / b
        # where b = win_loss_ratio, p = win_probability, q = 1 - p

        b = win_loss_ratio
        p = win_probability
        q = 1 - p

        # Calculate optimal fraction
        kelly_fraction = (b * p - q) / b

        # Kelly Criterion can go negative (don't trade) or above 1 (over-leverage)
        # Clamp to [0, 1] for safety
        kelly_fraction = max(0.0, min(1.0, kelly_fraction))

        # Conservative position: 25% of Kelly (or configured factor)
        conservative_fraction = kelly_fraction * self.conservative_factor

        # Calculate position sizes
        full_kelly_position = portfolio_value * kelly_fraction
        conservative_position = portfolio_value * conservative_fraction

        result = KellyResult(
            optimal_fraction=kelly_fraction,
            position_size=full_kelly_position,
            recommended_size=conservative_position,
            kelly_percentage=kelly_fraction * 100,
            win_probability=win_probability,
            win_loss_ratio=win_loss_ratio,
        )

        self.logger.info(
            f"Kelly Criterion: {result.kelly_percentage:.2f}% optimal, "
            f"Conservative: {conservative_position:.2f} EUR"
        )

        return result

    def kelly_edge(self, win_probability: float, win_loss_ratio: float) -> float:
        """
        Calculate the "edge" - whether the strategy is profitable long-term.

        Edge = (p * b) - (1 - p)

        Args:
            win_probability: Probability of winning
            win_loss_ratio: Win/loss ratio

        Returns:
            Edge value (positive = profitable, negative = losing)
        """
        edge = (win_probability * win_loss_ratio) - (1 - win_probability)
        return edge

    def breakeven_probability(self, win_loss_ratio: float) -> float:
        """
        Calculate minimum win probability needed to be profitable.

        Args:
            win_loss_ratio: Win/loss ratio

        Returns:
            Minimum win probability for breakeven (0.0 - 1.0)
        """
        if win_loss_ratio <= 0:
            raise ValueError("Ratio must be positive")

        # Breakeven: (p * b) - (1 - p) = 0
        # Solving: p * b + p = 1
        # p * (b + 1) = 1
        # p = 1 / (b + 1)

        return 1 / (win_loss_ratio + 1)

    def recommended_position_size(
        self,
        win_probability: float,
        win_loss_ratio: float,
        portfolio_value: float,
        max_risk_per_trade: float = 0.02,  # Max 2% risk per trade
    ) -> float:
        """
        Calculate recommended position size with risk limits.

        Args:
            win_probability: Win probability
            win_loss_ratio: Win/loss ratio
            portfolio_value: Portfolio value
            max_risk_per_trade: Maximum risk per trade (default: 2% of portfolio)

        Returns:
            Recommended position size in EUR
        """
        kelly_result = self.calculate(win_probability, win_loss_ratio, portfolio_value)

        # Also apply max risk constraint
        max_risk_amount = portfolio_value * max_risk_per_trade
        
        # FIX: Prevent division by zero when win_probability approaches 1
        # Cap denominator at minimum 0.05 (equivalent to max 20x multiplier)
        loss_probability = max(1 - win_probability, 0.05)
        risk_based_size = max_risk_amount / loss_probability
        
        # Also cap at reasonable maximum (20x the risk amount)
        risk_based_size = min(risk_based_size, max_risk_amount * 20)

        # Use minimum of Kelly and risk-based sizing
        recommended = min(kelly_result.recommended_size, risk_based_size)

        return recommended
