"""
Integrated Position Sizer - Combines Kelly Criterion, ATR-Volatility, and Drawdown Scaling.

Provides a unified position sizing interface that:
1. Calculates base size from fixed-risk formula (max loss / risk-per-unit)
2. Optionally scales via Kelly Criterion (fractional)
3. Optionally adjusts for volatility via ATR
4. Automatically reduces size during drawdowns
5. Caps at max_position_pct of equity per trade
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SizingResult:
    """Result of position sizing calculation."""

    quantity: float
    method: str
    risk_per_unit: float
    max_loss: float
    effective_risk_pct: float
    kelly_fraction: Optional[float] = None
    volatility_factor: Optional[float] = None


class IntegratedPositionSizer:
    """
    Unified position sizing that combines multiple approaches.

    Usage:
        sizer = IntegratedPositionSizer()
        result = sizer.size_with_kelly(equity=100000, entry=50000, stop=49000, ...)
    """

    def __init__(
        self,
        max_risk_pct: float = 0.01,
        max_position_pct: float = 0.02,
        kelly_multiplier: float = 0.25,
    ):
        """
        Args:
            max_risk_pct: Max risk per trade (default 1% of equity)
            max_position_pct: Max notional per trade (default 2% of equity)
            kelly_multiplier: Fractional Kelly multiplier (default 0.25 = quarter Kelly)
        """
        self.max_risk_pct = max_risk_pct
        self.max_position_pct = max_position_pct
        self.kelly_multiplier = kelly_multiplier

    def size_from_fixed_risk(
        self,
        equity: float,
        entry: float,
        stop: float,
        side: str = "long",
    ) -> SizingResult:
        """
        Calculate position size from fixed risk per trade.

        Args:
            equity: Current portfolio value
            entry: Entry price
            stop: Stop-loss price
            side: 'long' or 'short'

        Returns:
            SizingResult with calculated quantity
        """
        if side == "long":
            risk_per_unit = entry - stop
        else:
            risk_per_unit = stop - entry

        if risk_per_unit <= 0 or entry <= 0 or equity <= 0:
            return SizingResult(
                quantity=0.0,
                method="fixed_risk",
                risk_per_unit=0.0,
                max_loss=0.0,
                effective_risk_pct=0.0,
            )

        max_loss = equity * self.max_risk_pct
        raw_qty = max_loss / risk_per_unit

        # Cap on max notional exposure
        max_notional = equity * self.max_position_pct
        max_qty_by_notional = max_notional / entry

        quantity = max(0.0, min(raw_qty, max_qty_by_notional))

        return SizingResult(
            quantity=quantity,
            method="fixed_risk",
            risk_per_unit=risk_per_unit,
            max_loss=max_loss,
            effective_risk_pct=self.max_risk_pct,
        )

    def size_with_kelly(
        self,
        equity: float,
        entry: float,
        stop: float,
        win_probability: float,
        win_loss_ratio: float,
        side: str = "long",
    ) -> SizingResult:
        """
        Calculate position size using Kelly Criterion.

        Args:
            equity: Current portfolio value
            entry: Entry price
            stop: Stop-loss price
            win_probability: Win probability (0.0 - 1.0)
            win_loss_ratio: Average win / average loss
            side: 'long' or 'short'

        Returns:
            SizingResult with Kelly-adjusted quantity
        """
        if not (0 < win_probability < 1) or win_loss_ratio <= 0:
            return self.size_from_fixed_risk(equity, entry, stop, side)

        # Kelly formula: f* = (bp - q) / b
        b = win_loss_ratio
        p = win_probability
        q = 1 - p

        kelly_fraction = (b * p - q) / b
        kelly_fraction = max(0.0, min(1.0, kelly_fraction))

        # Apply fractional Kelly
        effective_risk_pct = kelly_fraction * self.kelly_multiplier

        # Clamp to max risk
        effective_risk_pct = min(effective_risk_pct, self.max_risk_pct)

        if side == "long":
            risk_per_unit = entry - stop
        else:
            risk_per_unit = stop - entry

        if risk_per_unit <= 0 or entry <= 0 or equity <= 0:
            return SizingResult(
                quantity=0.0,
                method="kelly",
                risk_per_unit=0.0,
                max_loss=0.0,
                effective_risk_pct=0.0,
                kelly_fraction=kelly_fraction,
            )

        max_loss = equity * effective_risk_pct
        raw_qty = max_loss / risk_per_unit

        # Cap on max notional
        max_notional = equity * self.max_position_pct
        max_qty_by_notional = max_notional / entry
        quantity = max(0.0, min(raw_qty, max_qty_by_notional))

        return SizingResult(
            quantity=quantity,
            method="kelly",
            risk_per_unit=risk_per_unit,
            max_loss=max_loss,
            effective_risk_pct=effective_risk_pct,
            kelly_fraction=kelly_fraction,
        )

    def size_with_volatility(
        self,
        equity: float,
        entry: float,
        stop: float,
        atr: float,
        side: str = "long",
        target_risk_per_atr: float = 0.02,
    ) -> SizingResult:
        """
        Calculate position size adjusted for volatility (ATR).

        Inversely scales position size with current ATR.
        Higher volatility -> smaller position.

        Args:
            equity: Current portfolio value
            entry: Entry price
            stop: Stop-loss price
            atr: Current Average True Range value
            side: 'long' or 'short'
            target_risk_per_atr: Target risk expressed as portfolio % per ATR unit.

        Returns:
            SizingResult with volatility-adjusted quantity
        """
        if atr <= 0 or entry <= 0 or equity <= 0:
            return self.size_from_fixed_risk(equity, entry, stop, side)

        # Volatility factor: scale risk based on ATR relative to price
        atr_pct = atr / entry
        if atr_pct <= 0:
            return self.size_from_fixed_risk(equity, entry, stop, side)

        vol_factor = min(1.0, target_risk_per_atr / atr_pct)

        # Apply vol factor to base risk
        effective_risk_pct = self.max_risk_pct * vol_factor

        if side == "long":
            risk_per_unit = entry - stop
        else:
            risk_per_unit = stop - entry

        if risk_per_unit <= 0:
            return SizingResult(
                quantity=0.0,
                method="volatility",
                risk_per_unit=0.0,
                max_loss=0.0,
                effective_risk_pct=0.0,
                volatility_factor=vol_factor,
            )

        max_loss = equity * effective_risk_pct
        raw_qty = max_loss / risk_per_unit

        # Cap
        max_notional = equity * self.max_position_pct
        max_qty_by_notional = max_notional / entry
        quantity = max(0.0, min(raw_qty, max_qty_by_notional))

        return SizingResult(
            quantity=quantity,
            method="volatility",
            risk_per_unit=risk_per_unit,
            max_loss=max_loss,
            effective_risk_pct=effective_risk_pct,
            volatility_factor=vol_factor,
        )

    @staticmethod
    def apply_drawdown_scaling(
        quantity: float,
        current_drawdown: float,
        soft_limit: float = 0.10,
    ) -> float:
        """
        Scale down position size based on current drawdown.

        Args:
            quantity: Base position size
            current_drawdown: Current drawdown (0.0 - 1.0)
            soft_limit: Drawdown threshold for scaling

        Returns:
            Scaled quantity (halved if drawdown > soft_limit)
        """
        if current_drawdown > soft_limit:
            return quantity * 0.5
        return quantity
