"""
Portfolio Risk Calculator — Enhanced Risk Intelligence (Spec §3.1, §6.2).

Provides:
- RiskState: 8-dimensional risk snapshot
- PortfolioRiskCalculator: capacity evaluation, Kelly sizing, Guna modulation
"""

import math
from typing import Optional, Tuple

from pydantic import BaseModel, field_validator

from backend.core.risk.guna_sizing import GunaType


class RiskState(BaseModel):
    """8-dimensional portfolio risk snapshot."""

    exposure: float
    margin: float
    var_95: float
    beta: float
    max_drawdown: float
    correlation: float
    liquidity: float
    volatility_percentile: float

    @field_validator("exposure", mode="before")
    @classmethod
    def clamp_exposure(cls, v: float) -> float:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return 0.0
        return max(0.0, v)

    @field_validator("margin", mode="before")
    @classmethod
    def clamp_margin(cls, v: float) -> float:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return 0.0
        return max(0.0, v)


class RiskDecisionResult(BaseModel):
    """Result of risk evaluation."""

    action: str  # "accept" or "hold"
    reason: str
    capacity: float
    threshold: float


# Guna → (risk_threshold, size_multiplier)
_GUNA_RISK_MAP = {
    GunaType.SATTVA: (0.3, 0.5),  # Conservative: low threshold, small size
    GunaType.RAJAS: (0.6, 1.0),  # Normal: moderate threshold, full size
    GunaType.TAMAS: (0.8, 0.2),  # Defensive: high threshold, tiny size
}


class PortfolioRiskCalculator:
    """Central risk intelligence for the consciousness architecture."""

    def get_risk_capacity(self, state: RiskState) -> float:
        """Calculate risk capacity as fraction of margin available.

        Returns: float in [0.0, 1.0] where 1.0 = fully available.
        """
        if state.margin <= 0.0 or math.isnan(state.margin):
            return 0.0
        if math.isnan(state.exposure):
            return 0.0

        capacity = 1.0 - (state.exposure / state.margin)
        return max(0.0, min(1.0, capacity))

    def get_guna_risk_params(self, guna: Optional[GunaType]) -> Tuple[float, float]:
        """Return (risk_threshold, size_multiplier) for given Guna.

        If guna is None, defaults to Sattva (conservative).
        """
        if guna is None:
            guna = GunaType.SATTVA
        return _GUNA_RISK_MAP.get(guna, _GUNA_RISK_MAP[GunaType.SATTVA])

    def calculate_kelly_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        fractional: float = 0.25,
    ) -> float:
        """Calculate Kelly Criterion fraction (quarter-Kelly by default).

        Kelly: f* = (b*p - q) / b  where b = avg_win/avg_loss, p = win_rate, q = 1-p

        Returns: float >= 0.0 (clamped, never negative).
        """
        if avg_loss <= 0.0:
            return 0.0

        b = avg_win / avg_loss
        if b <= 0.0:
            return 0.0

        p = win_rate
        q = 1.0 - p
        kelly_fraction = (b * p - q) / b

        if kelly_fraction <= 0.0:
            return 0.0

        return max(0.0, min(0.5, kelly_fraction * fractional))

    def modulated_size(
        self,
        kelly_size: float,
        guna_multiplier: float,
        risk_capacity: float,
    ) -> float:
        """Apply guna and capacity modulation to Kelly size.

        final = kelly_size × guna_multiplier × risk_capacity
        """
        return kelly_size * guna_multiplier * risk_capacity

    def evaluate(
        self,
        state: RiskState,
        guna: Optional[GunaType] = None,
    ) -> RiskDecisionResult:
        """Evaluate whether to accept or hold based on risk capacity and guna.

        Returns RiskDecisionResult with action, reason, capacity, threshold.
        """
        capacity = self.get_risk_capacity(state)
        threshold, _ = self.get_guna_risk_params(guna)

        if capacity >= threshold:
            return RiskDecisionResult(
                action="accept",
                reason="risk_capacity_sufficient",
                capacity=capacity,
                threshold=threshold,
            )
        else:
            return RiskDecisionResult(
                action="hold",
                reason="insufficient_risk_capacity",
                capacity=capacity,
                threshold=threshold,
            )
