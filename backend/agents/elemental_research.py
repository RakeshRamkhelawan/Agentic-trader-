"""
Air Elemental Agent (Vayu) - The Researcher.

Role: Research / Idea Generation
Element: Air (Movement/Vayu)
Guna Balance: High Rajas (Action/Movement)
Prana Cost: Moderate (10 units)
Tattva Layer: 33

Function:
- Generates hypotheses from data.
- Explores possibilities (divergent thinking).
- Contrarian analysis (moving against the wind).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.agents.elemental_base import ElementalBase
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)

class ElementalResearch(ElementalBase):
    """
    Air Agent: Movement, ideas, investigation.
    High Rajas drives active exploration and hypothesis generation.
    """
    
    def __init__(
        self,
        agent_name: str = "Research_Air",
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        system_identity: Optional[Any] = None,
        agent_role: AgentRole = AgentRole.RESEARCHER
    ):
        super().__init__(
            agent_name=agent_name,
            element="air",
            tattva_layer=33,
            guna_balance={
                "sattva": 0.3, # Clarity to see patterns
                "rajas": 0.6,  # High movement/investigation
                "tamas": 0.1   # Low inertia
            },
            llm_provider=llm_provider,
            event_bus=event_bus,
            system_identity=system_identity,
            agent_role=agent_role,
            max_prana=100.0,
            prana_decay_rate=10.0 # Moderate-High active cost
        )

    async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate research hypotheses from market signals.
        
        Args:
            signal: Market data, news, social sentiment
            
        Returns:
            Dict with 'hypothesis', 'direction', 'confidence'
        """
        if not await self.consume_prana():
            return self._degraded_response("Insufficient Prana for Research")

        try:
            data = signal.get("data", {})
            
            # Air moves where the wind blows, or against it
            hypothesis = await self._generate_hypothesis(data)
            
            result = {
                "agent": self.agent_name,
                "element": self.element,
                "hypothesis": hypothesis,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prana_remaining": self.prana
            }
            
            await self.publish_thought(
                reasoning=f"Generated Hypothesis: {hypothesis['summary']} (Conf: {hypothesis['confidence']:.2f})",
                confidence=hypothesis.get('confidence', 0.5),
                data={
                    "hypothesis": hypothesis,
                    "thought_type": "hypothesis"
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Air processing: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _generate_hypothesis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a trading hypothesis."""
        # Placeholder for LLM logic
        # For prototype: simple logic based on price change
        price_change = data.get("price_change_24h", 0)
        volume_change = data.get("volume_change_24h", 0)
        
        direction = "neutral"
        summary = "Insufficient data"
        confidence = 0.3
        
        # Rajasic Logic: Follow momentum or spot reversal
        if price_change > 5.0 and volume_change > 10.0:
            direction = "bullish"
            summary = "High momentum breakout detected"
            confidence = 0.8
        elif price_change < -5.0 and volume_change > 10.0:
            direction = "bearish"
            summary = "High volume sell-off detected"
            confidence = 0.75
        elif abs(price_change) < 1.0:
            direction = "neutral"
            summary = "Market consolidation/Indecision"
            confidence = 0.6
            
        return {
            "direction": direction,
            "summary": summary,
            "confidence": confidence,
            "factors": ["price_momentum", "volume_spike"]
        }

    def _degraded_response(self, reason: str) -> Dict:
        """Low Prana fallback."""
        return {
            "agent": self.agent_name,
            "status": "degraded",
            "reason": reason,
            "hypothesis": {
                "direction": "neutral",
                "summary": "Low Energy - Skipping Analysis",
                "confidence": 0.0
            }
        }
