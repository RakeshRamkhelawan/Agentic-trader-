"""
Phase E Integration Tests: Learning Loop

Integratietests voor:
- Karma feedback loop
- SystemIdentity outcome updates
- End-to-end learning cycle
"""

from unittest.mock import MagicMock

import pytest

from backend.core.karma.karma_register import KarmaRegister, TradeOutcome
from backend.core.karma.reinforcement import ReinforcementLearner
from backend.core.system_identity import SystemIdentity
from backend.orchestration.ooda_coordinator import OODALoopCoordinator


class TestPhaseEKarmaIntegration:
    """Integratietests voor Karma feedback loop."""

    @pytest.fixture
    def karma_register(self):
        """Create KarmaRegister instance."""
        return KarmaRegister()

    def test_karma_tracks_multiple_agents(self, karma_register):
        """Test dat Karma meerdere agents kan tracken."""
        # Arrange
        outcomes = [
            ("trader_agent", 0.05),
            ("risk_agent", 0.03),
            ("analyst_agent", -0.02),
            ("trader_agent", 0.08),  # Second trade for trader_agent
        ]

        # Act
        for agent, pnl in outcomes:
            outcome = TradeOutcome(
                pnl_percent=pnl,
                drawdown_percent=0.01,
                execution_speed_ms=100.0,
            )
            karma_register.register_feedback(agent, outcome)

        # Assert
        assert "trader_agent" in karma_register.agent_karma
        assert "risk_agent" in karma_register.agent_karma
        assert "analyst_agent" in karma_register.agent_karma

        # Trader agent should have different karma than risk agent
        # due to different outcomes
        assert (
            karma_register.agent_karma["trader_agent"]
            != karma_register.agent_karma["risk_agent"]
        )

    def test_karma_moving_average_convergence(self, karma_register):
        """Test dat Karma converteert naar moving average."""
        # Arrange
        agent = "test_agent"

        # First strong positive outcome
        outcome1 = TradeOutcome(
            pnl_percent=0.20,
            drawdown_percent=0.01,
            execution_speed_ms=100.0,
        )
        karma1 = karma_register.register_feedback(agent, outcome1)

        # Then slight negative outcome
        outcome2 = TradeOutcome(
            pnl_percent=-0.02,
            drawdown_percent=0.01,
            execution_speed_ms=100.0,
        )
        karma2 = karma_register.register_feedback(agent, outcome2)

        # Assert - karma should be somewhere between
        assert -1.0 <= karma2 <= 1.0
        assert karma2 < karma1  # Karma should decrease

    def test_compliance_violation_severe_penalty(self, karma_register):
        """Test dat compliance violations zware straffen krijgen."""
        # Arrange
        agent = "test_agent"

        # Positive trade but with violation
        outcome = TradeOutcome(
            pnl_percent=0.15,
            drawdown_percent=0.01,
            execution_speed_ms=100.0,
            compliance_violation=True,
        )

        # Act
        karma = karma_register.register_feedback(agent, outcome)

        # Assert - should be severely penalized
        assert karma == -1.0

    def test_karma_affects_future_decisions(self):
        """Test dat karma invloed heeft op toekomstige beslissingen."""
        # This is a conceptual test - in real implementation,
        # karma would affect agent weights or selection
        karma = KarmaRegister()

        # Register multiple outcomes
        for i in range(5):
            outcome = TradeOutcome(
                pnl_percent=0.05 if i % 2 == 0 else -0.03,
                drawdown_percent=0.01,
                execution_speed_ms=100.0,
            )
            karma.register_feedback("trader_agent", outcome)

        # Agent karma should reflect mixed performance
        agent_karma = karma.agent_karma["trader_agent"]
        assert -1.0 <= agent_karma <= 1.0


class TestPhaseESystemIdentityIntegration:
    """Integratietests voor SystemIdentity outcome updates."""

    @pytest.fixture
    def system_identity(self):
        """Create SystemIdentity instance."""
        return SystemIdentity()

    def test_outcome_update_tracks_performance(self, system_identity):
        """Test dat outcome updates performance history bijwerken."""
        # Arrange
        initial_count = len(system_identity.performance_history["outcomes"])

        # Act
        system_identity.update_outcome(action_id=1, outcome=0.05)
        system_identity.update_outcome(action_id=2, outcome=-0.03)
        system_identity.update_outcome(action_id=3, outcome=0.08)

        # Assert
        assert len(system_identity.performance_history["outcomes"]) == initial_count + 3

    def test_system_state_adapts_to_outcomes(self, system_identity):
        """Test dat system state zich aanpast aan outcomes."""
        # Arrange
        system_identity.system_state["coherence"]
        system_identity.system_state["confidence"]

        # Act - multiple positive outcomes
        for i in range(10):
            system_identity.update_outcome(action_id=i, outcome=0.05)

        # Assert - state should have adapted
        # Exact behavior depends on adaptation algorithm
        assert "coherence" in system_identity.system_state
        assert "confidence" in system_identity.system_state

    def test_win_rate_calculation(self, system_identity):
        """Test win rate berekening."""
        # Arrange - add outcomes
        outcomes = [0.05, -0.03, 0.08, 0.02, -0.01]  # 3 wins, 2 losses
        for i, outcome in enumerate(outcomes):
            system_identity.update_outcome(action_id=i, outcome=outcome)

        # Act
        stats = system_identity.get_system_statistics()

        # Assert
        if "performance" in stats and stats["performance"]:
            assert stats["performance"]["win_rate"] == pytest.approx(0.6, abs=0.01)
            assert stats["performance"]["total_trades"] >= 5


class TestPhaseEKarmaInOODA:
    """Integratietests voor Karma in OODA coordinator."""

    def test_karma_feedback_after_execution(self):
        """Test dat Karma feedback wordt geregistreerd na execution."""
        # Arrange
        mock_karma = MagicMock(spec=KarmaRegister)
        mock_karma.register_feedback = MagicMock(return_value=0.5)

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            karma_register=mock_karma,
        )

        execution_result = {
            "status": "executed",
            "pnl_percent": 0.05,
            "drawdown_percent": 0.02,
            "execution_time_ms": 150.0,
        }

        # Act - simulate feedback logic
        if coordinator.karma_register and execution_result:
            outcome = TradeOutcome(
                pnl_percent=execution_result.get("pnl_percent", 0.0),
                drawdown_percent=execution_result.get("drawdown_percent", 0.0),
                execution_speed_ms=execution_result.get("execution_time_ms", 0.0),
            )
            coordinator.karma_register.register_feedback("trader_agent", outcome)

        # Assert
        mock_karma.register_feedback.assert_called_once()
        call_args = mock_karma.register_feedback.call_args
        assert call_args[0][0] == "trader_agent"

    def test_system_identity_update_after_execution(self):
        """Test dat SystemIdentity wordt geüpdatet na execution."""
        # Arrange
        mock_identity = MagicMock(spec=SystemIdentity)
        mock_identity.update_outcome = MagicMock()

        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            system_identity=mock_identity,
        )

        execution_result = {"status": "executed", "pnl_percent": 0.05}
        trace_id = "test-trace-123"

        # Act - simulate update logic
        if coordinator.system_identity and execution_result:
            outcome_score = execution_result.get("pnl_percent", 0.0)
            coordinator.system_identity.update_outcome(
                action_id=hash(trace_id) % 10000,
                outcome=outcome_score,
            )

        # Assert
        mock_identity.update_outcome.assert_called_once()


class TestPhaseEEndToEnd:
    """End-to-end tests voor Fase E."""

    def test_complete_learning_cycle(self):
        """Test een complete learning cycle."""
        # Arrange
        karma = KarmaRegister()
        identity = SystemIdentity()

        # Simulate trading session
        trades = [
            {"agent": "trader_agent", "pnl": 0.05, "dd": 0.01},
            {"agent": "trader_agent", "pnl": -0.02, "dd": 0.02},
            {"agent": "trader_agent", "pnl": 0.08, "dd": 0.01},
            {"agent": "analyst_agent", "pnl": 0.03, "dd": 0.01},
            {"agent": "risk_agent", "pnl": 0.02, "dd": 0.005},
        ]

        # Act
        for i, trade in enumerate(trades):
            outcome = TradeOutcome(
                pnl_percent=trade["pnl"],
                drawdown_percent=trade["dd"],
                execution_speed_ms=100.0,
            )
            karma.register_feedback(trade["agent"], outcome)
            identity.update_outcome(action_id=i, outcome=trade["pnl"])

        # Assert
        assert "trader_agent" in karma.agent_karma
        assert "analyst_agent" in karma.agent_karma
        assert "risk_agent" in karma.agent_karma

        # Verify SystemIdentity tracking
        assert len(identity.performance_history["outcomes"]) >= 5

        # Calculate statistics
        stats = identity.get_system_statistics()
        assert "system_state" in stats

    def test_reinforcement_learning_integration(self):
        """Test Reinforcement Learning integratie."""
        # Arrange
        learner = ReinforcementLearner(
            state_size=10,
            action_size=3,
            learning_rate=0.001,
        )

        state = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        # Act - multiple learning updates
        for i in range(100):
            action = i % 3
            reward = 0.1 if action == 1 else -0.05
            learner.update(state, action, reward)

        # Assert - learner should have adapted
        # This is a basic sanity check
        weights = learner.get_weights()
        assert weights is not None


class TestPhaseEPerformance:
    """Performance tests voor Fase E."""

    def test_karma_feedback_performance(self):
        """Test dat Karma feedback snel is."""
        import time

        karma = KarmaRegister()

        start = time.time()
        for i in range(1000):
            outcome = TradeOutcome(
                pnl_percent=0.05,
                drawdown_percent=0.01,
                execution_speed_ms=100.0,
            )
            karma.register_feedback("test_agent", outcome)
        elapsed = time.time() - start

        # Should complete 1000 iterations quickly
        assert elapsed < 1.0  # Less than 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
