"""
Earth Elemental Agent (Prithvi) - Valuation & Execution.

Role: Valuation / Execution / Stability
Element: Earth (Stability/Prithvi)
Guna Balance: High Tamas (Stability), Sattva (Precision)
Prana Cost: Moderate (8 units)
Tattva Layer: 36

Function:
- Grounds abstract strategies into concrete orders.
- Calculates fair value (intrinsic worth).
- Ensures execution quality and sizing.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from backend.agents.elemental_base import ElementalBase
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)

class ElementalValuation(ElementalBase):
    """
    Earth Agent: Stability, manifestation, concrete value.
    High Tamas ensures grounding and resistance to volatility.
    """
    
    def __init__(
        self,
        agent_name: str = "Valuation_Earth",
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        system_identity: Optional[Any] = None,
        agent_role: AgentRole = AgentRole.EXECUTOR # Needs Execution rights
    ):
        super().__init__(
            agent_name=agent_name,
            element="earth",
            tattva_layer=36,
            guna_balance={
                "sattva": 0.1, 
                "rajas": 0.1,  
                "tamas": 0.8   # High inertia/stability
            },
            llm_provider=llm_provider,
            event_bus=event_bus,
            system_identity=system_identity,
            agent_role=agent_role,
            max_prana=100.0,
            prana_decay_rate=8.0
        )

    async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate valuation and propose execution details.
        """
        if not await self.consume_prana():
            return self._degraded_response("Insufficient Prana for Valuation")

        try:
            market_data = signal.get("data", {})
            strategy = signal.get("strategy", {})
            
            # 1. Valuation Gap
            valuation = self._calculate_valuation(market_data)
            
            # 2. Sizing / Execution Proposal
            proposal = self._generate_proposal(strategy, valuation)
            
            result = {
                "agent": self.agent_name,
                "element": self.element,
                "valuation_gap": valuation["gap"],
                "proposal": proposal,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prana_remaining": self.prana
            }
            
            await self.publish_thought(
                reasoning=f"Valuation Gap: {valuation['gap']:.2f}%. Proposing size: {proposal['size']}",
                confidence=0.9,
                data={
                    "valuation": valuation,
                    "proposal": proposal,
                    "thought_type": "valuation"
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Earth processing: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _calculate_valuation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine fair value."""
        # Placeholder logic
        # If price < moving_average, considered 'undervalued'
        price = data.get("price", 100)
        ma_200 = data.get("ma_200", 100)
        
        gap_percent = ((ma_200 - price) / price) * 100.0
        
        return {
            "fair_value": ma_200,
            "current_price": price,
            "gap": gap_percent, # Positive means undervalued
            "status": "undervalued" if gap_percent > 0 else "overvalued"
        }

    def _generate_proposal(self, strategy: Dict[str, Any], valuation: Dict[str, Any]) -> Dict[str, Any]:
        """Create concrete trade proposal."""
        direction = strategy.get("direction", "neutral")
        
        if direction == "neutral":
            return {"action": "hold", "size": 0}
            
        # Earth resists action unless valuation confirms
        if direction == "bullish" and valuation["gap"] < 0:
            # Conflict: Strategy says buy, Valuation says overvalued
            return {"action": "hold", "reason": "Overvalued - Earth Block", "size": 0}
            
        size = 1000 # Default unit
        if valuation["gap"] > 5.0:
            size = 2000 # Size up for deep value
            
        return {
            "action": "buy" if direction == "bullish" else "sell",
            "size": size,
            "type": "limit"
        }

    def _degraded_response(self, reason: str) -> Dict:
        """Low Prana fallback."""
        return {
            "agent": self.agent_name,
            "status": "degraded",
            "reason": reason,
            "valuation_gap": 0.0,
            "proposal": {"action": "hold", "reason": "Low Energy"}
        }
