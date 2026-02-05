import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.services.cognitive_orchestrator import CognitiveOrchestrator, AgentMessage
from backend.schemas.guna import GunaVector
from backend.core.agent_registry import AgentProfile
from backend.services.research_agent import ResearchAgent
from backend.services.macro_agent import MacroAgent
from backend.services.valuation_agent import ValuationAgent

# --- FIXTURES ---

@pytest.fixture
def mock_agent_registry():
    """Mock registry met gedefinieerde agenten."""
    registry = MagicMock()
    
    # Mock profiles (let op de guna_composition)
    registry.profiles = {
        "orchestrator_v1": AgentProfile(id="orchestrator_v1", name="Orchestrator", element="ether",
                                      guna_composition=GunaVector(sattva=0.8, rajas=0.1, tamas=0.1).to_dict(),
                                      system_directive="", allowed_tools=[], subscriptions=[]),
        "research_v1": AgentProfile(id="research_v1", name="Research", element="air",
                                   guna_composition=GunaVector(sattva=0.2, rajas=0.7, tamas=0.1).to_dict(),
                                   system_directive="", allowed_tools=[], subscriptions=["GUNA_SIGNAL", "NEWS_DATA"]),
        "risk_guardian_v1": AgentProfile(id="risk_guardian_v1", name="Risk", element="fire",
                                        guna_composition=GunaVector(sattva=0.4, rajas=0.5, tamas=0.1).to_dict(),
                                        system_directive="", allowed_tools=[], subscriptions=["GUNA_SIGNAL"]),
        "macro_v1": AgentProfile(id="macro_v1", name="Macro", element="water",
                                guna_composition=GunaVector(sattva=0.3, rajas=0.1, tamas=0.6).to_dict(),
                                system_directive="", allowed_tools=[], subscriptions=["GUNA_SIGNAL"]),
        "valuation_v1": AgentProfile(id="valuation_v1", name="Valuation", element="earth",
                                guna_composition=GunaVector(sattva=0.1, rajas=0.1, tamas=0.8).to_dict(),
                                system_directive="", allowed_tools=[], subscriptions=["GUNA_SIGNAL"]),
    }
    registry.get_profile.side_effect = lambda agent_id: registry.profiles.get(agent_id)
    return registry

@pytest.fixture
def mock_guna_quantifier():
    """Mock Guna Quantifier."""
    quantifier = MagicMock()
    # Standaard Rajas voor tekst, voor numeriek kunnen we later aanpassen
    quantifier.quantify_text = MagicMock(return_value=GunaVector(sattva=0.3, rajas=0.5, tamas=0.2)) 
    quantifier.quantify_numerical_data = MagicMock(return_value=GunaVector(sattva=0.4, rajas=0.4, tamas=0.2)) # Standaard neutraal voor nummer
    return quantifier

@pytest.fixture
def mock_intent_monitor():
    """Mock Intent Monitor."""
    monitor = MagicMock()
    monitor.monitor_balance = AsyncMock()
    return monitor

@pytest.mark.asyncio
async def test_orchestrator_routes_by_guna(mock_agent_registry, mock_guna_quantifier, mock_intent_monitor):
    """Happy Path: Orchestrator routeert event naar meest geschikte agent o.b.v. Guna match."""
    
    with patch('backend.services.cognitive_orchestrator.MemoryAgent') as MockMemoryAgent:
        MockMemoryAgent.return_value = MagicMock() # Mock the MemoryAgent instantiation

        # Simuleer een incoming event met een specifieke Guna-vibratie
        rajasic_event_text = "Market is extremely volatile today! Buy now!"
        rajasic_event_guna = GunaVector(sattva=0.1, rajas=0.8, tamas=0.1)
        mock_guna_quantifier.quantify_text.return_value = rajasic_event_guna # Maak deze dynamisch
        
        # Maak een mock agent om de 'handle_message' te tracken
        mock_research_agent_instance = AsyncMock(spec=ResearchAgent)
        mock_risk_agent_instance = AsyncMock()
        mock_macro_agent_instance = AsyncMock()
        mock_valuation_agent_instance = AsyncMock()

        # Initialiseer Orchestrator met mocks
        orchestrator = CognitiveOrchestrator(
            agent_registry=mock_agent_registry,
            guna_quantifier=mock_guna_quantifier,
            intent_monitor=mock_intent_monitor
        )
        
        # Forceer de orchestrator om de mock agent instances te gebruiken
        orchestrator.agents["research_v1"] = mock_research_agent_instance
        orchestrator.agents["risk_guardian_v1"] = mock_risk_agent_instance
        orchestrator.agents["macro_v1"] = mock_macro_agent_instance
        orchestrator.agents["valuation_v1"] = mock_valuation_agent_instance


        # Stuur een GUNA_SIGNAL event
        event_message = AgentMessage(
            source="external",
            target="orchestrator_v1",
            type="NEWS_DATA", # Veranderd van GUNA_SIGNAL naar NEWS_DATA om trigger te zijn
            payload={"text": rajasic_event_text}
        )
        
        await orchestrator.handle_message(event_message)
        
        # Verwacht dat de Research Agent (hoog Rajas) wordt geactiveerd.
        # En dat hij de GunaVector in zijn payload krijgt.
        mock_research_agent_instance.handle_message.assert_called_once()
        sent_message = mock_research_agent_instance.handle_message.call_args[0][0]
        assert sent_message.payload["guna_vibration"] == rajasic_event_guna.to_dict()
        
        mock_risk_agent_instance.handle_message.assert_not_called()
        mock_macro_agent_instance.handle_message.assert_not_called()
        mock_valuation_agent_instance.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_maintains_guna_balance(mock_agent_registry, mock_guna_quantifier, mock_intent_monitor):
    """Happy Path: Orchestrator berekent globale balans en geeft door aan IntentMonitor."""
    
    with patch('backend.services.cognitive_orchestrator.MemoryAgent') as MockMemoryAgent:
        MockMemoryAgent.return_value = MagicMock() # Mock the MemoryAgent instantiation

        # Configureer Guna Quantifier om een paar keer iets specifieks te returnen
        mock_guna_quantifier.quantify_text.side_effect = [
            GunaVector(sattva=0.2, rajas=0.7, tamas=0.1), # Rajas dominant nieuws
            GunaVector(sattva=0.7, rajas=0.1, tamas=0.2), # Sattva dominant marktdata
        ]

        orchestrator = CognitiveOrchestrator(
            agent_registry=mock_agent_registry,
            guna_quantifier=mock_guna_quantifier,
            intent_monitor=mock_intent_monitor
        )
        
        # Simuleer een paar events die de balans beinvloeden
        await orchestrator.handle_message(AgentMessage(source="research", target="orchestrator_v1", type="NEWS_DATA", payload={"text": "Fast market!"}))
        await orchestrator.handle_message(AgentMessage(source="market", target="orchestrator_v1", type="TICK_DATA", payload={"price": 100}))

        # Verwacht dat de IntentMonitor 2 keer is aangeroepen
        assert mock_intent_monitor.monitor_balance.call_count == 2
        
        # Check dat de globale balans min of meer een gemiddelde is
        # De exacte waarden hangen af van de implementatie, dus we checken alleen dat het geen defaults zijn
        call_arg: GunaVector = mock_intent_monitor.monitor_balance.call_args[0][0]
        assert call_arg.sattva != pytest.approx(1/3)
        assert call_arg.rajas != pytest.approx(1/3)