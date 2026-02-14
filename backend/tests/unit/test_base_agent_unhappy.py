"""
Unhappy Path Tests for BaseAgent Refactor.

Tests error handling, edge cases, and failure scenarios.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.base_agent import BaseAgent
from backend.events.event_bus import EventBus
from backend.llm.provider_interface import LLMProvider


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""
    
    async def analyze(self, features: dict, context: dict) -> dict:
        """Test implementation."""
        return {"action": "test", "confidence": 0.9}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_ask_llm_provider_error():
    """Unhappy: LLM provider raising error should be handled."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_text = AsyncMock(side_effect=Exception("LLM API Error"))
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        llm_provider=mock_provider
    )
    
    result = await agent.ask_llm("Test prompt")
    
    # Should return error message, not raise
    assert "error" in result.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_ask_llm_timeout():
    """Unhappy: LLM timeout should be handled gracefully."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_text = AsyncMock(side_effect=TimeoutError("Request timeout"))
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        llm_provider=mock_provider
    )
    
    result = await agent.ask_llm("Test prompt")
    
    assert "error" in result.lower() or "timeout" in result.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_publish_thought_bus_error():
    """Unhappy: Event bus publish error should be handled."""
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(side_effect=Exception("Redis connection lost"))
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        event_bus=mock_bus
    )
    
    # Should not raise, returns None on error
    result = await agent.publish_thought(
        reasoning="Test",
        confidence=0.8,
        data={}
    )
    
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_publish_thought_invalid_confidence():
    """Unhappy: Invalid confidence value should still attempt publish."""
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(return_value="msg-123")
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        event_bus=mock_bus
    )
    
    # Should convert to string and publish anyway
    await agent.publish_thought(
        reasoning="Test",
        confidence=999.9,  # Invalid but agent doesn't validate
        data={}
    )
    
    mock_bus.publish.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_health_check_no_heartbeat():
    """Unhappy: Agent with stale heartbeat should report unhealthy."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    # Set old heartbeat (> 60 seconds ago)
    import time
    agent.last_heartbeat = time.time() - 120
    
    health = agent.health_check()
    
    assert health["status"] == "unhealthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_health_check_high_error_rate():
    """Unhappy: Agent with many failures should show high error rate."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    # Simulate many failures
    agent.processed_events = 100
    agent.failed_events = 75
    agent.heartbeat()
    
    health = agent.health_check()
    
    assert health["error_rate"] == 0.75
    assert health["status"] == "healthy"  # Still healthy if recent heartbeat


@pytest.mark.unit
def test_base_agent_think_empty_observation():
    """Edge: Empty observation should still work."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    thought = agent.think("")
    
    assert thought == "[THINK] "
    assert len(agent.reasoning_history) == 1


@pytest.mark.unit
def test_base_agent_act_empty_rationale():
    """Edge: Empty rationale should still work."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    action = agent.act("test_action", "")
    
    assert action["action"] == "test_action"
    assert action["rationale"] == ""


@pytest.mark.unit
def test_base_agent_update_state_overwrite():
    """Edge: Updating same key should overwrite."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    agent.update_state("key", "value1")
    agent.update_state("key", "value2")
    
    state = agent.get_state()
    assert state["key"] == "value2"


@pytest.mark.unit
def test_base_agent_get_state_is_copy():
    """Edge: get_state should return a copy, not reference."""
    agent = ConcreteAgent(agent_name="TestAgent")
    agent.update_state("key", "value")
    
    state1 = agent.get_state()
    state1["modified"] = "externally"
    state2 = agent.get_state()
    
    assert "modified" not in state2


@pytest.mark.unit
def test_base_agent_get_reasoning_chain_is_copy():
    """Edge: get_reasoning_chain should return copy."""
    agent = ConcreteAgent(agent_name="TestAgent")
    agent.think("observation")
    
    chain1 = agent.get_reasoning_chain()
    chain1.append({"fake": "entry"})
    chain2 = agent.get_reasoning_chain()
    
    assert len(chain2) == 1  # Should not include fake entry


@pytest.mark.unit
def test_base_agent_record_activity_multiple_failures():
    """Edge: Recording multiple failures should accumulate."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    agent.record_activity(success=True)
    agent.record_activity(success=False)
    agent.record_activity(success=False)
    agent.record_activity(success=True)
    
    assert agent.processed_events == 4
    assert agent.failed_events == 2


@pytest.mark.unit
def test_base_agent_heartbeat_updates_timestamp():
    """Edge: Heartbeat should update timestamp."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    import time
    old_heartbeat = agent.last_heartbeat
    time.sleep(0.01)
    agent.heartbeat()
    
    assert agent.last_heartbeat > old_heartbeat


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_ask_llm_empty_prompt():
    """Edge: Empty prompt should still call LLM."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_text = AsyncMock(return_value="Empty prompt response")
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        llm_provider=mock_provider
    )
    
    result = await agent.ask_llm("")
    
    assert result == "Empty prompt response"
    mock_provider.generate_text.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_publish_thought_empty_data():
    """Edge: Empty data dict should still publish."""
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(return_value="msg-123")
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        event_bus=mock_bus
    )
    
    result = await agent.publish_thought(
        reasoning="Test",
        confidence=0.8,
        data={}
    )
    
    assert result == "msg-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_publish_thought_complex_data():
    """Edge: Complex nested data should be converted to string."""
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(return_value="msg-123")
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        event_bus=mock_bus
    )
    
    complex_data = {
        "nested": {"deeply": {"value": 123}},
        "list": [1, 2, 3],
        "mixed": {"a": [{"b": "c"}]}
    }
    
    result = await agent.publish_thought(
        reasoning="Test",
        confidence=0.8,
        data=complex_data
    )
    
    assert result == "msg-123"
    # Verify data was stringified in publish call
    call_args = mock_bus.publish.call_args[0][1]
    assert "data" in call_args
    assert isinstance(call_args["data"], str)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_ask_llm_with_system_prompt():
    """Edge: System prompt should be passed through."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_text = AsyncMock(return_value="Response")
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        llm_provider=mock_provider
    )
    
    await agent.ask_llm("Prompt", system_prompt="You are an expert")
    
    # Verify system_prompt was passed
    call_args = mock_provider.generate_text.call_args
    assert call_args[0][0] == "Prompt"
    assert call_args[0][1] == "You are an expert"


@pytest.mark.unit
def test_base_agent_reasoning_history_preserves_order():
    """Edge: Reasoning history should maintain chronological order."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    agent.think("First observation")
    agent.act("Action 1", "Rationale 1")
    agent.think("Second observation")
    agent.act("Action 2", "Rationale 2")
    
    chain = agent.get_reasoning_chain()
    
    assert len(chain) == 4
    assert "[THINK]" in chain[0] and "First observation" in chain[0]
    assert "[ACT]" in chain[1] and "Action 1" in chain[1]
    assert "[THINK]" in chain[2] and "Second observation" in chain[2]
    assert "[ACT]" in chain[3] and "Action 2" in chain[3]
