"""
Tests for OrchestratorAgent.
"""

from unittest.mock import MagicMock

import pytest

from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.core.schemas.ooda_types import (
    Observation,
    Orientation,
    ResearchHypothesis,
    RiskAssessment,
    TradeProposal,
)
from backend.governance.agent_gatekeeper import AgentRole


@pytest.fixture
def orchestrator():
    agent = OrchestratorAgent(llm_provider=None, event_bus=None)
    return agent


@pytest.fixture
def mock_observation():
    return MagicMock(spec=Observation, symbol="BTC/EUR", price=95000.0)


@pytest.fixture
def mock_orientation():
    return MagicMock(spec=Orientation, symbol="BTC/EUR", regime="trending_up")


@pytest.fixture
def mock_proposal():
    return MagicMock(
        spec=TradeProposal, symbol="BTC/EUR", side="buy", size=0.1, entry_price=95000.0
    )


@pytest.fixture
def mock_risk_approved():
    assessment = MagicMock(spec=RiskAssessment)
    decision_mock = MagicMock()
    decision_mock.value = "approve"
    assessment.decision = decision_mock
    assessment.rationale = "Within risk limits"
    return assessment


@pytest.fixture
def mock_risk_rejected():
    assessment = MagicMock(spec=RiskAssessment)
    decision_mock = MagicMock()
    decision_mock.value = "reject"
    assessment.decision = decision_mock
    assessment.rationale = "Too risky"
    return assessment


@pytest.fixture
def mock_bull_hypothesis():
    return MagicMock(spec=ResearchHypothesis, confidence=0.8, stance="bullish")


@pytest.fixture
def mock_bear_hypothesis():
    return MagicMock(spec=ResearchHypothesis, confidence=0.2, stance="bearish")


class TestOrchestratorAgent:
    """Tests voor OrchestratorAgent."""

    def test_init_sets_strategist_role(self, orchestrator):
        """Test dat Orchestrator de STRATEGIST role heeft."""
        assert orchestrator.agent_role == AgentRole.STRATEGIST
        assert orchestrator.agent_name == "Orchestrator"

    def test_init_harmony_score_starts_at_one(self, orchestrator):
        """Test dat harmony_score start op 1.0."""
        assert orchestrator.harmony_score == 1.0
        assert orchestrator.cycle_count == 0

    @pytest.mark.asyncio
    async def test_harmonize_no_proposal_returns_stillness(
        self, orchestrator, mock_observation, mock_orientation
    ):
        """Test dat geen proposals resulteert in STILLNESS."""
        result = await orchestrator.harmonize(
            observation=mock_observation,
            orientation=mock_orientation,
            bull_hypothesis=None,  # No research
            bear_hypothesis=None,
            proposals=[],
            risk_assessments=[],
        )
        assert result["status"] == "STILLNESS"
        # 1.0 base, no deductions because empty lists
        assert result["harmony_score"] == 1.0
        assert orchestrator.cycle_count == 1

    @pytest.mark.asyncio
    async def test_harmonize_all_approved_returns_synchronized(
        self,
        orchestrator,
        mock_observation,
        mock_orientation,
        mock_proposal,
        mock_risk_approved,
        mock_bull_hypothesis,
        mock_bear_hypothesis,
    ):
        """Test dat volledige goedkeuring SYNCHRONIZED oplevert."""
        result = await orchestrator.harmonize(
            observation=mock_observation,
            orientation=mock_orientation,
            bull_hypothesis=mock_bull_hypothesis,
            bear_hypothesis=mock_bear_hypothesis,
            proposals=[mock_proposal],
            risk_assessments=[mock_risk_approved],
        )
        assert result["status"] == "SYNCHRONIZED"
        assert result["harmony_score"] == 1.0

    @pytest.mark.asyncio
    async def test_harmonize_rejected_returns_discord(
        self,
        orchestrator,
        mock_observation,
        mock_orientation,
        mock_proposal,
        mock_risk_rejected,
    ):
        """Test dat afwijzing DISCORD oplevert."""
        result = await orchestrator.harmonize(
            observation=mock_observation,
            orientation=mock_orientation,
            bull_hypothesis=None,
            bear_hypothesis=None,
            proposals=[mock_proposal],
            risk_assessments=[mock_risk_rejected],
        )
        # 1.0 - 0.5 = 0.5 -> DISCORD (<0.6)
        assert result["status"] == "DISCORD"
        assert result["harmony_score"] == 0.5

    @pytest.mark.asyncio
    async def test_harmonize_increments_cycle_count(
        self, orchestrator, mock_observation, mock_orientation
    ):
        """Test dat elke harmonize call de cycle_count verhoogt."""
        await orchestrator.harmonize(
            observation=mock_observation,
            orientation=mock_orientation,
            bull_hypothesis=None,
            bear_hypothesis=None,
            proposals=[],
            risk_assessments=[],
        )
        await orchestrator.harmonize(
            observation=mock_observation,
            orientation=mock_orientation,
            bull_hypothesis=None,
            bear_hypothesis=None,
            proposals=[],
            risk_assessments=[],
        )
        assert orchestrator.cycle_count == 2

    @pytest.mark.asyncio
    async def test_cognitive_dissonance(
        self, orchestrator, mock_observation, mock_orientation
    ):
        """Test conflict between Bull and Bear."""
        high_bull = MagicMock(spec=ResearchHypothesis, confidence=0.9, stance="bullish")
        high_bear = MagicMock(spec=ResearchHypothesis, confidence=0.9, stance="bearish")

        result = await orchestrator.harmonize(
            observation=mock_observation,
            orientation=mock_orientation,
            bull_hypothesis=high_bull,
            bear_hypothesis=high_bear,
            proposals=[],
            risk_assessments=[],
        )

        # 1.0 - 0.2 (Dissonance) - 0.1 (Bear Divergence vs Trending Up) = 0.7
        assert result["status"] == "FRICTION"
        assert result["harmony_score"] == 0.7
        assert "Cognitive Dissonance" in result["rationale"]

    @pytest.mark.asyncio
    async def test_analyze_delegates_to_harmonize(
        self, orchestrator, mock_observation, mock_orientation
    ):
        """Test dat analyze() correct delegeert naar harmonize()."""
        context = {
            "observation": mock_observation,
            "orientation": mock_orientation,
            "bull_hypothesis": None,
            "bear_hypothesis": None,
            "proposals": [],
            "risk_assessments": [],
        }
        result = await orchestrator.analyze(features={}, context=context)
        assert result["status"] == "STILLNESS"
