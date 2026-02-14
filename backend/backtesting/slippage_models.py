"""
Slippage Models for Backtesting Engine.

Provides realistic market impact and slippage simulation for order execution.
"""

from abc import ABC, abstractmethod
from backend.backtesting.models import OrderSide


class SlippageModel(ABC):
    """Abstract base for slippage models."""

    @abstractmethod
    def apply(self, price: float, quantity: float, side: OrderSide) -> tuple:
        """Apply slippage to price.

        Args:
            price: Current market price
            quantity: Order quantity
            side: OrderSide.BUY or OrderSide.SELL

        Returns:
            Tuple of (adjusted_price, slippage_amount)
        """
        pass


class FixedSlippageModel(SlippageModel):
    """Fixed basis points slippage model.

    Example: 5 basis points = 0.05% cost on both sides
    """

    def __init__(self, basis_points: float = 5.0):
        """Initialize with basis points.

        Args:
            basis_points: Fixed slippage in basis points (default 5 bps = 0.05%)
        """
        self.basis_points = basis_points

    def apply(self, price: float, quantity: float, side: OrderSide) -> tuple:
        """Apply fixed slippage."""
        slippage_pct = self.basis_points / 10000.0
        slippage_amount = price * quantity * slippage_pct

        if side == OrderSide.BUY:
            adjusted_price = price * (1 + slippage_pct)
        else:  # SELL
            adjusted_price = price * (1 - slippage_pct)

        return adjusted_price, slippage_amount


class VolumeSlippageModel(SlippageModel):
    """Volume-based slippage model (market impact).

    Slippage increases with order size relative to bar volume.
    Simulates realistic market impact where large orders move prices.
    """

    def __init__(self, impact_factor: float = 0.1, base_slippage_bps: float = 2.0, avg_bar_volume: float = 1000.0):
        """Initialize volume slippage model.

        Args:
            impact_factor: Multiplier for volume impact (default 0.1)
            base_slippage_bps: Base slippage in basis points (default 2 bps)
            avg_bar_volume: Average bar volume for the asset (default 1000.0)
        """
        self.impact_factor = impact_factor
        self.base_slippage_bps = base_slippage_bps
        self.avg_bar_volume = avg_bar_volume

    def apply(
        self,
        price: float,
        quantity: float,
        side: OrderSide,
    ) -> tuple:
        """Apply volume-based slippage."""
        volume_ratio = quantity / self.avg_bar_volume if self.avg_bar_volume > 0 else 0

        # Impact = base + (volume_ratio * impact_factor), capped at 100 bps
        volume_impact_bps = min(
            100, self.base_slippage_bps + (volume_ratio * self.impact_factor * 10000)
        )
        slippage_pct = volume_impact_bps / 10000.0
        slippage_amount = price * quantity * slippage_pct

        if side == OrderSide.BUY:
            adjusted_price = price * (1 + slippage_pct)
        else:  # SELL
            adjusted_price = price * (1 - slippage_pct)

        return adjusted_price, slippage_amount
