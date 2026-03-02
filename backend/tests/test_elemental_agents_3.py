import pytest
import pytest_asyncio

from backend.agents.elemental_research import ElementalResearch  # Reuse Air for routing test
from backend.agents.elemental_router import ElementalRouter
from backend.agents.elemental_valuation import ElementalValuation


@pytest.fixture
def earth_agent():
    return ElementalValuation(agent_name="TestEarth")


@pytest.fixture
def air_agent():
    return ElementalResearch(agent_name="TestAir")


@pytest.fixture
def router(earth_agent, air_agent):
    r = ElementalRouter()
    r.register_agent(earth_agent)
    r.register_agent(air_agent)
    return r


@pytest.mark.asyncio
async def test_earth_valuation(earth_agent):
    """Test Earth agent valuation logic."""
    # Undervalued (Buy signal)
    data = {"data": {"price": 100, "ma_200": 110}, "strategy": {"direction": "bullish"}}  # 10% gap
    result = await earth_agent.process_signal(data)

    assert result["valuation_gap"] == 10.0
    assert result["proposal"]["action"] == "buy"
    assert result["proposal"]["size"] == 2000  # Deep value > 5%


@pytest.mark.asyncio
async def test_earth_block_overvalued(earth_agent):
    """Test Earth blocking overvalued buys."""
    # Overvalued (Price > MA)
    data = {
        "data": {"price": 110, "ma_200": 100},  # -9.09% gap
        "strategy": {"direction": "bullish"},  # Strategy wants to buy
    }
    result = await earth_agent.process_signal(data)

    assert result["valuation_gap"] < 0
    assert result["proposal"]["action"] == "hold"  # Blocked
    assert "Overvalued" in result["proposal"]["reason"]


@pytest.mark.asyncio
async def test_router_dispatch(router):
    """Test router dispatching to multiple agents."""
    # 'market_data' routes to Air and Earth (and Water, but not reg here)
    payload = {
        "data": {
            "price": 100,
            "ma_200": 110,
            "price_change_24h": 10.0,  # Trigger Air bullish
            "volume_change_24h": 15.0,  # Required for bullish confirmation
        },
        "strategy": {"direction": "bullish"},
    }

    results = await router.route_signal("market_data", payload)

    assert "air" in results
    assert "earth" in results

    # Check individual results
    assert results["air"]["hypothesis"]["direction"] == "bullish"
    assert results["earth"]["valuation_gap"] == 10.0


@pytest.mark.asyncio
async def test_router_missing_route(router):
    """Test router handling undefined routes."""
    results = await router.route_signal("unknown_signal", {})
    assert results == {}
