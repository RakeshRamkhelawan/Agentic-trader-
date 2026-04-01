"""
Phase C & D Integration Tests: Risk Pipeline & Strategy Integration

Integratietests voor:
- Fase C: RiskOrchestrator in OODA workflow
- Fase D: Dasha-based strategy selectie
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.core.navagraha.models import GunaDistribution, NavagrahaState, PlanetName
from backend.core.schemas.ooda_types import (
    MarketRegime,
    Orientation,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)
from backend.core.strategy.unified_strategy_registry import UnifiedStrategyRegistry
from backend.orchestration.ooda_coordinator import OODALoopCoordinator
from backend.risk.drawdown_monitor import DrawdownMonitor, DrawdownStatus
from backend.risk.risk_orchestrator import RiskOrchestrator, TradeSignal


class TestPhaseCRiskOrchestratorIntegration:
    """Integratietests voor RiskOrchestrator in OODA."""

    @pytest.fixture
    def risk_orchestrator(self):
        """Create RiskOrchestrator instance."""
        return RiskOrchestrator(
            max_daily_var_pct=0.05,
            max_positions=10,
        )

    @pytest.fixture
    def sample_trade_proposal(self):
        """Create sample trade proposal."""
        return TradeProposal(
            symbol="BTC/USD",
            side="buy",
            size=0.1,
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            leverage=2.0,
            rationale="Trending up",
            strategy_id="momentum",
            confidence=0.7,
        )

    @pytest.mark.asyncio
    async def test_risk_orchestrator_approves_valid_trade(
        self,
        risk_orchestrator,
        sample_trade_proposal,
    ):
        """Test dat RiskOrchestrator valide trades goedkeurt."""
        # Arrange
        signal = TradeSignal(
            symbol=sample_trade_proposal.symbol,
            side=sample_trade_proposal.side,
            entry_price=sample_trade_proposal.entry_price,
            stop_price=sample_trade_proposal.stop_loss,
            confidence=sample_trade_proposal.confidence,
            reward_to_risk=2.0,
        )

        # Act
        result = risk_orchestrator.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
            current_positions_count=2,
        )

        # Assert
        assert result.approved is True
        assert result.recommended_quantity > 0

    @pytest.mark.asyncio
    async def test_risk_orchestrator_blocks_during_kill_switch(
        self,
        sample_trade_proposal,
    ):
        """Test dat RiskOrchestrator blokkeert tijdens kill switch."""
        # Arrange
        mock_drawdown = MagicMock(spec=DrawdownMonitor)
        mock_drawdown.check.return_value = DrawdownStatus.KILL_SWITCH

        risk_orch = RiskOrchestrator(drawdown_monitor=mock_drawdown)

        signal = TradeSignal(
            symbol=sample_trade_proposal.symbol,
            side=sample_trade_proposal.side,
            entry_price=sample_trade_proposal.entry_price,
            stop_price=sample_trade_proposal.stop_loss,
            confidence=0.9,
            reward_to_risk=3.0,
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
        )

        # Assert
        assert result.approved is False
        assert "KILL SWITCH" in result.reason

    @pytest.mark.asyncio
    async def test_risk_orchestrator_in_ooda_decide_phase(self):
        """Test RiskOrchestrator integratie in OODA decide phase."""
        # Arrange
        mock_risk_orch = MagicMock(spec=RiskOrchestrator)

        # Mock approval
        mock_approval = MagicMock()
        mock_approval.approved = True
        mock_approval.recommended_quantity = 1.0
        mock_approval.sizing_method = "kelly"
        mock_approval.reason = "Trade approved"
        mock_risk_orch.pre_trade_check.return_value = mock_approval

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            risk_orchestrator=mock_risk_orch,
        )

        # Create test proposal
        proposal = TradeProposal(
            symbol="BTC/USD",
            side="buy",
            size=0.1,
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            leverage=2.0,
            rationale="Test",
            strategy_id="momentum",
            confidence=0.7,
        )

        # Mock trader
        coordinator.trader.propose_trade = AsyncMock(return_value=proposal)

        # Mock risk_manager
        coordinator.risk_manager.assess_risk = AsyncMock(
            return_value=RiskAssessment(
                decision=RiskDecision.APPROVE,
                risk_score=0.3,
                rationale="Low risk",
            )
        )

        orientation = Orientation(
            symbol="BTC/USD",
            regime=MarketRegime.TRENDING_UP,
            indicators={},
            core_sentiment=0.7,
            rag_context=[],
            confidence=0.8,
        )

        # Act
        result_proposal, result_risk, result_capital = await coordinator._decide(
            orientation, 50000.0, "momentum"
        )

        # Assert
        mock_risk_orch.pre_trade_check.assert_called_once()
        assert result_risk.decision == RiskDecision.APPROVE

    @pytest.mark.asyncio
    async def test_risk_orchestrator_rejection_in_ooda(self):
        """Test dat RiskOrchestrator rejectie correct werkt in OODA."""
        # Arrange
        mock_risk_orch = MagicMock(spec=RiskOrchestrator)

        # Mock rejection
        mock_rejection = MagicMock()
        mock_rejection.approved = False
        mock_rejection.reason = "Max positions limit reached"
        mock_risk_orch.pre_trade_check.return_value = mock_rejection

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            risk_orchestrator=mock_risk_orch,
        )

        proposal = TradeProposal(
            symbol="BTC/USD",
            side="buy",
            size=0.1,
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            leverage=2.0,
            rationale="Test",
            strategy_id="momentum",
            confidence=0.7,
        )

        coordinator.trader.propose_trade = AsyncMock(return_value=proposal)

        orientation = Orientation(
            symbol="BTC/USD",
            regime=MarketRegime.TRENDING_UP,
            indicators={},
            core_sentiment=0.7,
            rag_context=[],
            confidence=0.8,
        )

        # Act
        result_proposal, result_risk, result_capital = await coordinator._decide(
            orientation, 50000.0, "momentum"
        )

        # Assert
        assert result_risk.decision == RiskDecision.REJECT
        assert "Max positions limit reached" in result_risk.rationale


class TestPhaseDStrategyIntegration:
    """Integratietests voor Dasha-based strategy integratie."""

    @pytest.mark.asyncio
    async def test_strategy_selection_by_jupiter_dasha(self):
        """Test strategie selectie voor Jupiter Dasha."""
        # Arrange
        from backend.core.navagraha.service import NavagrahaService

        mock_navagraha = MagicMock(spec=NavagrahaService)

        async def mock_get_state(lat, lon, dt=None):
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
                current_dasha=PlanetName.JUPITER,
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        mock_navagraha.get_current_state = mock_get_state

        registry = UnifiedStrategyRegistry(navagraha_service=mock_navagraha)

        # Act
        strategy_id, strategy = await registry.get_strategy_for_current_dasha()

        # Assert
        assert strategy_id == "trend_following"  # Jupiter maps to trend following

    @pytest.mark.asyncio
    async def test_strategy_selection_by_rahu_dasha(self):
        """Test strategie selectie voor Rahu Dasha."""
        # Arrange
        from backend.core.navagraha.service import NavagrahaService

        mock_navagraha = MagicMock(spec=NavagrahaService)

        async def mock_get_state(lat, lon, dt=None):
            return NavagrahaState(
                planets={},
                guna_distribution=GunaDistribution(
                    sattva=0.3,
                    rajas=0.4,
                    tamas=0.3,
                    calculated_at=datetime.now(timezone.utc),
                ),
                aspects=[],
                rahu_kala_active=False,
                current_dasha=PlanetName.RAHU,
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        mock_navagraha.get_current_state = mock_get_state

        registry = UnifiedStrategyRegistry(navagraha_service=mock_navagraha)

        # Act
        strategy_id, strategy = await registry.get_strategy_for_current_dasha()

        # Assert
        assert strategy_id == "defensive"  # Rahu maps to defensive

    @pytest.mark.asyncio
    async def test_strategy_config_for_dasha(self):
        """Test strategie configuratie ophalen voor Dasha."""
        # Arrange
        registry = UnifiedStrategyRegistry(navagraha_service=None)

        # Act
        config = registry.get_strategy_config_for_current_dasha("Mars", "Mars")

        # Assert
        assert config["risk_profile"] == "aggressive"
        assert config["time_horizon"] == "scalp"
        assert "volatile" in config["asset_preference"]

    @pytest.mark.asyncio
    async def test_trader_agent_strategy_registry_integration(self):
        """Test TraderAgent met strategy registry integratie."""
        from backend.agents.trader_agent import TraderAgent
        from backend.core.zero_copy_bridge import TradingIntent

        # Arrange
        mock_registry = MagicMock(spec=UnifiedStrategyRegistry)
        mock_registry.analyze_with_dasha_strategy = AsyncMock(
            return_value=TradingIntent(
                action="buy",
                size=0.15,
                confidence=0.75,
                symbol="BTC/USD",
            )
        )

        trader = TraderAgent(strategy_registry=mock_registry)

        orientation = Orientation(
            symbol="BTC/USD",
            regime=MarketRegime.TRENDING_UP,
            indicators={"rsi": 65},
            core_sentiment=0.7,
            rag_context=[],
            confidence=0.8,
        )

        # Act
        proposal = await trader.propose_trade(orientation, 50000.0)

        # Assert
        mock_registry.analyze_with_dasha_strategy.assert_called_once()
        assert proposal is not None
        assert proposal.side == "buy"


class TestPhaseCDEndToEnd:
    """End-to-end tests voor Fase C & D."""

    @pytest.mark.asyncio
    async def test_risk_and_strategy_integration(self):
        """Test integratie van RiskOrchestrator en Strategy selectie."""
        # Arrange
        mock_navagraha = MagicMock()
        from backend.core.navagraha.models import GunaDistribution, NavagrahaState

        async def mock_get_state(lat, lon, dt=None):
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
                current_dasha=PlanetName.JUPITER,
                calculated_at=datetime.now(timezone.utc),
                location_lat=lat,
                location_lon=lon,
            )

        mock_navagraha.get_current_state = mock_get_state

        risk_orch = RiskOrchestrator()
        registry = UnifiedStrategyRegistry(navagraha_service=mock_navagraha)

        # Act - Get strategy
        strategy_id, strategy = await registry.get_strategy_for_current_dasha()

        # Act - Check risk for a signal
        signal = TradeSignal(
            symbol="BTC/USD",
            side="buy",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.7,
            reward_to_risk=2.0,
            strategy=strategy_id,
        )

        risk_result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
        )

        # Assert
        assert strategy_id == "trend_following"
        assert risk_result.approved is True
        assert risk_result.sizing_method == "kelly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
