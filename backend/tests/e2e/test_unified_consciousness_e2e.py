"""
End-to-End Tests: Unified Consciousness Integration

Complete end-to-end test suite voor het gehele unified consciousness systeem:
- Alle 6 fasen samen
- Full trading flow
- Frontend-backend integratie
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.guna_quantifier import GunaVector
from backend.core.karma.karma_register import KarmaRegister, TradeOutcome
from backend.core.navagraha.models import GunaDistribution, NavagrahaState, PlanetName
from backend.core.navagraha.service import NavagrahaService
from backend.core.schemas.ooda_types import (
    CapitalAllocation,
    MarketRegime,
    Observation,
    Orientation,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)
from backend.core.system_identity import SystemIdentity
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode
from backend.risk.risk_orchestrator import RiskOrchestrator, TradeSignal
from backend.services.cognitive_orchestrator import CognitiveOrchestrator


class TestUnifiedConsciousnessE2E:
    """End-to-end tests voor Unified Consciousness Integration."""

    @pytest.fixture
    async def unified_system(self):
        """Create complete unified consciousness system."""
        # Create all components
        cognitive_co = MagicMock(spec=CognitiveOrchestrator)
        cognitive_co.current_guna_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)
        cognitive_co.handle_market_tick = AsyncMock()

        navagraha_service = MagicMock(spec=NavagrahaService)

        async def mock_navagraha_state(lat, lon, dt=None):
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
                guna_distribution=GunaDistribution(
                    sattva=0.5,
                    rajas=0.3,
                    tamas=0.2,
                    calculated_at=datetime.now(timezone.utc),
                ),
                aspects=[],
                rahu_kala_active=False,
                current_dasha=PlanetName.JUPITER,
                consciousness_level="Discriminative Intelligence",
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        navagraha_service.get_current_state = mock_navagraha_state

        system_identity = SystemIdentity()

        risk_orchestrator = RiskOrchestrator(
            max_daily_var_pct=0.05,
            max_positions=10,
        )

        karma_register = KarmaRegister()

        # Create OODA coordinator with all components
        data_scout = MagicMock(spec=DataScoutAgent)
        data_scout.observe = AsyncMock(
            return_value=Observation(
                symbol="BTC/USD",
                price=50000.0,
                timestamp=datetime.now(timezone.utc),
                orderbook={"bids": [[49999, 1]], "asks": [[50001, 1]]},
                funding_rate=0.0001,
            )
        )

        analyst = MagicMock(spec=AnalystAgent)
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

        trader = MagicMock(spec=TraderAgent)
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
                strategy_id="trend_following",
                confidence=0.8,
            )
        )

        risk_manager = MagicMock(spec=RiskManagerAgent)
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

        fund_manager = MagicMock()
        fund_manager.allocate_capital = AsyncMock(
            return_value=CapitalAllocation(
                approved=True,
                position_size_usd=1000.0,
                reasoning="Capital allocated based on risk assessment",
            )
        )

        bull_researcher = MagicMock()
        bull_researcher.generate_hypothesis = AsyncMock(
            return_value={
                "confidence": 0.7,
                "direction": "bullish",
            }
        )

        bear_researcher = MagicMock()
        bear_researcher.generate_hypothesis = AsyncMock(
            return_value={
                "confidence": 0.3,
                "direction": "bearish",
            }
        )

        cognitive_bridge = MagicMock(spec=CognitiveBridge)
        cognitive_bridge.process_observation = AsyncMock(return_value=0.7)

        coordinator = OODALoopCoordinator(
            data_scout=data_scout,
            analyst=analyst,
            trader=trader,
            risk_manager=risk_manager,
            fund_manager=fund_manager,
            bull_researcher=bull_researcher,
            bear_researcher=bear_researcher,
            cognitive_bridge=cognitive_bridge,
            orchestrator=None,
            order_executor=None,
            circuit_breaker=None,
            trading_mode=TradingMode.NOTIFY_ONLY,
            cognitive_orchestrator=cognitive_co,
            navagraha_service=navagraha_service,
            system_identity=system_identity,
            risk_orchestrator=risk_orchestrator,
            karma_register=karma_register,
        )

        return {
            "coordinator": coordinator,
            "cognitive_co": cognitive_co,
            "navagraha_service": navagraha_service,
            "system_identity": system_identity,
            "risk_orchestrator": risk_orchestrator,
            "karma_register": karma_register,
        }

    @pytest.mark.asyncio
    async def test_e2e_complete_trading_cycle(self, unified_system):
        """Test E2E: Complete trading cycle met unified consciousness."""
        # Arrange
        coordinator = unified_system["coordinator"]

        # Act
        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        assert result["trace_id"] is not None
        assert result["symbol"] == "BTC/USD"
        assert result["observation"] is not None
        assert result["orientation"] is not None
        assert result["proposal"] is not None
        assert result["risk_assessment"] is not None

    @pytest.mark.asyncio
    async def test_e2e_consciousness_components_active(self, unified_system):
        """Test E2E: Alle consciousness components zijn actief."""
        # Arrange
        coordinator = unified_system["coordinator"]

        # Act
        state = coordinator.get_unified_consciousness_state()

        # Assert
        assert state["components"]["cognitive_orchestrator"]["enabled"] is True
        assert state["components"]["navagraha"]["enabled"] is True
        assert state["components"]["system_identity"]["enabled"] is True
        assert state["components"]["risk_orchestrator"]["enabled"] is True
        assert state["components"]["karma_register"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_e2e_navagraha_gate_blocks_during_rahu_kala(self):
        """Test E2E: Navagraha gate blokkeert tijdens Rahu Kala."""
        # Arrange
        mock_navagraha = MagicMock(spec=NavagrahaService)

        async def mock_blocked_state(lat, lon, dt=None):
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

        mock_navagraha.get_current_state = mock_blocked_state

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
        )

        # Act
        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        assert result["decision"] == "BLOCKED_BY_CONSCIOUSNESS_GATE"
        assert result["gate_open"] is False

    @pytest.mark.asyncio
    async def test_e2e_risk_orchestrator_integration(self, unified_system):
        """Test E2E: RiskOrchestrator in de trading flow."""
        # Arrange
        unified_system["coordinator"]
        risk_orch = unified_system["risk_orchestrator"]

        # Create test signal
        signal = TradeSignal(
            symbol="BTC/USD",
            side="buy",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.7,
            reward_to_risk=2.0,
            strategy="trend_following",
        )

        # Act
        risk_result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
            current_positions_count=2,
        )

        # Assert
        assert risk_result.approved is True
        assert risk_result.sizing_method == "kelly"
        assert risk_result.recommended_quantity > 0

    @pytest.mark.asyncio
    async def test_e2e_strategy_selection_by_dasha(self, unified_system):
        """Test E2E: Dasha-based strategy selectie."""
        # Arrange
        from backend.core.strategy.unified_strategy_registry import (
            UnifiedStrategyRegistry,
        )

        registry = UnifiedStrategyRegistry(
            navagraha_service=unified_system["navagraha_service"]
        )

        # Act
        strategy_id, strategy = await registry.get_strategy_for_current_dasha()

        # Assert
        assert strategy_id is not None
        assert strategy is not None
        # Jupiter period should give trend_following
        assert strategy_id == "trend_following"

    @pytest.mark.asyncio
    async def test_e2e_karma_feedback_loop(self, unified_system):
        """Test E2E: Karma feedback loop na trade."""
        # Arrange
        karma = unified_system["karma_register"]

        # Simulate trade execution
        execution_result = {
            "status": "executed",
            "pnl_percent": 0.05,
            "drawdown_percent": 0.02,
            "execution_time_ms": 150.0,
        }

        # Act
        outcome = TradeOutcome(
            pnl_percent=execution_result.get("pnl_percent", 0.0),
            drawdown_percent=execution_result.get("drawdown_percent", 0.0),
            execution_speed_ms=execution_result.get("execution_time_ms", 0.0),
        )
        karma.register_feedback("trader_agent", outcome)

        # Assert
        assert "trader_agent" in karma.agent_karma
        assert (
            karma.agent_karma["trader_agent"] > 0
        )  # Positive karma for positive trade

    @pytest.mark.asyncio
    async def test_e2e_system_identity_updates(self, unified_system):
        """Test E2E: SystemIdentity updates na trade."""
        # Arrange
        identity = unified_system["system_identity"]
        initial_outcomes = len(identity.performance_history["outcomes"])

        # Act
        identity.update_outcome(action_id=12345, outcome=0.05)

        # Assert
        assert len(identity.performance_history["outcomes"]) == initial_outcomes + 1

    @pytest.mark.asyncio
    async def test_e2e_full_flow_with_execution(self):
        """Test E2E: Volledige flow inclusief order execution."""
        # Arrange - Create system with order executor
        from backend.execution.order_executor import OrderExecutor

        mock_executor = MagicMock(spec=OrderExecutor)
        mock_executor.execute_trade = AsyncMock(
            return_value=MagicMock(
                success=True,
                filled_qty=0.1,
                avg_price=50000.0,
                error=None,
            )
        )

        mock_navagraha = MagicMock()

        async def mock_open_state(lat, lon, dt=None):
            return NavagrahaState(
                planets={},
                guna_distribution=GunaDistribution(
                    sattva=0.5,
                    rajas=0.3,
                    tamas=0.2,
                    calculated_at=datetime.now(timezone.utc),
                ),
                aspects=[],
                rahu_kala_active=False,
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        mock_navagraha.get_current_state = mock_open_state

        karma = KarmaRegister()
        identity = SystemIdentity()

        data_scout = MagicMock(spec=DataScoutAgent)
        data_scout.observe = AsyncMock(
            return_value=Observation(
                symbol="BTC/USD",
                price=50000.0,
                timestamp=datetime.now(timezone.utc),
                orderbook={},
                funding_rate=0.0001,
            )
        )

        analyst = MagicMock(spec=AnalystAgent)
        analyst.orient = AsyncMock(
            return_value=Orientation(
                symbol="BTC/USD",
                regime=MarketRegime.TRENDING_UP,
                indicators={},
                core_sentiment=0.7,
                rag_context=[],
                confidence=0.8,
            )
        )

        trader = MagicMock(spec=TraderAgent)
        trader.propose_trade = AsyncMock(
            return_value=TradeProposal(
                symbol="BTC/USD",
                side="buy",
                size=0.1,
                entry_price=50000.0,
                stop_loss=49000.0,
                take_profit=52000.0,
                leverage=2.0,
                rationale="Strong momentum",
                strategy_id="momentum",
                confidence=0.8,
            )
        )

        risk_manager = MagicMock(spec=RiskManagerAgent)
        risk_manager.assess_risk = AsyncMock(
            return_value=RiskAssessment(
                decision=RiskDecision.APPROVE,
                risk_score=0.3,
                rationale="Low risk",
            )
        )

        fund_manager = MagicMock()
        fund_manager.allocate_capital = AsyncMock(
            return_value=CapitalAllocation(
                approved=True,
                position_size_usd=1000.0,
                reasoning="Approved",
            )
        )

        coordinator = OODALoopCoordinator(
            data_scout=data_scout,
            analyst=analyst,
            trader=trader,
            risk_manager=risk_manager,
            fund_manager=fund_manager,
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            order_executor=mock_executor,
            trading_mode=TradingMode.AUTO,  # AUTO mode for execution
            navagraha_service=mock_navagraha,
            system_identity=identity,
            risk_orchestrator=RiskOrchestrator(),
            karma_register=karma,
        )

        # Act
        result = await coordinator.run_cycle("BTC/USD", 50000.0)

        # Assert
        assert result["execution"] is not None
        mock_executor.execute_trade.assert_called_once()


class TestE2EPerformance:
    """Performance tests voor E2E scenarios."""

    @pytest.mark.asyncio
    async def test_e2e_cycle_performance(self, unified_system):
        """Test E2E: Prestatie van een complete cycle."""
        import time

        coordinator = unified_system["coordinator"]

        start = time.time()
        result = await coordinator.run_cycle("BTC/USD", 50000.0)
        elapsed = time.time() - start

        # Should complete within reasonable time
        assert elapsed < 5.0  # Less than 5 seconds
        assert result["trace_id"] is not None

    @pytest.mark.asyncio
    async def test_e2e_multiple_cycles(self, unified_system):
        """Test E2E: Meerdere cycles achter elkaar."""
        coordinator = unified_system["coordinator"]

        results = []
        for i in range(5):
            result = await coordinator.run_cycle("BTC/USD", 50000.0 + i * 100)
            results.append(result)

        # Assert all cycles completed
        assert len(results) == 5
        assert all(r["trace_id"] is not None for r in results)

        # Verify cycles are tracked
        assert coordinator.cycles_completed >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
