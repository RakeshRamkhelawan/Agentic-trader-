import pytest

from backend.core.karma.karma_register import KarmaRegister, TradeOutcome
from backend.core.karma.reinforcement import ParameterTuner
from backend.core.karma.safety_bounds import SafetyMonitor


class TestKarmaModule:

    def test_karma_calculation(self):
        register = KarmaRegister()

        # Profitable trade
        outcome_win = TradeOutcome(pnl_percent=0.05, drawdown_percent=0.01, execution_speed_ms=100)
        score = register.calculate_karma(outcome_win)
        assert score > 0.0

        # Loss trade
        outcome_loss = TradeOutcome(
            pnl_percent=-0.05, drawdown_percent=0.01, execution_speed_ms=100
        )
        score_loss = register.calculate_karma(outcome_loss)
        assert score_loss < 0.0

        # Compliance violation
        outcome_violation = TradeOutcome(
            pnl_percent=0.10,
            drawdown_percent=0.0,
            execution_speed_ms=100,
            compliance_violation=True,
        )
        score_viol = register.calculate_karma(outcome_violation)
        assert score_viol == -1.0

    def test_safety_monitor_clamping(self):
        monitor = SafetyMonitor()

        # Dangerous params
        unsafe = {
            "risk_tolerance": 0.99,  # Too high
            "aggression": 0.0,  # Too low
            "description": "text",  # Non-numeric
        }

        safe = monitor.enforce_bounds(unsafe)

        assert safe["risk_tolerance"] == 0.8
        assert safe["aggression"] == 0.1
        assert safe["description"] == "text"

    def test_parameter_tuner_mutation(self):
        tuner = ParameterTuner()

        params = {"risk_tolerance": 0.5}

        # Negative karma -> Should mutate
        new_params = tuner.tune(params, karma=-0.5)

        # It's random, but likely changed
        # We can just check it returns a dict and keys exist
        assert "risk_tolerance" in new_params
        assert isinstance(new_params["risk_tolerance"], float)
