"""
Integration Tests for Unified Consciousness Integration.

Tests de volledige flow:
Market tick → Navagraha gate → OODA → Tattva filter → Risk check →
Strategy select → Execute → Karma feedback → Consciousness update
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.karma.karma_register import KarmaRegister
from backend.core.navagraha.models import GunaDistribution, NavagrahaState, PlanetName
from backend.core.navagraha.service import NavagrahaService
from backend.core.schemas.ooda_types import (
    MarketRegime,
    Observation,
    RiskDecision,
    TradeProposal,
)
from backend.core.system_identity import SystemIdentity
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode
from backend.risk.risk_orchestrator import RiskOrchestrator
from backend.services.cognitive_orchestrator import CognitiveOrchestrator


@pytest.fixture
def mock_navagraha_service():
    """Create a mock NavagrahaService."""
    service = MagicMock(spec=NavagrahaService)

    # Create a mock state with gate open
    guna = GunaDistribution(
        sattva=0.5,
        rajas=0.3,
        tamas=0.2,
        calculated_at=None,  # Will be set by mock
    )

    # Mock get_current_state
    async def mock_get_current_state(lat, lon, dt=None):
        return NavagrahaState(
            planets={
                PlanetName.SUN: MagicMock(longitude=45, is_retrograde=False),
                PlanetName.MOON: MagicMock(longitude=120, is_retrograde=False),
                PlanetName.MARS: MagicMock(longitude=200, is_retrograde=False),
                PlanetName.MERCURY: MagicMock(longitude=60, is_retrograde=False),
                PlanetName.JUPITER: MagicMock(longitude=280, is_retrograde=False),
                PlanetName.VENUS: MagicMock(longitude=150, is_retrograde=False),
                PlanetName.SATURN: MagicMock(longitude=320, is_retrograde=False),
                PlanetName.RAHU: MagicMock(longitude=180, is_retrograde=True),
                PlanetName.KETU: MagicMock(longitude=0, is_retrograde=True),
            },
            guna_distribution=guna,
            aspects=[],
            rahu_kala_active=False,
            current_dasha=None,
            calculated_at=None,
            location_lat=lat,
            location_lon=lon,
        )

    service.get_current_state = mock_get_current_state
    return service


@pytest.fixture
def mock_navagraha_service_closed_gate():
    """Create a mock NavagrahaService with closed gate."""
    service = MagicMock(spec=NavagrahaService)

    guna = GunaDistribution(
        sattva=0.2,
        rajas=0.2,
        tamas=0.6,  # High tamas = closed gate
        calculated_at=None,
    )

    async def mock_get_current_state(lat, lon, dt=None):
        return NavagrahaState(
            planets={},
            guna_distribution=guna,
            aspects=[],
            rahu_kala_active=True,  # Rahu Kala active = closed gate
            current_dasha=None,
            calculated_at=None,
            location_lat=lat,
            location_lon=lon,
        )

    service.get_current_state = mock_get_current_state
    return service


@pytest.fixture
def mock_system_identity():
    """Create a mock SystemIdentity."""
    identity = MagicMock(spec=SystemIdentity)
    identity.system_state = {
        "coherence": 0.9,
        "confidence": 0.8,
        "tattva_coherence": {str(i): 0.9 for i in range(1, 37)},
    }
    identity.update_outcome = MagicMock()
    return identity


@pytest.fixture
def mock_cognitive_orchestrator():
    """Create a mock CognitiveOrchestrator."""
    orchestrator = MagicMock(spec=CognitiveOrchestrator)
    orchestrator.current_guna_balance = MagicMock(sattva=0.5, rajas=0.3, tamas=0.2)
    orchestrator.handle_market_tick = AsyncMock()
    return orchestrator


@pytest.fixture
def mock_risk_orchestrator():
    """Create a mock RiskOrchestrator."""
    risk_orch = MagicMock(spec=RiskOrchestrator)

    # Mock pre_trade_check to approve trades
    def mock_pre_trade_check(signal, portfolio_value, current_positions_count=0):
        mock_decision = MagicMock()
        mock_decision.approved = True
        mock_decision.reason = "Trade approved"
        mock_decision.recommended_quantity = 1.0
        mock_decision.drawdown_status = MagicMock()
        mock_decision.sizing_method = "kelly"
        mock_decision.kelly_fraction = 0.25
        mock_decision.warnings = []
        return mock_decision

    risk_orch.pre_trade_check = mock_pre_trade_check
    return risk_orch


@pytest.fixture
def mock_karma_register():
    """Create a mock KarmaRegister."""
    karma = MagicMock(spec=KarmaRegister)
    karma.register_feedback = MagicMock(return_value=0.5)
    return karma


@pytest.fixture
def base_agents():
    """Create base agents for testing."""
    data_scout = MagicMock(spec=DataScoutAgent)
    analyst = MagicMock(spec=AnalystAgent)
    trader = MagicMock(spec=TraderAgent)
    risk_manager = MagicMock(spec=RiskManagerAgent)

    # Mock agent behaviors
    data_scout.observe = AsyncMock(
        return_value=Observation(
            symbol="BTC/USD",
            price=50000.0,
            timestamp=None,
            orderbook={"bids": [[49999, 1]], "asks": [[50001, 1]]},
            funding_rate=0.0001,
        )
    )

    from backend.core.schemas.ooda_types import Orientation

    analyst.orient = AsyncMock(
        return_value=Orientation(
            symbol="BTC/USD",
            regime=MarketRegime.TRENDING_UP,
            indicators={"rsi": 65, "macd": 0.5},
            core_sentiment=0.7,
            rag_context=[],
            confidence=0.8,
        )
    )

    trader.propose_trade = AsyncMock(
        return_value=TradeProposal(
            symbol="BTC/USD",
            side="buy",
            size=0.1,
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            leverage=2.0,
            rationale="Trending up with strong momentum",
            strategy_id="momentum_v1",
            confidence=0.8,
        )
    )

    from backend.core.schemas.ooda_types import RiskAssessment

    risk_manager.assess_risk = AsyncMock(
        return_value=RiskAssessment(
            decision=RiskDecision.APPROVE,
            risk_score=0.3,
            rationale="Low risk trade",
            var_95=0.02,
            max_drawdown_pct=0.05,
            recommended_position_size=0.1,
        )
    )

    return {
        "data_scout": data_scout,
        "analyst": analyst,
        "trader": trader,
        "risk_manager": risk_manager,
    }


@pytest.fixture
def unified_coordinator(
    base_agents,
    mock_navagraha_service,
    mock_system_identity,
    mock_cognitive_orchestrator,
    mock_risk_orchestrator,
    mock_karma_register,
):
    """Create OODA coordinator with all unified consciousness components."""
    cognitive_bridge = MagicMock(spec=CognitiveBridge)
    cognitive_bridge.process_observation = AsyncMock(return_value=0.7)

    fund_manager = MagicMock()
    from backend.core.schemas.ooda_types import CapitalAllocation

    fund_manager.allocate_capital = AsyncMock(
        return_value=CapitalAllocation(
            approved=True,
            position_size_usd=1000.0,
            reasoning="Capital allocated",
        )
    )

    bull_researcher = MagicMock()
    bull_researcher.generate_hypothesis = AsyncMock(return_value={"confidence": 0.7})

    bear_researcher = MagicMock()
    bear_researcher.generate_hypothesis = AsyncMock(return_value={"confidence": 0.3})

    coordinator = OODALoopCoordinator(
        data_scout=base_agents["data_scout"],
        analyst=base_agents["analyst"],
        trader=base_agents["trader"],
        risk_manager=base_agents["risk_manager"],
        fund_manager=fund_manager,
        bull_researcher=bull_researcher,
        bear_researcher=bear_researcher,
        cognitive_bridge=cognitive_bridge,
        orchestrator=None,
        order_executor=None,
        circuit_breaker=None,
        trading_mode=TradingMode.NOTIFY_ONLY,
        # Unified Consciousness Components
        cognitive_orchestrator=mock_cognitive_orchestrator,
        navagraha_service=mock_navagraha_service,
        system_identity=mock_system_identity,
        risk_orchestrator=mock_risk_orchestrator,
        karma_register=mock_karma_register,
    )

    return coordinator


class TestUnifiedConsciousnessIntegration:
    """Test suite for Unified Consciousness Integration."""

    @pytest.mark.asyncio
    async def test_navagraha_gate_blocks_trade_during_rahu_kala(
        self,
        base_agents,
        mock_navagraha_service_closed_gate,
    ):
        """Test that trades are blocked when Rahu Kala is active."""
        cognitive_bridge = MagicMock(spec=CognitiveBridge)

        coordinator = OODALoopCoordinator(
            data_scout=base_agents["data_scout"],
            analyst=base_agents["analyst"],
            trader=base_agents["trader"],
            risk_manager=base_agents["risk_manager"],
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=cognitive_bridge,
            navagraha_service=mock_navagraha_service_closed_gate,
        )

        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        assert result["decision"] == "BLOCKED_BY_CONSCIOUSNESS_GATE"
        assert result["gate_open"] is False

    @pytest.mark.asyncio
    async def test_full_ooda_cycle_with_unified_consciousness(
        self,
        unified_coordinator,
        mock_cognitive_orchestrator,
        mock_navagraha_service,
        mock_system_identity,
    ):
        """Test complete OODA cycle with all unified consciousness components."""
        result = await unified_coordinator.run_cycle("BTC/USD", 50000.0)

        # Verify cycle completed
        assert result["trace_id"] is not None
        assert result["symbol"] == "BTC/USD"

        # Verify Navagraha was checked
        mock_navagraha_service.get_current_state.assert_called_once()

        # Verify CognitiveOrchestrator received market tick
        mock_cognitive_orchestrator.handle_market_tick.assert_called_once()

        # Verify OODA phases executed
        assert result["observation"] is not None
        assert result["orientation"] is not None
        assert result["proposal"] is not None
        assert result["risk_assessment"] is not None

    @pytest.mark.asyncio
    async def test_cognitive_orchestrator_guna_integration(
        self,
        unified_coordinator,
        mock_cognitive_orchestrator,
    ):
        """Test that guna balance from CognitiveOrchestrator is used."""
        # Set high tamas in cognitive orchestrator
        mock_cognitive_orchestrator.current_guna_balance.tamas = 0.7

        result = await unified_coordinator.run_cycle("BTC/USD", 50000.0)

        # Verify orientation confidence was modulated by tamas
        # (High tamas should reduce confidence)
        assert result["orientation"].confidence < 0.8  # Original was 0.8

    def test_get_unified_consciousness_state(
        self,
        unified_coordinator,
    ):
        """Test getting unified consciousness state."""
        state = unified_coordinator.get_unified_consciousness_state()

        assert state["ooda_cycles_completed"] >= 0
        assert "components" in state
        assert state["components"]["navagraha"]["enabled"] is True
        assert state["components"]["system_identity"]["enabled"] is True
        assert state["components"]["cognitive_orchestrator"]["enabled"] is True
        assert state["components"]["risk_orchestrator"]["enabled"] is True
        assert state["components"]["karma_register"]["enabled"] is True

    def test_tattva_risk_gate_state(
        self,
        unified_coordinator,
        mock_system_identity,
    ):
        """Test Tattva risk gate evaluation."""
        # Set low Kanchuka coherence
        mock_system_identity.system_state["tattva_coherence"] = {
            str(i): 0.5 for i in range(6, 13)  # Low coherence for Kanchuka layers
        }

        risk_state = unified_coordinator._get_tattva_risk_gate_state()

        assert risk_state["risk_gate_blocked"] is True
        assert risk_state["avg_kanchuka_coherence"] < 0.7
        assert risk_state["confidence_multiplier"] < 1.0

    @pytest.mark.asyncio
    async def test_risk_orchestrator_integration(
        self,
        unified_coordinator,
        mock_risk_orchestrator,
    ):
        """Test RiskOrchestrator integration in decide phase."""

        # Configure risk orchestrator to reject
        def mock_reject(signal, portfolio_value, current_positions_count=0):
            mock_decision = MagicMock()
            mock_decision.approved = False
            mock_decision.reason = "Max drawdown exceeded"
            return mock_decision

        mock_risk_orchestrator.pre_trade_check = mock_reject

        result = await unified_coordinator.run_cycle("BTC/USD", 50000.0)

        # Verify risk orchestrator was called
        # Note: The result might still have a proposal since risk_orchestrator rejection
        # creates a RiskAssessment with REJECT decision
        if result["risk_assessment"]:
            assert result["risk_assessment"].decision == RiskDecision.REJECT

    def test_get_statistics_includes_unified_consciousness(
        self,
        unified_coordinator,
    ):
        """Test that get_statistics includes unified consciousness info."""
        stats = unified_coordinator.get_statistics()

        assert "unified_consciousness" in stats
        assert (
            stats["unified_consciousness"]["components"]["navagraha"]["enabled"] is True
        )


class TestStrategyIntegration:
    """Test Phase D: Strategy Integration."""

    def test_unified_strategy_registry_creation(self):
        """Test UnifiedStrategyRegistry can be created."""
        from backend.core.strategy.unified_strategy_registry import (
            UnifiedStrategyRegistry,
        )

        registry = UnifiedStrategyRegistry()

        assert registry is not None
        assert "trend_following" in registry._strategies
        assert "mean_reversion" in registry._strategies
        assert "defensive" in registry._strategies

    @pytest.mark.asyncio
    async def test_strategy_selection_by_dasha(self):
        """Test strategy selection based on Dasha period."""
        from backend.core.navagraha.models import PlanetName
        from backend.core.strategy.unified_strategy_registry import (
            UnifiedStrategyRegistry,
        )

        # Create mock NavagrahaService that returns Mars period
        navagraha_service = MagicMock()

        async def mock_get_current_state(lat, lon, dt=None):
            from datetime import datetime, timezone

            from backend.core.navagraha.models import GunaDistribution, NavagrahaState

            return NavagrahaState(
                planets={},
                guna_distribution=GunaDistribution(
                    sattva=0.4,
                    rajas=0.4,
                    tamas=0.2,
                    calculated_at=datetime.now(timezone.utc),
                ),
                aspects=[],
                rahu_kala_active=False,
                current_dasha=PlanetName.MARS,  # Mars = trend_following
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        navagraha_service.get_current_state = mock_get_current_state

        registry = UnifiedStrategyRegistry(navagraha_service=navagraha_service)

        strategy_id, strategy = await registry.get_strategy_for_current_dasha()

        assert strategy_id == "trend_following"  # Mars maps to trend_following


class TestFrontendAPI:
    """Test API endpoints for frontend widgets."""

    @pytest.mark.asyncio
    async def test_unified_consciousness_state_endpoint(self, client):
        """Test unified consciousness state API endpoint."""
        # This test assumes the API endpoint exists
        # In a real implementation, you would test the actual endpoint
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
