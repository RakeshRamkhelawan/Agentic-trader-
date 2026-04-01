from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.fund_manager_agent import FundManagerAgent
from backend.agents.researcher_agents import BearResearcher, BullResearcher
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.schemas.ooda_types import (
    CapitalAllocation,
    ExecutionOutcome,
    MarketRegime,
    Observation,
    Orientation,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)
from backend.execution.order_executor import OrderExecutor
from backend.governance.agent_gatekeeper import AgentRole
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode


@pytest.fixture
def mock_agents():
    """Mock agents voor testing."""
    return {
        "data_scout": AsyncMock(spec=DataScoutAgent),
        "analyst": AsyncMock(spec=AnalystAgent),
        "trader": AsyncMock(spec=TraderAgent),
        "risk_manager": AsyncMock(spec=RiskManagerAgent),
        "fund_manager": AsyncMock(spec=FundManagerAgent),
        "bull_researcher": AsyncMock(spec=BullResearcher),
        "bear_researcher": AsyncMock(spec=BearResearcher),
        "cognitive_bridge": AsyncMock(spec=CognitiveBridge),
        "order_executor": AsyncMock(spec=OrderExecutor),
    }


@pytest.fixture
def sample_observation():
    """Sample observation."""
    return Observation(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000.0,
        orderbook={"bids": [[49900, 1.0]], "asks": [[50100, 1.0]]},
        funding_rate=0.0001,
        social_sentiment=0.6,
    )


@pytest.fixture
def sample_orientation():
    """Sample orientation."""
    return Orientation(
        symbol="BTC/USDT",
        regime=MarketRegime.TRENDING_UP,
        indicators={"rsi": 65.0},
        core_sentiment=0.75,
        confidence=0.75,
    )


@pytest.fixture
def sample_proposal():
    """Sample trade proposal."""
    return TradeProposal(
        symbol="BTC/USDT",
        side="buy",
        size=0.1,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        leverage=2.0,
        rationale="Bullish momentum",
        strategy_id="momentum_v1",
        confidence=0.75,
    )


@pytest.fixture
def approved_assessment(sample_proposal):
    """Approved risk assessment."""
    return RiskAssessment(
        trade_id=sample_proposal.trade_id,
        decision=RiskDecision.APPROVE,
        rationale="All checks passed",
        risk_score=0.2,
        win_probability=0.7,
    )


@pytest.fixture
def successful_execution(sample_proposal):
    """Successful execution outcome."""
    return ExecutionOutcome(
        trace_id="test-trace-id",
        success=True,
        filled_qty=sample_proposal.size,
        avg_price=sample_proposal.entry_price,
        slippage=5.0,
        fees=0.0,
    )


@pytest.fixture
def sample_allocation():
    """Sample capital allocation."""
    return CapitalAllocation(
        position_size_usd=5000.0,
        position_fraction=0.5,
        kelly_fraction=1.0,
        approved=True,
        reasoning="Max allocation",
        timestamp=1234567890.0,
    )


class TestOODALoopCoordinator:
    """Tests for OODALoopCoordinator."""

    @pytest.mark.asyncio
    async def test_complete_cycle_approved(
        self,
        mock_agents,
        sample_observation,
        sample_orientation,
        sample_proposal,
        approved_assessment,
        sample_allocation,
    ):
        """Happy path: Complete cyclus met approved trade (NOTIFY_ONLY default)."""
        # Setup mocks
        mock_agents["data_scout"].observe = AsyncMock(return_value=sample_observation)
        mock_agents["cognitive_bridge"].process_observation = AsyncMock(return_value=0.75)
        mock_agents["analyst"].orient = AsyncMock(return_value=sample_orientation)
        mock_agents["bull_researcher"].generate_hypothesis = AsyncMock(
            return_value="Bullish hypothesis"
        )
        mock_agents["bear_researcher"].generate_hypothesis = AsyncMock(
            return_value="Bearish hypothesis"
        )
        mock_agents["trader"].propose_trade = AsyncMock(return_value=sample_proposal)
        mock_agents["risk_manager"].assess_risk = AsyncMock(return_value=approved_assessment)
        mock_agents["fund_manager"].allocate_capital = AsyncMock(return_value=sample_allocation)

        # Create coordinator (NOTIFY_ONLY default)
        coordinator = OODALoopCoordinator(
            data_scout=mock_agents["data_scout"],
            analyst=mock_agents["analyst"],
            trader=mock_agents["trader"],
            risk_manager=mock_agents["risk_manager"],
            fund_manager=mock_agents["fund_manager"],
            bull_researcher=mock_agents["bull_researcher"],
            bear_researcher=mock_agents["bear_researcher"],
            cognitive_bridge=mock_agents["cognitive_bridge"],
            order_executor=mock_agents["order_executor"],
            trading_mode=TradingMode.NOTIFY_ONLY,
        )

        # Run cycle
        result = await coordinator.run_cycle(symbol="BTC/USDT", current_price=50000.0)

        # Verify results
        assert result["symbol"] == "BTC/USDT"
        assert result["observation"] == sample_observation
        assert result["orientation"] == sample_orientation
        assert result["proposal"] == sample_proposal
        assert result["risk_assessment"] == approved_assessment
        assert result["capital_allocation"] == sample_allocation
        assert "APPROVED" in result["decision"]

        # Execution should NOT be called in NOTIFY_ONLY
        mock_agents["order_executor"].execute_trade.assert_not_called()

        # Verify all other agents called
        mock_agents["data_scout"].observe.assert_called_once()
        mock_agents["cognitive_bridge"].process_observation.assert_called_once()
        mock_agents["analyst"].orient.assert_called_once()
        mock_agents["bull_researcher"].generate_hypothesis.assert_called_once()
        mock_agents["bear_researcher"].generate_hypothesis.assert_called_once()
        mock_agents["trader"].propose_trade.assert_called_once()
        mock_agents["risk_manager"].assess_risk.assert_called_once()
        mock_agents["fund_manager"].allocate_capital.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_mode_executes_trade(
        self,
        mock_agents,
        sample_observation,
        sample_orientation,
        sample_proposal,
        approved_assessment,
        successful_execution,
        sample_allocation,
    ):
        """Test: AUTO mode executes trade."""
        # Setup mocks
        mock_agents["data_scout"].observe = AsyncMock(return_value=sample_observation)
        mock_agents["cognitive_bridge"].process_observation = AsyncMock(return_value=0.75)
        mock_agents["analyst"].orient = AsyncMock(return_value=sample_orientation)
        mock_agents["bull_researcher"].generate_hypothesis = AsyncMock(return_value="Bullish")
        mock_agents["bear_researcher"].generate_hypothesis = AsyncMock(return_value="Bearish")
        mock_agents["trader"].propose_trade = AsyncMock(return_value=sample_proposal)
        mock_agents["trader"].agent_name = "TraderAgent_1"
        mock_agents["trader"].agent_role = AgentRole.STRATEGIST
        mock_agents["risk_manager"].assess_risk = AsyncMock(return_value=approved_assessment)
        mock_agents["fund_manager"].allocate_capital = AsyncMock(return_value=sample_allocation)
        mock_agents["order_executor"].execute_trade = AsyncMock(return_value=successful_execution)

        # Create coordinator in AUTO mode
        coordinator = OODALoopCoordinator(
            data_scout=mock_agents["data_scout"],
            analyst=mock_agents["analyst"],
            trader=mock_agents["trader"],
            risk_manager=mock_agents["risk_manager"],
            fund_manager=mock_agents["fund_manager"],
            bull_researcher=mock_agents["bull_researcher"],
            bear_researcher=mock_agents["bear_researcher"],
            cognitive_bridge=mock_agents["cognitive_bridge"],
            order_executor=mock_agents["order_executor"],
            trading_mode=TradingMode.AUTO,
        )

        # Run cycle
        result = await coordinator.run_cycle(symbol="BTC/USDT", current_price=50000.0)

        # Verify execution was called
        mock_agents["order_executor"].execute_trade.assert_called_once()
        assert result["execution"]["status"] == "executed"
        assert result["execution"]["outcome"] == successful_execution

    @pytest.mark.asyncio
    async def test_cycle_rejected_by_risk(
        self, mock_agents, sample_observation, sample_orientation, sample_proposal
    ):
        """Trade rejected door RiskManager."""
        # Setup mocks
        mock_agents["data_scout"].observe = AsyncMock(return_value=sample_observation)
        mock_agents["cognitive_bridge"].process_observation = AsyncMock(return_value=0.75)
        mock_agents["analyst"].orient = AsyncMock(return_value=sample_orientation)
        mock_agents["trader"].propose_trade = AsyncMock(return_value=sample_proposal)

        rejected_assessment = RiskAssessment(
            trade_id=sample_proposal.trade_id,
            decision=RiskDecision.REJECT,
            rationale="Confidence too low",
            risk_score=0.8,
            win_probability=0.3,
        )
        mock_agents["risk_manager"].assess_risk = AsyncMock(return_value=rejected_assessment)

        coordinator = OODALoopCoordinator(
            data_scout=mock_agents["data_scout"],
            analyst=mock_agents["analyst"],
            trader=mock_agents["trader"],
            risk_manager=mock_agents["risk_manager"],
            fund_manager=mock_agents["fund_manager"],
            bull_researcher=mock_agents["bull_researcher"],
            bear_researcher=mock_agents["bear_researcher"],
            cognitive_bridge=mock_agents["cognitive_bridge"],
            trading_mode=TradingMode.AUTO,  # Even in AUTO mode, should not execute
        )

        result = await coordinator.run_cycle("BTC/USDT", 50000.0)

        assert result["risk_assessment"].decision == RiskDecision.REJECT
        assert "REJECTED" in result["decision"]
        assert result["execution"] is None  # Executie geskipped

    @pytest.mark.asyncio
    async def test_cycle_no_signal(self, mock_agents, sample_observation, sample_orientation):
        """Geen trade signal van Trader."""
        mock_agents["data_scout"].observe = AsyncMock(return_value=sample_observation)
        mock_agents["cognitive_bridge"].process_observation = AsyncMock(return_value=0.5)
        mock_agents["analyst"].orient = AsyncMock(return_value=sample_orientation)
        mock_agents["trader"].propose_trade = AsyncMock(return_value=None)  # No signal

        coordinator = OODALoopCoordinator(
            data_scout=mock_agents["data_scout"],
            analyst=mock_agents["analyst"],
            trader=mock_agents["trader"],
            risk_manager=mock_agents["risk_manager"],
            fund_manager=mock_agents["fund_manager"],
            bull_researcher=mock_agents["bull_researcher"],
            bear_researcher=mock_agents["bear_researcher"],
            cognitive_bridge=mock_agents["cognitive_bridge"],
        )

        result = await coordinator.run_cycle("BTC/USDT", 50000.0)

        assert result["proposal"] is None
        assert result["risk_assessment"] is None
        assert result["decision"] == "NO_SIGNAL"

        # RiskManager niet aangeroepen
        mock_agents["risk_manager"].assess_risk.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_only_mode(
        self,
        mock_agents,
        sample_observation,
        sample_orientation,
        sample_proposal,
        approved_assessment,
    ):
        """NOTIFY_ONLY mode stopt voor execution."""
        mock_agents["data_scout"].observe = AsyncMock(return_value=sample_observation)
        mock_agents["cognitive_bridge"].process_observation = AsyncMock(return_value=0.75)
        mock_agents["analyst"].orient = AsyncMock(return_value=sample_orientation)
        mock_agents["trader"].propose_trade = AsyncMock(return_value=sample_proposal)
        mock_agents["risk_manager"].assess_risk = AsyncMock(return_value=approved_assessment)

        coordinator = OODALoopCoordinator(
            data_scout=mock_agents["data_scout"],
            analyst=mock_agents["analyst"],
            trader=mock_agents["trader"],
            risk_manager=mock_agents["risk_manager"],
            fund_manager=mock_agents["fund_manager"],
            bull_researcher=mock_agents["bull_researcher"],
            bear_researcher=mock_agents["bear_researcher"],
            cognitive_bridge=mock_agents["cognitive_bridge"],
            order_executor=mock_agents["order_executor"],
            trading_mode=TradingMode.NOTIFY_ONLY,
        )

        result = await coordinator.run_cycle("BTC/USDT", 50000.0)

        # Execution niet uitgevoerd in notify_only mode
        assert result["execution"] is None
        assert result["mode"] == "notify_only"
        mock_agents["order_executor"].execute_trade.assert_not_called()

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, mock_agents):
        """Statistics van alle agents verzameld."""
        for agent in mock_agents.values():
            if hasattr(agent, "get_statistics"):
                agent.get_statistics = MagicMock(return_value={"test": 123})

        coordinator = OODALoopCoordinator(
            data_scout=mock_agents["data_scout"],
            analyst=mock_agents["analyst"],
            trader=mock_agents["trader"],
            risk_manager=mock_agents["risk_manager"],
            fund_manager=mock_agents["fund_manager"],
            bull_researcher=mock_agents["bull_researcher"],
            bear_researcher=mock_agents["bear_researcher"],
            cognitive_bridge=mock_agents["cognitive_bridge"],
        )

        stats = coordinator.get_statistics()

        assert "cycles_completed" in stats
        assert "trading_mode" in stats
        assert "agents" in stats
        assert "data_scout" in stats["agents"]
