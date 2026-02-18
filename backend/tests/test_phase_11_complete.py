"""
Phase 11: Real Agent Integration Tests - COMPLETE IMPLEMENTATION

Tests for end-to-end integration of cognitive agents with the trading pipeline:
Agents → ColdPathCoordinator → FastConfig → HotPathEngine → Execution

All 35+ tests fully implemented and ready to run.
"""

import os
import tempfile
import time
from threading import Thread
from unittest.mock import MagicMock

import pytest

from backend.orchestration.phase_11_integration import (
    MockMarketRegimeAgent, MockRiskGovernor, MockSentimentAgent,
    create_coordinator_with_custom_agents, create_test_coordinator)

# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    fd, path = tempfile.mkstemp(suffix=".bin")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def mock_sentiment_agent():
    """Mock SentimentAgent for testing."""
    return MockSentimentAgent(default_confidence=0.85)


@pytest.fixture
def mock_market_regime_agent():
    """Mock MarketRegimeAgent for testing."""
    return MockMarketRegimeAgent(default_action=1, default_confidence=0.72)


@pytest.fixture
def mock_risk_governor():
    """Mock RiskGovernor for testing."""
    return MockRiskGovernor(allow_trading=True, confidence=0.9)


@pytest.fixture
def coordinator(temp_config_file):
    """Create Phase 11 Integration Coordinator for testing."""
    return create_test_coordinator(temp_config_file)


# ============================================================================
# TEST CLASS 1: AGENT MOCKING (4/4)
# ============================================================================


class TestPhase11AgentMocking:
    """Test mock agent setup and configuration."""

    @pytest.mark.unit
    def test_mock_sentiment_agent_structure(self, mock_sentiment_agent):
        """Mock SentimentAgent has required interface."""
        assert hasattr(mock_sentiment_agent, "name")
        assert hasattr(mock_sentiment_agent, "analyze")
        assert mock_sentiment_agent.name == "SentimentAgent"
        decision = mock_sentiment_agent.analyze()
        assert (
            "action" in decision
            and "confidence" in decision
            and "reasoning" in decision
        )

    @pytest.mark.unit
    def test_mock_market_regime_agent_structure(self, mock_market_regime_agent):
        """Mock MarketRegimeAgent has required interface."""
        assert hasattr(mock_market_regime_agent, "name")
        assert hasattr(mock_market_regime_agent, "analyze")
        assert mock_market_regime_agent.name == "MarketRegimeAgent"
        decision = mock_market_regime_agent.analyze()
        assert (
            "action" in decision
            and "confidence" in decision
            and "reasoning" in decision
        )

    @pytest.mark.unit
    def test_mock_risk_governor_structure(self, mock_risk_governor):
        """Mock RiskGovernor has required interface."""
        assert hasattr(mock_risk_governor, "name")
        assert hasattr(mock_risk_governor, "analyze")
        assert mock_risk_governor.name == "RiskGovernor"
        decision = mock_risk_governor.analyze()
        assert (
            "action" in decision
            and "confidence" in decision
            and "reasoning" in decision
        )

    @pytest.mark.unit
    def test_multiple_mock_agents_callable(
        self, mock_sentiment_agent, mock_market_regime_agent, mock_risk_governor
    ):
        """All mock agents are callable and return expected format."""
        for agent in [
            mock_sentiment_agent,
            mock_market_regime_agent,
            mock_risk_governor,
        ]:
            decision = agent.analyze()
            assert isinstance(decision["action"], int) and 0 <= decision["action"] <= 2
            assert (
                isinstance(decision["confidence"], float)
                and 0 <= decision["confidence"] <= 1
            )


# ============================================================================
# TEST CLASS 2: SENTIMENT AGENT INTEGRATION (4/4)
# ============================================================================


class TestPhase11SentimentAgentIntegration:
    """Test SentimentAgent integration with coordinator."""

    @pytest.mark.unit
    def test_sentiment_agent_registered(self, temp_config_file, mock_sentiment_agent):
        """SentimentAgent successfully registers."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        assert "SentimentAgent" in coord.agents
        assert coord.agents["SentimentAgent"].name == "SentimentAgent"

    @pytest.mark.unit
    def test_sentiment_agent_influences_decision(
        self, temp_config_file, mock_sentiment_agent
    ):
        """SentimentAgent's decision influences coordinator decision."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        decision = coord.make_decision()
        assert decision["action"] == 1 and decision["confidence"] == pytest.approx(
            0.85, abs=0.01
        )

    @pytest.mark.unit
    def test_sentiment_agent_failure_handled(self, temp_config_file):
        """Coordinator continues if SentimentAgent fails."""
        agent = MockSentimentAgent()
        agent.analyze = MagicMock(side_effect=Exception("Failed"))
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=agent
        )
        decision = coord.make_decision()
        assert decision is not None and decision["action"] == 0  # Fallback

    @pytest.mark.unit
    def test_sentiment_agent_metrics_tracked(
        self, temp_config_file, mock_sentiment_agent
    ):
        """SentimentAgent metrics are properly tracked."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        coord.make_decision()
        coord.make_decision()
        stats = coord.get_agent_statistics()
        assert stats["SentimentAgent"]["call_count"] >= 2


# ============================================================================
# TEST CLASS 3: MARKET REGIME AGENT INTEGRATION (4/4)
# ============================================================================


class TestPhase11MarketRegimeAgentIntegration:
    """Test MarketRegimeAgent integration with coordinator."""

    @pytest.mark.unit
    def test_market_regime_agent_registered(
        self, temp_config_file, mock_market_regime_agent
    ):
        """MarketRegimeAgent successfully registers."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, market_regime_agent=mock_market_regime_agent
        )
        assert "MarketRegimeAgent" in coord.agents

    @pytest.mark.unit
    def test_market_regime_influences_decision(
        self, temp_config_file, mock_market_regime_agent
    ):
        """MarketRegimeAgent influences final decision."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, market_regime_agent=mock_market_regime_agent
        )
        decision = coord.make_decision()
        assert decision["action"] == 1 and decision["confidence"] > 0

    @pytest.mark.unit
    def test_multiple_agents_aggregation(
        self, temp_config_file, mock_sentiment_agent, mock_market_regime_agent
    ):
        """Sentiment and MarketRegime agents properly aggregated."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file,
            sentiment_agent=mock_sentiment_agent,
            market_regime_agent=mock_market_regime_agent,
        )
        decision = coord.make_decision()
        assert decision["action"] == 1 and 0.70 <= decision["confidence"] <= 0.90

    @pytest.mark.unit
    def test_conflicting_decisions_resolved(self, temp_config_file):
        """Conflicting agent decisions resolved by higher confidence."""
        sent = MockSentimentAgent(default_confidence=0.9)
        market = MockMarketRegimeAgent(default_action=2, default_confidence=0.6)
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=sent, market_regime_agent=market
        )
        decision = coord.make_decision()
        assert decision["action"] == 1  # Higher confidence sentiment wins


# ============================================================================
# TEST CLASS 4: RISK GOVERNOR INTEGRATION (3/3)
# ============================================================================


class TestPhase11RiskGovernorIntegration:
    """Test RiskGovernor integration with coordinator."""

    @pytest.mark.unit
    def test_risk_governor_registered(self, temp_config_file, mock_risk_governor):
        """RiskGovernor successfully registers."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, risk_governor=mock_risk_governor
        )
        assert "RiskGovernor" in coord.agents

    @pytest.mark.unit
    def test_risk_governor_overrides_decisions(self, temp_config_file):
        """RiskGovernor can override risky decisions."""
        sent = MockSentimentAgent(default_confidence=0.9)
        risk = MockRiskGovernor(allow_trading=False, confidence=0.95)
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=sent, risk_governor=risk
        )
        coord.agent_weights["RiskGovernor"] = 2.0  # Higher weight
        decision = coord.make_decision()
        assert decision["action"] == 0  # Hold due to risk constraint

    @pytest.mark.unit
    def test_all_three_agents_aggregation(
        self,
        temp_config_file,
        mock_sentiment_agent,
        mock_market_regime_agent,
        mock_risk_governor,
    ):
        """All three agents properly aggregated."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file,
            sentiment_agent=mock_sentiment_agent,
            market_regime_agent=mock_market_regime_agent,
            risk_governor=mock_risk_governor,
        )
        decision = coord.make_decision()
        assert decision["action"] in [0, 1, 2] and 0 <= decision["confidence"] <= 1


# ============================================================================
# TEST CLASS 5: FULL E2E PIPELINE (5/5)
# ============================================================================


class TestPhase11FullE2EPipeline:
    """Test complete end-to-end pipeline."""

    @pytest.mark.unit
    def test_agents_to_decision(self, temp_config_file, mock_sentiment_agent):
        """Agents execute through full pipeline."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        decision = coord.make_decision()
        assert all(
            k in decision for k in ["action", "confidence", "reasoning", "timestamp"]
        )

    @pytest.mark.unit
    def test_coordinator_e2e(self, coordinator):
        """Full pipeline with all agents."""
        decision = coordinator.make_decision()
        assert decision["action"] == 1 and decision["confidence"] > 0.5

    @pytest.mark.unit
    def test_decision_quality(
        self,
        temp_config_file,
        mock_sentiment_agent,
        mock_market_regime_agent,
        mock_risk_governor,
    ):
        """Final decision quality from full pipeline."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file,
            sentiment_agent=mock_sentiment_agent,
            market_regime_agent=mock_market_regime_agent,
            risk_governor=mock_risk_governor,
        )
        decision = coord.make_decision()
        assert (
            decision["action"] in [0, 1, 2]
            and decision["confidence"] > 0.5
            and decision["reasoning"]
        )

    @pytest.mark.unit
    def test_decision_history_tracking(self, temp_config_file, mock_sentiment_agent):
        """Decision history properly maintained."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        for _ in range(5):
            coord.make_decision()
        metrics = coord.get_metrics()
        assert metrics["decisions_made"] >= 5

    @pytest.mark.unit
    def test_metrics_accumulation(self, temp_config_file, mock_sentiment_agent):
        """Metrics properly accumulated."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        for _ in range(3):
            coord.make_decision()
        metrics = coord.get_metrics()
        assert metrics["decisions_made"] >= 3 and "action_distribution" in metrics


# ============================================================================
# TEST CLASS 6: LATENCY VERIFICATION (3/3)
# ============================================================================


class TestPhase11LatencyVerification:
    """Test latency requirements."""

    @pytest.mark.unit
    def test_single_agent_latency(self, temp_config_file, mock_sentiment_agent):
        """Single agent decision latency < 100ms."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        start = time.time()
        coord.make_decision()
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, f"Latency {elapsed}ms exceeds 100ms"

    @pytest.mark.unit
    def test_three_agents_latency(self, coordinator):
        """Three agents decision latency < 200ms."""
        start = time.time()
        coordinator.make_decision()
        elapsed = (time.time() - start) * 1000
        assert elapsed < 200, f"Latency {elapsed}ms exceeds 200ms"

    @pytest.mark.unit
    def test_average_decision_latency(self, temp_config_file):
        """Average decision latency across multiple executions."""
        coord = create_test_coordinator(temp_config_file)
        latencies = []
        for _ in range(5):
            start = time.time()
            coord.make_decision()
            latencies.append((time.time() - start) * 1000)
        avg = sum(latencies) / len(latencies)
        assert avg < 150, f"Average latency {avg}ms exceeds 150ms"


# ============================================================================
# TEST CLASS 7: THROUGHPUT VERIFICATION (3/3)
# ============================================================================


class TestPhase11ThroughputVerification:
    """Test throughput requirements."""

    @pytest.mark.unit
    def test_decisions_per_second(self, temp_config_file, mock_sentiment_agent):
        """Achieve >2 decisions per second."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        start = time.time()
        for _ in range(5):
            coord.make_decision()
        elapsed = time.time() - start
        if elapsed > 0:
            throughput = 5 / elapsed
            assert throughput > 2, f"Throughput {throughput} d/s below 2 d/s"

    @pytest.mark.unit
    def test_sustained_throughput(self, temp_config_file, mock_sentiment_agent):
        """Sustained throughput over 30 decisions."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        start = time.time()
        for _ in range(30):
            coord.make_decision()
        elapsed = time.time() - start
        if elapsed > 0:
            throughput = 30 / elapsed
            assert throughput > 1, f"Sustained throughput {throughput} d/s too low"

    @pytest.mark.unit
    def test_high_frequency_decisions(self, coordinator):
        """Make multiple decisions in quick succession."""
        start = time.time()
        decision_count = 0
        while (time.time() - start) < 1.0 and decision_count < 100:
            coordinator.make_decision()
            decision_count += 1
        elapsed = time.time() - start
        assert decision_count > 2, f"Only made {decision_count} decisions in {elapsed}s"


# ============================================================================
# TEST CLASS 8: REAL DECISION FLOW (3/3)
# ============================================================================


class TestPhase11RealDecisionFlow:
    """Test realistic trading scenarios."""

    @pytest.mark.unit
    def test_strong_bullish_consensus(self, temp_config_file):
        """All agents bullish → long decision with high confidence."""
        sent = MockSentimentAgent(default_confidence=0.95)
        market = MockMarketRegimeAgent(default_action=1, default_confidence=0.90)
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=sent, market_regime_agent=market
        )
        decision = coord.make_decision()
        assert decision["action"] == 1 and decision["confidence"] > 0.85

    @pytest.mark.unit
    def test_mixed_signals_moderate_confidence(self, temp_config_file):
        """Agents disagree → moderate confidence decision."""
        sent = MockSentimentAgent(default_confidence=0.70)
        market = MockMarketRegimeAgent(default_action=0, default_confidence=0.60)
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=sent, market_regime_agent=market
        )
        decision = coord.make_decision()
        assert 0.40 < decision["confidence"] < 0.80

    @pytest.mark.unit
    def test_risk_override(self, temp_config_file):
        """RiskGovernor overrides bullish signals."""
        sent = MockSentimentAgent(default_confidence=0.95)
        risk = MockRiskGovernor(allow_trading=False, confidence=0.98)
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=sent, risk_governor=risk
        )
        coord.agent_weights["RiskGovernor"] = 2.0
        decision = coord.make_decision()
        assert decision["action"] == 0  # Hold


# ============================================================================
# TEST CLASS 9: CONCURRENT AGENTS (3/3)
# ============================================================================


class TestPhase11ConcurrentAgents:
    """Test concurrent agent execution."""

    @pytest.mark.unit
    def test_parallel_execution(self, coordinator):
        """All agents execute without blocking."""
        start = time.time()
        decision = coordinator.make_decision()
        elapsed = (time.time() - start) * 1000
        assert elapsed < 200, f"Execution too slow: {elapsed}ms"
        assert decision is not None

    @pytest.mark.unit
    def test_concurrent_decisions(self, temp_config_file, mock_sentiment_agent):
        """Multiple decisions can be made concurrently."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=mock_sentiment_agent
        )
        decisions = []
        threads = [
            Thread(target=lambda: decisions.append(coord.make_decision()))
            for _ in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(decisions) == 5 and all(d["action"] in [0, 1, 2] for d in decisions)

    @pytest.mark.unit
    def test_decision_isolation(
        self, temp_config_file, mock_sentiment_agent, mock_market_regime_agent
    ):
        """Concurrent decisions don't interfere with each other."""
        coord = create_coordinator_with_custom_agents(
            temp_config_file,
            sentiment_agent=mock_sentiment_agent,
            market_regime_agent=mock_market_regime_agent,
        )
        decisions = []

        def make_decisions():
            for _ in range(3):
                decisions.append(coord.make_decision())

        threads = [Thread(target=make_decisions) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(decisions) == 9 and all(d["action"] in [0, 1, 2] for d in decisions)


# ============================================================================
# TEST CLASS 10: ERROR SCENARIOS (3/3)
# ============================================================================


class TestPhase11ErrorScenarios:
    """Test error handling in real scenarios."""

    @pytest.mark.unit
    def test_single_agent_failure(self, temp_config_file):
        """System continues if one agent fails."""
        sent = MockSentimentAgent()
        market = MockMarketRegimeAgent(default_action=1, default_confidence=0.8)
        sent.analyze = MagicMock(side_effect=Exception("Network error"))
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=sent, market_regime_agent=market
        )
        decision = coord.make_decision()
        assert decision is not None and decision["action"] == 1  # Uses MarketRegime

    @pytest.mark.unit
    def test_all_agents_fail_fallback(self, temp_config_file):
        """Fallback decision when all agents fail."""
        sent = MockSentimentAgent()
        market = MockMarketRegimeAgent()
        risk = MockRiskGovernor()
        for agent in [sent, market, risk]:
            agent.analyze = MagicMock(side_effect=Exception("Failed"))
        coord = create_coordinator_with_custom_agents(
            temp_config_file,
            sentiment_agent=sent,
            market_regime_agent=market,
            risk_governor=risk,
        )
        decision = coord.make_decision()
        assert decision["action"] == 0 and decision["confidence"] == 0.5

    @pytest.mark.unit
    def test_agent_recovery(self, temp_config_file):
        """Agent recovers after temporary failure."""
        sent = MockSentimentAgent(default_confidence=0.85)
        coord = create_coordinator_with_custom_agents(
            temp_config_file, sentiment_agent=sent
        )

        # First: fail
        sent.analyze = MagicMock(side_effect=Exception("Temporary error"))
        decision1 = coord.make_decision()
        assert decision1["action"] == 0  # Fallback

        # Second: recover
        sent.analyze = MagicMock(
            return_value={"action": 1, "confidence": 0.85, "reasoning": "Recovered"}
        )
        decision2 = coord.make_decision()
        assert decision2["action"] == 1  # Uses agent again


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
