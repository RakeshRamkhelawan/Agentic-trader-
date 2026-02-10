"""
RiskManager Agent - Risk Assessment in Decide Phase.

Beoordeelt trade proposals en genereert RiskAssessment (approve/reject).
"""

import logging
from typing import Dict, Any, Optional

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (
    TradeProposal,
    RiskAssessment,
    RiskDecision,
    MarketRegime
)

logger = logging.getLogger(__name__)


class RiskManagerAgent(BaseAgent):
    """
    RiskManager Agent - Risk & Compliance specialist.
    
    Rol in OODA: **DECIDE** (gatekeeping)
    - Beoordeelt proposed trades op risk constraints
    - Checked position limits
    - Evalueert market regime suitability
    - Output: RiskAssessment (APPROVE/REJECT/REDUCE_SIZE)
    """
    
    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        max_position_size: float = 1.0,
        max_leverage: float = 3.0,
        min_confidence: float = 0.6
    ):
        """
        Initialiseer RiskManager.
        
        Args:
            llm_provider: LLM (voor risk narratives)
            event_bus: Event bus
            max_position_size: Max position size als fractie van capital
            max_leverage: Max leverage multiplier
            min_confidence: Min confidence voor approval
        """
        super().__init__(
            agent_name="RiskManager",
            llm_provider=llm_provider,
            event_bus=event_bus
        )
        
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
        self.min_confidence = min_confidence
        
        self.assessments_made = 0
        self.trades_approved = 0
        self.trades_rejected = 0
    
    async def assess_risk(
        self,
        proposal: TradeProposal,
        current_regime: MarketRegime,
        current_position_size: float = 0.0
    ) -> RiskAssessment:
        """
        Beoordeel trade proposal en genereer RiskAssessment.
        
        Args:
            proposal: Trade voorstel van TraderAgent
            current_regime: Current market regime
            current_position_size: Huidige position size (als fractie van capital)
        
        Returns:
            RiskAssessment met decision + rationale
        """
        self.heartbeat()
        
        try:
            # Run risk checks
            violations = []
            
            # 1. Confidence check
            if proposal.confidence < self.min_confidence:
                violations.append(
                    f"Confidence {proposal.confidence:.2f} < minimum {self.min_confidence}"
                )
            
            # 2. Position size check
            if proposal.size > self.max_position_size:
                violations.append(
                    f"Size {proposal.size} > max {self.max_position_size}"
                )
            
            # 3. Leverage check
            if proposal.leverage and proposal.leverage > self.max_leverage:
                violations.append(
                    f"Leverage {proposal.leverage} > max {self.max_leverage}"
                )
            
            # 4. Regime suitability check
            if current_regime == MarketRegime.VOLATILE and proposal.leverage and proposal.leverage > 1.5:
                violations.append(
                    f"High leverage {proposal.leverage} in VOLATILE regime"
                )
            
            # 5. Position concentration check
            new_position = current_position_size + proposal.size
            if abs(new_position) > self.max_position_size * 1.5:
                violations.append(
                    f"New position {new_position:.2f} exceeds concentration limit"
                )
            
            # Determine decision
            if not violations:
                decision = RiskDecision.APPROVE
                rationale = f"All risk checks passed (confidence={proposal.confidence:.2f})"
                self.trades_approved += 1
            elif len(violations) == 1 and "Size" in violations[0]:
                # Size reduction scenario
                decision = RiskDecision.REDUCE_SIZE
                suggested_size = min(proposal.size, self.max_position_size)
                rationale = f"Reducing size from {proposal.size} to {suggested_size}: {violations[0]}"
            else:
                decision = RiskDecision.REJECT
                rationale = f"Risk violations: {'; '.join(violations)}"
                self.trades_rejected += 1
            
            # Create RiskAssessment
            assessment = RiskAssessment(
                trade_id=proposal.trade_id,
                decision=decision,
                rationale=rationale,
                risk_score=self._calculate_risk_score(proposal, violations)
            )
            
            self.assessments_made += 1
            self.record_activity(success=True)
            
            logger.info(
                f"Risk assessment: {proposal.symbol} {proposal.side} "
                f"→ {decision.value} (score={assessment.risk_score:.2f})"
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            self.record_activity(success=False)
            raise
    
    def _calculate_risk_score(
        self,
        proposal: TradeProposal,
        violations: list
    ) -> float:
        """
        Bereken risk score voor trade.
        
        Risk score: 0.0 (safe) tot 1.0 (zeer risicovol)
        
        Returns:
            Risk score in [0, 1]
        """
        # Base risk van violations
        violation_risk = len(violations) * 0.2
        
        # Confidence risk (lagere confidence = hoger risk)
        confidence_risk = 1.0 - proposal.confidence
        
        # Size risk
        size_risk = min(proposal.size / self.max_position_size, 1.0)
        
        # Leverage risk
        leverage = proposal.leverage or 1.0
        leverage_risk = min(leverage / self.max_leverage, 1.0)
        
        # Weighted average
        total_risk = (
            0.3 * violation_risk +
            0.3 * confidence_risk +
            0.2 * size_risk +
            0.2 * leverage_risk
        )
        
        return max(0.0, min(1.0, total_risk))
    
    async def analyze(self, features: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgent abstract - gebruik assess_risk()."""
        logger.warning("analyze() called on RiskManager - use assess_risk() instead")
        return {
            "recommendation": "Use assess_risk() for RiskManagerAgent",
            "confidence": 0.0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Krijg RiskManager statistieken."""
        health = self.health_check()
        
        approval_rate = 0.0
        if self.assessments_made > 0:
            approval_rate = self.trades_approved / self.assessments_made
        
        return {
            **health,
            "assessments_made": self.assessments_made,
            "trades_approved": self.trades_approved,
            "trades_rejected": self.trades_rejected,
            "approval_rate": approval_rate
        }
