"""
Fire Elemental Agent (Agni) - The Risk Guardian.

Role: Risk Management / Guardian
Element: Fire (Transformation/Agni)
Guna Balance: High Rajas/Sattva (Active Discrimination)
Prana Cost: Low (5 units) - Efficient but intense
Tattva Layer: 34

Function:
- Burns away impurities (bad trades/risks).
- Active protection (Circuit Breaking).
- Discriminating intellect (Tejas).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.agents.elemental_base import ElementalBase
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class ElementalRiskGuardian(ElementalBase):
    """
    Fire Agent: Active protection, discrimination, purification.
    """

    def __init__(
        self,
        agent_name: str = "RiskGuardian_Fire",
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        system_identity: Optional[Any] = None,
        agent_role: AgentRole = AgentRole.EXECUTOR,  # Configured as Executor for circuit breaking rights? Or Strategist? Risk needs to block.
    ):
        # Fire needs to be able to Assess Risk (Strategist) and potentially Block (Executor-like power, but Gatekeeper check is separate).
        # Let's check AgentRole.STRATEGIST has ASSESS_RISK. Yes.

        super().__init__(
            agent_name=agent_name,
            element="fire",
            tattva_layer=34,
            guna_balance={
                "sattva": 0.4,  # Discrimination (Viveka)
                "rajas": 0.5,  # Active protection
                "tamas": 0.1,  # Minimal inertia
            },
            llm_provider=llm_provider,
            event_bus=event_bus,
            system_identity=system_identity,
            agent_role=AgentRole.STRATEGIST,  # Needs ASSESS_RISK
            max_prana=100.0,
            prana_decay_rate=5.0,  # Efficient
        )

    async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk and approve/reject signals.
        """
        if not await self.consume_prana():
            # Fire depleted: default to blocking for safety? Or allow?
            # Safe fail: Block if guardian is down.
            return self._degraded_response("Insufficient Prana - SAFETY LOCK")

        try:
            trade_proposal = signal.get("proposal", {})
            market_state = signal.get("market_state", {})

            assessment = await self._assess_risk(trade_proposal, market_state)

            result = {
                "agent": self.agent_name,
                "element": self.element,
                "approved": assessment["approved"],
                "risk_score": assessment["risk_score"],
                "reason": assessment["reason"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prana_remaining": self.prana,
            }

            # Fire speaks clearly (Sattva/Rajas)
            thought_type = "risk_assessment" if assessment["approved"] else "risk_block"

            await self.publish_thought(
                reasoning=f"Risk Assessment: {'APPROVED' if assessment['approved'] else 'BLOCKED'}. Reason: {assessment['reason']}",
                confidence=assessment.get("confidence", 0.9),
                data={"assessment": assessment, "thought_type": thought_type},
            )

            return result

        except Exception as e:
            logger.error(f"Error in Fire processing: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "approved": False}

    async def _assess_risk(
        self, proposal: Dict[str, Any], market: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Core risk logic."""
        # Simple prototype logic
        # 1. Volatility Check
        volatility = market.get("volatility", 0.0)
        max_vol_threshold = 0.5  # Example

        if volatility > max_vol_threshold:
            return {
                "approved": False,
                "risk_score": 0.9,
                "reason": f"Volatility {volatility:.2f} exceeds threshold {max_vol_threshold}",
                "confidence": 1.0,
            }

        # 2. Exposure Check (mock)
        score = 0.2
        if proposal.get("size", 0) > 100000:
            return {
                "approved": False,
                "risk_score": 0.8,
                "reason": "Size exceeds Single Trade Limit",
                "confidence": 1.0,
            }

        return {
            "approved": True,
            "risk_score": 0.1,
            "reason": "Within limits",
            "confidence": 0.8,
        }

    def _degraded_response(self, reason: str) -> Dict:
        """Safety first - Block if depleted."""
        return {
            "agent": self.agent_name,
            "status": "degraded",
            "reason": reason,
            "approved": False,  # Fail-safe
            "risk_score": 1.0,
        }
