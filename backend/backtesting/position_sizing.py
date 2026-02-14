"""
Position Sizing Models for Backtesting Engine.

Provides intelligent position sizing strategies (fixed, percentage, Kelly Criterion).
"""

from abc import ABC, abstractmethod
import warnings


class PositionSizer(ABC):
    """Abstract base for position sizing models."""

    @abstractmethod
    def calculate_quantity(
        self,
        signal_strength: float,
        price: float,
        portfolio_value: float,
        risk_per_trade: float = 0.01,
    ) -> float:
        """Calculate position size.

        Args:
            signal_strength: Strength of trading signal (0.0-1.0+)
            price: Current market price
            portfolio_value: Current portfolio equity
            risk_per_trade: Max risk percentage per trade (default 1%)

        Returns:
            Quantity to trade
        """
        pass


class FixedQuantitySizer(PositionSizer):
    """Fixed quantity position sizer.

    Trades a fixed quantity, scaled by signal strength.
    Default: 1.0 BTC / 1.0 share scaled by signal
    """

    def __init__(self, base_quantity: float = 1.0):
        """Initialize fixed quantity sizer.

        Args:
            base_quantity: Base quantity per trade (default 1.0)
        """
        self.base_quantity = base_quantity

    def calculate_quantity(
        self,
        signal_strength: float,
        price: float,
        portfolio_value: float,
        risk_per_trade: float = 0.01,
    ) -> float:
        """Calculate fixed quantity scaled by signal strength."""
        return max(0.0, self.base_quantity * signal_strength)


class PercentOfEquitySizer(PositionSizer):
    """Percent of equity position sizer.

    Allocates a fixed % of portfolio per trade.
    Scales with portfolio growth/drawdown.
    """

    def __init__(self, percent_per_trade: float = 0.02):
        """Initialize percent of equity sizer.

        Args:
            percent_per_trade: % of portfolio per trade (default 2%)
        """
        self.percent_per_trade = percent_per_trade

    def calculate_quantity(
        self,
        signal_strength: float,
        price: float,
        portfolio_value: float,
        risk_per_trade: float = 0.01,
    ) -> float:
        """Calculate quantity as % of portfolio."""
        if price <= 0:
            return 0.0

        quantity = (portfolio_value * self.percent_per_trade * signal_strength) / price
        return max(0.0, quantity)


class RiskBasedSizer(PositionSizer):
    """Risk-based position sizing.

    Sizes positions based on risk per trade (e.g., 1% risk).
    Requires stop loss level to calculate quantity.
    """

    def __init__(self, risk_per_trade_pct: float = 0.01, stop_loss_pct: float = 0.02):
        """Initialize risk-based sizer.

        Args:
            risk_per_trade_pct: Max risk % per trade (default 1%)
            stop_loss_pct: Distance to stop loss as % of price (default 2%)
        """
        self.risk_per_trade_pct = risk_per_trade_pct
        self.stop_loss_pct = stop_loss_pct

    def calculate_quantity(
        self,
        signal_strength: float,
        price: float,
        portfolio_value: float,
        risk_per_trade: float = 0.01,
    ) -> float:
        """Calculate quantity based on risk per trade."""
        if price <= 0 or self.stop_loss_pct <= 0:
            return 0.0

        # Max loss = portfolio_value * risk_per_trade_pct
        max_loss = portfolio_value * self.risk_per_trade_pct

        # Price movement per unit = price * stop_loss_pct
        loss_per_unit = price * self.stop_loss_pct

        # Quantity = max_loss / loss_per_unit * signal_strength
        quantity = (max_loss / loss_per_unit) * signal_strength
        return max(0.0, quantity)


class KellyCriterionSizer(PositionSizer):
    """Kelly Criterion position sizing.

    Calculates optimal growth fraction based on win rate and payoff ratio.
    Should be fractional (25% Kelly) for safety in practice.

    Kelly Fraction = (p * b - (1 - p)) / b
    where p = win rate, b = avg_win / avg_loss
    """

    def __init__(
        self,
        win_rate: float = 0.55,
        avg_win: float = 1.0,
        avg_loss: float = 1.0,
        fractional_kelly: float = 0.25,
    ):
        """Initialize Kelly Criterion sizer.

        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average win size
            avg_loss: Average loss size
            fractional_kelly: Kelly fraction multiplier (0.25 = quarter Kelly for safety)
        """
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
        self.fractional_kelly = fractional_kelly

    def calculate_quantity(
        self,
        signal_strength: float,
        price: float,
        portfolio_value: float,
        risk_per_trade: float = 0.01,
    ) -> float:
        """Calculate quantity using Kelly Criterion."""
        if price <= 0 or self.avg_loss <= 0:
            return 0.0

        # Kelly Fraction: f* = (bp - q) / b
        b = self.avg_win / self.avg_loss
        p = self.win_rate
        q = 1.0 - p

        kelly_fraction = (b * p - q) / b if b > 0 else 0.0

        # Warn if Kelly suggests not trading (negative expectancy)
        if kelly_fraction < 0:
            warnings.warn(
                f"Kelly Criterion suggests not trading: negative expectancy "
                f"(kelly_fraction={kelly_fraction:.4f}, win_rate={p:.2f}, avg_win/loss={b:.2f}). "
                f"Position size set to 0."
            )

        # Use fractional Kelly for safety (typically 0.25x)
        position_fraction = max(0.0, min(0.5, kelly_fraction * self.fractional_kelly))

        quantity = (portfolio_value * position_fraction * signal_strength) / price
        return max(0.0, quantity)


class VolatilityScaledSizer(PositionSizer):
    """Volatility-scaled position sizing.

    Sizes positions inversely to volatility (smaller in high vol, larger in low vol).
    Maintains more consistent risk across different market regimes.
    """

    def __init__(self, target_vol: float = 0.02, base_pct: float = 0.02, current_volatility: float = 0.02):
        """Initialize volatility-scaled sizer.

        Args:
            target_vol: Target volatility level (default 2%)
            base_pct: Base % of portfolio at target volatility (default 2%)
            current_volatility: Initial market volatility (e.g., trailing std dev, default 2%)
        """
        self.target_vol = target_vol
        self.base_pct = base_pct
        self.current_volatility = current_volatility

    def calculate_quantity(
        self,
        signal_strength: float,
        price: float,
        portfolio_value: float,
        risk_per_trade: float = 0.01,
    ) -> float:
        """Calculate volatility-adjusted quantity."""
        if price <= 0 or self.current_volatility <= 0:
            return 0.0

        # Inverse relationship: when volatility is high, reduce position size
        vol_adjustment = self.target_vol / self.current_volatility

        quantity = (
            portfolio_value * self.base_pct * vol_adjustment * signal_strength
        ) / price
        return max(0.0, quantity)
