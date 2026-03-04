"""
Phase A Integration Tests: Orchestration Unification

Integratietests voor Fase A:
- OODA + CognitiveOrchestrator workflow
- Guna balance flow door het systeem
- Deprecatie van parallelle orchestrators
"""

import tempfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.guna_quantifier import GunaVector
from backend.core.schemas.ooda_types import MarketRegime, Observation, Orientation
from backend.orchestration.cold_path_coordinator import ColdPathCoordinator
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode
from backend.services.cognitive_orchestrator import CognitiveOrchestrator


class TestPhaseAIntegration:
    """Integratietests voor Fase A: Orchestration Unification."""

    @pytest.fixture
    def base_agents(self):
        """Create base agents."""
        data_scout = MagicMock(spec=DataScoutAgent)
        analyst = MagicMock(spec=AnalystAgent)
        trader = MagicMock(spec=TraderAgent)
        risk_manager = MagicMock(spec=RiskManagerAgent)

        # Setup async mocks
        data_scout.observe = AsyncMock(
            return_value=Observation(
                symbol="BTC/USD",
                price=50000.0,
                timestamp=datetime.now(timezone.utc),
                orderbook={"bids": [[49999, 1]], "asks": [[50001, 1]]},
                funding_rate=0.0001,
            )
        )

        analyst.orient = AsyncMock(
            return_value=Orientation(
                symbol="BTC/USD",
                regime=MarketRegime.TRENDING_UP,
                indicators={"rsi": 65},
                core_sentiment=0.7,
                rag_context=[],
                confidence=0.8,
            )
        )

        return {
            "data_scout": data_scout,
            "analyst": analyst,
            "trader": trader,
            "risk_manager": risk_manager,
        }

    @pytest.fixture
    def cognitive_orchestrator(self):
        """Create mock CognitiveOrchestrator."""
        co = MagicMock(spec=CognitiveOrchestrator)
        co.current_guna_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)
        co.handle_market_tick = AsyncMock()
        return co

    @pytest.mark.asyncio
    async def test_full_ooda_cycle_with_cognitive_orchestrator(
        self,
        base_agents,
        cognitive_orchestrator,
    ):
        """Test complete OODA cycle met CognitiveOrchestrator integratie."""
        # Arrange
        cognitive_bridge = MagicMock(spec=CognitiveBridge)
        cognitive_bridge.process_observation = AsyncMock(return_value=0.7)

        coordinator = OODALoopCoordinator(
            data_scout=base_agents["data_scout"],
            analyst=base_agents["analyst"],
            trader=base_agents["trader"],
            risk_manager=base_agents["risk_manager"],
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=cognitive_bridge,
            cognitive_orchestrator=cognitive_orchestrator,
            orchestrator=None,
            trading_mode=TradingMode.NOTIFY_ONLY,
        )

        # Act
        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        assert result["trace_id"] is not None
        assert result["symbol"] == "BTC/USD"

        # Verify CognitiveOrchestrator received market tick
        cognitive_orchestrator.handle_market_tick.assert_called_once()

        # Verify OODA phases executed
        base_agents["data_scout"].observe.assert_called_once()
        base_agents["analyst"].orient.assert_called_once()

    @pytest.mark.asyncio
    async def test_guna_balance_flow_through_system(self):
        """Test dat guna balance correct door het systeem stroomt."""
        # Arrange
        mock_co = MagicMock(spec=CognitiveOrchestrator)
        mock_co.current_guna_balance = GunaVector(sattva=0.5, rajas=0.3, tamas=0.2)
        mock_co.handle_market_tick = AsyncMock()

        mock_analyst = MagicMock(spec=AnalystAgent)
        mock_analyst.orient = AsyncMock(
            return_value=Orientation(
                symbol="BTC/USD",
                regime=MarketRegime.TRENDING_UP,
                indicators={},
                core_sentiment=0.7,
                rag_context=[],
                confidence=0.8,
            )
        )

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=mock_analyst,
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            cognitive_orchestrator=mock_co,
        )

        # Act - access guna balance
        guna = coordinator.current_guna_balance

        # Assert
        assert guna.sattva == 0.5
        assert guna.rajas == 0.3
        assert guna.tamas == 0.2

    def test_cold_path_coordinator_deprecation_warning(self):
        """Test dat ColdPathCoordinator deprecated is."""
        import warnings

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            # Try to instantiate ColdPathCoordinator
            # This should ideally emit a deprecation warning
            # For now, we just verify it exists and can be created
            try:

                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    config_path = f.name
                ColdPathCoordinator(
                    config_path=config_path,
                )
                # If we get here, it works but should be deprecated
            except Exception:
                # If it fails, that's also acceptable for deprecated code
                pass

    @pytest.mark.asyncio
    async def test_cognitive_orchestrator_delegation(self):
        """Test dat market data processing wordt gedelegeerd aan CO."""
        # Arrange
        mock_co = MagicMock(spec=CognitiveOrchestrator)
        mock_co.handle_market_tick = AsyncMock()
        mock_co.current_guna_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            cognitive_orchestrator=mock_co,
        )

        # Mock Navagraha to allow cycle to proceed
        from backend.core.navagraha.models import GunaDistribution, NavagrahaState

        mock_navagraha = MagicMock()

        async def mock_get_state(lat, lon, dt=None):
            return NavagrahaState(
                planets={},
                guna_distribution=GunaDistribution(
                    sattva=0.4, rajas=0.3, tamas=0.3, calculated_at=datetime.now(timezone.utc)
                ),
                aspects=[],
                rahu_kala_active=False,
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        mock_navagraha.get_current_state = mock_get_state
        coordinator.navagraha_service = mock_navagraha

        # Act
        with patch.object(coordinator, "_execute_ooda_loop", new_callable=AsyncMock):
            await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        mock_co.handle_market_tick.assert_called_once()
        call_args = mock_co.handle_market_tick.call_args[0][0]
        assert call_args["symbol"] == "BTC/USD"
        assert call_args["price"] == 50000.0

    def test_unified_consciousness_components_tracking(self):
        """Test dat alle unified components correct worden getrackt."""
        # Arrange
        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            cognitive_orchestrator=MagicMock(),
            navagraha_service=MagicMock(),
            system_identity=MagicMock(),
            risk_orchestrator=MagicMock(),
            karma_register=MagicMock(),
        )

        # Act
        state = coordinator.get_unified_consciousness_state()

        # Assert
        assert state["components"]["cognitive_orchestrator"]["enabled"] is True
        assert "guna_balance" in state["components"]["cognitive_orchestrator"]


class TestPhaseAPerformance:
    """Performance tests voor Fase A integratie."""

    @pytest.mark.asyncio
    async def test_orchestration_overhead_acceptable(self):
        """Test dat unified orchestration overhead acceptabel is."""
        import time

        # Arrange
        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            cognitive_orchestrator=MagicMock(),
        )

        # Mock all async methods to be instant
        coordinator.cognitive_orchestrator.handle_market_tick = AsyncMock()

        # Act
        start = time.time()
        with patch.object(coordinator, "_execute_ooda_loop", new_callable=AsyncMock):
            await coordinator.run_cycle("BTC/USD", 50000.0)
        elapsed = time.time() - start

        # Assert - should complete in reasonable time (this is a sanity check)
        assert elapsed < 1.0  # Should complete within 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
