"""
Unit tests for OODA type definitions.

Tests validation, immutability, and field constraints.
"""


import pytest
from pydantic import ValidationError

from backend.core.schemas.ooda_types import (
    ExecutionOutcome,
    ExecutionPlan,
    MarketRegime,
    Observation,
    Orientation,
    RiskAssessment,
    TradeProposal,
)


class TestObservation:
    """Tests for Observation model."""

    def test_valid_observation(self):
        """Happy path: Valid observation."""
        obs = Observation(
            symbol="BTC/USDT",
            price=50000.0,
            volume=100.5,
            orderbook={"bids": [[49999, 1.0]], "asks": [[50001, 1.0]]},
            funding_rate=0.0001,
            social_sentiment=0.5,
        )

        assert obs.symbol == "BTC/USDT"
        assert obs.price == 50000.0
        assert obs.volume == 100.5
        assert obs.social_sentiment == 0.5
        assert obs.timestamp > 0

    def test_immutability(self):
        """Observations should be frozen/immutable."""
        obs = Observation(symbol="BTC/USDT", price=50000, volume=100)

        with pytest.raises(ValidationError):
            obs.price = 51000  # Should fail

    def test_invalid_price(self):
        """Price must be positive."""
        with pytest.raises(ValidationError):
            Observation(symbol="BTC/USDT", price=-100, volume=100)

    def test_invalid_volume(self):
        """Volume must be non-negative."""
        with pytest.raises(ValidationError):
            Observation(symbol="BTC/USDT", price=50000, volume=-10)

    def test_sentiment_bounds(self):
        """Sentiment must be in [-1, 1]."""
        with pytest.raises(ValidationError):
            Observation(
                symbol="BTC/USDT", price=50000, volume=100, social_sentiment=1.5  # Out of bounds
            )


class TestOrientation:
    """Tests for Orientation model."""

    def test_valid_orientation(self):
        """Happy path: Valid orientation."""
        orient = Orientation(
            symbol="BTC/USDT",
            regime=MarketRegime.TRENDING_UP,
            indicators={"rsi": 65.0, "macd": 150.0},
            core_sentiment=0.8,
            rag_context=["Historical bull run pattern detected"],
            confidence=0.75,
        )

        assert orient.regime == MarketRegime.TRENDING_UP
        assert orient.core_sentiment == 0.8
        assert orient.confidence == 0.75
        assert len(orient.rag_context) == 1

    def test_confidence_bounds(self):
        """Confidence must be in [0, 1]."""
        with pytest.raises(ValidationError):
            Orientation(
                symbol="BTC/USDT",
                regime=MarketRegime.RANGING,
                core_sentiment=0.5,
                confidence=1.5,  # Out of bounds
            )


class TestTradeProposal:
    """Tests for TradeProposal model."""

    def test_valid_buy_proposal(self):
        """Happy path: Valid buy proposal."""
        proposal = TradeProposal(
            symbol="BTC/USDT",
            side="buy",
            size=0.1,
            entry_price=50000.0,
            stop_loss=49000.0,
            take_profit=52000.0,
            rationale="Strong bullish signal from technical analysis",
            strategy_id="momentum_v1",
            confidence=0.75,
        )

        assert proposal.side == "buy"
        assert proposal.size == 0.1
        assert proposal.stop_loss == 49000.0
        assert proposal.confidence == 0.75

    def test_invalid_side(self):
        """Side must be 'buy' or 'sell'."""
        with pytest.raises(ValidationError):
            TradeProposal(
                symbol="BTC/USDT",
                side="hold",  # Invalid
                size=0.1,
                stop_loss=49000,
                take_profit=52000,
                rationale="Test rationale here",
                strategy_id="test_strat",
            )

    def test_rationale_min_length(self):
        """Rationale must have meaningful content."""
        with pytest.raises(ValidationError):
            TradeProposal(
                symbol="BTC/USDT",
                side="buy",
                size=0.1,
                stop_loss=49000,
                take_profit=52000,
                rationale="Short",  # Too short
                strategy_id="test",
            )


class TestRiskAssessment:
    """Tests for RiskAssessment model."""

    def test_approved_assessment(self):
        """Happy path: Approved risk assessment."""
        from backend.core.schemas.ooda_types import RiskDecision

        assessment = RiskAssessment(
            trade_id="test-trade-123",
            decision=RiskDecision.APPROVE,
            risk_score=0.3,
            rationale="All risk checks passed",
            win_probability=0.55,
        )

        assert assessment.decision == RiskDecision.APPROVE
        assert assessment.risk_score == 0.3
        assert assessment.rationale == "All risk checks passed"

    def test_rejected_with_modified_size(self):
        """Rejected but with size modification suggestion."""
        from backend.core.schemas.ooda_types import RiskDecision

        assessment = RiskAssessment(
            trade_id="test-trade-456",
            decision=RiskDecision.REDUCE_SIZE,
            modified_size=0.05,
            risk_score=0.7,
            rationale="Position size too large, suggested reduction",
            win_probability=0.45,
        )

        assert assessment.decision == RiskDecision.REDUCE_SIZE
        assert assessment.modified_size == 0.05
        assert "reduction" in assessment.rationale.lower()


class TestExecutionPlan:
    """Tests for ExecutionPlan model."""

    def test_valid_limit_order(self):
        """Happy path: Valid limit order plan."""
        plan = ExecutionPlan(
            symbol="BTC/USDT",
            side="buy",
            quantity=0.1,
            order_type="LIMIT",
            price=50000.0,
            expected_price=50000.0,
            trace_id="trace-12345",
        )

        assert plan.order_type == "LIMIT"
        assert plan.price == 50000.0
        assert plan.trace_id == "trace-12345"

    def test_market_order_no_price(self):
        """Market orders don't require price."""
        plan = ExecutionPlan(
            symbol="BTC/USDT",
            side="sell",
            quantity=0.1,
            order_type="MARKET",
            expected_price=49900.0,
            trace_id="trace-67890",
        )

        assert plan.order_type == "MARKET"
        assert plan.price is None


class TestExecutionOutcome:
    """Tests for ExecutionOutcome model."""

    def test_successful_execution(self):
        """Happy path: Successful execution."""
        outcome = ExecutionOutcome(
            success=True,
            order_id="exchange-order-123",
            filled_qty=0.1,
            avg_price=50050.0,
            fee=5.005,
            execution_latency_ms=120.5,
        )

        assert outcome.success is True
        assert outcome.order_id == "exchange-order-123"
        assert outcome.filled_qty == 0.1
        assert outcome.fee > 0

    def test_failed_execution(self):
        """Failed execution with error message."""
        outcome = ExecutionOutcome(
            success=False,
            error="Insufficient funds",
        )

        assert outcome.success is False
        assert outcome.error == "Insufficient funds"
        assert outcome.order_id is None
        assert outcome.filled_qty == 0.0
