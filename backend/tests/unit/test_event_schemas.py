"""
Tests for Event Schemas.

TDD Test Suite - Write tests FIRST before implementation.
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from backend.events.schemas import (
    MarketTick,
    AgentThought,
    TradeProposal,
    EventBase
)


@pytest.mark.unit
def test_event_base_exists():
    """RED: EventBase schema should exist."""
    assert EventBase is not None


@pytest.mark.unit
def test_market_tick_schema():
    """RED: MarketTick schema with required fields."""
    tick = MarketTick(
        symbol="BTC/USD",
        price=50000.0,
        volume=1.5,
        timestamp=datetime.now(timezone.utc)
    )
    
    assert tick.symbol == "BTC/USD"
    assert tick.price == 50000.0
    assert tick.volume == 1.5
    assert isinstance(tick.timestamp, datetime)


@pytest.mark.unit
def test_market_tick_validation():
    """RED: MarketTick should validate negative price."""
    with pytest.raises(ValidationError):
        MarketTick(
            symbol="BTC/USD",
            price=-100.0,  # Invalid
            volume=1.0,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_agent_thought_schema():
    """RED: AgentThought schema with reasoning."""
    thought = AgentThought(
        agent_name="SentimentAgent",
        reasoning="Market shows bullish signals based on social sentiment.",
        confidence=0.85,
        data={"sentiment_score": 0.75, "volume_surge": True},
        timestamp=datetime.now(timezone.utc)
    )
    
    assert thought.agent_name == "SentimentAgent"
    assert thought.reasoning.startswith("Market shows")
    assert thought.confidence == 0.85
    assert thought.data["sentiment_score"] == 0.75


@pytest.mark.unit
def test_agent_thought_confidence_bounds():
    """RED: AgentThought confidence should be between 0 and 1."""
    with pytest.raises(ValidationError):
        AgentThought(
            agent_name="TestAgent",
            reasoning="Test",
            confidence=1.5,  # Invalid
            data={},
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_trade_proposal_schema():
    """RED: TradeProposal with buy/sell action."""
    proposal = TradeProposal(
        agent_name="StrategyAgent",
        symbol="ETH/USD",
        action="buy",
        quantity=2.0,
        target_price=3000.0,
        stop_loss=2800.0,
        take_profit=3200.0,
        rationale="Support level confirmed at 2900",
        confidence=0.78,
        timestamp=datetime.now(timezone.utc)
    )
    
    assert proposal.action == "buy"
    assert proposal.symbol == "ETH/USD"
    assert proposal.quantity == 2.0
    assert proposal.target_price == 3000.0
    assert proposal.stop_loss == 2800.0


@pytest.mark.unit
def test_trade_proposal_invalid_action():
    """RED: TradeProposal should only allow buy/sell/hold."""
    with pytest.raises(ValidationError):
        TradeProposal(
            agent_name="TestAgent",
            symbol="BTC/USD",
            action="invalid_action",  # Should fail
            quantity=1.0,
            target_price=50000.0,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_event_serialization():
    """RED: Events should serialize to dict."""
    tick = MarketTick(
        symbol="BTC/USD",
        price=50000.0,
        volume=1.5,
        timestamp=datetime.now(timezone.utc)
    )
    
    data = tick.model_dump()
    assert isinstance(data, dict)
    assert data["symbol"] == "BTC/USD"
    assert data["price"] == 50000.0


@pytest.mark.unit
def test_event_json_serialization():
    """RED: Events should serialize to JSON string."""
    thought = AgentThought(
        agent_name="TestAgent",
        reasoning="Test reasoning",
        confidence=0.9,
        data={"key": "value"},
        timestamp=datetime.now(timezone.utc)
    )
    
    json_str = thought.model_dump_json()
    assert isinstance(json_str, str)
    assert "TestAgent" in json_str
    assert "Test reasoning" in json_str
