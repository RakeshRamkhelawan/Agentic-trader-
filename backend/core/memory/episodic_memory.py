"""
Episodic Memory System - Karma Tracking

Stores trading decisions and their outcomes for:
1. Pattern recognition (similar situations)
2. Karma scoring (performance tracking)
3. Self-reflection (learning from mistakes)
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TradingEpisode:
    """A complete trading episode stored in episodic memory."""
    id: str
    session_id: str
    timestamp: datetime
    market_context: dict
    volatility: float
    trend: str
    volume_profile: str
    guna_vector: dict
    fear_greed_index: float
    execution_quality: str
    action: str
    confidence: float
    coherence: float
    rationale: str
    outcome: str | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    exit_reason: str | None = None
    exit_timestamp: datetime | None = None
    karma_score: float = 0.5

    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        data['exit_timestamp'] = self.exit_timestamp.isoformat() if self.exit_timestamp else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "TradingEpisode":
        if data.get('timestamp'):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('exit_timestamp'):
            data['exit_timestamp'] = datetime.fromisoformat(data['exit_timestamp'])
        return cls(**data)


class EpisodicMemory:
    """Episodic memory for trading decisions."""

    def __init__(self, storage_path: str = "data/episodic_memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.episodes: list[TradingEpisode] = []
        self._load_episodes()
        logger.info(f"EpisodicMemory initialized with {len(self.episodes)} episodes")

    def _load_episodes(self):
        memory_file = self.storage_path / "episodes.json"
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    data = json.load(f)
                    self.episodes = [TradingEpisode.from_dict(ep) for ep in data]
            except Exception as e:
                logger.error(f"Failed to load episodes: {e}")
                self.episodes = []

    def _save_episodes(self):
        memory_file = self.storage_path / "episodes.json"
        try:
            data = [ep.to_dict() for ep in self.episodes]
            with open(memory_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save episodes: {e}")

    def store_episode(self, episode: TradingEpisode) -> str:
        self.episodes.append(episode)
        self._save_episodes()
        logger.info(f"Stored episode {episode.id} ({episode.action})")
        return episode.id

    def update_outcome(self, episode_id: str, outcome: str,
                       pnl: float, exit_reason: str) -> bool:
        for ep in self.episodes:
            if ep.id == episode_id:
                ep.outcome = outcome
                ep.pnl = pnl
                ep.exit_reason = exit_reason
                ep.exit_timestamp = datetime.utcnow()
                if ep.market_context.get('price'):
                    ep.pnl_pct = pnl / ep.market_context['price']
                self._save_episodes()
                logger.info(f"Updated episode {episode_id}: {outcome}, PnL: {pnl:.2f}")
                return True
        return False

    def find_similar_episodes(self, market_context: dict, limit: int = 5) -> list[TradingEpisode]:
        if not self.episodes:
            return []

        scores = []
        for ep in self.episodes:
            score = 0.0
            vol_diff = abs(ep.volatility - market_context.get('volatility_1m', 0.02))
            if vol_diff < 0.005:
                score += 0.3
            elif vol_diff < 0.01:
                score += 0.2

            if ep.trend == market_context.get('trend_direction', 'neutral'):
                score += 0.3

            if ep.volume_profile == self._classify_volume(market_context.get('volume_ratio', 1.0)):
                score += 0.2

            current_fg = market_context.get('fear_greed', 50)
            if abs(ep.fear_greed_index - current_fg) < 15:
                score += 0.2

            scores.append((ep, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        similar = [ep for ep, score in scores[:limit] if score > 0.3]
        logger.info(f"Found {len(similar)} similar episodes")
        return similar

    def calculate_karma_score(self, episodes: list[TradingEpisode]) -> float:
        if not episodes:
            return 0.5

        weighted_score = 0.0
        total_weight = 0.0
        now = datetime.utcnow()

        for ep in episodes:
            if ep.outcome is None:
                continue

            if ep.outcome == "success":
                base_score = 1.0
            elif ep.outcome == "failure":
                base_score = 0.0
            else:
                base_score = 0.5

            days_ago = (now - ep.timestamp).days
            recency_weight = max(0.1, 1.0 - (days_ago / 30))
            confidence_weight = ep.confidence
            weight = recency_weight * confidence_weight

            weighted_score += base_score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.5

        return weighted_score / total_weight

    def get_performance_stats(self, lookback_days: int = 30) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        recent = [ep for ep in self.episodes
                  if ep.timestamp > cutoff and ep.outcome is not None]

        if not recent:
            return {"total_trades": 0, "win_rate": 0.0, "avg_pnl": 0.0, "total_pnl": 0.0}

        wins = sum(1 for ep in recent if ep.outcome == "success")
        total_pnl = sum(ep.pnl for ep in recent if ep.pnl is not None)

        return {
            "total_trades": len(recent),
            "win_rate": wins / len(recent),
            "avg_pnl": total_pnl / len(recent),
            "total_pnl": total_pnl,
            "avg_confidence": sum(ep.confidence for ep in recent) / len(recent),
            "avg_coherence": sum(ep.coherence for ep in recent) / len(recent)
        }

    def _classify_volume(self, volume_ratio: float) -> str:
        if volume_ratio > 2.0:
            return "extreme"
        elif volume_ratio > 1.5:
            return "high"
        elif volume_ratio > 0.8:
            return "normal"
        else:
            return "low"

    def get_lessons_learned(self, min_episodes: int = 10) -> list:
        """Extract lessons from episode history."""
        if len(self.episodes) < min_episodes:
            return ["Insufficient data for pattern analysis"]

        lessons = []
        successful = [ep for ep in self.episodes if ep.outcome == 'success']
        failed = [ep for ep in self.episodes if ep.outcome == 'failure']

        if successful:
            avg_conf = sum(ep.confidence for ep in successful) / len(successful)
            lessons.append(f"Successful trades avg confidence: {avg_conf:.2f}")

        if failed:
            avg_conf = sum(ep.confidence for ep in failed) / len(failed)
            lessons.append(f"Failed trades avg confidence: {avg_conf:.2f}")

        return lessons


_episodic_memory = None


def get_episodic_memory() -> EpisodicMemory:
    global _episodic_memory
    if _episodic_memory is None:
        _episodic_memory = EpisodicMemory()
    return _episodic_memory
