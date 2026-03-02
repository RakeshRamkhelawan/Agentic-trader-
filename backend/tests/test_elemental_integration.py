from typing import Any, Dict

import pytest

from backend.agents.elemental_macro import ElementalMacro
from backend.agents.elemental_orchestrator import ElementalOrchestrator
from backend.agents.elemental_research import ElementalResearch
from backend.agents.elemental_risk_guardian import ElementalRiskGuardian
from backend.agents.elemental_router import ElementalRouter
from backend.agents.elemental_valuation import ElementalValuation


# Mock EventBus for integration (in-memory)
class MockEventBus:
    def __init__(self):
        self.events = []

    async def publish(self, stream: str, data: Dict[str, Any]) -> str:
        self.events.append({"stream": stream, "data": data})
        return "msg_id_123"


@pytest.fixture
def mock_event_bus():
    return MockEventBus()


@pytest.fixture
def elemental_system(mock_event_bus):
    """Setup full elemental system."""
    router = ElementalRouter()

    # Instantiate all agents
    ether = ElementalOrchestrator(agent_name="Ether_Orch", event_bus=mock_event_bus)
    air = ElementalResearch(agent_name="Air_Research", event_bus=mock_event_bus)
    fire = ElementalRiskGuardian(agent_name="Fire_Risk", event_bus=mock_event_bus)
    water = ElementalMacro(agent_name="Water_Macro", event_bus=mock_event_bus)
    earth = ElementalValuation(agent_name="Earth_Value", event_bus=mock_event_bus)

    # Register agents
    router.register_agent(ether)
    router.register_agent(air)
    router.register_agent(fire)
    router.register_agent(water)
    router.register_agent(earth)

    return {
        "router": router,
        "agents": {"ether": ether, "air": air, "fire": fire, "water": water, "earth": earth},
        "bus": mock_event_bus,
    }


@pytest.mark.asyncio
async def test_full_ooda_flow(elemental_system):
    """
    Test a full OODA loop flow:
    1. Observe: Market Data -> Air (Hypothesis) & Water (Macro)
    2. Orient: Air/Water outputs -> Ether (Harmonization/Strategy)
    3. Decide: Strategy -> Fire (Risk Check)
    4. Act: Approved Strategy -> Earth (Valuation/Execution)
    """
    router = elemental_system["router"]
    bus = elemental_system["bus"]

    # --- Step 1: Observe (Air & Water) ---
    market_data = {
        "price": 100,
        "ma_200": 110,  # Deep value (Earth likes)
        "price_change_24h": 12.0,  # High Momentum (Air likes)
        "volume_change_24h": 20.0,
        "volatility": 0.2,  # Low vol (Fire likes)
        "trend": 1.0,  # Strong uptrend (Water likes)
    }

    # Route 'market_data' to Air, Water, Earth
    observations = await router.route_signal("market_data", {"data": market_data})

    assert "air" in observations
    assert "water" in observations
    assert observations["air"]["hypothesis"]["direction"] == "bullish"
    assert observations["water"]["regime"] == "strong_bull_quiet"

    # --- Step 2: Orient (Ether) ---
    # Ether takes observations and synthesizes a strategy
    orient_input = {
        "inputs": observations,  # Air/Water/Earth results
        "context": {"global_state": "stable"},
    }

    ether_result = await elemental_system["agents"]["ether"].process_signal(orient_input)

    assert ether_result["harmony_score"] > 0
    assert "synthesis" in ether_result

    strategy = {
        "direction": "bullish",  # Derived from synthesis (mocked logical flow here)
        "confidence": ether_result["synthesis"]["confidence"],
    }

    # --- Step 3: Decide (Fire) ---
    # Fire checks the strategy against risk limits
    risk_input = {
        "proposal": {"size": 1000},  # Initial sizing
        "market_state": market_data,
        "strategy": strategy,
    }

    fire_result = await elemental_system["agents"]["fire"].process_signal(risk_input)

    assert fire_result["approved"] is True
    assert fire_result["risk_score"] < 0.5

    # --- Step 4: Act (Earth) ---
    # Earth executes if Fire approves and Valuation aligns
    execution_input = {"data": market_data, "strategy": strategy, "risk_approval": fire_result}

    earth_result = await elemental_system["agents"]["earth"].process_signal(execution_input)

    assert earth_result["proposal"]["action"] == "buy"
    assert earth_result["proposal"]["size"] >= 1000

    # Verify thoughts were published
    assert len(bus.events) >= 5  # At least one thought per agent
    agent_names = [e["data"]["agent_name"] for e in bus.events]
    assert "Ether_Orch" in agent_names
    assert "Air_Research" in agent_names
    assert "Fire_Risk" in agent_names
    assert "Water_Macro" in agent_names
    assert "Earth_Value" in agent_names


@pytest.mark.asyncio
async def test_risk_block_flow(elemental_system):
    """
    Test flow where Fire blocks the trade.
    """
    fire = elemental_system["agents"]["fire"]

    # High risk market data
    risky_input = {
        "proposal": {"size": 1000000},  # Too big
        "market_state": {"volatility": 0.9},  # Too volatile
    }

    result = await fire.process_signal(risky_input)

    assert result["approved"] is False
    assert result["element"] == "fire"
    # Earth should technically not be called if Fire blocks,
    # but here we test the agent logic itself.
