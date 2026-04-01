"""
Step 2A — RED Phase: Tests for EpisodeMemory (Karma Memory System).
TDD: All tests written FIRST, expected to FAIL until Step 2B implements production code.

Tests cover:
- KarmaEpisode creation
- Regime-specific decay rates
- Causal weight calculation (regime match + recency)
- Causality threshold computation
- Record and retrieve episodes
- Buffer eviction
- Unhappy paths: empty memory, zero duration, extreme drawdown, all same regime
"""

import time

import pytest

from backend.core.karma.episode_memory import EpisodeMemory, KarmaEpisode


class TestKarmaEpisodeCreation:
    """Happy path: KarmaEpisode model creation."""

    def test_karma_episode_creation(self):
        """KarmaEpisode with all fields → valid object."""
        episode = KarmaEpisode(
            timestamp=time.time(),
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=0.05,
            drawdown_percent=0.01,
            duration_ms=500,
            karma_score=0.8,
        )
        assert episode.regime == "BULL"
        assert episode.strategy == "TrendFollowing"
        assert episode.karma_score == 0.8


class TestRegimeDecay:
    """Happy path: Regime-specific decay rates."""

    def test_regime_decay_trending_slow(self):
        """regime="BULL", decay_rate=0.95 → half-life ~14 episodes."""
        memory = EpisodeMemory()
        decay = memory.get_decay_rate("BULL")
        assert decay == pytest.approx(0.95, abs=0.01)

    def test_regime_decay_ranging_medium(self):
        """regime="SIDEWAYS", decay_rate=0.85 → half-life ~4 episodes."""
        memory = EpisodeMemory()
        decay = memory.get_decay_rate("SIDEWAYS")
        assert decay == pytest.approx(0.85, abs=0.01)

    def test_regime_decay_volatile_fast(self):
        """regime="VOLATILE", decay_rate=0.70 → half-life ~2 episodes."""
        memory = EpisodeMemory()
        decay = memory.get_decay_rate("VOLATILE")
        assert decay == pytest.approx(0.70, abs=0.01)


class TestCausalWeight:
    """Happy path: Causal weight based on regime match + recency."""

    def test_causal_weight_same_regime_high(self):
        """current regime matches episode regime → weight > 0.8."""
        memory = EpisodeMemory()
        now = time.time()
        episode = KarmaEpisode(
            timestamp=now - 10,  # 10 seconds ago
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=0.05,
            drawdown_percent=0.01,
            duration_ms=500,
            karma_score=0.8,
        )
        weight = memory.get_causal_weight(episode, current_regime="BULL", current_time=now)
        assert weight > 0.8

    def test_causal_weight_different_regime_low(self):
        """current regime != episode regime → weight < 0.3."""
        memory = EpisodeMemory()
        now = time.time()
        episode = KarmaEpisode(
            timestamp=now - 10,
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=0.05,
            drawdown_percent=0.01,
            duration_ms=500,
            karma_score=0.8,
        )
        weight = memory.get_causal_weight(episode, current_regime="VOLATILE", current_time=now)
        assert weight < 0.3

    def test_causal_weight_recent_higher_than_old(self):
        """1min ago > 1hour ago (same regime)."""
        memory = EpisodeMemory()
        now = time.time()
        recent = KarmaEpisode(
            timestamp=now - 60,  # 1 min ago
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=0.05,
            drawdown_percent=0.01,
            duration_ms=500,
            karma_score=0.8,
        )
        old = KarmaEpisode(
            timestamp=now - 3600,  # 1 hour ago
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=0.05,
            drawdown_percent=0.01,
            duration_ms=500,
            karma_score=0.8,
        )
        w_recent = memory.get_causal_weight(recent, current_regime="BULL", current_time=now)
        w_old = memory.get_causal_weight(old, current_regime="BULL", current_time=now)
        assert w_recent > w_old


class TestCausalityThreshold:
    """Happy path: Causality threshold based on recent karma."""

    def test_causality_threshold_good_karma_normal(self):
        """recent episodes positive → threshold=0.6 (normal)."""
        memory = EpisodeMemory()
        now = time.time()
        for i in range(5):
            memory.record(
                KarmaEpisode(
                    timestamp=now - (5 - i),
                    regime="BULL",
                    strategy="TrendFollowing",
                    action=1,
                    pnl_percent=0.05,
                    drawdown_percent=0.01,
                    duration_ms=500,
                    karma_score=0.8,
                )
            )
        threshold = memory.get_causality_threshold(current_regime="BULL")
        assert threshold == pytest.approx(0.6, abs=0.05)

    def test_causality_threshold_bad_karma_elevated(self):
        """recent episodes negative → threshold=0.8 (stricter)."""
        memory = EpisodeMemory()
        now = time.time()
        for i in range(5):
            memory.record(
                KarmaEpisode(
                    timestamp=now - (5 - i),
                    regime="BULL",
                    strategy="TrendFollowing",
                    action=1,
                    pnl_percent=-0.05,
                    drawdown_percent=0.08,
                    duration_ms=500,
                    karma_score=-0.8,
                )
            )
        threshold = memory.get_causality_threshold(current_regime="BULL")
        assert threshold == pytest.approx(0.8, abs=0.05)


class TestRecordRetrieve:
    """Happy path: Record and retrieve episodes."""

    def test_record_and_retrieve_episodes(self):
        """record 5 episodes → retrieve returns 5 in order."""
        memory = EpisodeMemory()
        now = time.time()
        for i in range(5):
            memory.record(
                KarmaEpisode(
                    timestamp=now + i,
                    regime="BULL",
                    strategy="TrendFollowing",
                    action=1,
                    pnl_percent=0.01 * i,
                    drawdown_percent=0.0,
                    duration_ms=100,
                    karma_score=0.5,
                )
            )
        episodes = memory.get_episodes()
        assert len(episodes) == 5

    def test_episode_max_buffer_evicts_oldest(self):
        """buffer=100, add 101 → oldest gone, newest present."""
        memory = EpisodeMemory(max_episodes=100)
        now = time.time()
        for i in range(101):
            memory.record(
                KarmaEpisode(
                    timestamp=now + i,
                    regime="BULL",
                    strategy="TrendFollowing",
                    action=1,
                    pnl_percent=0.01,
                    drawdown_percent=0.0,
                    duration_ms=100,
                    karma_score=0.5,
                )
            )
        episodes = memory.get_episodes()
        assert len(episodes) == 100
        # Oldest (timestamp=now) should be evicted, newest (timestamp=now+100) should be present
        assert episodes[-1].timestamp == pytest.approx(now + 100, abs=0.01)


# ── Unhappy Path Tests ──


class TestEpisodeMemoryUnhappy:
    """Unhappy path: edge cases and error handling."""

    def test_causal_weight_no_episodes_returns_default(self):
        """empty memory → default threshold=0.6."""
        memory = EpisodeMemory()
        threshold = memory.get_causality_threshold(current_regime="BULL")
        assert threshold == pytest.approx(0.6, abs=0.01)

    def test_episode_with_zero_duration_accepted(self):
        """duration=0 → valid (flash trade)."""
        episode = KarmaEpisode(
            timestamp=time.time(),
            regime="BULL",
            strategy="TrendFollowing",
            action=1,
            pnl_percent=0.01,
            drawdown_percent=0.0,
            duration_ms=0,
            karma_score=0.5,
        )
        assert episode.duration_ms == 0

    def test_episode_with_extreme_drawdown_capped(self):
        """drawdown_pct=5.0 → capped at 1.0."""
        episode = KarmaEpisode(
            timestamp=time.time(),
            regime="VOLATILE",
            strategy="Defensive",
            action=0,
            pnl_percent=-0.5,
            drawdown_percent=5.0,
            duration_ms=1000,
            karma_score=-1.0,
        )
        assert episode.drawdown_percent <= 1.0

    def test_causality_threshold_all_same_regime_no_crash(self):
        """100 episodes all BULL → no division by zero."""
        memory = EpisodeMemory()
        now = time.time()
        for i in range(100):
            memory.record(
                KarmaEpisode(
                    timestamp=now + i,
                    regime="BULL",
                    strategy="TrendFollowing",
                    action=1,
                    pnl_percent=0.01,
                    drawdown_percent=0.0,
                    duration_ms=100,
                    karma_score=0.5,
                )
            )
        threshold = memory.get_causality_threshold(current_regime="BULL")
        assert 0.0 <= threshold <= 1.0
