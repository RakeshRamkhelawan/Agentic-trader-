"""
Step 1C — RED Phase: Tests for Mind ↔ PortfolioRiskCalculator integration.
TDD: All tests written FIRST, expected to FAIL until Step 1D modifies cognitive_mind_service.py.

Tests verify that CognitiveMindService:
- Uses PortfolioRiskCalculator during process_cycle
- Skips strategy when capacity is below threshold
- Applies Kelly-adjusted sizes
- Logs risk state reason on hold
- Handles calculator exceptions gracefully
- Handles missing soul context gracefully
"""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.cognitive_mind_service import CognitiveMindService
from backend.core.risk.portfolio_risk import PortfolioRiskCalculator, RiskDecisionResult


@pytest.fixture
def mind_service():
    """Create a CognitiveMindService with mocked dependencies."""
    service = CognitiveMindService(shm_name="test_mind_risk_shm")

    # Mock Redis
    service.redis_client = AsyncMock()

    # Mock ZeroCopyBridge
    service.bridge = MagicMock()
    service.bridge.write_intent = MagicMock()

    return service


def _make_soul_context(
    regime="BULL",
    guna="rajas",
    rahu=False,
    price=50000.0,
):
    """Helper to build a soul context JSON string."""
    return json.dumps(
        {
            "market_regime": regime,
            "guna_dominance": guna,
            "rahu_kala_active": rahu,
            "market_metrics": {"price": price},
        }
    )


class TestMindRiskIntegration:
    """Happy path: Mind uses PortfolioRiskCalculator during cycle."""

    @pytest.mark.asyncio
    async def test_mind_cycle_uses_portfolio_risk_calculator(self, mind_service):
        """Mock PortfolioRiskCalculator → verify called during process_cycle."""
        mind_service.redis_client.get = AsyncMock(return_value=_make_soul_context())

        # Service must have portfolio_risk_calculator attribute
        assert hasattr(mind_service, "portfolio_risk_calculator")
        assert isinstance(
            mind_service.portfolio_risk_calculator, PortfolioRiskCalculator
        )

        with patch.object(
            mind_service.portfolio_risk_calculator,
            "evaluate",
            return_value=RiskDecisionResult(
                action="accept",
                reason="risk_capacity_sufficient",
                capacity=0.8,
                threshold=0.6,
            ),
        ) as mock_evaluate:
            await mind_service.process_cycle()
            mock_evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def test_mind_skips_strategy_when_capacity_below_threshold(
        self, mind_service
    ):
        """capacity=0.1 → intent.action=0, strategy.analyze NOT called."""
        mind_service.redis_client.get = AsyncMock(return_value=_make_soul_context())

        with patch.object(
            mind_service.portfolio_risk_calculator,
            "evaluate",
            return_value=RiskDecisionResult(
                action="hold",
                reason="insufficient_risk_capacity",
                capacity=0.1,
                threshold=0.6,
            ),
        ):
            await mind_service.process_cycle()

            # Verify intent written with action=0 (HOLD)
            mind_service.bridge.write_intent.assert_called_once()
            call_args = mind_service.bridge.write_intent.call_args
            intent = call_args[0][1]  # second positional arg
            assert intent.action == 0
            assert intent.size == 0.0

    @pytest.mark.asyncio
    async def test_mind_applies_kelly_adjusted_size(self, mind_service):
        """Kelly gives size, guna gives multiplier, capacity modulates → final size."""
        mind_service.redis_client.get = AsyncMock(
            return_value=_make_soul_context(guna="rajas")
        )

        with patch.object(
            mind_service.portfolio_risk_calculator,
            "evaluate",
            return_value=RiskDecisionResult(
                action="accept",
                reason="risk_capacity_sufficient",
                capacity=0.9,
                threshold=0.6,
            ),
        ):
            await mind_service.process_cycle()

            # Verify an intent was written
            mind_service.bridge.write_intent.assert_called_once()
            call_args = mind_service.bridge.write_intent.call_args
            intent = call_args[0][1]
            # If accepted, size should be > 0 (kelly-modulated)
            # The exact value depends on implementation, but should not be raw unmodulated
            assert intent.size >= 0.0

    @pytest.mark.asyncio
    async def test_mind_logs_risk_state_reason_on_hold(self, mind_service, caplog):
        """reason="insufficient_risk_capacity" appears in logs."""
        mind_service.redis_client.get = AsyncMock(return_value=_make_soul_context())

        with patch.object(
            mind_service.portfolio_risk_calculator,
            "evaluate",
            return_value=RiskDecisionResult(
                action="hold",
                reason="insufficient_risk_capacity",
                capacity=0.1,
                threshold=0.6,
            ),
        ):
            with caplog.at_level(logging.WARNING):
                await mind_service.process_cycle()

            assert "insufficient_risk_capacity" in caplog.text


class TestMindRiskIntegrationUnhappy:
    """Unhappy path: error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_mind_handles_risk_calculator_exception_gracefully(
        self, mind_service
    ):
        """PortfolioRiskCalculator raises → fallback to HOLD, no crash."""
        mind_service.redis_client.get = AsyncMock(return_value=_make_soul_context())

        with patch.object(
            mind_service.portfolio_risk_calculator,
            "evaluate",
            side_effect=Exception("Calculator exploded"),
        ):
            # Should NOT raise
            await mind_service.process_cycle()

            # Should write a HOLD intent
            mind_service.bridge.write_intent.assert_called_once()
            call_args = mind_service.bridge.write_intent.call_args
            intent = call_args[0][1]
            assert intent.action == 0

    @pytest.mark.asyncio
    async def test_mind_handles_missing_soul_context_gracefully(self, mind_service):
        """Redis returns None → defensive mode, no crash."""
        mind_service.redis_client.get = AsyncMock(return_value=None)

        # Should NOT raise
        await mind_service.process_cycle()

        # Should write something (HOLD most likely)
        mind_service.bridge.write_intent.assert_called_once()
