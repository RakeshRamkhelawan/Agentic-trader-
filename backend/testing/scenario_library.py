"""
Scenario Library - Pre-built test scenarios.

Quick access to common market scenarios.
"""

from datetime import datetime, UTC

from backend.testing.market_datasets import MarketScenario, EvaluationDataset
from backend.testing.synthetic_data import (
    generate_trending_market,
    generate_ranging_market,
    generate_volatile_market,
    generate_flash_crash,
)
from backend.core.schemas.ooda_types import MarketRegime


class ScenarioLibrary:
    """
    Pre-configured market scenarios voor testing.
    """

    @staticmethod
    def trending_bull() -> MarketScenario:
        """
        Strong uptrend scenario (+50% over 30 days).

        Returns:
            Bull market scenario
        """
        return MarketScenario(
            name="trending_bull",
            description="Strong uptrend +50% over 30 days",
            symbol="BTC/USDT",
            timeframe="1d",
            data_points=generate_trending_market(
                start_price=40000.0,
                trend_strength=0.015,  # 1.5% daily
                num_days=30,
                volatility=0.01,
            ),
            expected_regime=MarketRegime.TRENDING_UP,
            metadata={
                "category": "trending",
                "direction": "up",
                "expected_trades": "long",
            },
        )

    @staticmethod
    def trending_bear() -> MarketScenario:
        """
        Strong downtrend scenario (-40% over 30 days).

        Returns:
            Bear market scenario
        """
        return MarketScenario(
            name="trending_bear",
            description="Strong downtrend -40% over 30 days",
            symbol="BTC/USDT",
            timeframe="1d",
            data_points=generate_trending_market(
                start_price=60000.0,
                trend_strength=-0.018,  # -1.8% daily
                num_days=30,
                volatility=0.015,
            ),
            expected_regime=MarketRegime.TRENDING_DOWN,
            metadata={
                "category": "trending",
                "direction": "down",
                "expected_trades": "short or avoid",
            },
        )

    @staticmethod
    def ranging_consolidation() -> MarketScenario:
        """
        Sideways market scenario (±5% range over 30 days).

        Returns:
            Ranging market scenario
        """
        return MarketScenario(
            name="ranging_consolidation",
            description="Sideways consolidation ±5% range",
            symbol="ETH/USDT",
            timeframe="1d",
            data_points=generate_ranging_market(
                center_price=3000.0, range_pct=0.05, num_days=30
            ),
            expected_regime=MarketRegime.RANGING,
            metadata={
                "category": "ranging",
                "expected_trades": "range trading or avoid",
            },
        )

    @staticmethod
    def volatile_choppy() -> MarketScenario:
        """
        High volatility choppy market (±8% daily swings).

        Returns:
            Volatile market scenario
        """
        return MarketScenario(
            name="volatile_choppy",
            description="High volatility choppy market ±8% swings",
            symbol="SOL/USDT",
            timeframe="1d",
            data_points=generate_volatile_market(
                start_price=150.0, volatility=0.08, num_days=30
            ),
            expected_regime=MarketRegime.VOLATILE,
            metadata={"category": "volatile", "expected_trades": "cautious or avoid"},
        )

    @staticmethod
    def flash_crash_recovery() -> MarketScenario:
        """
        Flash crash scenario (-20% crash met 6h recovery).

        Returns:
            Flash crash scenario
        """
        return MarketScenario(
            name="flash_crash_recovery",
            description="Flash crash -20% with 6h recovery",
            symbol="BTC/USDT",
            timeframe="1h",
            data_points=generate_flash_crash(
                start_price=50000.0, crash_depth=0.20, recovery_hours=6
            ),
            expected_regime=MarketRegime.VOLATILE,
            metadata={
                "category": "crash",
                "expected_trades": "circuit breaker should trip",
            },
        )

    @staticmethod
    def gentle_uptrend() -> MarketScenario:
        """
        Gentle uptrend scenario (+20% over 60 days).

        Returns:
            Gentle uptrend scenario
        """
        return MarketScenario(
            name="gentle_uptrend",
            description="Gentle uptrend +20% over 60 days",
            symbol="BTC/USDT",
            timeframe="1d",
            data_points=generate_trending_market(
                start_price=45000.0,
                trend_strength=0.003,  # 0.3% daily
                num_days=60,
                volatility=0.008,
            ),
            expected_regime=MarketRegime.TRENDING_UP,
            metadata={"category": "trending", "direction": "up", "strength": "gentle"},
        )

    @staticmethod
    def all_scenarios() -> EvaluationDataset:
        """
        Get all pre-built scenarios.

        Returns:
            EvaluationDataset met alle scenarios
        """
        dataset = EvaluationDataset()

        dataset.add_scenario(ScenarioLibrary.trending_bull())
        dataset.add_scenario(ScenarioLibrary.trending_bear())
        dataset.add_scenario(ScenarioLibrary.ranging_consolidation())
        dataset.add_scenario(ScenarioLibrary.volatile_choppy())
        dataset.add_scenario(ScenarioLibrary.flash_crash_recovery())
        dataset.add_scenario(ScenarioLibrary.gentle_uptrend())

        return dataset
