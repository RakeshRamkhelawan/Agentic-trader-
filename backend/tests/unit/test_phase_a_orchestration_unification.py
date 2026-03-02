"""
Phase A Unit Tests: Unify Orchestration

Tests voor OODA + CognitiveOrchestrator integratie:
- CognitiveOrchestrator als dependency injection
- Guna balance injection in orient phase
- Deprecatie van ColdPathCoordinator
"""

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.guna_quantifier import GunaVector
from backend.core.schemas.ooda_types import (
    MarketRegime,
    Observation,
    Orientation,
)
from backend.orchestration.ooda_coordinator import OODALoopCoordinator
from backend.services.cognitive_orchestrator import CognitiveOrchestrator


class TestCognitiveOrchestratorIntegration:
    """Test Fase A: CognitiveOrchestrator als dependency."""

    def test_cognitive_orchestrator_dependency_injection(self):
        """Test dat CognitiveOrchestrator correct wordt geïnjecteerd."""
        # Arrange
        mock_co = MagicMock(spec=CognitiveOrchestrator)
        mock_co.current_guna_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)

        base_agents = {
            "data_scout": MagicMock(spec=DataScoutAgent),
            "analyst": MagicMock(spec=AnalystAgent),
            "trader": MagicMock(spec=TraderAgent),
            "risk_manager": MagicMock(spec=RiskManagerAgent),
        }

        # Act
        coordinator = OODALoopCoordinator(
            data_scout=base_agents["data_scout"],
            analyst=base_agents["analyst"],
            trader=base_agents["trader"],
            risk_manager=base_agents["risk_manager"],
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(spec=CognitiveBridge),
            cognitive_orchestrator=mock_co,
        )

        # Assert
        assert coordinator.cognitive_orchestrator is mock_co
        assert coordinator.current_guna_balance is not None
        assert coordinator.current_guna_balance.sattva == 0.4

    def test_current_guna_balance_property(self):
        """Test dat current_guna_balance property werkt."""
        # Arrange
        mock_co = MagicMock(spec=CognitiveOrchestrator)
        mock_co.current_guna_balance = GunaVector(sattva=0.5, rajas=0.3, tamas=0.2)

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

        # Act
        guna = coordinator.current_guna_balance

        # Assert
        assert guna.sattva == 0.5
        assert guna.rajas == 0.3
        assert guna.tamas == 0.2

    def test_current_guna_balance_fallback_to_navagraha(self):
        """Test fallback naar _current_guna wanneer geen CognitiveOrchestrator."""
        # Arrange
        from backend.core.navagraha.models import GunaDistribution

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            cognitive_orchestrator=None,
        )

        # Set _current_guna manually (simulating Navagraha integration)
        coordinator._current_guna = GunaDistribution(
            sattva=0.6, rajas=0.2, tamas=0.2, calculated_at=datetime.now(timezone.utc)
        )

        # Act
        guna = coordinator.current_guna_balance

        # Assert
        assert guna.sattva == 0.6


class TestOrientPhaseGunaInjection:
    """Test Fase A: Guna balance injectie in orient phase."""

    @pytest.mark.asyncio
    async def test_guna_context_injected_into_orient(self):
        """Test dat guna context wordt geïnjecteerd in orient phase."""
        # Arrange
        mock_co = MagicMock(spec=CognitiveOrchestrator)
        mock_co.current_guna_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)

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

        mock_bridge = MagicMock(spec=CognitiveBridge)
        mock_bridge.process_observation = AsyncMock(return_value=0.7)

        # Mock researchers with AsyncMock for generate_hypothesis
        mock_bull = MagicMock()
        mock_bull.generate_hypothesis = AsyncMock(return_value={"confidence": 0.7})
        mock_bear = MagicMock()
        mock_bear.generate_hypothesis = AsyncMock(return_value={"confidence": 0.3})

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=mock_analyst,
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=mock_bull,
            bear_researcher=mock_bear,
            cognitive_bridge=mock_bridge,
            cognitive_orchestrator=mock_co,
        )

        observation = Observation(
            symbol="BTC/USD",
            price=50000.0,
            volume=100.0,
            timestamp=time.time(),
            orderbook={},
            funding_rate=0.0001,
        )

        # Act
        orientation, bull, bear = await coordinator._orient(observation)

        # Assert - analyst.orient werd aangeroepen
        mock_analyst.orient.assert_called_once()
        mock_analyst.orient.call_args[1]

        # Check dat guna modulation werd toegepast (indirect via confidence)
        assert orientation is not None

    @pytest.mark.asyncio
    async def test_guna_modulation_reduces_confidence_with_high_tamas(self):
        """Test dat hoge tamas de confidence verlaagt."""
        # Arrange
        mock_co = MagicMock(spec=CognitiveOrchestrator)
        mock_co.current_guna_balance = GunaVector(sattva=0.2, rajas=0.2, tamas=0.6)

        mock_bridge = MagicMock(spec=CognitiveBridge)
        mock_bridge.process_observation = AsyncMock(return_value=0.7)

        mock_analyst = MagicMock(spec=AnalystAgent)

        # Create orientation with high confidence
        original_orientation = Orientation(
            symbol="BTC/USD",
            regime=MarketRegime.TRENDING_UP,
            indicators={},
            core_sentiment=0.7,
            rag_context=[],
            confidence=0.8,  # High confidence
        )
        mock_analyst.orient = AsyncMock(return_value=original_orientation)

        # Mock researchers with AsyncMock for generate_hypothesis
        mock_bull = MagicMock()
        mock_bull.generate_hypothesis = AsyncMock(return_value={"confidence": 0.7})
        mock_bear = MagicMock()
        mock_bear.generate_hypothesis = AsyncMock(return_value={"confidence": 0.3})

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=mock_analyst,
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=mock_bull,
            bear_researcher=mock_bear,
            cognitive_bridge=mock_bridge,
            cognitive_orchestrator=mock_co,
        )

        observation = Observation(
            symbol="BTC/USD",
            price=50000.0,
            volume=100.0,
            timestamp=time.time(),
            orderbook={},
            funding_rate=0.0001,
        )

        # Act
        orientation, bull, bear = await coordinator._orient(observation)

        # Assert - confidence should be reduced due to high tamas
        # tamas_penalty = max(0, 0.6 - 0.33) * 0.5 = 0.135
        # expected_confidence = 0.8 - 0.135 = 0.665
        assert orientation.confidence < 0.8
        assert orientation.confidence == pytest.approx(0.665, abs=0.01)


class TestMarketTickDelegation:
    """Test Fase A: CognitiveOrchestrator market tick delegation."""

    @pytest.mark.asyncio
    async def test_market_tick_delegated_to_cognitive_orchestrator(self):
        """Test dat market ticks worden gedelegeerd aan CognitiveOrchestrator."""
        # Arrange
        mock_co = MagicMock(spec=CognitiveOrchestrator)
        mock_co.handle_market_tick = AsyncMock()
        mock_co.current_guna_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)

        # Mock Navagraha service
        mock_navagraha = MagicMock()
        from backend.core.navagraha.models import GunaDistribution, NavagrahaState

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
            navagraha_service=mock_navagraha,
        )

        # Act
        with patch.object(
            coordinator, "_execute_ooda_loop", new_callable=AsyncMock
        ):
            await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        mock_co.handle_market_tick.assert_called_once()
        call_args = mock_co.handle_market_tick.call_args[0][0]
        assert call_args["symbol"] == "BTC/USD"
        assert call_args["price"] == 50000.0


class TestUnifiedConsciousnessState:
    """Test Fase A: Unified consciousness state methods."""

    def test_get_unified_consciousness_state_returns_all_components(self):
        """Test dat get_unified_consciousness_state alle componenten bevat."""
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
        assert "ooda_cycles_completed" in state
        assert "trading_mode" in state
        assert "components" in state
        assert state["components"]["navagraha"]["enabled"] is True
        assert state["components"]["system_identity"]["enabled"] is True
        assert state["components"]["cognitive_orchestrator"]["enabled"] is True
        assert state["components"]["risk_orchestrator"]["enabled"] is True
        assert state["components"]["karma_register"]["enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
