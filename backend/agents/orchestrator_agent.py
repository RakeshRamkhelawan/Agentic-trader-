"""
Orchestrator Agent - The Cognitive Core (Ether element).

De Orchestrator fungeert als het 'geweten' van het systeem. Het harmoniseert 
signalen van andere agents en bewaakt de algehele systeemcoherentie.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC

from backend.agents.base_agent import BaseAgent
from backend.governance.agent_gatekeeper import AgentRole
from backend.core.schemas.ooda_types import Observation, Orientation, TradeProposal, RiskAssessment

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
    
    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None
    ):
        super().__init__(
            agent_name="Orchestrator",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST # De Orchestrator heeft strategische permissies
        )
        self.cycle_count = 0
        self.harmony_score = 1.0 # 0.0 (chaos) to 1.0 (harmony)

    async def harmonize(
        self,
        observation: Observation,
        orientation: Orientation,
        proposals: List[TradeProposal],
        risk_assessments: List[RiskAssessment]
    ) -> Dict[str, Any]:
        """
        Harmoniseert de outputs van de verschillende agents.
        
        Kijkt of de beslissingen in lijn zijn met de overkoepelende 'Sattva' staat.
        """
        self.heartbeat()
        self.cycle_count += 1
        
        # In een volwaardige implementatie zou dit een LLM call zijn die de 
        # argumenten van Bull/Bear researchers, Analyst en RiskManager weegt.
        # Voor nu implementeren we de logic die de consensus berekent.
        
        has_proposal = len(proposals) > 0
        all_approved = all(r.decision.value == "approve" for r in risk_assessments) if risk_assessments else False
        
        if not has_proposal:
            self.harmony_score = 0.9 # Rust is harmonie
            status = "STILLNESS"
            rationale = "No action required, system in state of observation."
        elif all_approved:
            self.harmony_score = 1.0
            status = "SYNCHRONIZED"
            rationale = "Full alignment between strategy and risk management."
        else:
            self.harmony_score = 0.5
            status = "FRICTION"
            rationale = "Divergence detected between proposal and risk parameters."

        result = {
            "status": status,
            "harmony_score": self.harmony_score,
            "rationale": rationale,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        self.logger.info(f"Harmony check: {status} (score={self.harmony_score})")
        
        # Publish meta-thought
        await self.publish_thought(
            reasoning=rationale,
            confidence=self.harmony_score,
            data=result
        )
        
        return result

    async def analyze(self, features: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgent abstract method override."""
        return await self.harmonize(
            observation=context.get('observation'),
            orientation=context.get('orientation'),
            proposals=context.get('proposals', []),
            risk_assessments=context.get('risk_assessments', [])
        )
