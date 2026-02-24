"""
Ether Elemental Agent (Akasha) - The Harmonizer.

Role: Orchestrator / Cognitive Core
Element: Ether (Space/Akasha)
Guna Balance: High Sattva (Pure Awareness)
Prana Cost: High (15 units) - Maintains field of coherence
Tattva Layer: 32

Function:
- Harmonizes signals from other elemental agents.
- maintaining system coherence (Sattva).
- Synthesizes fragmented insights into holistic strategy.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from backend.agents.elemental_base import ElementalBase
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class ElementalOrchestrator(ElementalBase):
    """
    Ether Agent: The space in which all other elements operate.
    Responsible for harmony, synthesis, and high-level direction.
    """

    def __init__(
        self,
        agent_name: str = "Orchestrator_Ether",
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        system_identity: Any | None = None,
        agent_role: AgentRole = AgentRole.STRATEGIST,
    ):
        super().__init__(
            agent_name=agent_name,
            element="ether",
            tattva_layer=32,
            guna_balance={
                "sattva": 0.8,  # Pure awareness/clarity
                "rajas": 0.1,  # Minimal movement
                "tamas": 0.1,  # Minimal inertia
            },
            llm_provider=llm_provider,
            event_bus=event_bus,
            system_identity=system_identity,
            agent_role=agent_role,
            max_prana=100.0,
            prana_decay_rate=15.0,  # High cognitive load
        )
        self.harmony_history: list[float] = []

    async def process_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        """
        Harmonize input signals into a coherent system state.

        Args:
            signal: Contains 'inputs' from other agents (Earth, Air, Fire, Water)

        Returns:
            Dict with 'harmony_score', 'synthesis', 'dominant_element'
        """
        # 1. Prana Check
        if not await self.consume_prana():
            return self._degraded_response(signal, "Insufficient Prana for Harmonization")

        try:
            inputs = signal.get("inputs", {})

            # 2. Calculate System Harmony Score
            # Based on agreement/conflict between agent signals
            harmony_score = self._calculate_harmony(inputs)
            self.harmony_history.append(harmony_score)

            # 3. Synthesize Strategy
            synthesis = await self._synthesize_strategy(inputs, harmony_score)

            result = {
                "agent": self.agent_name,
                "element": self.element,
                "harmony_score": harmony_score,
                "synthesis": synthesis,
                "timestamp": datetime.now(UTC).isoformat(),
                "prana_remaining": self.prana,
            }

            # Publish thought
            await self.publish_thought(
                reasoning=f"Harmonized system state. Score: {harmony_score:.2f}. Synthesis: {synthesis['summary']}",
                confidence=synthesis.get("confidence", 0.5),
                data={
                    "harmony_score": harmony_score,
                    "synthesis": synthesis,
                    "thought_type": "harmonization",
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error in Ether processing: {e}", exc_info=True)
            return {"agent": self.agent_name, "error": str(e), "status": "error"}

    def _calculate_harmony(self, inputs: dict[str, Any]) -> float:
        """
        Calculate harmony score (0.0 - 1.0).
        High harmony: Agents agree or complementary.
        Low harmony: Direct conflict (e.g., Earth says Buy, Fire says Block).
        """
        if not inputs:
            return 1.0  # Void is harmonious

        score = 0.5  # Neutral start

        # Extract core signals
        sentiment = inputs.get("air", {}).get("sentiment", 0)  # -1 to 1
        risk_ok = inputs.get("fire", {}).get("approved", True)
        macro_regime = inputs.get("water", {}).get("regime", "neutral")
        valuation_gap = inputs.get("earth", {}).get("valuation_gap", 0)

        # Conflict detection logic
        if not risk_ok:
            score -= 0.3  # Risk blockage creates tension

        # Coherence check: Bullish sentiment + Undervalued + Good Regime = Harmony
        is_bullish = sentiment > 0.2
        is_undervalued = valuation_gap > 0
        is_favorable = macro_regime in ["expansion", "recovery"]

        if is_bullish and is_undervalued and is_favorable:
            score += 0.4
        elif is_bullish and not is_undervalued:  # FOMO tension
            score -= 0.2
        elif not is_bullish and is_undervalued:  # Contrarian tension
            score -= 0.1  # Mild tension, nature of markets

        return max(0.0, min(1.0, score))

    async def _synthesize_strategy(self, inputs: dict[str, Any], harmony: float) -> dict[str, Any]:
        """Generate high-level strategic direction."""
        # In a real implementation, this would use LLM to synthesize narrative
        # For now, deterministic logic for reliability

        summary = "Hold"
        confidence = 0.5

        if harmony > 0.7:
            summary = "Execute Coherent Strategy"
            confidence = 0.9
        elif harmony < 0.3:
            summary = "Defensive Posture - High Conflict"
            confidence = 0.8  # Confident in doing nothing
        else:
            summary = "Cautious Accumulation / Observation"
            confidence = 0.6

        return {
            "summary": summary,
            "confidence": confidence,
            "focus_element": self._determine_focus_element(inputs),
        }

    def _determine_focus_element(self, inputs: dict[str, Any]) -> str:
        """Identify which element needs attention."""
        if not inputs.get("fire", {}).get("approved", True):
            return "fire"  # Risk needs attention
        return "earth"  # Default to execution focus

    def _degraded_response(self, signal: dict, reason: str) -> dict:
        """Low Prana fallback."""
        return {
            "agent": self.agent_name,
            "status": "degraded",
            "reason": reason,
            "harmony_score": 0.5,  # Neutral assumption
            "synthesis": {"summary": "Standby (Low Energy)", "confidence": 0.1},
        }
