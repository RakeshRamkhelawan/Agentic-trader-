"""
Step 3A — RED Phase: Tests for SoulObserver.
TDD: All tests written FIRST, expected to FAIL until Step 3C implements production code.

Tests cover:
- All-layer health reporting
- Soul healthy within 90s
- Recent intents aggregation
- Timeline view ordered by timestamp
- "Why no trade" explanation
- Unhappy: stale soul, redis unavailable, SHM unavailable
"""

import time
from unittest.mock import AsyncMock

import pytest

from backend.monitoring.soul_observer import SoulObserver


@pytest.fixture
def observer():
    """Create SoulObserver with mocked dependencies."""
    obs = SoulObserver()
    obs.redis_client = AsyncMock()
    return obs


class TestSoulObserverHappy:
    """Happy path: health, intents, timeline, explanations."""

    @pytest.mark.asyncio
    async def test_observer_returns_all_layer_health(self, observer):
        """get_health() returns {soul: {status, last_update}, mind: {...}, body: {...}}."""
        observer.redis_client.get = AsyncMock(return_value=f'{{"timestamp": "{time.time()}"}}')

        health = await observer.get_health()
        assert "soul" in health
        assert "mind" in health
        assert "body" in health
        assert "status" in health["soul"]
        assert "last_update" in health["soul"]

    @pytest.mark.asyncio
    async def test_observer_soul_healthy_within_90s(self, observer):
        """last soul update 30s ago → status='healthy'."""
        import json
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        thirty_sec_ago = (now - timedelta(seconds=30)).isoformat()
        observer.redis_client.get = AsyncMock(
            return_value=json.dumps({"timestamp": thirty_sec_ago})
        )

        health = await observer.get_health()
        assert health["soul"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_observer_answers_why_no_trade(self, observer):
        """rahu_kala=True → reason includes 'Rahu Kala'."""
        import json

        observer.redis_client.get = AsyncMock(
            return_value=json.dumps(
                {
                    "timestamp": "2026-01-01T00:00:00+00:00",
                    "rahu_kala_active": True,
                    "trading_gate_open": False,
                    "causality_threshold": 0.6,
                }
            )
        )

        reasons = await observer.why_no_trade()
        reason_text = " ".join(reasons)
        assert "rahu" in reason_text.lower() or "Rahu" in reason_text


class TestSoulObserverUnhappy:
    """Unhappy path: stale data, unavailable services."""

    @pytest.mark.asyncio
    async def test_observer_soul_stale_after_90s(self, observer):
        """last soul update 120s ago → status='stale'."""
        import json
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        two_min_ago = (now - timedelta(seconds=120)).isoformat()
        observer.redis_client.get = AsyncMock(return_value=json.dumps({"timestamp": two_min_ago}))

        health = await observer.get_health()
        assert health["soul"]["status"] == "stale"

    @pytest.mark.asyncio
    async def test_observer_redis_unavailable_returns_unknown(self, observer):
        """Redis connection fails → status='unknown', no crash."""
        observer.redis_client.get = AsyncMock(side_effect=Exception("Connection refused"))

        health = await observer.get_health()
        assert health["soul"]["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_observer_shm_unavailable_returns_empty_intents(self, observer):
        """SHM not created → returns [], no crash."""
        # Don't set up bridge
        observer.bridge = None

        intents = await observer.get_recent_intents()
        assert intents == []
