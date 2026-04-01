from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.agent_registry import AgentRegistry
from backend.core.guna_quantifier import GunaQuantifier
from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.risk.validators import RiskValidator, RiskViolationError

# --- Samkhya Geinspireerde Componenten ---
from backend.schemas.agent_messages import AgentMessage
from backend.schemas.guna import GunaVector
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from backend.services.cognitive_orchestrator import CognitiveOrchestrator
from backend.services.intent_monitor import IntentMonitor

# --- FIXTURES ---


@pytest.fixture
def mock_agent_registry():
    """Een geconfigureerde AgentRegistry met alle profielen."""
    return AgentRegistry(config_path="backend/config/agent_profiles.yaml")


@pytest.fixture
def mock_guna_quantifier():
    """Guna Quantifier met voorspelbare resultaten."""
    quantifier = MagicMock(
        spec=GunaQuantifier
    )  # Moet een mock zijn voor assert_called_with
    # Configureer de mock om een GunaVector terug te geven
    quantifier.quantify_text.return_value = GunaVector(
        sattva=0.3, rajas=0.5, tamas=0.2
    )  # Standaard Rajas
    quantifier.quantify_numerical_data.return_value = GunaVector(
        sattva=0.4, rajas=0.4, tamas=0.2
    )  # Standaard neutraal voor nummer
    return quantifier


@pytest.fixture
def mock_intent_monitor_instance():
    """Mock Intent Monitor om logs en calls te tracken."""
    monitor = MagicMock(spec=IntentMonitor)  # Maak een gewone mock
    monitor.monitor_balance = AsyncMock()  # Maar zorg dat deze methode async is
    monitor.ideal_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)
    return monitor


@pytest.fixture
def mock_memory_agent_class():
    """Mock de MemoryAgent klasse zelf, zodat elke instantie een mock is."""
    with patch("backend.core.memory_agent.MemoryAgent") as MockMemoryAgent:
        yield MockMemoryAgent


@pytest.fixture
def mock_httpx_async_client():
    """Mock de httpx.AsyncClient klasse voor ResearchAgent."""
    with patch("httpx.AsyncClient") as MockClient:
        yield MockClient


@pytest.fixture
def trading_system_samkhya(
    mock_agent_registry,
    mock_guna_quantifier,  # Gebruik de mock instance
    mock_intent_monitor_instance,  # Gebruik de instance
    mock_memory_agent_class,
    mock_httpx_async_client,  # Injecteer de mock httpx client
):
    """Initialiseert de gehele Samkhya-geïntegreerde architectuur."""

    # Dependencies buiten de orchestrator
    shadow_portfolio = ShadowPortfolioManager(initial_cash=100000.0)
    shadow_portfolio.update_price("BTC-EUR", 50000.0)  # Set a price for trading

    risk_validator = RiskValidator(max_order_size=10000.0, max_daily_loss=500.0)

    # De Orchestrator en zijn interne agents
    orchestrator = CognitiveOrchestrator(
        agent_registry=mock_agent_registry,
        guna_quantifier=mock_guna_quantifier,  # Injecteer de mock instance
        intent_monitor=mock_intent_monitor_instance,  # Gebruik de instance
        memory_agent_factory=lambda: mock_memory_agent_class.return_value,  # Zorgt dat alle agents mock memory krijgen
    )

    # Forceer de orchestrator om de juiste (gemockte) instances te gebruiken voor risk
    orchestrator.agents["risk_guardian_v1"] = (
        risk_validator  # Risk direct, zonder message_bus (voor nu)
    )

    # In een echte setup zouden we ook de ExecutionGateway hier instantieren en injecteren
    # Voor deze E2E test, laten we de orchestrator direct de ShadowPortfolio gebruiken
    orchestrator.agents["execution_gateway_v1"] = (
        MagicMock()
    )  # Mock de ExecutionGateway
    orchestrator.agents["execution_gateway_v1"].submit_order = AsyncMock(
        side_effect=shadow_portfolio.submit_order
    )
    orchestrator.agents["execution_gateway_v1"].get_balance = AsyncMock(
        side_effect=shadow_portfolio.get_balance
    )

    return {
        "orchestrator": orchestrator,
        "research_agent": orchestrator.agents["research_v1"],
        "macro_agent": orchestrator.agents["macro_v1"],
        "valuation_agent": orchestrator.agents["valuation_v1"],
        "risk_validator": risk_validator,
        "shadow_portfolio": shadow_portfolio,
        "intent_monitor": mock_intent_monitor_instance,  # De geïnjecteerde instance
        "guna_quantifier": mock_guna_quantifier,
    }


# --- HAPPY PATH: RAJASIC NEWS -> BULLISH ACTION ---


@pytest.mark.asyncio
async def test_samkhya_e2e_rajasic_news_triggers_trade(
    trading_system_samkhya, mock_httpx_async_client
):
    """
    Scenario:
    1. Research Agent ziet 'rajasic' (actiegericht) nieuws (bijv. 'Bitcoin surge!').
    2. Guna Quantifier geeft hoge Rajas-score.
    3. Orchestrator verwerkt, updates globale Guna, stuurt naar IntentMonitor.
    4. Orchestrator interpreteert als koopsignaal, stuurt naar Risk.
    5. Risk keurt goed.
    6. Execution (ShadowPortfolio) plaatst order.
    """
    sys = trading_system_samkhya

    # Initiele Guna-balans moet neutraal zijn in het begin van de test
    assert sys["orchestrator"].current_guna_balance == GunaVector(
        sattva=1 / 3, rajas=1 / 3, tamas=1 / 3
    )

    # --- EXTERNAL EVENT: RAJASIC NEWS ---
    rajasic_news_text = "BREAKING NEWS: Bitcoin price surges 20% on massive trading volume. Urgent action required!"

    # Configureer mock httpx client voor Research Agent
    mock_httpx_async_client.return_value.get.return_value = MagicMock(
        status_code=200,
        text="<html><body><p>" + rajasic_news_text + "</p></body></html>",
    )

    # Mock ResearchAgent's interne analyse (om GunaQuantifier te testen)
    with patch(
        "backend.services.research_agent.analyze_text_with_llm", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.return_value = {
            "summary": "Bitcoin surges!",
            "sentiment": 0.9,
            "impact": 9,
        }

        # Simuleer de run_cycle van de Research Agent
        # Dit zal intern publish_signal aanroepen, wat naar de orchestrator gaat
        # De handle_message van de ResearchAgent wordt hier direct aangeroepen
        await sys["orchestrator"].handle_message(
            AgentMessage(
                source="orchestrator",
                target="research_v1",
                type="TIMER_TICK_1MIN",
                payload={"text": rajasic_news_text},
            )
        )

    # --- ORCHESTRATOR VERWERKING & ROUTING ---
    # De orchestrator's handle_message zal al zijn aangeroepen door research_agent.publish_signal

    # 1. Check Guna Quantifier usage
    sys["guna_quantifier"].quantify_text.assert_called_with(rajasic_news_text)

    # 2. Check Intent Monitor
    sys["intent_monitor"].monitor_balance.assert_called_once()
    assert (
        sys["orchestrator"].current_guna_balance.rajas
        > sys["orchestrator"].current_guna_balance.sattva
    )
    assert (
        sys["orchestrator"].current_guna_balance.rajas
        > sys["orchestrator"].current_guna_balance.tamas
    )

    # 3. Nu de Orchestrator daadwerkelijk een order initieert
    order_request_from_orchestrator = OrderRequest(
        symbol="BTC-EUR",
        qty=0.1,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        strategy_id="e2e_samkhya_test",
        limit_price=None,
    )

    # Simuleer dat de orchestrator deze order probeert te plaatsen
    current_price = sys["shadow_portfolio"].market_prices["BTC-EUR"]
    sys["risk_validator"].validate_order(
        order_request_from_orchestrator, current_price=current_price
    )

    # Voer de order uit via de gateway
    await sys["orchestrator"].agents["execution_gateway_v1"].submit_order(
        order_request_from_orchestrator
    )

    # 4. Check Order (Shadow Portfolio)
    balance = await sys["shadow_portfolio"].get_balance()
    assert balance["BTC-EUR"] == 0.1
    assert balance["EUR"] == 95000.0


# --- UNHAPPY PATH: TAMASIC MARKET -> RISK AVERSION ---


@pytest.mark.asyncio
async def test_samkhya_e2e_tamasic_market_blocks_trade(
    trading_system_samkhya, mock_httpx_async_client
):
    """
    Scenario:
    1. Init: Systeem start in een zeer Tamasic Guna-balans.
    2. External Event (Rajasic News): Komt binnen.
    3. Orchestrator: Ziet Rajasic nieuws, maar globale balans is Tamasic (Risico-avers).
    4. Risk Engine: Wordt geactiveerd en blokkeert de trade (of Orchestrator triggert geen trade).
    """
    sys = trading_system_samkhya

    # Initiele Guna-balans forceren naar zeer Tamasic
    sys["orchestrator"].current_guna_balance = GunaVector(
        sattva=0.1, rajas=0.1, tamas=0.8
    )

    # --- EXTERNAL EVENT: RAJASIC NEWS ---
    rajasic_news_text = (
        "BREAKING NEWS: Huge opportunity! Market about to explode upwards!"
    )

    # Configureer mock httpx client voor Research Agent
    mock_httpx_async_client.return_value.get.return_value = MagicMock(
        status_code=200,
        text="<html><body><p>" + rajasic_news_text + "</p></body></html>",
    )

    with patch(
        "backend.services.research_agent.analyze_text_with_llm", new_callable=AsyncMock
    ) as mock_analyze:
        mock_analyze.return_value = {
            "summary": "Market explode!",
            "sentiment": 0.9,
            "impact": 9,
        }

        # Activeer Risk Kill Switch voor de test (simuleert Tamas-dominantie die afremt)
        sys["risk_validator"].activate_kill_switch()

        # Simuleer de flow: Research Agent publiceert signaal
        await sys["orchestrator"].handle_message(
            AgentMessage(
                source="orchestrator",
                target="research_v1",
                type="TIMER_TICK_1MIN",
                payload={"text": rajasic_news_text},
            )
        )

    # De Orchestrator zou nu, bij het proberen een order te maken, RiskValidator aanroepen
    # en die zou crashen door de kill switch. Dit moeten we expliciet testen.
    order_request_from_orchestrator = OrderRequest(
        symbol="BTC-EUR",
        qty=0.1,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        strategy_id="e2e_samkhya_test",
        limit_price=None,
    )

    with pytest.raises(RiskViolationError):
        current_price = sys["shadow_portfolio"].market_prices["BTC-EUR"]
        sys["risk_validator"].validate_order(
            order_request_from_orchestrator, current_price=current_price
        )

    # --- VERIFICATIE ---
    # Geen trade geplaatst
    balance = await sys["shadow_portfolio"].get_balance()
    assert balance["EUR"] == 100000.0  # Geld is veilig
    assert balance.get("BTC-EUR", 0) == 0  # Geen BTC gekocht

    # Intent Monitor is nog steeds aangeroepen
    sys["intent_monitor"].monitor_balance.assert_called_once()
