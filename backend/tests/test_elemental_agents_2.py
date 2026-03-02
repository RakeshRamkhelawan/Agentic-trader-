import pytest
import pytest_asyncio

from backend.agents.elemental_macro import ElementalMacro
from backend.agents.elemental_risk_guardian import ElementalRiskGuardian


@pytest.fixture
def fire_agent():
    return ElementalRiskGuardian(agent_name="TestFire")


@pytest.fixture
def water_agent():
    return ElementalMacro(agent_name="TestWater")


@pytest.mark.asyncio
async def test_fire_risk_approval(fire_agent):
    """Test Fire agent risk assessment logic."""
    # Safe proposal
    safe_signal = {"proposal": {"size": 50000}, "market_state": {"volatility": 0.2}}
    result = await fire_agent.process_signal(safe_signal)

    assert result["approved"] is True
    assert result["risk_score"] < 0.5
    assert fire_agent.prana == 95.0  # 100 - 5 cost


@pytest.mark.asyncio
async def test_fire_risk_block(fire_agent):
    """Test Fire agent blocking logic."""
    # Hazardous proposal (High Volatility)
    risky_signal = {
        "proposal": {"size": 50000},
        "market_state": {"volatility": 0.8},  # > 0.5 threshold
    }
    result = await fire_agent.process_signal(risky_signal)

    assert result["approved"] is False
    assert "exceeds threshold" in result["reason"]


@pytest.mark.asyncio
async def test_water_regime_detection(water_agent):
    """Test Water agent regime detection."""
    # Bullish quiet
    trend_signal = {"data": {"trend": 0.8, "volatility": 0.1}}
    result = await water_agent.process_signal(trend_signal)

    assert result["regime"] == "strong_bull_quiet"
    assert len(result["similar_patterns"]) > 0
    assert water_agent.prana == 92.0  # 100 - 8 cost


@pytest.mark.asyncio
async def test_fire_degraded_safety(fire_agent):
    """Test Fire agent fails SAFE (blocks) when depleted."""
    fire_agent.prana = 4.0  # Depleted below 10

    result = await fire_agent.process_signal({})

    assert result["status"] == "degraded"
    assert result["approved"] is False  # Must block if down
    assert result["risk_score"] == 1.0
