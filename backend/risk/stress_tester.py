"""Stress testing module for risk management."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np


class StressScenario(Enum):
    """Predefined stress scenarios."""
    MARKET_CRASH_2008 = "market_crash_2008"
    COVID_CRASH_2020 = "covid_crash_2020"
    INTEREST_RATE_SHOCK = "interest_rate_shock"
    INFLATION_SPIKE = "inflation_spike"
    CRYPTO_WINTER = "crypto_winter"
    FLASH_CRASH = "flash_crash"
    CUSTOM = "custom"


@dataclass
class StressTestResult:
    """Result of a stress test."""
    scenario: str
    portfolio_value_before: float
    portfolio_value_after: float
    pnl: float
    pnl_percentage: float
    max_drawdown: float

    # Risk metrics during stress
    var_95: float
    var_99: float

    # Scenario details
    scenario_params: dict[str, Any]

    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "portfolio_value_before": round(self.portfolio_value_before, 2),
            "portfolio_value_after": round(self.portfolio_value_after, 2),
            "pnl": round(self.pnl, 2),
            "pnl_percentage": f"{self.pnl_percentage * 100:.2f}%",
            "max_drawdown": f"{self.max_drawdown * 100:.2f}%",
            "var_95": round(self.var_95, 2),
            "var_99": round(self.var_99, 2),
            "timestamp": self.timestamp.isoformat(),
        }


class StressTester:
    """
    Portfolio stress testing system.

    Simulates portfolio performance under various stress scenarios
    to identify potential vulnerabilities.
    """

    # Predefined scenario parameters
    SCENARIOS = {
        StressScenario.MARKET_CRASH_2008: {
            "description": "2008 Financial Crisis scenario",
            "equity_shock": -0.40,
            "credit_spread_widening": 0.05,
            "volatility_spike": 3.0,
            "correlation_increase": 0.3,
        },
        StressScenario.COVID_CRASH_2020: {
            "description": "March 2020 COVID crash",
            "equity_shock": -0.35,
            "bond_flight_to_quality": 0.05,
            "volatility_spike": 4.0,
            "liquidity_crunch": True,
        },
        StressScenario.INTEREST_RATE_SHOCK: {
            "description": "Sudden interest rate increase",
            "rate_increase_bps": 200,
            "bond_price_impact": -0.10,
            "equity_valuation_impact": -0.15,
        },
        StressScenario.INFLATION_SPIKE: {
            "description": "Unexpected inflation surge",
            "inflation_increase": 0.03,
            "real_rates_increase": 0.02,
            "equity_impact": -0.20,
            "commodity_boom": 0.30,
        },
        StressScenario.CRYPTO_WINTER: {
            "description": "Cryptocurrency bear market",
            "btc_shock": -0.70,
            "altcoin_shock": -0.80,
            "correlation_to_equities": 0.5,
        },
        StressScenario.FLASH_CRASH: {
            "description": "Intraday flash crash",
            "instant_drop": -0.10,
            "recovery_time_hours": 2,
            "liquidity_dry_up": True,
        },
    }

    def __init__(self):
        self.test_history: list[StressTestResult] = []

    def run_stress_test(
        self,
        portfolio_value: float,
        scenario: StressScenario,
        custom_params: dict | None = None,
        positions: list[dict] | None = None,
    ) -> StressTestResult:
        """
        Run stress test for a portfolio.

        Args:
            portfolio_value: Current portfolio value
            scenario: Stress scenario to simulate
            custom_params: Custom scenario parameters
            positions: Portfolio positions breakdown

        Returns:
            Stress test result
        """
        # Get scenario parameters
        if scenario == StressScenario.CUSTOM and custom_params:
            params = custom_params
        else:
            params = self.SCENARIOS.get(scenario, {})

        # Calculate impact (simplified model)
        if positions:
            impact = self._calculate_position_impact(positions, params)
        else:
            impact = self._calculate_aggregate_impact(params)

        # Apply impact to portfolio
        pnl_percentage = impact
        pnl = portfolio_value * pnl_percentage
        portfolio_value_after = portfolio_value + pnl

        # Calculate max drawdown (worse case within scenario)
        max_drawdown = abs(min(impact * 1.2, -0.01))  # 20% worse than final

        # Calculate VaR under stress
        stressed_volatility = 0.05 * params.get("volatility_spike", 1)
        var_95 = portfolio_value_after * 1.645 * stressed_volatility
        var_99 = portfolio_value_after * 2.326 * stressed_volatility

        result = StressTestResult(
            scenario=scenario.value,
            portfolio_value_before=portfolio_value,
            portfolio_value_after=portfolio_value_after,
            pnl=pnl,
            pnl_percentage=pnl_percentage,
            max_drawdown=max_drawdown,
            var_95=var_95,
            var_99=var_99,
            scenario_params=params,
            timestamp=datetime.utcnow(),
        )

        self.test_history.append(result)
        return result

    def _calculate_position_impact(
        self,
        positions: list[dict],
        params: dict,
    ) -> float:
        """Calculate impact based on position breakdown."""
        total_impact = 0
        total_value = sum(p.get("value", 0) for p in positions)

        if total_value == 0:
            return 0

        for position in positions:
            asset_class = position.get("asset_class", "equity")
            weight = position.get("value", 0) / total_value

            # Apply asset-class specific shocks
            if asset_class == "equity":
                shock = params.get("equity_shock", -0.20)
            elif asset_class == "bond":
                shock = params.get("bond_price_impact", -0.05)
            elif asset_class == "crypto":
                shock = params.get("btc_shock", -0.50)
            elif asset_class == "commodity":
                shock = params.get("commodity_boom", 0) if params.get("commodity_boom") else -0.15
            else:
                shock = -0.10  # Default

            total_impact += weight * shock

        return total_impact

    def _calculate_aggregate_impact(self, params: dict) -> float:
        """Calculate aggregate portfolio impact."""
        # Simplified: use equity shock as primary driver
        return params.get("equity_shock", -0.20)

    def run_all_scenarios(
        self,
        portfolio_value: float,
        positions: list[dict] | None = None,
    ) -> dict[str, StressTestResult]:
        """Run all predefined stress scenarios."""
        results = {}

        for scenario in StressScenario:
            if scenario != StressScenario.CUSTOM:
                results[scenario.value] = self.run_stress_test(
                    portfolio_value=portfolio_value,
                    scenario=scenario,
                    positions=positions,
                )

        return results

    def get_worst_scenario(
        self,
        results: dict[str, StressTestResult],
    ) -> tuple:
        """Find worst performing scenario."""
        if not results:
            return None, None

        worst = min(results.values(), key=lambda r: r.pnl_percentage)
        worst_name = [k for k, v in results.items() if v == worst][0]

        return worst_name, worst

    def generate_report(self, results: dict[str, StressTestResult]) -> dict:
        """Generate comprehensive stress test report."""
        worst_name, worst_result = self.get_worst_scenario(results)

        total_scenarios = len(results)
        negative_scenarios = sum(1 for r in results.values() if r.pnl < 0)

        avg_loss = np.mean([r.pnl for r in results.values()])
        max_loss = min([r.pnl for r in results.values()])

        return {
            "summary": {
                "scenarios_tested": total_scenarios,
                "negative_outcomes": negative_scenarios,
                "worst_scenario": worst_name,
                "worst_loss_percentage": f"{worst_result.pnl_percentage * 100:.2f}%" if worst_result else "N/A",
            },
            "statistics": {
                "average_pnl": round(avg_loss, 2),
                "max_loss": round(max_loss, 2),
                "median_var_95": round(np.median([r.var_95 for r in results.values()]), 2),
            },
            "recommendations": self._generate_recommendations(results),
            "details": {k: v.to_dict() for k, v in results.items()},
        }

    def _generate_recommendations(
        self,
        results: dict[str, StressTestResult],
    ) -> list[str]:
        """Generate risk management recommendations."""
        recommendations = []

        worst_name, worst = self.get_worst_scenario(results)

        if worst and worst.pnl_percentage < -0.30:
            recommendations.append(
                f"CRITICAL: {worst_name} shows losses >30%. Consider reducing exposure."
            )

        negative_count = sum(1 for r in results.values() if r.pnl < 0)
        if negative_count > len(results) * 0.7:
            recommendations.append(
                "Portfolio shows vulnerability in most scenarios. Diversification recommended."
            )

        high_var_count = sum(1 for r in results.values() if r.var_95 / r.portfolio_value_before > 0.05)
        if high_var_count > 3:
            recommendations.append(
                "High VaR in multiple scenarios. Consider hedging strategies."
            )

        return recommendations


# Global stress tester
stress_tester = StressTester()
