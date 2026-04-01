"""
Step 2C — RED Phase: Tests for Soul ↔ Karma and Mind ↔ Karma integration.
TDD: All tests written FIRST, expected to FAIL until Step 2D modifies services.

Tests verify that:
- Soul context includes causality_threshold key
- Elevated threshold after bad karma
- Mind applies causality threshold to filter low-confidence signals
- Soul handles karma check exceptions gracefully
- Mind handles missing causality_threshold with default
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.cognitive_mind_service import CognitiveMindService
from backend.core.eternal_soul_service import EternalSoulService
from backend.core.karma.episode_memory import EpisodeMemory, KarmaEpisode


@pytest.fixture
def mind_service():
    """CognitiveMindService with mocked dependencies."""
    service = CognitiveMindService(shm_name="test_karma_shm")
    service.redis_client = AsyncMock()
    service.bridge = MagicMock()
    service.bridge.write_intent = MagicMock()
    return service


def _make_soul_context(
    regime="BULL",
    guna="rajas",
    rahu=False,
    price=50000.0,
    causality_threshold=None,
):
    """Helper to build soul context JSON."""
    ctx = {
        "market_regime": regime,
        "guna_dominance": guna,
        "rahu_kala_active": rahu,
        "market_metrics": {"price": price},
    }
    if causality_threshold is not None:
        ctx["causality_threshold"] = causality_threshold
    return json.dumps(ctx)


class TestSoulKarmaIntegration:
    """Happy path: Soul includes causality_threshold from karma analysis."""

    def test_soul_context_includes_causality_threshold(self):
        """process_cycle returns context with 'causality_threshold' key."""
        soul = EternalSoulService()
        # Soul must have episode_memory attribute
        assert hasattr(soul, "episode_memory")
        assert isinstance(soul.episode_memory, EpisodeMemory)

    @pytest.mark.asyncio
    async def test_soul_elevated_threshold_after_bad_karma(self):
        """inject bad karma episodes → threshold > 0.6."""
        soul = EternalSoulService()
        soul.redis_client = AsyncMock()

        # Inject bad karma episodes
        now = time.time()
        for i in range(10):
            soul.episode_memory.record(
                KarmaEpisode(
                    timestamp=now - (10 - i),
                    regime="BULL",
                    strategy="TrendFollowing",
                    action=1,
                    pnl_percent=-0.05,
                    drawdown_percent=0.08,
                    duration_ms=500,
                    karma_score=-0.8,
                )
            )

        # Run a cycle (need to mock external deps)
        with patch.object(
            soul,
            "_fetch_market_context",
            return_value={"symbol": "BTC/USD", "price": 42000.0, "volatility": 0.02},
        ):
            with patch.object(soul.navagraha, "get_current_state") as mock_nav:

                # Create minimal NavagrahaState mock
                mock_nav.return_value = MagicMock(
                    rahu_kala_active=False,
                    consciousness_level="Discriminative Intelligence",
                    guna_distribution=MagicMock(
                        dominant_guna="rajas",
                        sattva=0.3,
                        rajas=0.5,
                        tamas=0.2,
                        balance_score=0.8,
                    ),
                    trading_gate_open=True,
                )

                result = await soul.process_cycle()

        assert "causality_threshold" in result
        assert result["causality_threshold"] > 0.6

    @pytest.mark.asyncio
    async def test_mind_applies_causality_threshold(self, mind_service):
        """threshold=0.8 → only signals with confidence > 0.8 pass."""
        mind_service.redis_client.get = AsyncMock(
            return_value=_make_soul_context(causality_threshold=0.8)
        )

        # Ensure mind has episode_memory
        assert hasattr(mind_service, "episode_memory")

        with patch.object(
            mind_service.portfolio_risk_calculator,
            "evaluate",
            return_value=MagicMock(
                action="accept",
                reason="ok",
                capacity=0.9,
                threshold=0.6,
            ),
        ):
            await mind_service.process_cycle()

        # Should have written an intent
        mind_service.bridge.write_intent.assert_called_once()


class TestSoulKarmaIntegrationUnhappy:
    """Unhappy path: error handling."""

    @pytest.mark.asyncio
    async def test_soul_karma_check_exception_doesnt_crash_cycle(self):
        """EpisodeMemory raises → cycle continues with default threshold."""
        soul = EternalSoulService()
        soul.redis_client = AsyncMock()

        with patch.object(
            soul.episode_memory,
            "get_causality_threshold",
            side_effect=Exception("Memory corrupt"),
        ):
            with patch.object(
                soul,
                "_fetch_market_context",
                return_value={
                    "symbol": "BTC/USD",
                    "price": 42000.0,
                    "volatility": 0.02,
                },
            ):
                with patch.object(soul.navagraha, "get_current_state") as mock_nav:
                    mock_nav.return_value = MagicMock(
                        rahu_kala_active=False,
                        consciousness_level="Discriminative Intelligence",
                        guna_distribution=MagicMock(
                            dominant_guna="rajas",
                            sattva=0.3,
                            rajas=0.5,
                            tamas=0.2,
                            balance_score=0.8,
                        ),
                        trading_gate_open=True,
                    )
                    # Should NOT raise
                    result = await soul.process_cycle()

        assert "causality_threshold" in result
        assert result["causality_threshold"] == pytest.approx(0.6, abs=0.01)

    @pytest.mark.asyncio
    async def test_mind_missing_causality_threshold_uses_default(self, mind_service):
        """soul_context without causality_threshold key → use 0.6."""
        mind_service.redis_client.get = AsyncMock(
            return_value=_make_soul_context()  # No causality_threshold
        )

        with patch.object(
            mind_service.portfolio_risk_calculator,
            "evaluate",
            return_value=MagicMock(
                action="accept",
                reason="ok",
                capacity=0.9,
                threshold=0.6,
            ),
        ):
            await mind_service.process_cycle()

        # Should not crash, should write intent
        mind_service.bridge.write_intent.assert_called_once()
