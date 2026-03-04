"""
Intelligent Regime Detector module.

Classifies market regimes (BULL, BEAR, SIDEWAYS) based on a feature set.
Ideally integrates with `river` for online learning, but provides a 
robust heuristic fallback based on composite multi-feature scoring.
"""

from typing import Dict, Any, List
from backend.core.schemas.ooda_types import MarketRegime

class IntelligentRegimeDetector:
    """
    ML-inspired regime detection evaluating multiple normalized features
    to classify the current market environment into a MarketRegime.
    """
    
    EXPECTED_FEATURES = [
        "volatility_20d",      # 0.0 - 1.0 (normalized)
        "price_momentum_10d",  # -1.0 to 1.0 (normalized return)
        "rsi_14",              # 0.0 - 100.0
        "adx_14",              # 0.0 - 100.0 (trend strength)
        "bb_width_norm",       # 0.0 - 1.0 (bollinger band squeeze/expansion)
    ]
    
    def __init__(self):
        # Placeholders for online learning weights (e.g. Scikit-Learn SGDClassifier / River)
        # Using a fixed heuristic weighting in absence of trained model weights.
        self._weights = {
            "volatility_20d": 0.0,      # High vol doesn't dictate direction, just strength
            "price_momentum_10d": 1.5,  # Strongest directional indicator
            "rsi_14": 0.5,              # Overbought/Oversold context
            "adx_14": 0.8,              # Determines if Sideways or Trending
            "bb_width_norm": 0.2        # Confirms ADX
        }
        
    def _normalize_features(self, raw_features: Dict[str, float]) -> Dict[str, float]:
        """Normalize specific bounded features around 0 for calculation."""
        norm = {}
        for feature in self.EXPECTED_FEATURES:
            val = raw_features.get(feature, 0.0)
            if feature == "rsi_14":
                # Center around 0 (-1.0 to 1.0)
                norm[feature] = (val - 50.0) / 50.0
            elif feature == "adx_14":
                # 0 to 100 -> 0.0 to 1.0
                norm[feature] = val / 100.0
            else:
                norm[feature] = val
        return norm

    def detect_regime(self, features: Dict[str, float]) -> MarketRegime:
        """
        Classify the regime incrementally based on current feature snapshot.
        
        Args:
            features: Dictionary containing at least the EXPECTED_FEATURES.
                      Missing features default to 0.0/neutral.
        """
        norm_features = self._normalize_features(features)
        
        # 1. Evaluate Trend Strength (Is it Sideways?)
        # Combine ADX and BB Width to determine if there's any trend at all.
        adx_strength = norm_features.get("adx_14", 0.0)
        vol_strength = norm_features.get("volatility_20d", 0.0)
        
        # Arbitrary threshold: If ADX is very low (< 0.20 i.e. 20) it's likely sideways
        # unless volatility is extremely high (breakout phase).
        is_ranging = (adx_strength < 0.25) and (vol_strength < 0.8)
        
        if is_ranging:
            # Check price momentum; if it's completely flat, definitely sideways.
            return MarketRegime.SIDEWAYS
            
        # 2. Evaluate Directional Score (Bull vs Bear)
        score = 0.0
        score += norm_features.get("price_momentum_10d", 0.0) * self._weights["price_momentum_10d"]
        score += norm_features.get("rsi_14", 0.0) * self._weights["rsi_14"]
        
        # We multiply by ADX so that strong trends amplify the score, weak trends dampen it.
        trend_multiplier = adx_strength * self._weights["adx_14"]
        # Ensure multiplier is at least a baseline so we can still get a direction
        trend_multiplier = max(0.1, trend_multiplier)
        
        final_score = score * (1.0 + trend_multiplier)
        
        if final_score > 0.15:
            return MarketRegime.BULL
        elif final_score < -0.15:
            return MarketRegime.BEAR
        else:
            return MarketRegime.SIDEWAYS
