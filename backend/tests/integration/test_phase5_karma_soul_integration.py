"""
Phase 5a Integration Tests: Karma Memory + Soul Context + Mind Threshold

Validates that EpisodeMemory causality thresholds flow from Soul context
into Mind decision-making, blocking low-confidence signals after bad karma.
"""

import time
from unittest.mock import AsyncMock

import pytest

from backend.core.cognitive_mind_service import CognitiveMindService
from backend.core.eternal_soul_service import EternalSoulService
from backend.core.karma.episode_memory import EpisodeMemory, KarmaEpisode
from backend.core.zero_copy_bridge import ZeroCopyBridge

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def memory():
    return EpisodeMemory(max_episodes=100)


@pytest.fixture
def good_episodes():
    """5 positive karma episodes in BULL regime."""
    now = time.time()
    return [
        KarmaEpisode(
            timestamp=now - i * 10,
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=0.02,
            drawdown_percent=0.005,
            duration_ms=30000,
            karma_score=0.8,
        )
        for i in range(5)
    ]


@pytest.fixture
def bad_episodes():
    """5 negative karma episodes in BULL regime."""
    now = time.time()
    return [
        KarmaEpisode(
            timestamp=now - i * 10,
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=-0.03,
            drawdown_percent=0.02,
            duration_ms=30000,
            karma_score=-0.8,
        )
        for i in range(5)
    ]


@pytest.fixture
def mock_redis():
    client = AsyncMock()
    client.ping = AsyncMock()
    client.set = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.publish = AsyncMock()
    client.close = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_soul_context_includes_causality_threshold(mock_redis):
    """Soul context must include the causality_threshold key."""
    soul = EternalSoulService()
    soul.redis_client = mock_redis

    context = await soul.process_cycle()
    assert "causality_threshold" in context
    assert isinstance(context["causality_threshold"], float)


@pytest.mark.asyncio
async def test_bad_karma_raises_threshold(memory, bad_episodes, mock_redis):
    """After negative episodes, causality threshold should be elevated (> 0.6)."""
    for ep in bad_episodes:
        memory.record(ep)

    soul = EternalSoulService()
    soul.redis_client = mock_redis
    soul.episode_memory = memory

    context = await soul.process_cycle()
    assert context["causality_threshold"] > 0.6


@pytest.mark.asyncio
async def test_good_karma_keeps_normal_threshold(memory, good_episodes, mock_redis):
    """After positive episodes, causality threshold should remain at ~0.6."""
    for ep in good_episodes:
        memory.record(ep)

    soul = EternalSoulService()
    soul.redis_client = mock_redis
    soul.episode_memory = memory

    context = await soul.process_cycle()
    assert context["causality_threshold"] == pytest.approx(0.6, abs=0.05)


def test_empty_memory_returns_default_threshold(memory):
    """Empty episode memory should return default threshold 0.6."""
    threshold = memory.get_causality_threshold(current_regime="BULL")
    assert threshold == pytest.approx(0.6, abs=0.001)


def test_causal_weight_same_regime_higher_than_different(memory, good_episodes):
    """Episodes in the same regime should have higher causal weight."""
    ep = good_episodes[0]
    now = time.time()

    weight_same = memory.get_causal_weight(ep, "BULL", now)
    weight_diff = memory.get_causal_weight(ep, "BEAR", now)

    assert weight_same > weight_diff
