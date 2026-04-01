from unittest.mock import MagicMock

import pytest

from backend.core.memory_agent import MemoryAgent
from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.risk.validators import RiskValidator
from backend.schemas.agent_messages import AgentMessage
from backend.schemas.orders import OrderRequest, OrderSide, OrderStatus, OrderType
from backend.services.research_agent import ResearchAgent


# --- MOCK ORCHESTRATOR ---
class MockOrchestrator:
    """
    Simuleert de centrale hub die berichten routeert.
    In prod zou dit via Kafka gaan.
    """

    def __init__(self, risk_engine, execution_engine):
        self.risk = risk_engine
        self.execution = execution_engine
        self.inbox = []

    async def handle_message(self, msg: AgentMessage):
        self.inbox.append(msg)

        if msg.type == "NEWS_DATA" and msg.payload.get("sentiment", 0) > 0.7:
            # High sentiment -> Trigger Buy
            # print(f"[Orchestrator] Received STRONG signal: {msg.payload['summary']}")

            order = OrderRequest(
                symbol="BTC-EUR",
                qty=0.1,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                strategy_id="news_momentum",
            )

            # Risk Check
            self.risk.validate_order(order, current_price=50000.0)

            # Execution
            result = await self.execution.submit_order(order)
            return result

        return None


# --- TESTS ---


@pytest.mark.asyncio
async def test_news_triggers_trade_flow():
    """
    Happy Path:
    1. Research Agent vindt nieuws.
    2. Orchestrator ziet signaal.
    3. Risk keurt goed.
    4. Execution koopt.
    """
    # 1. Setup System
    memory = MagicMock(spec=MemoryAgent)
    portfolio = ShadowPortfolioManager(initial_cash=100000.0)
    # Zet prijs voor simulatie
    portfolio.update_price("BTC-EUR", 50000.0)

    risk = RiskValidator(max_order_size=10000.0, max_daily_loss=500.0)
    orchestrator = MockOrchestrator(risk, portfolio)

    # 2. Research Agent (Injecteer de message bus)
    research_agent = ResearchAgent(
        memory_agent=memory, message_bus=orchestrator.handle_message
    )

    # Simulatie van analyse resultaat
    analysis = {
        "summary": "Bitcoin ETF Approved!",
        "sentiment": 0.9,  # Very Bullish
        "impact": 10,
    }

    # Act: Research Agent "publishes" via normale flow
    result = await research_agent.publish_signal(analysis)

    # Assert
    assert result is not None
    assert result.status == OrderStatus.FILLED
    assert result.filled_qty == 0.1

    # Check Portfolio
    balance = await portfolio.get_balance()
    assert balance["BTC-EUR"] == 0.1
    assert balance["EUR"] == 95000.0


@pytest.mark.asyncio
async def test_risk_blocks_news_trade():
    """
    Unhappy Path:
    Nieuws is goed, maar Risk limiet wordt overschreden.
    """
    memory = MagicMock()
    portfolio = ShadowPortfolioManager()
    portfolio.update_price("BTC-EUR", 50000.0)

    # Risk limiet heel laag zetten (10 EUR)
    risk = RiskValidator(max_order_size=10.0, max_daily_loss=500.0)
    orchestrator = MockOrchestrator(risk, portfolio)

    research_agent = ResearchAgent(
        memory_agent=memory, message_bus=orchestrator.handle_message
    )

    analysis = {"summary": "Super Bullish News", "sentiment": 0.9, "impact": 10}

    # Act & Assert
    from backend.risk.validators import RiskViolationError

    with pytest.raises(RiskViolationError):
        await research_agent.publish_signal(analysis)

    # Check dat er NIET is gehandeld
    balance = await portfolio.get_balance()
    assert balance.get("BTC-EUR", 0) == 0
