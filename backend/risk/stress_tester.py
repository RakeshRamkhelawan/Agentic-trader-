"""
Stress Testing Suite - Scenario Analysis for Portfolio Risk.

Simulates extreme market conditions (2008 crisis, flash crash, etc.) to test strategy robustness.
Used for regulatory compliance (Basel III, MiFID II stress tests).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import numpy as np


class StressScenario(str, Enum):
    """Predefined stress test scenarios."""

    CRISIS_2008 = "2008_financial_crisis"
    FLASH_CRASH = "flash_crash"
    VOLATILITY_SPIKE = "volatility_spike"
    RATE_SHOCK = "interest_rate_shock"
    CURRENCY_CRASH = "currency_crash"
    TECH_COLLAPSE = "tech_sector_collapse"


@dataclass
class StressTestResult:
    """Result of a stress test scenario."""

    scenario: StressScenario
    portfolio_value_before: float
    portfolio_value_after: float
    max_drawdown: float  # Percentage
    recovery_days: Optional[int]  # Days to recover or None if not recovered
    affected_assets: List[str]  # Which assets were hit hardest


class StressTestSuite:
    """
    Run stress tests on portfolio under extreme scenarios.

    Each scenario simulates a historical crisis or market shock.
    """

    def __init__(self):
        self.scenarios = self._define_scenarios()

    def _define_scenarios(self) -> Dict[StressScenario, Dict[str, float]]:
        """
        Define asset price shocks for each scenario.

        Returns:
            Dict mapping scenario to asset shocks (negative = decline)
        """
        return {
            StressScenario.CRISIS_2008: {
                "equities": -0.50,  # 50% decline
                "corporate_bonds": -0.30,
                "commodities": -0.40,
                "crypto": -0.80,  # Crypto didn't exist then, but would have crashed
            },
            StressScenario.FLASH_CRASH: {
                "equities": -0.10,  # 10% intraday crash
                "commodities": -0.15,
                "crypto": -0.25,
            },
            StressScenario.VOLATILITY_SPIKE: {
                "equities": -0.20,  # VIX spike
                "crypto": -0.40,  # Crypto usually hits harder
                "bonds": 0.05,  # Bonds rally in crisis
            },
            StressScenario.RATE_SHOCK: {
                "bonds": -0.15,  # Rising rates = bond price decline
                "equities": -0.10,
                "real_estate": -0.15,
            },
            StressScenario.CURRENCY_CRASH: {
                "fx_exposure": -0.30,
                "emerging_market": -0.35,
                "commodities": -0.20,
            },
            StressScenario.TECH_COLLAPSE: {
                "tech_stocks": -0.40,
                "crypto": -0.60,
                "equities": -0.15,  # Spillover to broader market
            },
        }

    def apply_scenario(
        self,
        portfolio: Dict[str, float],  # {asset: value_usd}
        scenario: StressScenario,
    ) -> StressTestResult:
        """
        Apply a stress scenario to portfolio and calculate impact.

        Args:
            portfolio: Dict of asset values in USD
            scenario: Which scenario to apply

        Returns:
            StressTestResult with impact analysis

        Raises:
            ValueError: If portfolio is empty or scenario invalid
        """
        if not portfolio:
            raise ValueError("Portfolio cannot be empty")

        if scenario not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario}")

        scenario_shocks = self.scenarios[scenario]
        portfolio_value_before = sum(portfolio.values())

        # Apply shocks to each asset
        shocked_portfolio = {}
        affected_assets = []

        for asset, value in portfolio.items():
            # Find matching shock (exact match or partial)
            shock = 0.0
            for shock_key, shock_value in scenario_shocks.items():
                if shock_key.lower() in asset.lower():
                    shock = shock_value
                    affected_assets.append(asset)
                    break

            shocked_portfolio[asset] = value * (1 + shock)

        portfolio_value_after = sum(shocked_portfolio.values())
        max_drawdown = (
            portfolio_value_before - portfolio_value_after
        ) / portfolio_value_before

        # Estimate recovery (simplified: -1% recovery per day)
        recovery_days = None
        if max_drawdown > 0:
            recovery_days = int(
                abs(max_drawdown) * 100
            )  # 50% loss = ~50 days to recover

        return StressTestResult(
            scenario=scenario,
            portfolio_value_before=portfolio_value_before,
            portfolio_value_after=portfolio_value_after,
            max_drawdown=max_drawdown,
            recovery_days=recovery_days,
            affected_assets=affected_assets,
        )

    def run_all_scenarios(self, portfolio: Dict[str, float]) -> List[StressTestResult]:
        """
        Run all defined stress scenarios on portfolio.

        Args:
            portfolio: Dict of asset values

        Returns:
            List of StressTestResult for each scenario
        """
        results = []
        for scenario in StressScenario:
            try:
                result = self.apply_scenario(portfolio, scenario)
                results.append(result)
            except Exception as e:
                # Log but continue with other scenarios
                print(f"Error in scenario {scenario}: {e}")

        return results

    def get_worst_case(self, portfolio: Dict[str, float]) -> StressTestResult:
        """
        Find which scenario causes the biggest loss.

        Args:
            portfolio: Dict of asset values

        Returns:
            StressTestResult with largest drawdown
        """
        results = self.run_all_scenarios(portfolio)

        if not results:
            raise ValueError("No scenarios could be run")

        return max(results, key=lambda r: r.max_drawdown)
