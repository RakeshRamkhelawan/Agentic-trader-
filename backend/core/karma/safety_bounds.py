from typing import Dict, Any

class SafetyMonitor:
    """
    Enforces hard bounds on agent parameters to prevent dangerous behavior.
    """
    
    # Define hard bounds for known parameters
    BOUNDS = {
        "risk_tolerance": (0.1, 0.8), # Never > 0.8, Never < 0.1 (need some risk)
        "aggression": (0.1, 0.9),
        "position_size_limit": (0.01, 0.20) # Max 20% portfolio
    }

    def enforce_bounds(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clamp parameters to safe ranges.
        """
        safe_params = params.copy()
        
        for key, value in safe_params.items():
            if key in self.BOUNDS:
                min_val, max_val = self.BOUNDS[key]
                if value < min_val:
                    safe_params[key] = min_val
                elif value > max_val:
                    safe_params[key] = max_val
                    
        return safe_params
