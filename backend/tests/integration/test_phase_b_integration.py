"""
Phase B Integration Tests: Connect Consciousness

Integratietests voor Fase B:
- Navagraha gate + OODA workflow
- Tattva risk gate + trade decisions
- Guna modulation door het systeem
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.navagraha.models import GunaDistribution, NavagrahaState, PlanetName
from backend.core.navagraha.service import NavagrahaService
from backend.core.schemas.ooda_types import MarketRegime, Observation, Orientation
from backend.core.system_identity import SystemIdentity
from backend.orchestration.ooda_coordinator import OODALoopCoordinator


class TestPhaseBNavagrahaIntegration:
    """Integratietests voor Navagraha + OODA."""

    @pytest.fixture
    def mock_navagraha_open_gate(self):
        """Navagraha met open gate."""
        service = MagicMock(spec=NavagrahaService)

        async def mock_get_state(lat, lon, dt=None):
            return NavagrahaState(
                planets={
                    PlanetName.SUN: MagicMock(longitude=45, is_retrograde=False),
                    PlanetName.MOON: MagicMock(longitude=120, is_retrograde=False),
                },
                guna_distribution=GunaDistribution(
                    sattva=0.5,
                    rajas=0.3,
                    tamas=0.2,
                    calculated_at=datetime.now(timezone.utc),
                ),
                aspects=[],
                rahu_kala_active=False,
                consciousness_level="Discriminative Intelligence",
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        service.get_current_state = mock_get_state
        return service

    @pytest.fixture
    def mock_navagraha_closed_gate(self):
        """Navagraha met gesloten gate (Rahu Kala)."""
        service = MagicMock(spec=NavagrahaService)

        async def mock_get_state(lat, lon, dt=None):
            return NavagrahaState(
                planets={},
                guna_distribution=GunaDistribution(
                    sattva=0.2,
                    rajas=0.2,
                    tamas=0.6,
                    calculated_at=datetime.now(timezone.utc),
                ),
                aspects=[],
                rahu_kala_active=True,
                consciousness_level="Material Density",
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        service.get_current_state = mock_get_state
        return service

    @pytest.mark.asyncio
    async def test_trade_executes_when_gate_open(self, mock_navagraha_open_gate):
        """Test dat trade uitvoert wanneer gate open is."""
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
            navagraha_service=mock_navagraha_open_gate,
        )

        # Act
        with patch.object(
            coordinator, "_execute_ooda_loop", new_callable=AsyncMock
        ) as mock_execute:
            result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        assert result.get("decision") != "BLOCKED_BY_CONSCIOUSNESS_GATE"
        mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_trade_blocked_when_rahu_kala_active(self, mock_navagraha_closed_gate):
        """Test dat trade wordt geblokkeerd tijdens Rahu Kala."""
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
            navagraha_service=mock_navagraha_closed_gate,
        )

        # Act
        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        assert result["decision"] == "BLOCKED_BY_CONSCIOUSNESS_GATE"
        assert result["gate_open"] is False
        assert result["rahu_kala_active"] is True

    @pytest.mark.asyncio
    async def test_guna_distribution_preserved_in_result(self, mock_navagraha_open_gate):
        """Test dat guna distribution wordt bewaard in resultaat."""
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
            navagraha_service=mock_navagraha_open_gate,
        )

        # Act
        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert - blocked result should include guna distribution
        if result.get("decision") == "BLOCKED_BY_CONSCIOUSNESS_GATE":
            assert "guna_distribution" in result
            assert result["guna_distribution"]["sattva"] == 0.5

    @pytest.mark.asyncio
    async def test_consciousness_level_in_result(self, mock_navagraha_open_gate):
        """Test dat consciousness level in resultaat zit."""
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
            navagraha_service=mock_navagraha_open_gate,
        )

        # Act
        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        if result.get("decision") == "BLOCKED_BY_CONSCIOUSNESS_GATE":
            assert result["consciousness_level"] == "Discriminative Intelligence"


class TestPhaseBTattvaIntegration:
    """Integratietests voor Tattva + OODA."""

    @pytest.fixture
    def system_identity_high_coherence(self):
        """SystemIdentity met hoge coherence."""
        identity = MagicMock(spec=SystemIdentity)
        identity.system_state = {
            "coherence": 0.9,
            "confidence": 0.8,
            "tattva_coherence": {str(i): 0.9 for i in range(1, 37)},
        }
        identity.update_outcome = MagicMock()
        return identity

    @pytest.fixture
    def system_identity_low_kanchuka(self):
        """SystemIdentity met lage Kanchuka coherence."""
        identity = MagicMock(spec=SystemIdentity)
        identity.system_state = {
            "coherence": 0.6,
            "confidence": 0.6,
            "tattva_coherence": {
                **{str(i): 0.9 for i in range(1, 6)},  # High Shuddha
                **{str(i): 0.4 for i in range(6, 13)},  # Low Kanchuka
                **{str(i): 0.9 for i in range(13, 37)},  # High rest
            },
        }
        identity.update_outcome = MagicMock()
        return identity

    def test_kanchuka_gate_open_with_high_coherence(self, system_identity_high_coherence):
        """Test dat Kanchuka gate open is bij hoge coherence."""
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
            system_identity=system_identity_high_coherence,
        )

        # Act
        risk_state = coordinator._get_tattva_risk_gate_state()

        # Assert
        assert risk_state["risk_gate_blocked"] is False
        assert risk_state["avg_kanchuka_coherence"] > 0.7

    def test_kanchuka_gate_blocked_with_low_coherence(self, system_identity_low_kanchuka):
        """Test dat Kanchuka gate geblokkeerd is bij lage coherence."""
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
            system_identity=system_identity_low_kanchuka,
        )

        # Act
        risk_state = coordinator._get_tattva_risk_gate_state()

        # Assert
        assert risk_state["risk_gate_blocked"] is True
        assert risk_state["avg_kanchuka_coherence"] < 0.7

    def test_tattva_state_stored_in_coordinator(self, system_identity_low_kanchuka):
        """Test dat Tattva state wordt opgeslagen in coordinator."""
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
            system_identity=system_identity_low_kanchuka,
        )

        # Act
        risk_state = coordinator._get_tattva_risk_gate_state()
        coordinator._current_tattva_state = risk_state

        # Assert
        assert coordinator._current_tattva_state is not None
        assert "risk_gate_blocked" in coordinator._current_tattva_state


class TestPhaseBGunaModulation:
    """Integratietests voor Guna modulation."""

    @pytest.mark.asyncio
    async def test_high_tamas_reduces_confidence(self):
        """Test dat hoge tamas de confidence verlaagt."""
        from backend.agents.analyst_agent import AnalystAgent
        from backend.core.guna_quantifier import GunaVector

        # Arrange
        mock_co = MagicMock()
        mock_co.current_guna_balance = GunaVector(sattva=0.2, rajas=0.2, tamas=0.6)

        mock_bridge = MagicMock()
        mock_bridge.process_observation = AsyncMock(return_value=0.7)

        mock_analyst = MagicMock(spec=AnalystAgent)
        mock_analyst.orient = AsyncMock(
            return_value=Orientation(
                symbol="BTC/USD",
                regime=MarketRegime.TRENDING_UP,
                indicators={},
                core_sentiment=0.7,
                rag_context=[],
                confidence=0.8,  # Original high confidence
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
            cognitive_bridge=mock_bridge,
            cognitive_orchestrator=mock_co,
        )

        observation = Observation(
            symbol="BTC/USD",
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            orderbook={},
            funding_rate=0.0001,
        )

        # Act
        orientation, _, _ = await coordinator._orient(observation)

        # Assert - confidence should be reduced
        assert orientation.confidence < 0.8
        # tamas_penalty = max(0, 0.6 - 0.33) * 0.5 = 0.135
        assert orientation.confidence == pytest.approx(0.665, abs=0.01)


class TestPhaseBEndToEnd:
    """End-to-end tests voor Fase B."""

    @pytest.mark.asyncio
    async def test_complete_consciousness_flow(self):
        """Test complete consciousness flow: Navagraha → Tattva → Guna."""
        # Arrange
        from backend.core.navagraha.models import GunaDistribution, NavagrahaState

        mock_navagraha = MagicMock()

        async def mock_get_state(lat, lon, dt=None):
            return NavagrahaState(
                planets={},
                guna_distribution=GunaDistribution(
                    sattva=0.6,
                    rajas=0.3,
                    tamas=0.1,  # High sattva
                    calculated_at=datetime.now(timezone.utc),
                ),
                aspects=[],
                rahu_kala_active=False,
                consciousness_level="Pure Awareness",
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        mock_navagraha.get_current_state = mock_get_state

        mock_identity = MagicMock(spec=SystemIdentity)
        mock_identity.system_state = {
            "tattva_coherence": {str(i): 0.9 for i in range(1, 37)},
        }

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            navagraha_service=mock_navagraha,
            system_identity=mock_identity,
        )

        # Act
        with patch.object(coordinator, "_execute_ooda_loop", new_callable=AsyncMock):
            await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        assert coordinator._current_guna is not None
        assert coordinator._current_guna.sattva == 0.6

        risk_state = coordinator._get_tattva_risk_gate_state()
        assert risk_state["risk_gate_blocked"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
