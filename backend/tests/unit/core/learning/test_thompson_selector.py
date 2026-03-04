"""
Tests for ThompsonSamplingSelector.
"""

import random
from backend.core.learning.thompson_selector import ThompsonSamplingSelector


class TestThompsonSamplingSelector:

    def test_single_strategy_always_selected(self):
        """With only one strategy, it must always be selected."""
        ts = ThompsonSamplingSelector(["only_one"])
        for _ in range(10):
            assert ts.select_strategy() == "only_one"

    def test_update_increases_alpha_on_win(self):
        """Positive reward should increment alpha."""
        ts = ThompsonSamplingSelector(["a", "b"])
        ts.update("a", reward=1.0)
        assert ts.alpha["a"] == 2.0
        assert ts.beta["a"] == 1.0

    def test_update_increases_beta_on_loss(self):
        """Zero/negative reward should increment beta."""
        ts = ThompsonSamplingSelector(["a", "b"])
        ts.update("a", reward=-0.5)
        assert ts.alpha["a"] == 1.0
        assert ts.beta["a"] == 2.0

    def test_convergence_to_best_strategy(self):
        """After many updates, Thompson should favor the best strategy."""
        random.seed(42)
        ts = ThompsonSamplingSelector(["good", "bad"])

        # Simulate: good wins 80%, bad wins 20%
        for _ in range(200):
            ts.update("good", reward=1.0 if random.random() < 0.8 else -1.0)
            ts.update("bad", reward=1.0 if random.random() < 0.2 else -1.0)

        # Sample 100 selections, majority should be "good"
        selections = [ts.select_strategy() for _ in range(100)]
        good_count = selections.count("good")
        assert good_count > 80, f"Expected >80 good selections, got {good_count}"

    def test_get_weights(self):
        """Weights should be the expected value of Beta distributions."""
        ts = ThompsonSamplingSelector(["x"])
        # Beta(1,1) => E = 0.5
        weights = ts.get_weights()
        assert abs(weights["x"] - 0.5) < 0.01

        # After 9 wins, 0 losses: Beta(10, 1) => E = 10/11
        for _ in range(9):
            ts.update("x", reward=1.0)
        weights = ts.get_weights()
        assert abs(weights["x"] - (10.0 / 11.0)) < 0.01

    def test_empty_strategies_raises(self):
        """Creating with empty list should raise ValueError."""
        try:
            ThompsonSamplingSelector([])
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_unknown_strategy_update_raises(self):
        """Updating an unknown strategy should raise ValueError."""
        ts = ThompsonSamplingSelector(["a"])
        try:
            ts.update("nonexistent", reward=1.0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
