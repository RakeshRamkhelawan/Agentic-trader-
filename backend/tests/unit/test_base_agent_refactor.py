"""
Tests for Refactored BaseAgent with Dependency Injection.

TDD Test Suite - Write tests FIRST before refactoring.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.base_agent import BaseAgent
from backend.events.event_bus import EventBus
from backend.events.schemas import AgentThought
from backend.llm.provider_interface import LLMProvider


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""
    
    async def analyze(self, features: dict, context: dict) -> dict:
        """Test implementation."""
        return {"action": "test", "confidence": 0.9}


@pytest.mark.unit
def test_base_agent_accepts_llm_provider():
    """RED: BaseAgent should accept LLMProvider via dependency injection."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_bus = MagicMock(spec=EventBus)
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        llm_provider=mock_provider,
        event_bus=mock_bus
    )
    
    assert agent.llm_provider is mock_provider
    assert agent.event_bus is mock_bus


@pytest.mark.unit
def test_base_agent_works_without_dependencies():
    """RED: BaseAgent should work without optional dependencies."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    assert agent.agent_name == "TestAgent"
    assert agent.llm_provider is None
    assert agent.event_bus is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_publishes_thoughts():
    """RED: BaseAgent should publish thoughts to event bus."""
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(return_value="msg-123")
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        event_bus=mock_bus
    )
    
    # Agent should publish thought
    await agent.publish_thought(
        reasoning="Test reasoning",
        confidence=0.85,
        data={"key": "value"}
    )
    
    # Verify publish was called
    mock_bus.publish.assert_called_once()
    call_args = mock_bus.publish.call_args
    assert call_args[0][0] == "agent_thoughts"  # Stream name
    
    # Verify event structure
    event_data = call_args[0][1]
    assert event_data["agent_name"] == "TestAgent"
    assert event_data["reasoning"] == "Test reasoning"
    assert event_data["confidence"] == "0.85"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_uses_llm_for_reasoning():
    """RED: BaseAgent should use LLM provider for reasoning."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_text = AsyncMock(return_value="LLM generated reasoning")
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        llm_provider=mock_provider
    )
    
    result = await agent.ask_llm(prompt="Why is the market bullish?")
    
    assert result == "LLM generated reasoning"
    mock_provider.generate_text.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_handles_missing_llm():
    """RED: BaseAgent should handle missing LLM gracefully."""
    agent = ConcreteAgent(agent_name="TestAgent")  # No LLM provider
    
    result = await agent.ask_llm(prompt="Test prompt")
    
    # Should return fallback message
    assert "not available" in result.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_skips_publish_if_no_bus():
    """RED: BaseAgent should skip publishing if event bus not provided."""
    agent = ConcreteAgent(agent_name="TestAgent")  # No event bus
    
    # Should not raise error
    await agent.publish_thought(
        reasoning="Test",
        confidence=0.9,
        data={}
    )


@pytest.mark.unit
def test_base_agent_maintains_backward_compatibility():
    """RED: Refactored BaseAgent should maintain existing interface."""
    agent = ConcreteAgent(agent_name="TestAgent")
    
    # Old interface methods should still work
    assert hasattr(agent, "think")
    assert hasattr(agent, "act")
    assert hasattr(agent, "get_reasoning_chain")
    assert hasattr(agent, "update_state")
    assert hasattr(agent, "get_state")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_agent_health_check():
    """RED: BaseAgent health check should work with new dependencies."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_bus = MagicMock(spec=EventBus)
    
    agent = ConcreteAgent(
        agent_name="TestAgent",
        llm_provider=mock_provider,
        event_bus=mock_bus
    )
    
    agent.heartbeat()
    health = agent.health_check()
    
    assert health["status"] == "healthy"
    assert health["agent_name"] == "TestAgent"


@pytest.mark.unit
def test_base_agent_stores_agent_name():
    """RED: BaseAgent should store agent_name for event identification."""
    agent = ConcreteAgent(agent_name="SentimentAnalyzer")
    
    assert agent.agent_name == "SentimentAnalyzer"
