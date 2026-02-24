"""
Water Elemental Agent (Jala) - Macro & Memory.

Role: Context / Memory / Flow
Element: Water (Cohesion/Jala)
Guna Balance: High Tamas (Stability/Memory), Sattva (Reflection)
Prana Cost: Moderate (8 units)
Tattva Layer: 35

Function:
- Maintains systemic memory (past trades, market regimes).
- Detects macro cycles (flow of markets).
- Provides context (hydration) to dry logic.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from backend.agents.elemental_base import ElementalBase
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class ElementalMacro(ElementalBase):
    """
    Water Agent: Memory, context, flow.
    High Tamas ensures retention and stability.
    """

    def __init__(
        self,
        agent_name: str = "Macro_Water",
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        system_identity: Any | None = None,
        agent_role: AgentRole = AgentRole.RESEARCHER,  # Analyst/Researcher role
    ):
        super().__init__(
            agent_name=agent_name,
            element="water",
            tattva_layer=35,
            guna_balance={
                "sattva": 0.3,  # Reflection/Clarity
                "rajas": 0.1,  # Low agitation
                "tamas": 0.6,  # High retention/memory/mass
            },
            llm_provider=llm_provider,
            event_bus=event_bus,
            system_identity=system_identity,
            agent_role=AgentRole.RESEARCHER,
            max_prana=100.0,
            prana_decay_rate=8.0,
        )
        self.memory_buffer: list[dict] = []

    async def process_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze macro regime and recall similar contexts.
        """
        if not await self.consume_prana():
            return self._degraded_response("Insufficient Prana for Memory Recall")

        try:
            current_data = signal.get("data", {})

            # 1. Determine Regime (Flow)
            regime = self._determine_regime(current_data)

            # 2. Recall Memory (Reflection)
            # In real system, query vector DB
            similar_patterns = self._query_memory(current_data)

            result = {
                "agent": self.agent_name,
                "element": self.element,
                "regime": regime,
                "context_score": 0.8 if similar_patterns else 0.2,
                "similar_patterns": similar_patterns,
                "timestamp": datetime.now(UTC).isoformat(),
                "prana_remaining": self.prana,
            }

            await self.publish_thought(
                reasoning=f"Identified Regime: {regime}. Found {len(similar_patterns)} historical analogs.",
                confidence=0.75,
                data={"regime": regime, "thought_type": "macro_context"},
            )

            return result

        except Exception as e:
            logger.error(f"Error in Water processing: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _determine_regime(self, data: dict[str, Any]) -> str:
        """Identify market regime (expansion/contraction)."""
        # Placeholder logic
        trend = data.get("trend", 0)
        volatility = data.get("volatility", 0)

        if trend > 0.5 and volatility < 0.3:
            return "strong_bull_quiet"
        elif trend > 0.5 and volatility >= 0.3:
            return "volatile_bull"
        elif trend < -0.5:
            return "bear_trend"
        else:
            return "sideways_chop"

    def _query_memory(self, data: dict[str, Any]) -> list[str]:
        """Mock memory query."""
        # This would interface with RAG/VectorDB
        return ["2024-Q1-Rally", "2023-Correction"] if data.get("trend", 0) > 0.2 else []

    def _degraded_response(self, reason: str) -> dict:
        """Low Prana fallback."""
        return {
            "agent": self.agent_name,
            "status": "degraded",
            "reason": reason,
            "regime": "unknown",
            "context_score": 0.0,
        }
