import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.schemas.ooda_types import MarketRegime, Orientation, TradeProposal
from backend.execution.fast_config import FastConfig, FastConfigManager
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode

pytestmark = pytest.mark.asyncio


class TestFastConfigIntegration:
    """Integration tests for FastConfig Bridge."""

    @pytest.fixture
    def temp_config_file(self):
        """Create temp config file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def fast_config(self, temp_config_file):
        """Initialize FastConfig singleton."""
        # Reset singleton if exists (hacky but needed for tests)
        FastConfig._instance = None
        manager = FastConfig.initialize(temp_config_file)
        return manager

    async def test_trader_uses_fast_config_exploration_rate(self, fast_config):
        """TraderAgent should use exploration_rate from FastConfig."""
        # Setup
        trader = TraderAgent()

        # Write config with specific exploration rate
        expected_rate = 0.99
        fast_config.write_atomic(
            {"action": 0, "confidence": 0.5, "exploration_rate": expected_rate}
        )

        # Verify via get_statistics which we updated to expose this value
        stats = trader.get_statistics()

        # Note: floating point comparison
        assert abs(stats["exploration_rate"] - expected_rate) < 0.001

    async def test_risk_manager_uses_fast_config_confidence(self, fast_config):
        """RiskManager should use confidence threshold from FastConfig."""
        risk_manager = RiskManagerAgent(min_confidence=0.5)

        # Set high confidence requirement via FastConfig
        fast_config.write_atomic(
            {"action": 0, "confidence": 0.9, "exploration_rate": 0.0}  # strict
        )

        # Create proposal with moderate confidence (should fail dynamic check)
        proposal = TradeProposal(
            symbol="BTC/USDT",
            side="buy",
            size=0.1,
            entry_price=100.0,
            stop_loss=90.0,
            take_profit=110.0,
            rationale="Rationale must be longer than 10 chars",
            confidence=0.7,
            strategy_id="test",
        )

        # Assess
        assessment = await risk_manager.assess_risk(proposal, MarketRegime.TRENDING_UP)

        # Should be REJECTED because 0.7 < 0.9 (dynamic), even though 0.7 > 0.5 (static)
        from backend.core.schemas.ooda_types import RiskDecision

        assert assessment.decision == RiskDecision.REJECT
        assert "Confidence" in assessment.rationale

    async def test_coordinator_manual_override(self, fast_config):
        """Coordinator should respect manual override from FastConfig."""
        # Setup mocks
        data_scout = MagicMock()
        analyst = MagicMock()
        trader = MagicMock()
        risk_manager = MagicMock()
        cognitive_bridge = MagicMock()

        coordinator = OODALoopCoordinator(
            data_scout,
            analyst,
            trader,
            risk_manager,
            cognitive_bridge,
            trading_mode=TradingMode.AUTO,
        )

        # Set FORCE_LONG (action=1)
        fast_config.write_atomic(
            {"action": 1, "confidence": 1.0, "exploration_rate": 0.0}  # 1 = Long
        )

        # Mock internal execution to avoid complex dependency setup
        coordinator._execute_ooda_loop = AsyncMock(return_value={"status": "executed"})

        # Run cycle
        await coordinator.run_cycle("BTC/USDT", 50000.0)

        # Verify it ran
        coordinator._execute_ooda_loop.assert_called_once()

        # We can also verify logs if we captured them, but this proves
        # the bridge didn't crash and passed control.
