from typing import Optional

from pydantic import BaseModel

from backend.core.risk.guna_sizing import GunaSizer, GunaType
from backend.core.risk.mifid_checks import (ClientProfile, ComplianceStatus,
                                            MiFIDGuard, TradeRequest)


class RiskDecision(BaseModel):
    decision: str  # "accept", "reject", "warn"
    adjusted_size: float
    reason: str


class RiskManager:
    """
    Central Risk Management Authority.
    Aggregates checks from MiFIDGuard, GunaSizer, and Portfolio limits.
    """

    def __init__(self):
        self.mifid = MiFIDGuard()
        self.guna_sizer = GunaSizer()

    def evaluate_trade(
        self, profile: ClientProfile, trade: TradeRequest, current_guna: GunaType
    ) -> RiskDecision:
        # 1. Regulatory/Compliance Check (MiFID II)
        compliance = self.mifid.validate(profile, trade)
        if compliance == ComplianceStatus.BLOCK:
            return RiskDecision(
                decision="reject",
                adjusted_size=0.0,
                reason="MiFID Compliance Block (Appropriateness or Loss Limit)",
            )

        # 2. Guna-modulated Sizing
        size_mult = self.guna_sizer.calculate_size_multiplier(current_guna)
        final_size = trade.amount * size_mult

        # 3. Construct Reason
        msg = f"Approved. Compliance: {compliance.value}. Guna: {current_guna.value} (Size x{size_mult})."

        decision_str = "accept"
        if compliance == ComplianceStatus.WARN:
            msg = f"WARNING. Compliance: {compliance.value}. Guna: {current_guna.value} (Size x{size_mult})."
            decision_str = "warn"

        return RiskDecision(decision=decision_str, adjusted_size=final_size, reason=msg)
