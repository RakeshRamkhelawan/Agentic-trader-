from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from backend.agents.elemental_base import ElementalBase
from backend.governance.agent_gatekeeper import AgentRole


# Concrete implementation for testing
class TestElementalAgent(ElementalBase):
    async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        return {"processed": True, "signal": signal}


@pytest.fixture
def base_config():
    return {
        "agent_name": "TestFire",
        "element": "fire",
        "tattva_layer": 34,
        "guna_balance": {"sattva": 0.4, "rajas": 0.5, "tamas": 0.1},
        "max_prana": 100.0,
        "prana_decay_rate": 5.0,
    }


@pytest.mark.asyncio
async def test_initialization(base_config):
    """Test standard initialization."""
    agent = TestElementalAgent(**base_config)
    assert agent.element == "fire"
    assert agent.prana == 100.0
    assert agent.tattva_layer == 34
    assert agent.get_dominant_guna() == "rajas"


@pytest.mark.asyncio
async def test_guna_validation_error():
    """Test that invalid Guna sums raise ValueError."""
    with pytest.raises(ValueError, match="sum to 1.0"):
        TestElementalAgent(
            agent_name="BadMath",
            element="air",
            tattva_layer=33,
            guna_balance={"sattva": 0.5, "rajas": 0.5, "tamas": 0.5},  # Sums to 1.5
        )


@pytest.mark.asyncio
async def test_prana_consumption(base_config):
    """Test prana consumption logic."""
    agent = TestElementalAgent(**base_config)

    # Initial state
    assert agent.prana == 100.0

    # Consume default amount (5.0)
    success = await agent.consume_prana()
    assert success is True
    assert agent.prana == 95.0

    # Consume specific amount
    success = await agent.consume_prana(20.0)
    assert success is True
    assert agent.prana == 75.0


@pytest.mark.asyncio
async def test_prana_depletion(base_config):
    """Test that agent reports depletion when prana < 10."""
    agent = TestElementalAgent(**base_config)

    # Drain prana manually to 12
    agent.prana = 12.0
    assert await agent.consume_prana(1.0) is True  # Now 11.0

    agent.prana = 9.0
    success = await agent.consume_prana(1.0)
    assert success is False
    assert agent.prana == 9.0  # Should not decrease when blocked


@pytest.mark.asyncio
async def test_prana_regeneration(base_config):
    """Test prana regeneration."""
    agent = TestElementalAgent(**base_config)
    agent.prana = 50.0

    # Rest for 1 hour (3600s) -> +20 prana
    await agent.regenerate_prana(3601)
    assert agent.prana > 69.0  # approx 70

    # Cap at max
    await agent.regenerate_prana(36000)  # 10 hours
    assert agent.prana == 100.0


@pytest.mark.asyncio
async def test_system_identity_registration(base_config):
    """Test interaction with SystemIdentity."""
    mock_identity = MagicMock()

    agent = TestElementalAgent(**base_config, system_identity=mock_identity)

    # Verify registration call
    mock_identity.register_elemental_agent.assert_called_once_with(
        tattva_id=34, agent_id="TestFire", element="fire"
    )


@pytest.mark.asyncio
async def test_analyze_bridge(base_config):
    """Test that analyze() correctly bridges to process_signal()."""
    agent = TestElementalAgent(**base_config)
    result = await agent.analyze({"data": 123}, {"context": "test"})
    assert result["processed"] is True
    assert result["signal"]["data"] == 123
    assert result["signal"]["context"] == "test"


@pytest.mark.asyncio
async def test_health_check_extension(base_config):
    """Test that health check includes elemental metrics."""
    agent = TestElementalAgent(**base_config)
    health = agent.elemental_health_check()

    assert "element" in health
    assert "prana" in health
    assert health["guna_balance"]["sattva"] == 0.4
    assert health["element"] == "fire"
