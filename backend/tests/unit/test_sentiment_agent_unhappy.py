"""
Unhappy Path Tests for SentimentAgent.

Tests error handling, edge cases, and failure scenarios for LLM-based sentiment analysis.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, ValidationError

from backend.agents.sentiment_agent import SentimentAgent, SentimentAnalysis
from backend.events.event_bus import EventBus
from backend.llm.provider_interface import LLMProvider


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_llm_timeout():
    """Unhappy: LLM timeout should return fallback result."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        side_effect=TimeoutError("LLM request timeout")
    )
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze(
        features={"price": 50000},
        context={"news": "Test"}
    )
    
    # Should return fallback with low confidence
    assert result["sentiment"] == "neutral"
    assert result["confidence"] < 0.5
    assert "error" in result["reasoning"].lower() or "timeout" in result["reasoning"].lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_llm_api_error():
    """Unhappy: LLM API error should be handled gracefully."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        side_effect=Exception("API rate limit exceeded")
    )
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    assert result["sentiment"] == "neutral"
    assert result["action"] == "hold"
    assert "error" in result["reasoning"].lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_invalid_llm_response():
    """Unhappy: Invalid LLM response structure should be handled."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "validation_error",
            [{"type": "missing", "loc": ("sentiment",), "msg": "Field required"}]
        )
    )
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    assert result["sentiment"] == "neutral"
    assert result["confidence"] < 0.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_empty_features():
    """Edge: Empty features dict should still work."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="neutral",
        confidence=0.5,
        reasoning="No data available",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze(features={}, context={})
    
    assert result["sentiment"] == "neutral"
    assert result["action"] == "hold"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_empty_context():
    """Edge: Empty context should still work."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="bullish",
        confidence=0.7,
        reasoning="Default analysis",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze(
        features={"price": 50000},
        context={}
    )
    
    assert result["sentiment"] == "bullish"
    assert result["action"] == "buy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_missing_symbol():
    """Edge: Missing symbol in context should use default."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="neutral",
        confidence=0.6,
        reasoning="Test",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze(
        features={},
        context={"news": "Some news"}
    )
    
    # Should not crash, uses "Unknown" as default
    assert "sentiment" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_malformed_news():
    """Edge: Malformed news data should be handled."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="neutral",
        confidence=0.5,
        reasoning="Test",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze(
        features={},
        context={"news": None}  # None instead of string
    )
    
    assert result is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_very_long_context():
    """Edge: Very long context should be handled."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="bearish",
        confidence=0.8,
        reasoning="Long context analysis",
        key_factors=["factor1"]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    # Create very long context
    long_news = "A" * 100000
    result = await agent.analyze(
        features={},
        context={"news": long_news}
    )
    
    assert result["sentiment"] == "bearish"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_unknown_sentiment_value():
    """Edge: Unknown sentiment value should map to hold."""
    mock_provider = AsyncMock(spec=LLMProvider)
    
    # Create analysis with non-standard sentiment
    class CustomSentiment(BaseModel):
        sentiment: str
        confidence: float
        reasoning: str
        key_factors: list[str]
    
    mock_provider.generate_structured = AsyncMock(return_value=CustomSentiment(
        sentiment="sideways",  # Not bullish/bearish/neutral
        confidence=0.7,
        reasoning="Market moving sideways",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    # Should default to hold for unknown sentiment
    assert result["action"] == "hold"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_zero_confidence():
    """Edge: Zero confidence should still work."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="neutral",
        confidence=0.0,
        reasoning="No confidence",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    assert result["confidence"] == 0.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_max_confidence():
    """Edge: Maximum confidence 1.0 should work."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="bullish",
        confidence=1.0,
        reasoning="100% certain",
        key_factors=["clear signal"]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    assert result["confidence"] == 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_empty_key_factors():
    """Edge: Empty key factors list should work."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="neutral",
        confidence=0.5,
        reasoning="No specific factors",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    assert result["key_factors"] == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_event_bus_publish_fails():
    """Unhappy: Event bus publish failure should not crash analysis."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="bullish",
        confidence=0.8,
        reasoning="Strong signals",
        key_factors=["factor1"]
    ))
    
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.publish = AsyncMock(side_effect=Exception("Bus error"))
    
    agent = SentimentAgent(
        llm_provider=mock_provider,
        event_bus=mock_bus
    )
    
    # Should complete analysis even if publish fails
    result = await agent.analyze({}, {})
    
    assert result["sentiment"] == "bullish"
    assert result["confidence"] == 0.8


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_mixed_case_sentiment():
    """Edge: Mixed case sentiment should be handled."""
    mock_provider = AsyncMock(spec=LLMProvider)
    
    class MixedCaseSentiment(BaseModel):
        sentiment: str
        confidence: float
        reasoning: str
        key_factors: list[str]
    
    mock_provider.generate_structured = AsyncMock(return_value=MixedCaseSentiment(
        sentiment="Bullish",  # Capital B
        confidence=0.8,
        reasoning="Test",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    # Should normalize to lowercase and map correctly
    assert result["action"] == "buy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_special_characters_in_context():
    """Edge: Special characters in context should be handled."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="neutral",
        confidence=0.6,
        reasoning="Test",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze(
        features={},
        context={
            "news": "Bitcoin 🚀 to the 🌙! $BTC #crypto @elonmusk 💎🙌",
            "symbol": "BTC/USD"
        }
    )
    
    assert result is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_non_string_price():
    """Edge: Non-string price in features should convert properly."""
    mock_provider = AsyncMock(spec=LLMProvider)
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="bullish",
        confidence=0.7,
        reasoning="Test",
        key_factors=[]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze(
        features={"price": 50000, "volume": 1500.5},  # Numbers not strings
        context={}
    )
    
    assert result["sentiment"] == "bullish"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_none_provider_empty_result():
    """Unhappy: None provider should return fallback immediately."""
    agent = SentimentAgent()  # No provider
    
    result = await agent.analyze(
        features={"price": 50000},
        context={"news": "Test news"}
    )
    
    assert result["sentiment"] == "neutral"
    assert result["action"] == "hold"
    assert result["confidence"] == 0.3
    assert "not available" in result["reasoning"].lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sentiment_agent_extremely_long_reasoning():
    """Edge: Very long reasoning should be handled."""
    mock_provider = AsyncMock(spec=LLMProvider)
    
    long_reasoning = "X" * 50000
    mock_provider.generate_structured = AsyncMock(return_value=SentimentAnalysis(
        sentiment="bearish",
        confidence=0.75,
        reasoning=long_reasoning,
        key_factors=["factor"]
    ))
    
    agent = SentimentAgent(llm_provider=mock_provider)
    
    result = await agent.analyze({}, {})
    
    assert len(result["reasoning"]) == 50000
