import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.fund_manager_agent import FundManagerAgent
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.agents.researcher_agents import BearResearcher, BullResearcher
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.database import SessionManager
from backend.core.schemas.ooda_types import (
    CapitalAllocation,
    MarketRegime,
    Observation,
    Orientation,
    ResearchHypothesis,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)
from backend.execution.adapters import StubExchangeAdapter
from backend.execution.order_executor import OrderExecutor
from backend.governance.agent_gatekeeper import AgentRole
from backend.governance.decision_audit import DecisionAuditLog
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode


@pytest.mark.asyncio
async def test_full_ooda_flow_with_audit():
    """
    Test complete OODA flow:
    1. Agents produce signals
    2. Coordinator executes loop
    3. Trade is executed (Stub)
    4. Audit log is persisted to DB
    """

    # 1. Setup Agents (Mocked for speed, but flow is real)
    data_scout = MagicMock(spec=DataScoutAgent)
    data_scout.observe = AsyncMock(
        return_value=Observation(symbol="BTC/USDT", price=50000.0, volume=100.0)
    )
    # data_scout.get_statistics = MagicMock(return_value={}) # Added to coordinator recently

    analyst = MagicMock(spec=AnalystAgent)
    analyst.orient = AsyncMock(
        return_value=Orientation(
            symbol="BTC/USDT", regime="trending_up", core_sentiment=0.8, confidence=0.9
        )
    )

    trader = MagicMock(spec=TraderAgent)
    trader.agent_name = "TraderBot"
    trader.agent_role = AgentRole.STRATEGIST
    trader.propose_trade = AsyncMock(
        return_value=TradeProposal(
            symbol="BTC/USDT",
            side="buy",
            size=0.1,
            stop_loss=49000,
            take_profit=52000,
            rationale="Integration Test Signal",
            strategy_id="integration_v1",
            confidence=0.9,
        )
    )

    risk_manager = MagicMock(spec=RiskManagerAgent)
    risk_manager.assess_risk = AsyncMock(
        return_value=RiskAssessment(
            trade_id="trace_123",
            decision=RiskDecision.APPROVE,
            rationale="Risk Acceptable",
            risk_score=0.1,
            win_probability=0.6,
        )
    )

    fund_manager = MagicMock(spec=FundManagerAgent)
    fund_manager.allocate_capital = AsyncMock(
        return_value=CapitalAllocation(
            position_size_usd=5000.0,
            position_fraction=0.1,
            kelly_fraction=0.1,
            approved=True,
            reasoning="Capital Available",
        )
    )

    bull_researcher = MagicMock(spec=BullResearcher)
    bull_researcher.generate_hypothesis = AsyncMock(
        return_value=ResearchHypothesis(
            stance="bullish", confidence=0.7, arguments=["Up"], contrarian_score=0.1
        )
    )

    bear_researcher = MagicMock(spec=BearResearcher)
    bear_researcher.generate_hypothesis = AsyncMock(
        return_value=ResearchHypothesis(
            stance="bearish", confidence=0.3, arguments=["Down"], contrarian_score=0.1
        )
    )

    cognitive_bridge = MagicMock(spec=CognitiveBridge)
    cognitive_bridge.process_observation = AsyncMock(return_value=0.5)

    orchestrator = OrchestratorAgent()
    orchestrator.publish_thought = AsyncMock()

    # 2. Setup Execution
    stub_adapter = StubExchangeAdapter()

    # Mock Gatekeeper to allow execution
    mock_gatekeeper = MagicMock()
    mock_gatekeeper.require_permission = MagicMock(return_value=True)

    executor = OrderExecutor(exchange_adapter=stub_adapter, gatekeeper=mock_gatekeeper)

    # 3. Setup Coordinator with Real DB Session
    # We use system_admin_session factory
    coordinator = OODALoopCoordinator(
        data_scout=data_scout,
        analyst=analyst,
        trader=trader,
        risk_manager=risk_manager,
        fund_manager=fund_manager,
        bull_researcher=bull_researcher,
        bear_researcher=bear_researcher,
        cognitive_bridge=cognitive_bridge,
        orchestrator=orchestrator,
        order_executor=executor,
        trading_mode=TradingMode.AUTO,
        audit_session_factory=SessionManager.system_admin_session,
    )

    # 4. Run Cycle
    print("Running OODA Cycle...")
    result = await coordinator.run_cycle("BTC/USDT", 50000.0)

    # 5. Verify Execution
    assert len(stub_adapter.placed_orders) == 1
    order = stub_adapter.placed_orders[0]
    assert order.symbol == "BTC/USDT"
    print(f"Verified Execution: {order}")

    # 6. Verify Audit Log in DB
    trace_id = result["trace_id"]
    print(f"Checking DB for trace_id: {trace_id}")

    async with SessionManager.system_admin_session() as session:
        stmt = select(DecisionAuditLog).where(DecisionAuditLog.trace_id == trace_id)
        db_result = await session.execute(stmt)
        record = db_result.scalar_one_or_none()

        assert record is not None
        assert record.symbol == "BTC/USDT"
        assert record.trading_mode == "auto"
        assert record.execution_status == "executed"
        print(f"Verified DB Record: {record}")
