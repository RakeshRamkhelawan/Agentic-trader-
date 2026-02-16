from typing import Dict, Any, Optional
from pydantic import BaseModel

class TradeOutcome(BaseModel):
    pnl_percent: float
    drawdown_percent: float
    execution_speed_ms: float
    compliance_violation: bool = False

class KarmaRegister:
    """
    Tracks feedback (Karma) for agents.
    """
    
    def __init__(self):
        self.agent_karma: Dict[str, float] = {}

    def calculate_karma(self, outcome: TradeOutcome) -> float:
        """
        Derive a Karma Score from -1.0 to +1.0.
        """
        if outcome.compliance_violation:
            return -1.0 # Severe punishment for breaking rules
            
        score = 0.0
        
        # PnL reward/penalty
        if outcome.pnl_percent > 0:
            score += min(1.0, outcome.pnl_percent * 10) # 10% gain = max score likely
        else:
            score -= min(1.0, abs(outcome.pnl_percent) * 10)
            
        # Drawdown penalty
        if outcome.drawdown_percent > 0.05: # > 5% drawdown
            score -= 0.2
            
        return max(-1.0, min(1.0, score))

    def register_feedback(self, agent_name: str, outcome: TradeOutcome):
        score = self.calculate_karma(outcome)
        
        # Simple moving average of Karma
        current = self.agent_karma.get(agent_name, 0.0)
        new_karma = (current * 0.9) + (score * 0.1)
        self.agent_karma[agent_name] = new_karma
        
        return new_karma
