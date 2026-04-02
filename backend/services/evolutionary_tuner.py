import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.learning.thompson_selector import ThompsonSamplingSelector

logger = logging.getLogger(__name__)


class EvolutionaryTuner:
    """
    Automated Hyperparameter Tuner (Auto-Pilot).

    Uses Thompson Sampling per market regime to dynamically adjust agent weights
    based on real-time trade performance.

    Features:
    - Regime-specific bandits (Expansion, Contraction, Neutral)
    - Maximum Aggressiveness: Lower priors for faster adaptation
    - Persistence: Saves/loads weights from JSON
    - Safe-Floors: Ensures weights never drop below a minimum threshold
    """

    DEFAULT_WEIGHTS = {
        "expansion": {
            "vedastro": 0.40,
            "earth": 0.25,
            "fire": 0.25,
            "water": 0.10,
            "threshold": 0.35,
        },
        "contraction": {
            "vedastro": 0.20,
            "earth": 0.45,
            "fire": 0.15,
            "water": 0.20,
            "threshold": 0.40,
        },
        "neutral": {
            "vedastro": 0.30,
            "earth": 0.30,
            "fire": 0.25,
            "water": 0.15,
            "threshold": 0.35,
        },
    }

    def __init__(self, config_path: str = "backend/data/adaptive_weights.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Agents to tune
        self.agents = ["vedastro", "earth", "fire", "water"]

        # Max Aggressiveness: Use a thin prior (0.5, 0.5) for fast response to wins/losses
        self.regimes = ["expansion", "contraction", "neutral"]
        self.bandits = {regime: ThompsonSamplingSelector(self.agents) for regime in self.regimes}

        # Set aggressive priors (0.5 means first trade has huge impact)
        for b in self.bandits.values():
            for agent in self.agents:
                b.alpha[agent] = 0.5
                b.beta[agent] = 0.5

        # Current working weights
        self.current_weights = self.load_weights()

        # Slippage tracking (Phase 5)
        self.avg_slippage = {r: 0.0 for r in self.regimes}
        self.slippage_counts = {r: 0 for r in self.regimes}

    def load_weights(self) -> Dict[str, Any]:
        """Load weights from persistent storage or return defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    # Simple validation
                    if "expansion" in data:
                        return data
            except Exception as e:
                logger.error(f"[TUNER] Failed to load weights: {e}")

        return self.DEFAULT_WEIGHTS

    def save_weights(self) -> None:
        """Persist current weights to JSON."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.current_weights, f, indent=4)
            logger.info(f"[TUNER] Saved adaptive weights to {self.config_path}")
        except Exception as e:
            logger.error(f"[TUNER] Failed to save weights: {e}")

    def update_performance(
        self, regime: str, outcome: float, agents_involved: List[str], slippage: float = 0.0
    ) -> None:
        """
        Update the Thompson Bandit for a specific regime based on trade outcome.

        Args:
            regime: The market regime (expansion/contraction/neutral)
            outcome: Return % of the trade (>0 is success)
            agents_involved: List of agents that contributed to this decision
            slippage: Observed slippage % for this trade
        """
        if regime not in self.regimes:
            logger.warning(f"[TUNER] Unknown regime: {regime}")
            return

        bandit = self.bandits[regime]

        # SLIPPAGE-AWARE REWARD:
        # A trade is a "Success" (1.0) only if the outcome (PnL%)
        # is greater than the slippage costs.
        # We use a 1.5x multiplier for slippage to be conservative.
        effective_outcome = outcome - (slippage * 1.5)
        reward = 1.0 if effective_outcome > 0 else 0.0

        # Update all agents involved in the successful or failed decision
        for agent in agents_involved:
            if agent in self.agents:
                bandit.update(agent, reward)

        # SLIPPAGE TRACKING (Running Average)
        if slippage > 0:
            count = self.slippage_counts[regime]
            current_avg = self.avg_slippage[regime]
            self.avg_slippage[regime] = (current_avg * count + slippage) / (count + 1)
            self.slippage_counts[regime] += 1

        # Recalculate weights for this regime
        self._optimize_regime(regime)

    def _optimize_regime(self, regime: str) -> None:
        """Recalculate weights based on Thompson sampling stats."""
        bandit = self.bandits[regime]
        stats = bandit.get_stats()

        # Total "success probability" sum for normalization
        total_p = sum(s["expected_winrate"] for s in stats.values())

        if total_p == 0:
            return

        # Calculate new weights based on expected winrate proportions
        new_weights = {}
        for agent, stat in stats.items():
            # Apply a safe floor of 10% to prevent an agent from completely disappearing
            raw_weight = stat["expected_winrate"] / total_p
            new_weights[agent] = max(0.10, round(raw_weight, 3))

        # Re-normalize after floors to ensure sum = 1.0 (excluding threshold)
        weight_sum = sum(new_weights.values())
        for agent in new_weights:
            new_weights[agent] = round(new_weights[agent] / weight_sum, 3)

        # Ensure it sums exactly to 1.0 (adjust largest)
        diff = 1.0 - sum(new_weights.values())
        if abs(diff) > 0.001:
            largest = max(new_weights, key=new_weights.get)
            new_weights[largest] += diff

        # Update current weights (preserving threshold)
        self.current_weights[regime].update(new_weights)

        # Agressive threshold adjustment:
        # If the best agent has a low winrate, increase threshold
        best_winrate = max(s["expected_winrate"] for s in stats.values())
        if best_winrate < 0.45:
            # Raise threshold to be more selective
            current_t = self.current_weights[regime].get("threshold", 0.35)
            self.current_weights[regime]["threshold"] = min(0.50, round(current_t + 0.02, 3))
        elif best_winrate > 0.60:
            # Lower threshold to be more aggressive
            current_t = self.current_weights[regime].get("threshold", 0.35)
            self.current_weights[regime]["threshold"] = max(0.30, round(current_t - 0.01, 3))

        self.save_weights()
        logger.info(
            f"[TUNER] Re-optimized {regime} weights: {new_weights} (Threshold: {self.current_weights[regime]['threshold']})"
        )

    def get_weights(self, regime: str) -> Dict[str, float]:
        """Get the current weights for a regime."""
        regime = regime.lower()
        if regime not in self.current_weights:
            return self.DEFAULT_WEIGHTS.get(regime, self.DEFAULT_WEIGHTS["neutral"])
        return self.current_weights[regime]


# Global instance for shared use
tuner = EvolutionaryTuner()
