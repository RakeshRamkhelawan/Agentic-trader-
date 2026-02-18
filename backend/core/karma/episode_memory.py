"""
Karma Episode Memory — Regime-aware memory with causal decay (Spec §5.3, §6.3).

Provides:
- KarmaEpisode: single trade outcome record
- EpisodeMemory: ring buffer with regime-specific decay, causality threshold
"""

import math
import time
from collections import deque
from typing import List, Optional

from pydantic import BaseModel, field_validator


class KarmaEpisode(BaseModel):
    """Single trade outcome record for karma memory."""

    timestamp: float
    regime: str
    strategy: str
    action: int
    pnl_percent: float
    drawdown_percent: float
    duration_ms: int
    karma_score: float

    @field_validator("drawdown_percent", mode="before")
    @classmethod
    def cap_drawdown(cls, v: float) -> float:
        return min(max(v, 0.0), 1.0)


# Regime → decay rate mapping (spec: trending=0.95, ranging=0.85, volatile=0.70)
_REGIME_DECAY = {
    "BULL": 0.95,
    "BEAR": 0.95,
    "SIDEWAYS": 0.85,
    "VOLATILE": 0.70,
}

# Default thresholds
_DEFAULT_THRESHOLD = 0.6
_ELEVATED_THRESHOLD = 0.8


class EpisodeMemory:
    """Ring-buffer karma memory with regime-aware decay and causality thresholds."""

    def __init__(self, max_episodes: int = 100):
        self._episodes: deque = deque(maxlen=max_episodes)
        self._max = max_episodes

    def record(self, episode: KarmaEpisode) -> None:
        """Add an episode to memory (evicts oldest if full)."""
        self._episodes.append(episode)

    def get_episodes(self) -> List[KarmaEpisode]:
        """Return all episodes in order."""
        return list(self._episodes)

    def get_decay_rate(self, regime: str) -> float:
        """Return decay rate for given regime."""
        return _REGIME_DECAY.get(regime, 0.85)

    def get_causal_weight(
        self,
        episode: KarmaEpisode,
        current_regime: str,
        current_time: Optional[float] = None,
    ) -> float:
        """Calculate causal relevance weight for an episode.

        Weight = regime_match_factor × recency_factor

        - regime_match_factor: 1.0 if same regime, 0.2 if different
        - recency_factor: decay_rate ^ (age_seconds / 60) — decays per minute
        """
        if current_time is None:
            current_time = time.time()

        # Regime match
        regime_factor = 1.0 if episode.regime == current_regime else 0.2

        # Recency decay
        age_seconds = max(0.0, current_time - episode.timestamp)
        age_minutes = age_seconds / 60.0
        decay_rate = self.get_decay_rate(current_regime)
        recency_factor = math.pow(decay_rate, age_minutes)

        return regime_factor * recency_factor

    def get_causality_threshold(self, current_regime: str) -> float:
        """Calculate causality threshold based on recent karma.

        - If recent episodes are mostly positive karma → 0.6 (normal)
        - If recent episodes are mostly negative karma → 0.8 (stricter)
        - Empty memory → 0.6 (default)
        """
        if not self._episodes:
            return _DEFAULT_THRESHOLD

        now = time.time()
        weighted_karma = 0.0
        total_weight = 0.0

        for ep in self._episodes:
            w = self.get_causal_weight(ep, current_regime, now)
            weighted_karma += ep.karma_score * w
            total_weight += w

        if total_weight == 0.0:
            return _DEFAULT_THRESHOLD

        avg_karma = weighted_karma / total_weight

        # Map karma [-1, 1] to threshold [0.8, 0.6]
        # avg_karma = 1.0 → threshold = 0.6
        # avg_karma = -1.0 → threshold = 0.8
        # Linear interpolation
        threshold = _ELEVATED_THRESHOLD - (avg_karma + 1.0) / 2.0 * (
            _ELEVATED_THRESHOLD - _DEFAULT_THRESHOLD
        )
        return max(_DEFAULT_THRESHOLD, min(_ELEVATED_THRESHOLD, threshold))
