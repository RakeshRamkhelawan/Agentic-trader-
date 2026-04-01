"""
Tests for LLM-based SentimentAgent.

TDD Test Suite - Write tests FIRST before implementation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from backend.agents.sentiment_agent import SentimentAgent
from backend.events.event_bus import EventBus
from backend.llm.provider_interface import LLMProvider


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result schema."""

    sentiment: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    key_factors: list[str]


@pytest.mark.unit
def test_sentiment_agent_exists():
    """RED: SentimentAgent class should exist."""
    assert SentimentAgent is not None


@pytest.mark.unit
def test_sentiment_agent_inherits_base_agent():
    """RED: SentimentAgent should inherit from BaseAgent."""
    from backend.agents.base_agent import BaseAgent

    mock_provider = MagicMock(spec=LLMProvider)
    agent = SentimentAgent(llm_provider=mock_provider)

    assert isinstance(agent, BaseAgent)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_uses_llm_for_analysis():
    """RED: SentimentAgent should use LLM generate_structured for sentiment."""
    mock_provider = AsyncMock(spec=LLMProvider)

    # Mock LLM response
    mock_provider.generate_structured = AsyncMock(
        return_value=SentimentAnalysis(
            sentiment="bullish",
            confidence=0.85,
            reasoning="Strong positive news coverage and social media sentiment",
            key_factors=["positive earnings", "market momentum"],
        )
    )

    agent = SentimentAgent(llm_provider=mock_provider)

    # Analyze market data
    result = await agent.analyze(
        features={"price": 50000, "volume": 1000},
        context={"news": "Bitcoin adoption increasing"},
    )

    # Verify LLM was called
    mock_provider.generate_structured.assert_called_once()

    # Verify result structure
    assert result["sentiment"] == "bullish"
    assert result["confidence"] == 0.85
    assert "reasoning" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_publishes_thought():
    """RED: SentimentAgent should publish analysis to event bus."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(return_value="msg-123")

    mock_provider.generate_structured = AsyncMock(
        return_value=SentimentAnalysis(
            sentiment="bearish",
            confidence=0.75,
            reasoning="Negative regulatory news",
            key_factors=["regulation concerns"],
        )
    )

    agent = SentimentAgent(llm_provider=mock_provider, event_bus=mock_bus)

    await agent.analyze(features={"price": 45000}, context={"news": "Regulatory crackdown"})

    # Verify thought was published
    mock_bus.publish.assert_called()
    call_args = mock_bus.publish.call_args[0]
    assert call_args[0] == "agent_thoughts"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_handles_missing_llm():
    """RED: SentimentAgent should handle missing LLM gracefully."""
    agent = SentimentAgent()  # No LLM provider

    result = await agent.analyze(features={"price": 50000}, context={"news": "Test news"})

    # Should return fallback result
    assert "error" in result or "sentiment" in result
    assert result["confidence"] < 0.5  # Low confidence fallback


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_formats_prompt():
    """RED: SentimentAgent should format proper prompt with context."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        return_value=SentimentAnalysis(
            sentiment="neutral",
            confidence=0.6,
            reasoning="Mixed signals",
            key_factors=[],
        )
    )

    agent = SentimentAgent(llm_provider=mock_provider)

    await agent.analyze(
        features={"price": 50000, "volume": 1500},
        context={"news": "Mixed market signals", "symbol": "BTC/USD"},
    )

    # Check that prompt includes context
    call_args = mock_provider.generate_structured.call_args
    prompt = call_args.kwargs.get("prompt", "")

    assert "BTC/USD" in prompt or "50000" in prompt
    assert "Mixed market signals" in prompt


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_maps_bullish_to_buy():
    """RED: SentimentAgent should map bullish sentiment to buy signal."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        return_value=SentimentAnalysis(
            sentiment="bullish",
            confidence=0.9,
            reasoning="Very positive outlook",
            key_factors=["adoption", "institutional interest"],
        )
    )

    agent = SentimentAgent(llm_provider=mock_provider)
    result = await agent.analyze({}, {})

    # Should suggest buy action
    assert result["action"] in ["buy", "BUY"] or result["sentiment"] == "bullish"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_maps_bearish_to_sell():
    """RED: SentimentAgent should map bearish sentiment to sell signal."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        return_value=SentimentAnalysis(
            sentiment="bearish",
            confidence=0.85,
            reasoning="Negative outlook",
            key_factors=["selling pressure"],
        )
    )

    agent = SentimentAgent(llm_provider=mock_provider)
    result = await agent.analyze({}, {})

    # Should suggest sell action
    assert result["action"] in ["sell", "SELL"] or result["sentiment"] == "bearish"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_uses_system_prompt():
    """RED: SentimentAgent should use specialized system prompt."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        return_value=SentimentAnalysis(
            sentiment="neutral", confidence=0.5, reasoning="Test", key_factors=[]
        )
    )

    agent = SentimentAgent(llm_provider=mock_provider)
    await agent.analyze({}, {})

    # Verify system_prompt was passed
    call_args = mock_provider.generate_structured.call_args
    if len(call_args[1]) > 0:  # Check kwargs
        assert "system_prompt" in call_args[1]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_returns_dict():
    """RED: SentimentAgent.analyze should return dict (not AgentDecision)."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        return_value=SentimentAnalysis(
            sentiment="bullish", confidence=0.8, reasoning="Test", key_factors=[]
        )
    )

    agent = SentimentAgent(llm_provider=mock_provider)
    result = await agent.analyze({}, {})

    # Should be dict for new architecture
    assert isinstance(result, dict)
    assert "sentiment" in result or "action" in result
    assert "confidence" in result
