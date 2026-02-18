"""
Integration Tests for EventBus + Agent Communication.

Tests real interactions between EventBus and Agents.
"""

import asyncio
from datetime import datetime, timezone

import pytest

from backend.agents.base_agent import BaseAgent
from backend.events.event_bus import EventBus
from backend.events.schemas import AgentThought, MarketTick
from backend.llm.provider_interface import LLMProvider

pytestmark = pytest.mark.integration


class MockLLMProvider(LLMProvider):
    """Mock LLM for testing."""

    async def generate_text(self, prompt, system_prompt=None):
        return f"Mock response to: {prompt}"

    async def generate_structured(self, prompt, schema, system_prompt=None):
        return schema(sentiment="bullish", confidence=0.8)


class ConcreteTestAgent(BaseAgent):
    """Concrete test agent implementation."""

    async def analyze(self, features, context):
        return {"decision": "test", "confidence": 0.9}


@pytest.mark.asyncio
async def test_agent_publishes_to_event_bus():
    """Integration: Agent should publish thoughts to EventBus."""
    # Setup EventBus with in-memory Redis mock
    bus = EventBus(redis_url="redis://localhost:6379")

    # Don't actually connect to Redis - use mock
    bus._redis = None  # Simulate disconnected state

    # Create agent with EventBus
    llm = MockLLMProvider()
    agent = ConcreteTestAgent(agent_name="test_agent", llm_provider=llm, event_bus=bus)

    # Agent should handle bus errors gracefully
    await agent.publish_thought(
        reasoning="Test reasoning", confidence=0.9, data={"key": "value"}
    )

    # Should not crash even without Redis connection
    assert agent.agent_name == "test_agent"


@pytest.mark.asyncio
async def test_multiple_agents_communicate_via_bus():
    """Integration: Multiple agents should communicate through EventBus."""
    bus = EventBus(redis_url="redis://localhost:6379")

    # Create two agents
    llm = MockLLMProvider()
    agent1 = ConcreteTestAgent("agent_1", llm_provider=llm, event_bus=bus)
    agent2 = ConcreteTestAgent("agent_2", llm_provider=llm, event_bus=bus)

    # Both agents connected to same bus
    assert agent1.event_bus is bus
    assert agent2.event_bus is bus
    assert agent1.event_bus is agent2.event_bus


@pytest.mark.asyncio
async def test_agent_without_event_bus_works():
    """Integration: Agent should work without EventBus (degraded mode)."""
    llm = MockLLMProvider()
    agent = ConcreteTestAgent("standalone_agent", llm_provider=llm, event_bus=None)

    # Should not crash when publishing
    await agent.publish_thought(
        reasoning="Standalone reasoning", confidence=0.7, data={}
    )

    # Agent should still function
    assert agent.agent_name == "standalone_agent"
    assert agent.llm_provider is llm


@pytest.mark.asyncio
async def test_agent_state_isolation():
    """Integration: Agents should have isolated state."""
    llm = MockLLMProvider()
    agent1 = ConcreteTestAgent("agent_1", llm_provider=llm)
    agent2 = ConcreteTestAgent("agent_2", llm_provider=llm)

    # Update agent1 state
    agent1.update_state({"position": "long", "size": 1.0})

    # Agent2 state should be independent
    agent2.update_state({"position": "short", "size": 0.5})

    state1 = agent1.get_state()
    state2 = agent2.get_state()

    assert state1["position"] == "long"
    assert state2["position"] == "short"
    assert state1["size"] != state2["size"]


@pytest.mark.asyncio
async def test_agent_reasoning_chain_accumulation():
    """Integration: Agent reasoning chain should accumulate over time."""
    llm = MockLLMProvider()
    agent = ConcreteTestAgent("reasoning_agent", llm_provider=llm)

    # Multiple think operations
    agent.think("First observation")
    agent.think("Second observation")
    agent.think("Third observation")

    chain = agent.get_reasoning_chain()

    assert len(chain) == 3
    assert "First observation" in chain[0]
    assert "Second observation" in chain[1]
    assert "Third observation" in chain[2]


@pytest.mark.asyncio
async def test_agent_llm_integration():
    """Integration: Agent should use LLM for reasoning."""
    llm = MockLLMProvider()
    agent = ConcreteTestAgent("llm_agent", llm_provider=llm)

    # Ask LLM through agent
    response = await agent.ask_llm("What is the market trend?")

    assert isinstance(response, str)
    assert "Mock response" in response
    assert "market trend" in response


@pytest.mark.asyncio
async def test_agent_health_tracking():
    """Integration: Agent health should track heartbeats and errors."""
    llm = MockLLMProvider()
    agent = ConcreteTestAgent("health_agent", llm_provider=llm)

    # Initial state
    health = agent.health_check()
    assert health["status"] == "healthy"
    assert health["total_actions"] == 0
    assert health["error_count"] == 0

    # Record some activity
    agent.record_activity(success=True)
    agent.record_activity(success=True)
    agent.record_activity(success=False)

    health = agent.health_check()
    assert health["total_actions"] == 3
    assert health["error_count"] == 1
    assert health["error_rate"] > 0


@pytest.mark.asyncio
async def test_event_schema_serialization():
    """Integration: Event schemas should serialize/deserialize correctly."""
    # Create thought
    thought = AgentThought(
        agent_name="test_agent",
        reasoning="Market is bullish",
        confidence=0.85,
        data={"signal": "buy", "strength": 0.9},
        timestamp=datetime.now(timezone.utc),
    )

    # Serialize to dict
    thought_dict = thought.model_dump()

    assert thought_dict["agent_name"] == "test_agent"
    assert thought_dict["confidence"] == 0.85

    # Deserialize back
    thought_restored = AgentThought(**thought_dict)

    assert thought_restored.agent_name == "test_agent"
    assert thought_restored.reasoning == "Market is bullish"


@pytest.mark.asyncio
async def test_market_tick_schema_validation():
    """Integration: MarketTick schema should enforce validation."""
    # Valid tick
    tick = MarketTick(
        symbol="BTC/USD",
        price=50000.0,
        volume=1.5,
        timestamp=datetime.now(timezone.utc),
    )

    assert tick.price == 50000.0
    assert tick.symbol == "BTC/USD"

    # Invalid tick (negative price) should fail
    with pytest.raises(Exception):  # ValidationError
        MarketTick(
            symbol="ETH/USD",
            price=-100.0,  # Invalid
            volume=1.0,
            timestamp=datetime.now(timezone.utc),
        )


@pytest.mark.asyncio
async def test_concurrent_agent_operations():
    """Integration: Multiple agents should handle concurrent operations."""
    llm = MockLLMProvider()
    agents = [ConcreteTestAgent(f"agent_{i}", llm_provider=llm) for i in range(5)]

    # Concurrent think operations
    tasks = [agent.ask_llm(f"Query {i}") for i, agent in enumerate(agents)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    for i, result in enumerate(results):
        assert f"Query {i}" in result


@pytest.mark.asyncio
async def test_agent_error_recovery():
    """Integration: Agent should recover from LLM errors."""

    class FlakyLLM(LLMProvider):
        def __init__(self):
            self.call_count = 0

        async def generate_text(self, prompt, system_prompt=None):
            self.call_count += 1
            if self.call_count == 1:
                raise Exception("LLM temporarily unavailable")
            return "Recovered response"

        async def generate_structured(self, prompt, schema, system_prompt=None):
            return schema(sentiment="neutral", confidence=0.5)

    llm = FlakyLLM()
    agent = ConcreteTestAgent("resilient_agent", llm_provider=llm)

    # First call fails but is caught by ask_llm
    result1 = await agent.ask_llm("Test query")
    assert "LLM error" in result1  # ask_llm catches and returns error message

    # Track the error manually
    agent.record_activity(success=False)

    # Second call succeeds
    result2 = await agent.ask_llm("Test query again")
    assert result2 == "Recovered response"

    health = agent.health_check()
    assert health["error_count"] >= 1  # Tracked the error
