"""
Strategy Weight Adapter - Online updates for strategy selection weights.

Adapts strategy weights based on online learning performance.
Updates happen in cold path and are atomically swapped to hot path.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy."""

    strategy_name: str
    win_count: int = 0
    loss_count: int = 0
    total_pnl: float = 0.0
    avg_return: float = 0.0
    sharpe: float = 0.0
    sample_count: int = 0


class StrategyWeightAdapter:
    """
    Adapts strategy weights based on performance.

    Uses exponential moving average for weight updates:
    weight_new = alpha * performance_score + (1 - alpha) * weight_old

    Hot path reads atomic snapshot, cold path updates weights.
    """

    def __init__(
        self,
        strategies: List[str],
        alpha: float = 0.1,
        min_samples: int = 10,
        epsilon: float = 0.1,  # Minimum weight (exploration)
    ):
        """
        Initialize strategy adapter.

        Args:
            strategies: List of strategy names
            alpha: EMA learning rate (0.1 = 10% new, 90% old)
            min_samples: Minimum samples before weight updates
            epsilon: Minimum weight for exploration
        """
        self.strategies = strategies
        self.alpha = alpha
        self.min_samples = min_samples
        self.epsilon = epsilon

        # Initialize equal weights
        n_strategies = len(strategies)
        self._weights: Dict[str, float] = {s: 1.0 / n_strategies for s in strategies}

        # Performance tracking
        self._performance: Dict[str, StrategyPerformance] = {
            s: StrategyPerformance(strategy_name=s) for s in strategies
        }

        # Atomic snapshot for hot path
        self._weight_snapshot: Dict[str, float] = self._weights.copy()
        self._snapshot_lock = asyncio.Lock()

        logger.info(
            f"StrategyWeightAdapter initialized: strategies={strategies}, "
            f"alpha={alpha}"
        )

    async def update_performance(
        self,
        strategy_name: str,
        return_value: float,
        win: bool,
    ) -> None:
        """
        Update strategy performance (cold path).

        Args:
            strategy_name: Name of strategy
            return_value: Return from trade (positive/negative)
            win: Whether trade was profitable
        """
        if strategy_name not in self._performance:
            logger.warning(f"Unknown strategy: {strategy_name}")
            return

        perf = self._performance[strategy_name]
        perf.sample_count += 1
        perf.total_pnl += return_value

        if win:
            perf.win_count += 1
        else:
            perf.loss_count += 1

        # Update average return (EMA)
        perf.avg_return = self.alpha * return_value + (1 - self.alpha) * perf.avg_return

        # Update weights periodically
        if perf.sample_count >= self.min_samples:
            await self._update_weights()

    async def _update_weights(self) -> None:
        """Update strategy weights based on performance."""
        # Calculate performance scores
        scores = {}
        for name, perf in self._performance.items():
            if perf.sample_count < self.min_samples:
                scores[name] = 0.5  # Neutral score
            else:
                # Win rate component
                win_rate = perf.win_count / max(perf.sample_count, 1)

                # Return component (normalized)
                return_score = np.tanh(perf.avg_return * 10)  # Scale to [-1, 1]

                # Combined score
                scores[name] = 0.6 * win_rate + 0.4 * (return_score + 1) / 2

        # Softmax to get weights
        exp_scores = {k: np.exp(v) for k, v in scores.items()}
        total = sum(exp_scores.values())

        new_weights = {k: v / total for k, v in exp_scores.items()}

        # Apply epsilon floor (ensure minimum exploration)
        for name in new_weights:
            new_weights[name] = max(new_weights[name], self.epsilon)

        # Renormalize after floor
        total = sum(new_weights.values())
        new_weights = {k: v / total for k, v in new_weights.items()}

        # Update weights
        self._weights = new_weights

        # Atomic snapshot update
        async with self._snapshot_lock:
            self._weight_snapshot = new_weights.copy()

        logger.debug(f"Strategy weights updated: {new_weights}")

    def get_weights(self) -> Dict[str, float]:
        """
        Get current strategy weights (hot path - O(1)).

        Returns atomic snapshot without blocking.
        """
        return self._weight_snapshot.copy()

    def get_strategy_ranking(self) -> List[tuple]:
        """Get strategies ranked by weight."""
        weights = self.get_weights()
        return sorted(weights.items(), key=lambda x: x[1], reverse=True)

    def get_performance_summary(self) -> Dict:
        """Get performance summary for all strategies."""
        return {
            name: {
                "win_rate": perf.win_count / max(perf.sample_count, 1),
                "total_pnl": perf.total_pnl,
                "avg_return": perf.avg_return,
                "sample_count": perf.sample_count,
            }
            for name, perf in self._performance.items()
        }

    def reset(self) -> None:
        """Reset all weights and performance."""
        n_strategies = len(self.strategies)
        self._weights = {s: 1.0 / n_strategies for s in self.strategies}
        self._performance = {
            s: StrategyPerformance(strategy_name=s) for s in self.strategies
        }
        self._weight_snapshot = self._weights.copy()
        logger.info("StrategyWeightAdapter reset")
