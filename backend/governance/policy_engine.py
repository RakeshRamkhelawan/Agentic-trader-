"""
Policy Engine for Trade Governance - ADR-007
"""

from dataclasses import dataclass
from enum import Enum


class ApprovalLevel(Enum):
    AUTO = "auto"
    AUTO_NOTIFY = "auto_notify"
    REQUIRES_APPROVAL = "approval"
    BLOCKED = "blocked"


@dataclass
class PolicyResult:
    level: ApprovalLevel
    reason: str
    approvers: list[str]
    risk_score: float


class PolicyEngine:
    """Evaluates trades against governance policies."""

    async def evaluate(self, trade, agent_ctx, portfolio, market, user) -> PolicyResult:
        risk = await self._calculate_risk(trade, portfolio, market)

        # Hard blocks
        if trade.value > user.get("hard_limit", float("inf")):
            return PolicyResult(ApprovalLevel.BLOCKED, "Exceeds hard limit", [], 1.0)

        # Auto-approve
        if (
            trade.value < user.get("daily_limit", 1000) * 0.1
            and agent_ctx.get("confidence", 0) > 0.85
            and risk < 0.3
        ):
            return PolicyResult(ApprovalLevel.AUTO, "Within parameters", [], risk)

        # Requires approval
        approvers = ["senior_trader"]
        if risk > 0.8:
            approvers.append("risk_manager")
        if trade.value > 100_000:
            approvers.append("compliance")

        return PolicyResult(ApprovalLevel.REQUIRES_APPROVAL, f"Risk {risk:.2f}", approvers, risk)

    async def _calculate_risk(self, trade, portfolio, market) -> float:
        # Simplified risk calculation
        return 0.5
