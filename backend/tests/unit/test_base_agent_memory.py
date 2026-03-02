"""
Unit tests for BaseAgent memory safety (deque with maxlen).
"""

import sys
from collections import deque
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.base_agent import BaseAgent, DEFAULT_MAX_HISTORY
from backend.governance.agent_gatekeeper import AgentRole


class MockAgent(BaseAgent):
    """Mock implementation of BaseAgent for testing."""

    async def analyze(self, features, context):
        return {"action": "hold", "confidence": 0.5}


@pytest.fixture
def base_agent():
    """Create a BaseAgent with default settings."""
    return MockAgent(
        agent_name="test_agent",
        agent_role=AgentRole.TRUSTED,
    )


@pytest.fixture
def agent_with_small_buffer():
    """Create a BaseAgent with small buffer for testing."""
    return MockAgent(
        agent_name="test_agent_small",
        agent_role=AgentRole.TRUSTED,
        max_reasoning_history=10,
        max_event_buffer=5,
    )


class TestBaseAgentInitialization:
    """Test cases for BaseAgent initialization."""

    def test_reasoning_history_is_deque(self, base_agent):
        """Test that reasoning_history is a deque."""
        assert isinstance(base_agent.reasoning_history, deque)

    def test_reasoning_history_has_maxlen(self, base_agent):
        """Test that reasoning_history has maxlen attribute."""
        assert base_agent.reasoning_history.maxlen == DEFAULT_MAX_HISTORY

    def test_event_buffer_is_deque(self, base_agent):
        """Test that event_buffer is a deque."""
        assert isinstance(base_agent._event_buffer, deque)

    def test_custom_maxlen(self, agent_with_small_buffer):
        """Test that custom maxlen is respected."""
        assert agent_with_small_buffer.reasoning_history.maxlen == 10
        assert agent_with_small_buffer._event_buffer.maxlen == 5

    def test_initial_state_empty(self, base_agent):
        """Test that initial state is empty."""
        assert len(base_agent.reasoning_history) == 0
        assert len(base_agent._event_buffer) == 0


class TestBaseAgentThink:
    """Test cases for think() method."""

    def test_think_adds_to_history(self, base_agent):
        """Test that think() adds entry to history."""
        base_agent.think("BTC is bullish")

        assert len(base_agent.reasoning_history) == 1
        entry = base_agent.reasoning_history[0]
        assert entry["type"] == "think"
        assert entry["content"] == "BTC is bullish"

    def test_think_includes_timestamp(self, base_agent):
        """Test that think() includes timestamp."""
        base_agent.think("Test observation")

        entry = base_agent.reasoning_history[0]
        assert "timestamp" in entry
        assert isinstance(entry["timestamp"], datetime)

    def test_think_returns_formatted_string(self, base_agent):
        """Test that think() returns formatted string."""
        result = base_agent.think("Test observation")

        assert result == "[THINK] Test observation"


class TestBaseAgentAct:
    """Test cases for act() method."""

    def test_act_adds_to_history(self, base_agent):
        """Test that act() adds entry to history."""
        result = base_agent.act("buy", "Strong momentum")

        assert len(base_agent.reasoning_history) == 1
        entry = base_agent.reasoning_history[0]
        assert entry["type"] == "act"
        assert entry["action"] == "buy"
        assert entry["rationale"] == "Strong momentum"

    def test_act_returns_record(self, base_agent):
        """Test that act() returns action record."""
        result = base_agent.act("sell", "Profit taking")

        assert result["type"] == "act"
        assert result["action"] == "sell"
        assert result["rationale"] == "Profit taking"


class TestBaseAgentMemoryBounds:
    """Test cases for memory bounds (critical P0 fix)."""

    def test_reasoning_history_does_not_exceed_maxlen(self, agent_with_small_buffer):
        """Test that reasoning_history respects maxlen (P0 fix)."""
        max_len = agent_with_small_buffer._max_reasoning_history

        # Add more entries than maxlen
        for i in range(max_len + 20):
            agent_with_small_buffer.think(f"Observation {i}")

        # Should be bounded by maxlen
        assert len(agent_with_small_buffer.reasoning_history) == max_len

    def test_oldest_entries_removed_first(self, agent_with_small_buffer):
        """Test that oldest entries are removed when maxlen reached."""
        # Add entries
        for i in range(15):
            agent_with_small_buffer.think(f"Observation {i}")

        # First 5 should be removed (15 - 10 = 5)
        contents = [e["content"] for e in agent_with_small_buffer.reasoning_history]
        assert "Observation 0" not in contents
        assert "Observation 4" not in contents
        assert "Observation 5" in contents
        assert "Observation 14" in contents

    def test_event_buffer_does_not_exceed_maxlen(self, agent_with_small_buffer):
        """Test that event buffer respects maxlen."""
        max_len = agent_with_small_buffer._max_event_buffer

        # Add more events than maxlen
        for i in range(max_len + 10):
            agent_with_small_buffer.buffer_event({"id": i})

        assert len(agent_with_small_buffer._event_buffer) == max_len

    def test_buffer_full_returns_false(self, agent_with_small_buffer):
        """Test that buffer_event returns False when full."""
        max_len = agent_with_small_buffer._max_event_buffer

        # Fill buffer
        for i in range(max_len):
            result = agent_with_small_buffer.buffer_event({"id": i})
            assert result is True

        # Next should fail
        result = agent_with_small_buffer.buffer_event({"id": "overflow"})
        assert result is False


class TestBaseAgentGetReasoningChain:
    """Test cases for get_reasoning_chain() method."""

    def test_get_reasoning_chain_format(self, base_agent):
        """Test formatting of reasoning chain."""
        base_agent.think("Market is up")
        base_agent.act("buy", "Momentum")

        chain = base_agent.get_reasoning_chain()

        assert len(chain) == 2
        assert chain[0] == "[THINK] Market is up"
        assert chain[1] == "[ACT] buy: Momentum"

    def test_get_reasoning_chain_with_limit(self, base_agent):
        """Test limit parameter."""
        for i in range(10):
            base_agent.think(f"Observation {i}")

        chain = base_agent.get_reasoning_chain(limit=3)

        assert len(chain) == 3
        assert "Observation 7" in chain[0]
        assert "Observation 9" in chain[2]

    def test_get_reasoning_chain_empty(self, base_agent):
        """Test empty reasoning chain."""
        chain = base_agent.get_reasoning_chain()

        assert chain == []


class TestBaseAgentClearHistory:
    """Test cases for clear_reasoning_history() method."""

    def test_clear_history(self, base_agent):
        """Test clearing reasoning history."""
        for i in range(10):
            base_agent.think(f"Observation {i}")

        assert len(base_agent.reasoning_history) == 10

        cleared = base_agent.clear_reasoning_history()

        assert cleared == 10
        assert len(base_agent.reasoning_history) == 0

    def test_clear_empty_history(self, base_agent):
        """Test clearing empty history."""
        cleared = base_agent.clear_reasoning_history()

        assert cleared == 0


class TestBaseAgentGetBufferedEvents:
    """Test cases for get_buffered_events() method."""

    def test_get_buffered_events(self, base_agent):
        """Test retrieving buffered events."""
        base_agent.buffer_event({"id": 1})
        base_agent.buffer_event({"id": 2})

        events = base_agent.get_buffered_events(clear=False)

        assert len(events) == 2
        assert events[0]["id"] == 1

    def test_get_buffered_events_clears_buffer(self, base_agent):
        """Test that get_buffered_events clears buffer by default."""
        base_agent.buffer_event({"id": 1})

        events = base_agent.get_buffered_events(clear=True)

        assert len(events) == 1
        assert len(base_agent._event_buffer) == 0

    def test_get_buffered_events_without_clear(self, base_agent):
        """Test retrieving without clearing."""
        base_agent.buffer_event({"id": 1})

        events = base_agent.get_buffered_events(clear=False)

        assert len(events) == 1
        assert len(base_agent._event_buffer) == 1


class TestBaseAgentHealthCheck:
    """Test cases for health_check() method."""

    def test_health_check_includes_memory_stats(self, base_agent):
        """Test that health check includes memory statistics."""
        base_agent.think("Test")
        base_agent.buffer_event({"test": "data"})

        health = base_agent.health_check()

        assert "memory" in health
        assert health["memory"]["reasoning_history_size"] == 1
        assert health["memory"]["event_buffer_size"] == 1

    def test_health_check_tracks_peak_size(self, base_agent):
        """Test that health check tracks peak history size."""
        for i in range(5):
            base_agent.think(f"Observation {i}")

        health = base_agent.health_check()

        assert health["memory"]["peak_size"] == 5

    def test_health_check_alive_status(self, base_agent):
        """Test health check alive status."""
        import time

        # Agent should be healthy
        health = base_agent.health_check()
        assert health["status"] == "healthy"

        # Simulate stale heartbeat
        base_agent.last_heartbeat = time.time() - 120  # 2 minutes ago
        health = base_agent.health_check()
        assert health["status"] == "unhealthy"


class TestBaseAgentGetMemoryStats:
    """Test cases for get_memory_stats() method."""

    def test_get_memory_stats(self, base_agent):
        """Test getting detailed memory statistics."""
        for i in range(50):
            base_agent.think(f"Observation {i}")

        for i in range(10):
            base_agent.buffer_event({"id": i})

        stats = base_agent.get_memory_stats()

        assert stats["reasoning_history"]["current"] == 50
        assert stats["reasoning_history"]["max"] == DEFAULT_MAX_HISTORY
        assert stats["reasoning_history"]["utilization"] == 50 / DEFAULT_MAX_HISTORY

        assert stats["event_buffer"]["current"] == 10
        assert stats["state"]["keys"] == 0


class TestBaseAgentState:
    """Test cases for state management."""

    def test_update_state_dict(self, base_agent):
        """Test updating state with dictionary."""
        base_agent.update_state({"key1": "value1", "key2": "value2"})

        assert base_agent.state["key1"] == "value1"
        assert base_agent.state["key2"] == "value2"

    def test_update_state_key_value(self, base_agent):
        """Test updating state with key-value pair."""
        base_agent.update_state("test_key", "test_value")

        assert base_agent.state["test_key"] == "test_value"

    def test_get_state_returns_copy(self, base_agent):
        """Test that get_state returns a copy."""
        base_agent.update_state("key", "value")

        state_copy = base_agent.get_state()
        state_copy["new_key"] = "new_value"

        # Original should not be modified
        assert "new_key" not in base_agent.state


class TestBaseAgentMemorySafetyIntegration:
    """Integration tests for memory safety."""

    def test_long_running_simulation(self, agent_with_small_buffer):
        """Simulate long-running trading session."""
        max_history = agent_with_small_buffer._max_reasoning_history

        # Simulate 10,000 ticks (way more than maxlen)
        for i in range(10000):
            agent_with_small_buffer.think(f"Tick {i} observation")
            if i % 10 == 0:
                agent_with_small_buffer.act("hold", "No action")

        # Memory should be bounded
        assert len(agent_with_small_buffer.reasoning_history) == max_history

        # Should still have recent entries
        contents = [e["content"] for e in agent_with_small_buffer.reasoning_history]
        assert any("Tick 999" in str(c) for c in contents)

    def test_memory_usage_stability(self, agent_with_small_buffer):
        """Test that memory usage doesn't grow unbounded."""
        import sys

        # Get initial size
        initial_size = sys.getsizeof(agent_with_small_buffer.reasoning_history)

        # Add many entries
        for i in range(1000):
            agent_with_small_buffer.think(f"Observation {i}")

        # Size should not grow significantly beyond initial
        final_size = sys.getsizeof(agent_with_small_buffer.reasoning_history)

        # Should be roughly same size (deque with maxlen)
        assert final_size < initial_size * 2  # Allow some growth but not unbounded
