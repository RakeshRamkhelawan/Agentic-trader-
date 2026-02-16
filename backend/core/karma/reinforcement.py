import random
from typing import Dict, Any

class ParameterTuner:
    """
    Adjusts agent parameters based on Karma feedback (Simple RL).
    """

    def tune(self, current_params: Dict[str, float], karma: float, learning_rate: float = 0.05) -> Dict[str, float]:
        """
        Nudge parameters. 
        If Karma > 0, we assume recent "random" nudges or state was good. 
        But here we don't track *which* direction caused the karma yet (simplified).
        
        Simplified Strategy:
        - If Karma is high, stability (reduce mutations).
        - If Karma is negative, explore (mutate parameters).
        """
        
        new_params = current_params.copy()
        
        if karma > 0.5:
            # Good state, keep it stable, maybe very slight refinement
            return new_params
            
        # If Karma is low/negative, try to mutate to find better state
        # Direction is random in this simple version (Random Walk / Simulated Annealing lite)
        for key, value in new_params.items():
            if isinstance(value, (int, float)):
                # Nudge by +/- learning_rate %
                nudge = random.uniform(-learning_rate, learning_rate)
                new_params[key] = value * (1 + nudge)
                
        return new_params
