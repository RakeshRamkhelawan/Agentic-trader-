"""
Shiva-Shakti Synchronizer (v7)

Shaivism-based logic to manage the gap between Strategy (Shiva)
and Execution (Shakti) using Market Vibration (Spanda).

Shiva: The static, pure consciousness (Our long-term strategy/Capital preservation)
Shakti: The dynamic, creative energy (The active trade execution)
Spanda: The bridge (The pulsation/vibration of the market)
"""

import logging
import math

logger = logging.getLogger(__name__)


class ShivaShaktiSynchronizer:
    def __init__(self):
        self.shiva_state = "stable"  # "pure intention"
        self.spanda_threshold = 0.7  # Maximum allowed disharmony

    def calculate_sync(self, strategy_pnl: float, market_vol: float, current_equity: float) -> dict:
        """
        Calculate the Synchronicity between Intent and Manifestation.
        """
        # Spanda is the market's vibration. High volatility is Spanda out of control.
        # If market vibration is too high, Shakti (execution) risks breaking away from Shiva (strategy).

        spanda_score = min(1.0, market_vol * 20.0)  # Normalized vibration

        # Sync Factor: How well is our strategy manifesting?
        # If high equity drawdown, the sync is low.
        equity_purity = current_equity / (current_equity + abs(strategy_pnl) + 0.001)

        sync_factor = (1.0 - spanda_score) * 0.4 + (equity_purity * 0.6)

        harmony_level = "high"
        if sync_factor < 0.4:
            harmony_level = "low"
        elif sync_factor < 0.65:
            harmony_level = "medium"

        return {
            "sync_factor": round(sync_factor, 3),
            "spanda_vibration": round(spanda_score, 3),
            "harmony_level": harmony_level,
            "action_advice": self._get_advice(harmony_level, spanda_score),
        }

    def _get_advice(self, harmony: str, spanda: float) -> str:
        if harmony == "low":
            return "Dissolve Shakti: Stop trading. Intention (Shiva) is lost in chaos."
        if spanda > 0.8:
            return "Restrict Shakti: Market vibration too violent. Reduce size."
        if harmony == "high":
            return "Perfect Tandava: Execution and Strategy are in pure sync."
        return "Stable Flow: Maintain existing positions."


# Singleton instance
_sync = None


def get_synchronizer():
    global _sync
    if _sync is None:
        _sync = ShivaShaktiSynchronizer()
    return _sync
