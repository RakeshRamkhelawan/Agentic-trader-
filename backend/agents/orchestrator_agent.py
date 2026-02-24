"""
Orchestrator Agent - The Cognitive Core (Ether element).

De Orchestrator fungeert als het 'geweten' van het systeem. Het harmoniseert
signalen van andere agents en bewaakt de algehele systeemcoherentie.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (
    Observation,
    Orientation,
    ResearchHypothesis,
    RiskAssessment,
    TradeProposal,
)
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Central coordination and harmony.

    Element: Ether (Akasha)
    Guna: Sattva (0.8)

    Verantwoordelijkheden:
    - Harmoniseren van tegenstrijdige signalen.
    - Bewaken van de meta-strategie.
    - Zorgen voor 'balance' en 'non-attachment' in de trading cycle.
    """

    def __init__(self, llm_provider: Any | None = None, event_bus: Any | None = None):
        super().__init__(
            agent_name="Orchestrator",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST,  # De Orchestrator heeft strategische permissies
        )
        self.cycle_count = 0
        self.harmony_score = 1.0  # 0.0 (chaos) to 1.0 (harmony)

    async def harmonize(
        self,
        observation: Observation,
        orientation: Orientation,
        bull_hypothesis: ResearchHypothesis | None,
        bear_hypothesis: ResearchHypothesis | None,
        proposals: list[TradeProposal],
        risk_assessments: list[RiskAssessment],
    ) -> dict[str, Any]:
        """
        Harmoniseert de outputs van de verschillende agents.

        Kijkt of de beslissingen in lijn zijn met de overkoepelende 'Sattva' staat.
        Weegt risk assessments en contrarian research.
        """
        self.heartbeat()
        self.cycle_count += 1

        # Start met perfecte harmonie
        self.harmony_score = 1.0
        status_reasons = []

        # 1. Risk Check
        all_approved = (
            all(r.decision.value == "approve" for r in risk_assessments)
            if risk_assessments
            else True
        )
        if risk_assessments and not all_approved:
            self.harmony_score -= 0.5
            status_reasons.append("Risk Rejection")

        # 2. Cognitive Dissonance Check (Bull vs Bear collision)
        if bull_hypothesis and bear_hypothesis:
            if bull_hypothesis.confidence > 0.7 and bear_hypothesis.confidence > 0.7:
                self.harmony_score -= 0.2
                status_reasons.append("Cognitive Dissonance (High Conviction Conflict)")

        # 3. Directional Conflict (Analyst vs Contrarian)
        # Als Analyst BULLISH is, maar Bear Researcher is very confident (>0.8)
        if (
            orientation.regime == "trending_up"
            and bear_hypothesis
            and bear_hypothesis.confidence > 0.8
        ):
            self.harmony_score -= 0.1
            status_reasons.append("Bearish Divergence")

        # Als Analyst BEARISH is, maar Bull Researcher is very confident (>0.8)
        if (
            orientation.regime == "trending_down"
            and bull_hypothesis
            and bull_hypothesis.confidence > 0.8
        ):
            self.harmony_score -= 0.1
            status_reasons.append("Bullish Divergence")

        # 4. Determine final status
        if self.harmony_score >= 0.9:
            status = "SYNCHRONIZED"
        elif self.harmony_score >= 0.6:
            status = "FRICTION"
        else:
            status = "DISCORD"

        has_proposal = len(proposals) > 0
        if not has_proposal and status == "SYNCHRONIZED":
            status = "STILLNESS"
            rationale = "System in equilibrium. No trade signal, risks nominal."
        else:
            rationale = f"Harmony Score {self.harmony_score:.2f}. Issues: {', '.join(status_reasons) if status_reasons else 'None'}"

        result = {
            "status": status,
            "harmony_score": round(self.harmony_score, 2),
            "rationale": rationale,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.logger.info(f"Harmony check: {status} (score={self.harmony_score:.2f})")

        # Publish meta-thought
        await self.publish_thought(reasoning=rationale, confidence=self.harmony_score, data=result)

        return result

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent abstract method override."""
        return await self.harmonize(
            observation=context.get("observation"),
            orientation=context.get("orientation"),
            bull_hypothesis=context.get("bull_hypothesis"),
            bear_hypothesis=context.get("bear_hypothesis"),
            proposals=context.get("proposals", []),
            risk_assessments=context.get("risk_assessments", []),
        )
