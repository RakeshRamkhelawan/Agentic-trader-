"""
FundManagerAgent - Capital Allocation & Position Sizing

Uses Kelly Criterion for optimal position sizing with safety multipliers.
Enforces portfolio-level risk constraints (max limits, exposure).
"""

from datetime import datetime, timezone
from typing import Any, Optional

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (CapitalAllocation, PortfolioState,
                                             RiskAssessment, TradeProposal)
from backend.governance.agent_gatekeeper import AgentRole


class FundManagerAgent(BaseAgent):
    """
    Capital allocation agent.

    Determines position sizes using Kelly Criterion and portfolio-level
    risk constraints.
    """

    def __init__(
        self,
        agent_name: str = "FundManager",
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        max_position_pct: float = 0.10,  # 10% max per position
        max_total_exposure: float = 0.90,  # 90% max total exposure
        kelly_multiplier: float = 0.5,  # Half-Kelly safety
    ):
        """
        Initialize FundManager.

        Args:
            max_position_pct: Max position as % of equity
            max_total_exposure: Max total exposure
            kelly_multiplier: Kelly safety multiplier (0.5 = half-Kelly)
        """
        super().__init__(
            agent_name=agent_name,
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST,
        )
        self.max_position_pct = max_position_pct
        self.max_total_exposure = max_total_exposure
        self.kelly_multiplier = kelly_multiplier

    async def analyze(self, *args, **kwargs):
        """
        BaseAgent abstract method implementation.
        FundManager provides capital services via allocate_capital, not typical analysis.
        """
        return {"status": "FundManager active", "mode": "capital_allocation"}

    async def allocate_capital(
        self,
        trade_proposal: TradeProposal,
        risk_assessment: RiskAssessment,
        portfolio_state: PortfolioState,
    ) -> CapitalAllocation:
        """
        Determine position size for trade.

        Steps:
        1. Check Risk Approval
        2. Calculate Kelly Fraction
        3. Apply Safety Multiplier
        4. Enforce Limits (Max %)
        5. Check Portfolio Exposure
        6. Calculate Final USD Size
        """

        # 0. Risk Gate
        # RiskAssessment decision is an Enum (RiskDecision.APPROVE, etc.)
        # We need to check if it's approved.
        # Assuming RiskDecision is a string-based Enum as seen in ooda_types.py
        if (
            risk_assessment.decision != "approve"
            and risk_assessment.decision != "reduce_size"
        ):
            return self._create_rejection(
                f"Risk Rejected: {risk_assessment.decision} - {risk_assessment.rationale}"
            )

        self.logger.info(
            f"Allocating capital for {trade_proposal.symbol}, "
            f"Equ={portfolio_state.total_equity:.2f}, Avail={portfolio_state.available_capital:.2f}"
        )

        # 1. Estimate Stats
        avg_win = self._estimate_avg_win(trade_proposal)
        avg_loss = self._estimate_avg_loss(trade_proposal)

        # 2. Calculate Kelly
        kelly_fraction = self._calculate_kelly(
            win_probability=risk_assessment.win_probability,
            avg_win=avg_win,
            avg_loss=avg_loss,
        )

        if kelly_fraction <= 0:
            return self._create_rejection(f"Zero/Negative Kelly: {kelly_fraction:.4f}")

        # 3. Apply Safety Multiplier
        safe_fraction = kelly_fraction * self.kelly_multiplier

        # 4. Position Limits
        final_fraction = min(safe_fraction, self.max_position_pct)

        # 5. Exposure Limits
        current_exp = portfolio_state.total_exposure_pct
        remaining_cap = max(0.0, self.max_total_exposure - current_exp)
        final_fraction = min(final_fraction, remaining_cap)

        if final_fraction <= 0:
            return self._create_rejection(f"Max Exposure Reached ({current_exp:.1%})")

        # 6. USD Size
        size_usd = portfolio_state.total_equity * final_fraction

        # Check against available liquid capital
        if size_usd > portfolio_state.available_capital:
            self.logger.warning("Allocation capped by available liquidity")
            size_usd = portfolio_state.available_capital
            # Recalculate fraction based on actual liquidity
            if portfolio_state.total_equity > 0:
                final_fraction = size_usd / portfolio_state.total_equity
            else:
                final_fraction = 0.0

        # Min size check
        if size_usd < 10.0:
            return self._create_rejection(f"Size ${size_usd:.2f} below minimum $10")

        # Success
        reasoning = (
            f"Kelly={kelly_fraction:.2%}, Safe={self.kelly_multiplier}x, "
            f"Final={final_fraction:.2%} (${size_usd:.2f})"
        )

        # Publish Thought
        await self.publish_thought(
            reasoning=reasoning,
            confidence=0.95,
            data={
                "allocation": {
                    "usd": size_usd,
                    "fraction": final_fraction,
                    "kelly": kelly_fraction,
                },
                "thought_type": "capital_allocation",
            },
        )

        return CapitalAllocation(
            position_size_usd=size_usd,
            position_fraction=final_fraction,
            kelly_fraction=kelly_fraction,
            approved=True,
            reasoning=reasoning,
            timestamp=datetime.now(timezone.utc).timestamp(),
        )

    def _calculate_kelly(
        self, win_probability: float, avg_win: float, avg_loss: float
    ) -> float:
        """
        Kelly = p/a - q/b ? No, usually: f = p/L - q/W ... no
        Standard: f = (bp - q) / b where b = odds (win_amt/loss_amt)

        Equivalent to: (p * win_amt - q * loss_amt) / win_amt
        """
        if avg_win <= 0:
            return 0.0
        if avg_loss == 0:
            return win_probability  # Theoretical max

        numerator = (win_probability * avg_win) - ((1 - win_probability) * avg_loss)
        kelly = numerator / avg_win

        return max(0.0, min(kelly, 1.0))

    def _estimate_avg_win(self, proposal: TradeProposal) -> float:
        """Estimate win % based on take profit."""
        entry = (
            proposal.entry_price if proposal.entry_price else proposal.stop_loss * 1.01
        )  # Fallback
        if entry == 0:
            return 0.0

        if proposal.side == "buy":
            return max(0.0, (proposal.take_profit - entry) / entry)
        else:
            return max(0.0, (entry - proposal.take_profit) / entry)

    def _estimate_avg_loss(self, proposal: TradeProposal) -> float:
        """Estimate loss % based on stop loss."""
        entry = (
            proposal.entry_price if proposal.entry_price else proposal.stop_loss * 1.01
        )
        if entry == 0:
            return 0.0

        if proposal.side == "buy":
            return abs((entry - proposal.stop_loss) / entry)
        else:
            return abs((proposal.stop_loss - entry) / entry)

    def _create_rejection(self, reason: str) -> CapitalAllocation:
        return CapitalAllocation(
            position_size_usd=0.0,
            position_fraction=0.0,
            kelly_fraction=0.0,
            approved=False,
            reasoning=reason,
            timestamp=datetime.now(timezone.utc).timestamp(),
        )
