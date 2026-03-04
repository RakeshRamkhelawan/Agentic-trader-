import pytest

from backend.agents.elemental_orchestrator import ElementalOrchestrator
from backend.agents.elemental_research import ElementalResearch


@pytest.fixture
def orchestrator():
    return ElementalOrchestrator(agent_name="TestEther")


@pytest.fixture
def researcher():
    return ElementalResearch(agent_name="TestAir")


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_ether_harmony_calculation(orchestrator):
    """Test harmony logic in Ether agent."""
    # Scenario 1: High Harmony
    inputs_harmony = {
        "air": {"sentiment": 0.8},
        "fire": {"approved": True},
        "water": {"regime": "expansion"},
        "earth": {"valuation_gap": 10},
    }
    result = await orchestrator.process_signal({"inputs": inputs_harmony})
    assert result["harmony_score"] > 0.8
    assert result["prana_remaining"] < 100.0  # Consumed prana

    # Scenario 2: Conflict (Risk Block)
    inputs_conflict = {"fire": {"approved": False}, "earth": {"valuation_gap": 10}}  # Blocker
    result = await orchestrator.process_signal({"inputs": inputs_conflict})
    assert result["harmony_score"] < 0.6


@pytest.mark.asyncio
async def test_air_hypothesis_generation(researcher):
    """Test hypothesis generation in Air agent."""
    # Bullish data
    market_data = {"data": {"price_change_24h": 6.0, "volume_change_24h": 15.0}}
    result = await researcher.process_signal(market_data)

    # Check hypothesis structure
    hypothesis = result.get("hypothesis", {})
    assert hypothesis.get("direction") == "bullish"
    assert hypothesis.get("confidence", 0) > 0.7

    # Prana check
    assert researcher.prana == 90.0  # Start 100 - 10 cost


@pytest.mark.asyncio
async def test_degraded_mode(orchestrator):
    """Test agent behavior when depleted."""
    orchestrator.prana = 5.0  # Below 10 threshold
    result = await orchestrator.process_signal({"inputs": {}})

    assert result["status"] == "degraded"
    assert result["reason"] == "Insufficient Prana for Harmonization"
    assert orchestrator.prana == 5.0  # No further consumption
