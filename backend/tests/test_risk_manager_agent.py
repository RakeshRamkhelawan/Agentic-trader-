"""
Tests voor RiskManager Agent.

Test risk assessments, constraint checks, en decision logic.
"""

import pytest

from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.core.schemas.ooda_types import (
    MarketRegime,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)


class TestRiskManagerAgent:
    """Tests for RiskManagerAgent."""

    @pytest.mark.asyncio
    async def test_approve_valid_proposal(self, sample_proposal):
        """Happy path: Valid proposal approved."""
        agent = RiskManagerAgent(
            max_position_size=1.0, max_leverage=3.0, min_confidence=0.6
        )

        assessment = await agent.assess_risk(
            proposal=sample_proposal,
            current_regime=MarketRegime.TRENDING_UP,
            current_position_size=0.0,
        )

        assert isinstance(assessment, RiskAssessment)
        assert assessment.decision == RiskDecision.APPROVE
        assert assessment.trade_id == sample_proposal.trade_id
        assert 0.0 <= assessment.risk_score <= 1.0
        assert len(assessment.rationale) > 0

    @pytest.mark.asyncio
    async def test_reject_low_confidence(self, sample_proposal):
        """Reject proposal met te lage confidence."""
        agent = RiskManagerAgent(min_confidence=0.9)  # Hoog

        # sample_proposal heeft confidence=0.75
        assessment = await agent.assess_risk(
            proposal=sample_proposal, current_regime=MarketRegime.RANGING
        )

        assert assessment.decision == RiskDecision.REJECT
        assert "Confidence" in assessment.rationale

    @pytest.mark.asyncio
    async def test_reject_oversized_position(self, sample_proposal):
        """Reject position groter dan max."""
        agent = RiskManagerAgent(max_position_size=0.3)  # Klein

        # sample_proposal.size = 0.5
        assessment = await agent.assess_risk(
            proposal=sample_proposal, current_regime=MarketRegime.RANGING
        )

        # Zou REDUCE_SIZE of REJECT moeten zijn
        assert assessment.decision in [RiskDecision.REDUCE_SIZE, RiskDecision.REJECT]

    @pytest.mark.asyncio
    async def test_reject_excessive_leverage(self, sample_proposal):
        """Reject excessive leverage."""
        agent = RiskManagerAgent(max_leverage=1.5)  # Laag

        # sample_proposal.leverage = 2.0
        assessment = await agent.assess_risk(
            proposal=sample_proposal, current_regime=MarketRegime.RANGING
        )

        assert assessment.decision == RiskDecision.REJECT
        assert "Leverage" in assessment.rationale

    @pytest.mark.asyncio
    async def test_reject_volatile_with_leverage(self, sample_proposal):
        """Reject high leverage in volatile regime."""
        agent = RiskManagerAgent(max_leverage=3.0)

        assessment = await agent.assess_risk(
            proposal=sample_proposal,
            current_regime=MarketRegime.VOLATILE,  # leverage = 2.0
        )

        assert assessment.decision == RiskDecision.REJECT
        assert "VOLATILE" in assessment.rationale

    @pytest.mark.asyncio
    async def test_reject_position_concentration(self, sample_proposal):
        """Reject bij te hoge position concentration."""
        agent = RiskManagerAgent(max_position_size=1.0)

        # Huidige position = 1.0, nieuwe = 0.5, totaal = 1.5 > 1.5 limiet (gelijk aan grens)
        # Verhoog naar 1.1 om over de grens te gaan
        assessment = await agent.assess_risk(
            proposal=sample_proposal,
            current_regime=MarketRegime.RANGING,
            current_position_size=1.1,  # Changed from 0.8
        )

        assert assessment.decision == RiskDecision.REJECT
        assert "concentration" in assessment.rationale.lower()

    @pytest.mark.asyncio
    async def test_risk_score_calculation(self, sample_proposal):
        """Risk score correct berekend."""
        agent = RiskManagerAgent()

        assessment = await agent.assess_risk(
            proposal=sample_proposal, current_regime=MarketRegime.RANGING
        )

        # Risk score moet tussen 0 en 1 zijn
        assert 0.0 <= assessment.risk_score <= 1.0

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, sample_proposal):
        """Statistics correct getrackt."""
        agent = RiskManagerAgent()

        # Approve one
        await agent.assess_risk(sample_proposal, MarketRegime.RANGING)

        # Reject one (low confidence)
        low_conf_proposal = TradeProposal(
            symbol="ETH/USDT",
            side="sell",
            size=0.5,
            entry_price=3000.0,
            stop_loss=3100.0,
            take_profit=2900.0,
            rationale="Low confidence test proposal",
            strategy_id="test",
            confidence=0.1,  # Too low
        )
        await agent.assess_risk(low_conf_proposal, MarketRegime.RANGING)

        stats = agent.get_statistics()

        assert stats["assessments_made"] == 2
        assert stats["trades_approved"] == 1
        assert stats["trades_rejected"] == 1
        assert stats["approval_rate"] == 0.5
