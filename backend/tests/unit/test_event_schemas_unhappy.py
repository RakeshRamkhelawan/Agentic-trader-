"""
Unhappy Path Tests for Event Schemas.

Tests validation errors, edge cases, and invalid data.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.events.schemas import (AgentThought, EventBase, MarketTick,
                                    TradeProposal)


@pytest.mark.unit
def test_market_tick_negative_price():
    """Unhappy: Negative price should fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        MarketTick(
            symbol="BTC/USD",
            price=-1000.0,
            volume=1.0,
            timestamp=datetime.now(timezone.utc)
        )
    
    assert "price" in str(exc_info.value).lower()


@pytest.mark.unit
def test_market_tick_zero_price():
    """Unhappy: Zero price should fail validation."""
    with pytest.raises(ValidationError):
        MarketTick(
            symbol="BTC/USD",
            price=0.0,
            volume=1.0,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_market_tick_negative_volume():
    """Unhappy: Negative volume should fail validation."""
    with pytest.raises(ValidationError):
        MarketTick(
            symbol="BTC/USD",
            price=50000.0,
            volume=-10.0,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_market_tick_missing_symbol():
    """Unhappy: Missing required field should fail."""
    with pytest.raises(ValidationError) as exc_info:
        MarketTick(
            price=50000.0,
            volume=1.0,
            timestamp=datetime.now(timezone.utc)
        )
    
    assert "symbol" in str(exc_info.value).lower()


@pytest.mark.unit
def test_market_tick_empty_symbol():
    """Unhappy: Empty symbol should still validate (no min length)."""
    # This should actually pass if we don't enforce min length
    tick = MarketTick(
        symbol="",
        price=50000.0,
        volume=1.0,
        timestamp=datetime.now(timezone.utc)
    )
    assert tick.symbol == ""


@pytest.mark.unit
def test_agent_thought_confidence_too_high():
    """Unhappy: Confidence > 1.0 should fail."""
    with pytest.raises(ValidationError) as exc_info:
        AgentThought(
            agent_name="TestAgent",
            reasoning="Test",
            confidence=1.5,
            data={},
            timestamp=datetime.now(timezone.utc)
        )
    
    assert "confidence" in str(exc_info.value).lower()


@pytest.mark.unit
def test_agent_thought_confidence_negative():
    """Unhappy: Negative confidence should fail."""
    with pytest.raises(ValidationError):
        AgentThought(
            agent_name="TestAgent",
            reasoning="Test",
            confidence=-0.1,
            data={},
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_agent_thought_missing_reasoning():
    """Unhappy: Missing reasoning should fail."""
    with pytest.raises(ValidationError) as exc_info:
        AgentThought(
            agent_name="TestAgent",
            confidence=0.8,
            data={},
            timestamp=datetime.now(timezone.utc)
        )
    
    assert "reasoning" in str(exc_info.value).lower()


@pytest.mark.unit
def test_agent_thought_empty_agent_name():
    """Unhappy: Empty agent name should still validate."""
    thought = AgentThought(
        agent_name="",
        reasoning="Test reasoning",
        confidence=0.8,
        data={},
        timestamp=datetime.now(timezone.utc)
    )
    assert thought.agent_name == ""


@pytest.mark.unit
def test_trade_proposal_invalid_action():
    """Unhappy: Invalid action type should fail."""
    with pytest.raises(ValidationError) as exc_info:
        TradeProposal(
            agent_name="TestAgent",
            symbol="BTC/USD",
            action="invalid",
            quantity=1.0,
            target_price=50000.0,
            rationale="Test",
            confidence=0.8,
            timestamp=datetime.now(timezone.utc)
        )
    
    assert "action" in str(exc_info.value).lower()


@pytest.mark.unit
def test_trade_proposal_zero_quantity():
    """Unhappy: Zero quantity should fail."""
    with pytest.raises(ValidationError):
        TradeProposal(
            agent_name="TestAgent",
            symbol="BTC/USD",
            action="buy",
            quantity=0.0,
            target_price=50000.0,
            rationale="Test",
            confidence=0.8,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_trade_proposal_negative_quantity():
    """Unhappy: Negative quantity should fail."""
    with pytest.raises(ValidationError):
        TradeProposal(
            agent_name="TestAgent",
            symbol="BTC/USD",
            action="buy",
            quantity=-5.0,
            target_price=50000.0,
            rationale="Test",
            confidence=0.8,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_trade_proposal_missing_rationale():
    """Unhappy: Missing rationale should fail."""
    with pytest.raises(ValidationError) as exc_info:
        TradeProposal(
            agent_name="TestAgent",
            symbol="BTC/USD",
            action="buy",
            quantity=1.0,
            target_price=50000.0,
            confidence=0.8,
            timestamp=datetime.now(timezone.utc)
        )
    
    assert "rationale" in str(exc_info.value).lower()


@pytest.mark.unit
def test_trade_proposal_confidence_out_of_range():
    """Unhappy: Confidence outside 0-1 range should fail."""
    with pytest.raises(ValidationError):
        TradeProposal(
            agent_name="TestAgent",
            symbol="BTC/USD",
            action="sell",
            quantity=1.0,
            target_price=50000.0,
            rationale="Test",
            confidence=2.0,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_trade_proposal_case_sensitive_action():
    """Unhappy: Wrong case action should fail (not normalized)."""
    # Test if action is case-sensitive
    with pytest.raises(ValidationError):
        TradeProposal(
            agent_name="TestAgent",
            symbol="BTC/USD",
            action="BUY",  # Should be lowercase
            quantity=1.0,
            target_price=50000.0,
            rationale="Test",
            confidence=0.8,
            timestamp=datetime.now(timezone.utc)
        )


@pytest.mark.unit
def test_market_tick_invalid_timestamp_type():
    """Unhappy: Invalid timestamp type should fail."""
    with pytest.raises(ValidationError):
        MarketTick(
            symbol="BTC/USD",
            price=50000.0,
            volume=1.0,
            timestamp="not a datetime"
        )


@pytest.mark.unit
def test_agent_thought_data_with_none():
    """Unhappy: None as data should use default empty dict."""
    thought = AgentThought(
        agent_name="TestAgent",
        reasoning="Test",
        confidence=0.8,
        timestamp=datetime.now(timezone.utc)
    )
    assert thought.data == {}


@pytest.mark.unit
def test_trade_proposal_negative_stop_loss():
    """Edge: Negative stop loss should still validate (prices can be any float)."""
    proposal = TradeProposal(
        agent_name="TestAgent",
        symbol="BTC/USD",
        action="buy",
        quantity=1.0,
        target_price=50000.0,
        stop_loss=-100.0,  # Unusual but technically valid
        rationale="Test",
        confidence=0.8,
        timestamp=datetime.now(timezone.utc)
    )
    assert proposal.stop_loss == -100.0


@pytest.mark.unit
def test_event_base_timestamp_auto_generated():
    """Edge: EventBase should auto-generate timestamp if not provided."""
    class TestEvent(EventBase):
        test_field: str
    
    event = TestEvent(test_field="test")
    assert event.timestamp is not None
    assert isinstance(event.timestamp, datetime)


@pytest.mark.unit
def test_market_tick_extreme_price():
    """Edge: Extremely large price should still validate."""
    tick = MarketTick(
        symbol="BTC/USD",
        price=999999999999.99,
        volume=1.0,
        timestamp=datetime.now(timezone.utc)
    )
    assert tick.price == 999999999999.99


@pytest.mark.unit
def test_agent_thought_very_long_reasoning():
    """Edge: Very long reasoning should validate."""
    long_reasoning = "A" * 10000
    thought = AgentThought(
        agent_name="TestAgent",
        reasoning=long_reasoning,
        confidence=0.8,
        data={},
        timestamp=datetime.now(timezone.utc)
    )
    assert len(thought.reasoning) == 10000
