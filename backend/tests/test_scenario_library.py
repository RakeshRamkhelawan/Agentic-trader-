"""
Tests voor Scenario Library.

Test pre-built scenarios en dataset creation.
"""

from backend.core.schemas.ooda_types import MarketRegime
from backend.testing.scenario_library import ScenarioLibrary


class TestScenarioLibrary:
    """Tests for ScenarioLibrary."""

    def test_trending_bull_scenario(self):
        """Trending bull scenario."""
        scenario = ScenarioLibrary.trending_bull()

        assert scenario.name == "trending_bull"
        assert scenario.expected_regime == MarketRegime.TRENDING_UP
        assert len(scenario.data_points) > 0
        assert scenario.symbol == "BTC/USDT"

        # Should have price increase
        start_price = scenario.data_points[0].open
        end_price = scenario.data_points[-1].close
        assert end_price > start_price

    def test_trending_bear_scenario(self):
        """Trending bear scenario."""
        scenario = ScenarioLibrary.trending_bear()

        assert scenario.name == "trending_bear"
        assert scenario.expected_regime == MarketRegime.TRENDING_DOWN

        # Should have price decrease
        start_price = scenario.data_points[0].open
        end_price = scenario.data_points[-1].close
        assert end_price < start_price

    def test_ranging_consolidation_scenario(self):
        """Ranging consolidation scenario."""
        scenario = ScenarioLibrary.ranging_consolidation()

        assert scenario.name == "ranging_consolidation"
        assert scenario.expected_regime == MarketRegime.RANGING
        assert scenario.symbol == "ETH/USDT"

    def test_volatile_choppy_scenario(self):
        """Volatile choppy scenario."""
        scenario = ScenarioLibrary.volatile_choppy()

        assert scenario.name == "volatile_choppy"
        assert scenario.expected_regime == MarketRegime.VOLATILE
        assert scenario.symbol == "SOL/USDT"

    def test_flash_crash_recovery_scenario(self):
        """Flash crash recovery scenario."""
        scenario = ScenarioLibrary.flash_crash_recovery()

        assert scenario.name == "flash_crash_recovery"
        assert scenario.expected_regime == MarketRegime.VOLATILE
        assert scenario.timeframe == "1h"

    def test_gentle_uptrend_scenario(self):
        """Gentle uptrend scenario."""
        scenario = ScenarioLibrary.gentle_uptrend()

        assert scenario.name == "gentle_uptrend"
        assert scenario.expected_regime == MarketRegime.TRENDING_UP
        assert len(scenario.data_points) == 60  # 60 days

    def test_all_scenarios_returns_dataset(self):
        """all_scenarios returns EvaluationDataset."""
        dataset = ScenarioLibrary.all_scenarios()

        scenarios = dataset.list_scenarios()

        assert len(scenarios) >= 6
        assert "trending_bull" in scenarios
        assert "trending_bear" in scenarios
        assert "ranging_consolidation" in scenarios
        assert "volatile_choppy" in scenarios
        assert "flash_crash_recovery" in scenarios
        assert "gentle_uptrend" in scenarios

    def test_all_scenarios_no_duplicates(self):
        """All scenarios have unique names."""
        dataset = ScenarioLibrary.all_scenarios()

        scenarios = dataset.list_scenarios()

        # No duplicates
        assert len(scenarios) == len(set(scenarios))

    def test_scenario_metadata_present(self):
        """Scenarios have metadata."""
        scenario = ScenarioLibrary.trending_bull()

        assert "category" in scenario.metadata
        assert scenario.metadata["category"] == "trending"
