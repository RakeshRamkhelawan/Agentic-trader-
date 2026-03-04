"""
Thompson Sampling Strategy Selector.

Uses a Bayesian Multi-Armed Bandit approach (Beta distributions)
to adaptively select the best-performing trading strategy over time.
Replaces the slower EMA-based StrategyWeightAdapter.
"""

import random


class ThompsonSamplingSelector:
    """
    Bayesian strategy selector using Thompson Sampling.

    Each strategy maintains a Beta(alpha, beta) distribution.
    - alpha tracks successes (profitable trades)
    - beta tracks failures (losing trades)

    Selection samples from each Beta distribution and picks the highest.
    Over time this converges on the best strategy while still exploring.
    """

    def __init__(self, strategies: list[str]):
        """
        Args:
            strategies: List of strategy identifiers to track.
        """
        if not strategies:
            raise ValueError("At least one strategy is required")

        # Uninformative prior: Beta(1, 1) = Uniform(0, 1)
        self.alpha: dict[str, float] = {s: 1.0 for s in strategies}
        self.beta: dict[str, float] = {s: 1.0 for s in strategies}

    @property
    def strategies(self) -> list[str]:
        return list(self.alpha.keys())

    def select_strategy(self) -> str:
        """
        Sample from each strategy's Beta distribution and return
        the strategy with the highest sampled value.
        """
        samples = {
            s: random.betavariate(self.alpha[s], self.beta[s])
            for s in self.alpha
        }
        return max(samples, key=samples.get)

    def update(self, strategy: str, reward: float) -> None:
        """
        Update the Beta distribution for a strategy based on trade outcome.

        Args:
            strategy: The strategy identifier.
            reward: Positive value = success, zero or negative = failure.
        """
        if strategy not in self.alpha:
            raise ValueError(f"Unknown strategy: {strategy}")

        if reward > 0:
            self.alpha[strategy] += 1.0
        else:
            self.beta[strategy] += 1.0

    def get_weights(self) -> dict[str, float]:
        """
        Return the expected success probability (mean of Beta distribution)
        for each strategy: E[Beta(a,b)] = a / (a + b).
        """
        return {
            s: self.alpha[s] / (self.alpha[s] + self.beta[s])
            for s in self.alpha
        }

    def get_stats(self) -> dict[str, dict[str, float]]:
        """Return full alpha/beta stats per strategy for monitoring."""
        return {
            s: {
                "alpha": self.alpha[s],
                "beta": self.beta[s],
                "expected_winrate": self.alpha[s] / (self.alpha[s] + self.beta[s]),
            }
            for s in self.alpha
        }
