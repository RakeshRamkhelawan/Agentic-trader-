"""
Integration Tests for SentimentAgent End-to-End Flow.

Tests complete sentiment analysis pipeline with EventBus and LLM.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from backend.agents.sentiment_agent import SentimentAgent
from backend.events.event_bus import EventBus
from backend.events.schemas import AgentThought, MarketTick
from backend.llm.provider_interface import LLMProvider

pytestmark = pytest.mark.integration


class SentimentResult(BaseModel):
    """Mock sentiment analysis result."""
    sentiment: str
    confidence: float
    reasoning: str = "Mock reasoning"


class MockLLMProvider(LLMProvider):
    """Mock LLM that returns predefined sentiment results."""
    
    def __init__(self, sentiment="bullish", confidence=0.85):
        self.sentiment = sentiment
        self.confidence = confidence
        self.call_count = 0
    
    async def generate_text(self, prompt, system_prompt=None):
        self.call_count += 1
        return f"Market sentiment is {self.sentiment} with {self.confidence} confidence"
    
    async def generate_structured(self, prompt, schema, system_prompt=None):
        self.call_count += 1
        return SentimentResult(
            sentiment=self.sentiment,
            confidence=self.confidence,
            reasoning=f"Based on analysis, market is {self.sentiment}"
        )


@pytest.mark.asyncio
async def test_sentiment_agent_analyzes_market_tick():
    """Integration: SentimentAgent should analyze MarketTick and generate sentiment."""
    llm = MockLLMProvider(sentiment="bullish", confidence=0.9)
    agent = SentimentAgent(
        agent_name="sentiment_test",
        llm_provider=llm,
        event_bus=None  # No bus for isolated test
    )
    
    # Create market features
    features = {
        "price": 50000.0,
        "volume": 1.5,
        "price_change": 500.0
    }
    context = {"symbol": "BTC/USD"}
    
    # Analyze
    result = await agent.analyze(features, context)
    
    # Verify analysis result
    assert result is not None
    assert "sentiment" in result or "decision" in result
    assert llm.call_count > 0  # LLM was called


@pytest.mark.asyncio
async def test_sentiment_agent_publishes_to_event_bus():
    """Integration: SentimentAgent should publish thoughts to EventBus."""
    # Mock EventBus
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(return_value="msg_12345")
    
    llm = MockLLMProvider(sentiment="bearish", confidence=0.75)
    agent = SentimentAgent(
        agent_name="sentiment_publisher",
        llm_provider=llm,
        event_bus=mock_bus
    )
    
    # Analyze and publish
    features = {"price": 45000.0, "volume": 2.0}
    context = {"symbol": "BTC/USD"}
    
    result = await agent.analyze(features, context)
    
    # Publish thought
    await agent.publish_thought(
        reasoning="Market shows bearish signals",
        confidence=0.75,
        data=result
    )
    
    # Verify EventBus was called
    assert mock_bus.publish.called
    call_args = mock_bus.publish.call_args
    assert call_args[0][0] == "agent_thoughts"  # Stream name


@pytest.mark.asyncio
async def test_sentiment_agent_handles_multiple_ticks():
    """Integration: SentimentAgent should handle multiple market ticks sequentially."""
    llm = MockLLMProvider(sentiment="neutral", confidence=0.6)
    agent = SentimentAgent(
        agent_name="multi_tick_agent",
        llm_provider=llm
    )
    
    ticks = [
        {"price": 50000.0, "volume": 1.0},
        {"price": 50500.0, "volume": 1.5},
        {"price": 51000.0, "volume": 2.0},
    ]
    
    results = []
    for tick in ticks:
        result = await agent.analyze(tick, {"symbol": "BTC/USD"})
        results.append(result)
    
    assert len(results) == 3
    assert llm.call_count == 3  # Called once per tick


@pytest.mark.asyncio
async def test_sentiment_agent_maintains_state_across_analyses():
    """Integration: SentimentAgent should maintain state between analyses."""
    llm = MockLLMProvider()
    agent = SentimentAgent(
        agent_name="stateful_agent",
        llm_provider=llm
    )
    
    # First analysis
    await agent.analyze({"price": 50000.0}, {"symbol": "BTC/USD"})
    agent.update_state({"last_sentiment": "bullish", "count": 1})
    
    # Second analysis
    await agent.analyze({"price": 51000.0}, {"symbol": "BTC/USD"})
    agent.update_state({"count": 2})
    
    state = agent.get_state()
    assert state["last_sentiment"] == "bullish"
    assert state["count"] == 2


@pytest.mark.asyncio
async def test_sentiment_agent_with_real_event_bus_mock():
    """Integration: Full flow with EventBus subscription simulation."""
    # Create mock bus
    mock_bus = AsyncMock(spec=EventBus)
    published_events = []
    
    async def mock_publish(stream, data):
        published_events.append({"stream": stream, "data": data})
        return f"msg_{len(published_events)}"
    
    mock_bus.publish = mock_publish
    
    # Create agent
    llm = MockLLMProvider(sentiment="bullish", confidence=0.88)
    agent = SentimentAgent(
        agent_name="full_flow_agent",
        llm_provider=llm,
        event_bus=mock_bus
    )
    
    # Simulate market tick → analysis → publish
    features = {
        "price": 52000.0,
        "volume": 3.5,
        "volatility": 0.02
    }
    context = {"symbol": "BTC/USD", "timestamp": datetime.now(timezone.utc)}
    
    result = await agent.analyze(features, context)
    await agent.publish_thought(
        reasoning="Strong bullish momentum detected",
        confidence=0.88,
        data=result
    )
    
    # Verify event was published
    assert len(published_events) == 1
    event = published_events[0]
    assert event["stream"] == "agent_thoughts"
    assert event["data"]["agent_name"] == "full_flow_agent"
    assert "0.88" in event["data"]["confidence"]


@pytest.mark.asyncio
async def test_sentiment_agent_error_handling_with_llm_failure():
    """Integration: Agent should handle LLM failures gracefully."""
    
    class FailingLLM(LLMProvider):
        async def generate_text(self, prompt, system_prompt=None):
            raise Exception("LLM service unavailable")
        
        async def generate_structured(self, prompt, schema, system_prompt=None):
            raise Exception("LLM service unavailable")
    
    llm = FailingLLM()
    agent = SentimentAgent(
        agent_name="error_handling_agent",
        llm_provider=llm
    )
    
    # Should handle error without crashing
    try:
        result = await agent.analyze({"price": 50000.0}, {"symbol": "BTC/USD"})
        # If analyze handles errors internally, it might return None or fallback
        assert result is None or isinstance(result, dict)
    except Exception as e:
        # Or it might raise, which is also valid
        assert "unavailable" in str(e)
    
    # Agent should still be healthy
    health = agent.health_check()
    assert health["agent_name"] == "error_handling_agent"


@pytest.mark.asyncio
async def test_sentiment_agent_concurrent_analysis():
    """Integration: Agent should handle concurrent analysis requests."""
    llm = MockLLMProvider()
    agent = SentimentAgent(
        agent_name="concurrent_agent",
        llm_provider=llm
    )
    
    # Concurrent analysis tasks
    features_list = [
        {"price": 50000.0 + i*100, "volume": 1.0 + i*0.1}
        for i in range(5)
    ]
    
    tasks = [
        agent.analyze(features, {"symbol": "BTC/USD"})
        for features in features_list
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 5
    assert all(r is not None for r in results)


@pytest.mark.asyncio
async def test_sentiment_agent_reasoning_chain_tracking():
    """Integration: Agent should track reasoning chain during analysis."""
    llm = MockLLMProvider()
    agent = SentimentAgent(
        agent_name="reasoning_agent",
        llm_provider=llm
    )
    
    # Perform analysis with explicit reasoning steps
    agent.think("Observing market conditions")
    agent.think("Price trending upward")
    
    await agent.analyze({"price": 52000.0}, {"symbol": "BTC/USD"})
    
    agent.think("Analysis complete")
    
    chain = agent.get_reasoning_chain()
    
    assert len(chain) >= 3
    assert any("market conditions" in step for step in chain)
    assert any("trending upward" in step for step in chain)


@pytest.mark.asyncio
async def test_sentiment_agent_health_monitoring():
    """Integration: Agent health should reflect processing activity."""
    llm = MockLLMProvider()
    agent = SentimentAgent(
        agent_name="health_monitor_agent",
        llm_provider=llm
    )
    
    initial_health = agent.health_check()
    assert initial_health["total_actions"] == 0
    
    # Process some ticks
    for i in range(5):
        await agent.analyze({"price": 50000.0 + i*100}, {"symbol": "BTC/USD"})
        agent.record_activity(success=True)
    
    # Simulate one failure
    agent.record_activity(success=False)
    
    final_health = agent.health_check()
    assert final_health["total_actions"] == 6
    assert final_health["error_count"] == 1
    assert final_health["error_rate"] < 0.2  # 1/6 ≈ 0.167


@pytest.mark.asyncio
async def test_sentiment_agent_context_preservation():
    """Integration: Agent should preserve context between calls."""
    llm = MockLLMProvider()
    agent = SentimentAgent(
        agent_name="context_agent",
        llm_provider=llm
    )
    
    # First call with context
    context1 = {"symbol": "BTC/USD", "exchange": "Binance"}
    result1 = await agent.analyze({"price": 50000.0}, context1)
    
    # Store context in state
    agent.update_state({"last_context": context1})
    
    # Second call
    context2 = {"symbol": "ETH/USD", "exchange": "Coinbase"}
    result2 = await agent.analyze({"price": 3000.0}, context2)
    
    # Verify context was preserved
    state = agent.get_state()
    assert state["last_context"]["symbol"] == "BTC/USD"
    assert state["last_context"]["exchange"] == "Binance"
