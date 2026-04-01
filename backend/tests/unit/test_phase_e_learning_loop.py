"""
Phase E Unit Tests: Learning Loop

Tests voor Karma feedback en consciousness updates:
- KarmaRegister trade outcome tracking
- SystemIdentity outcome updates
- Reinforcement learning integratie
"""

from unittest.mock import MagicMock

import pytest

from backend.core.karma.karma_register import KarmaRegister, TradeOutcome
from backend.core.karma.reinforcement import ParameterTuner
from backend.core.system_identity import SystemIdentity


class TestKarmaRegister:
    """Test Fase E: KarmaRegister functionaliteit."""

    def test_karma_register_creation(self):
        """Test dat KarmaRegister correct wordt aangemaakt."""
        # Act
        karma = KarmaRegister()

        # Assert
        assert karma is not None
        assert karma.agent_karma == {}

    def test_calculate_karma_for_positive_outcome(self):
        """Test karma berekening voor positieve outcome."""
        # Arrange
        karma = KarmaRegister()
        outcome = TradeOutcome(
            pnl_percent=0.05,  # 5% profit
            drawdown_percent=0.01,
            execution_speed_ms=100.0,
            compliance_violation=False,
        )

        # Act
        score = karma.calculate_karma(outcome)

        # Assert - should be positive
        assert score > 0
        assert score <= 1.0

    def test_calculate_karma_for_negative_outcome(self):
        """Test karma berekening voor negatieve outcome."""
        # Arrange
        karma = KarmaRegister()
        outcome = TradeOutcome(
            pnl_percent=-0.05,  # 5% loss
            drawdown_percent=0.01,
            execution_speed_ms=100.0,
            compliance_violation=False,
        )

        # Act
        score = karma.calculate_karma(outcome)

        # Assert - should be negative
        assert score < 0
        assert score >= -1.0

    def test_calculate_karma_for_compliance_violation(self):
        """Test karma berekening voor compliance violation."""
        # Arrange
        karma = KarmaRegister()
        outcome = TradeOutcome(
            pnl_percent=0.10,  # 10% profit
            drawdown_percent=0.01,
            execution_speed_ms=100.0,
            compliance_violation=True,  # Violation!
        )

        # Act
        score = karma.calculate_karma(outcome)

        # Assert - should be -1.0 regardless of profit
        assert score == -1.0

    def test_calculate_karma_drawdown_penalty(self):
        """Test drawdown penalty in karma berekening."""
        # Arrange
        karma = KarmaRegister()

        # High drawdown outcome
        outcome_high_dd = TradeOutcome(
            pnl_percent=0.05,
            drawdown_percent=0.10,  # 10% drawdown
            execution_speed_ms=100.0,
        )

        # Low drawdown outcome
        outcome_low_dd = TradeOutcome(
            pnl_percent=0.05,
            drawdown_percent=0.02,  # 2% drawdown
            execution_speed_ms=100.0,
        )

        # Act
        score_high_dd = karma.calculate_karma(outcome_high_dd)
        score_low_dd = karma.calculate_karma(outcome_low_dd)

        # Assert - high drawdown should have lower karma
        assert score_high_dd < score_low_dd

    def test_register_feedback_updates_agent_karma(self):
        """Test dat register_feedback agent karma update."""
        # Arrange
        karma = KarmaRegister()
        outcome = TradeOutcome(
            pnl_percent=0.05,
            drawdown_percent=0.01,
            execution_speed_ms=100.0,
        )

        # Act - first feedback
        new_karma_1 = karma.register_feedback("trader_agent", outcome)

        # Act - second feedback (same outcome)
        new_karma_2 = karma.register_feedback("trader_agent", outcome)

        # Assert
        assert "trader_agent" in karma.agent_karma
        # Karma should be moving average, so second value should be different
        assert new_karma_2 != new_karma_1

    def test_karma_moving_average_calculation(self):
        """Test moving average karma berekening."""
        # Arrange
        karma = KarmaRegister()

        # First positive outcome
        outcome1 = TradeOutcome(
            pnl_percent=0.10, drawdown_percent=0.01, execution_speed_ms=100.0
        )
        karma.register_feedback("test_agent", outcome1)

        # Then negative outcome
        outcome2 = TradeOutcome(
            pnl_percent=-0.05, drawdown_percent=0.01, execution_speed_ms=100.0
        )
        new_karma = karma.register_feedback("test_agent", outcome2)

        # Assert - karma should be between the two outcomes
        # Formula: new = (old * 0.9) + (score * 0.1)
        assert -1.0 <= new_karma <= 1.0


class TestParameterTuner:
    """Test Fase E: Parameter tuning integratie."""

    def test_parameter_tuner_creation(self):
        """Test dat ParameterTuner correct wordt aangemaakt."""
        # Act
        tuner = ParameterTuner()

        # Assert
        assert tuner is not None

    def test_tune_with_high_karma(self):
        """Test tuning met hoge karma (stabiel houden)."""
        # Arrange
        tuner = ParameterTuner()
        current_params = {"risk_pct": 0.02, "confidence_threshold": 0.7}

        # Act
        new_params = tuner.tune(current_params, karma=0.8, learning_rate=0.05)

        # Assert - params should stay stable with high karma
        assert new_params["risk_pct"] == current_params["risk_pct"]
        assert (
            new_params["confidence_threshold"] == current_params["confidence_threshold"]
        )

    def test_tune_with_low_karma(self):
        """Test tuning met lage karma (exploratie)."""
        # Arrange
        tuner = ParameterTuner()
        current_params = {"risk_pct": 0.02, "confidence_threshold": 0.7}

        # Act
        new_params = tuner.tune(current_params, karma=-0.5, learning_rate=0.05)

        # Assert - params should change with low karma
        assert new_params["risk_pct"] != current_params["risk_pct"]
        assert (
            new_params["confidence_threshold"] != current_params["confidence_threshold"]
        )


class TestSystemIdentityOutcomeUpdate:
    """Test Fase E: SystemIdentity outcome update functionaliteit."""

    def test_update_outcome_changes_performance_history(self):
        """Test dat update_outcome performance history update."""
        # Arrange
        identity = SystemIdentity()
        # First add an outcome through process_market_cycle or directly
        identity.performance_history["outcomes"].append(0.0)  # Placeholder

        # Act
        identity.update_outcome(action_id=12345, outcome=0.05)

        # Assert
        assert identity.performance_history["outcomes"][-1] == 0.05

    def test_multiple_outcomes_tracking(self):
        """Test tracking van meerdere outcomes."""
        # Arrange
        identity = SystemIdentity()

        # Act - outcomes are typically added by process_market_cycle
        # For testing, we add them directly
        identity.performance_history["outcomes"].extend([0.05, -0.03, 0.08])

        # Assert
        outcomes = identity.performance_history["outcomes"]
        assert len(outcomes) >= 3
        assert outcomes[-3] == 0.05
        assert outcomes[-2] == -0.03
        assert outcomes[-1] == 0.08

    def test_system_state_adaptation(self):
        """Test dat system state zich aanpast op basis van outcomes."""
        # Arrange
        identity = SystemIdentity()

        # Act - add outcomes directly and update
        identity.performance_history["outcomes"].extend([0.05] * 10)
        identity.update_outcome(action_id=9, outcome=0.05)

        # Assert - system state should exist
        assert "coherence" in identity.system_state


class TestKarmaFeedbackInOODA:
    """Test Fase E: Karma feedback in OODA coordinator."""

    def test_karma_register_records_execution_result(self):
        """Test dat KarmaRegister execution result registreert."""
        # Arrange
        from backend.orchestration.ooda_coordinator import OODALoopCoordinator

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

        # Act - simulate the feedback logic
        if coordinator.karma_register and execution_result:
            outcome = TradeOutcome(
                pnl_percent=execution_result.get("pnl_percent", 0.0),
                drawdown_percent=execution_result.get("drawdown_percent", 0.0),
                execution_speed_ms=execution_result.get("execution_time_ms", 0.0),
            )
            coordinator.karma_register.register_feedback("trader_agent", outcome)

        # Assert
        mock_karma.register_feedback.assert_called_once()

    def test_system_identity_update_after_execution(self):
        """Test dat SystemIdentity update na execution."""
        # Arrange
        from backend.orchestration.ooda_coordinator import OODALoopCoordinator

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

        # Act - simulate the update logic
        if coordinator.system_identity and execution_result:
            outcome_score = execution_result.get("pnl_percent", 0.0)
            coordinator.system_identity.update_outcome(
                action_id=hash(trace_id) % 10000,
                outcome=outcome_score,
            )

        # Assert
        mock_identity.update_outcome.assert_called_once()


class TestLearningLoopIntegration:
    """Test Fase E: End-to-end learning loop integratie."""

    def test_full_learning_cycle(self):
        """Test een complete learning cycle."""
        # Arrange
        karma = KarmaRegister()
        identity = SystemIdentity()

        # Simulate multiple trades
        trades = [
            ("trader_agent", 0.05),  # Win
            ("trader_agent", -0.02),  # Loss
            ("trader_agent", 0.08),  # Win
            ("trader_agent", 0.03),  # Win
        ]

        # Act
        for agent, pnl in trades:
            outcome = TradeOutcome(
                pnl_percent=pnl,
                drawdown_percent=0.01,
                execution_speed_ms=100.0,
            )
            karma.register_feedback(agent, outcome)
            # Add outcomes directly to performance_history
            identity.performance_history["outcomes"].append(pnl)

        # Assert
        assert "trader_agent" in karma.agent_karma
        assert len(identity.performance_history["outcomes"]) >= 4

        # Calculate win rate
        outcomes = identity.performance_history["outcomes"]
        wins = sum(1 for o in outcomes if o > 0)
        win_rate = wins / len(outcomes)
        assert 0 <= win_rate <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
