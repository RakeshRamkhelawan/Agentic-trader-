"""
Tests voor Market Datasets.

Test OHLCV, MarketScenario, en EvaluationDataset.
"""

from datetime import UTC, datetime

import pytest

from backend.core.schemas.ooda_types import MarketRegime
from backend.testing.market_datasets import OHLCV, EvaluationDataset, MarketScenario


class TestOHLCV:
    """Tests for OHLCV dataclass."""

    def test_valid_ohlcv(self):
        """Create valid OHLCV."""
        candle = OHLCV(
            timestamp=datetime.now(UTC),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
        )

        assert candle.open == 100.0
        assert candle.high == 105.0
        assert candle.low == 98.0
        assert candle.close == 103.0
        assert candle.volume == 1000.0

    def test_high_lower_than_low_raises(self):
        """High < Low raises ValueError."""
        with pytest.raises(ValueError, match="High.*must be.*Low"):
            OHLCV(
                timestamp=datetime.now(UTC),
                open=100.0,
                high=95.0,  # Lower than low!
                low=98.0,
                close=97.0,
                volume=1000.0,
            )

    def test_close_above_high_raises(self):
        """Close > High raises ValueError."""
        with pytest.raises(ValueError, match="High.*must be.*Close"):
            OHLCV(
                timestamp=datetime.now(UTC),
                open=100.0,
                high=102.0,
                low=98.0,
                close=105.0,  # Above high!
                volume=1000.0,
            )

    def test_close_below_low_raises(self):
        """Close < Low raises ValueError."""
        with pytest.raises(ValueError, match="Low.*must be.*Close"):
            OHLCV(
                timestamp=datetime.now(UTC),
                open=100.0,
                high=105.0,
                low=98.0,
                close=95.0,  # Below low!
                volume=1000.0,
            )

    def test_negative_volume_raises(self):
        """Negative volume raises ValueError."""
        with pytest.raises(ValueError, match="Volume.*must be"):
            OHLCV(
                timestamp=datetime.now(UTC),
                open=100.0,
                high=105.0,
                low=98.0,
                close=103.0,
                volume=-100.0,  # Negative!
            )

    def test_to_dict(self):
        """Convert OHLCV to dict."""
        ts = datetime.now(UTC)
        candle = OHLCV(timestamp=ts, open=100.0, high=105.0, low=98.0, close=103.0, volume=1000.0)

        d = candle.to_dict()

        assert d["timestamp"] == ts.isoformat()
        assert d["open"] == 100.0
        assert d["high"] == 105.0


class TestMarketScenario:
    """Tests for MarketScenario."""

    def test_create_scenario(self):
        """Create valid MarketScenario."""
        candles = [OHLCV(datetime.now(UTC), 100.0, 105.0, 98.0, 103.0, 1000.0)]

        scenario = MarketScenario(
            name="test_scenario",
            description="Test description",
            symbol="BTC/USDT",
            timeframe="1h",
            data_points=candles,
            expected_regime=MarketRegime.TRENDING_UP,
            metadata={"test": "value"},
        )

        assert scenario.name == "test_scenario"
        assert len(scenario.data_points) == 1
        assert scenario.expected_regime == MarketRegime.TRENDING_UP

    def test_empty_data_points_raises(self):
        """Empty data_points raises ValueError."""
        with pytest.raises(ValueError, match="at least 1 data point"):
            MarketScenario(
                name="test",
                description="Test",
                symbol="BTC/USDT",
                timeframe="1h",
                data_points=[],  # Empty!
                expected_regime=MarketRegime.RANGING,
                metadata={},
            )

    def test_invalid_timeframe_raises(self):
        """Invalid timeframe raises ValueError."""
        candles = [OHLCV(datetime.now(UTC), 100.0, 105.0, 98.0, 103.0, 1000.0)]

        with pytest.raises(ValueError, match="Invalid timeframe"):
            MarketScenario(
                name="test",
                description="Test",
                symbol="BTC/USDT",
                timeframe="invalid",  # Invalid!
                data_points=candles,
                expected_regime=MarketRegime.RANGING,
                metadata={},
            )

    def test_get_price_range(self):
        """Get min/max prices."""
        candles = [
            OHLCV(datetime.now(UTC), 100.0, 110.0, 95.0, 105.0, 1000.0),
            OHLCV(datetime.now(UTC), 105.0, 120.0, 100.0, 115.0, 1000.0),
        ]

        scenario = MarketScenario(
            name="test",
            description="Test",
            symbol="BTC/USDT",
            timeframe="1h",
            data_points=candles,
            expected_regime=MarketRegime.TRENDING_UP,
            metadata={},
        )

        min_price, max_price = scenario.get_price_range()

        assert min_price == 95.0
        assert max_price == 120.0


class TestEvaluationDataset:
    """Tests for EvaluationDataset."""

    def test_add_and_get_scenario(self):
        """Add en retrieve scenario."""
        dataset = EvaluationDataset()
        candles = [OHLCV(datetime.now(UTC), 100.0, 105.0, 98.0, 103.0, 1000.0)]

        scenario = MarketScenario(
            name="test_scenario",
            description="Test",
            symbol="BTC/USDT",
            timeframe="1h",
            data_points=candles,
            expected_regime=MarketRegime.TRENDING_UP,
            metadata={},
        )

        dataset.add_scenario(scenario)
        retrieved = dataset.get_scenario("test_scenario")

        assert retrieved is not None
        assert retrieved.name == "test_scenario"

    def test_list_scenarios(self):
        """List all scenario names."""
        dataset = EvaluationDataset()
        candles = [OHLCV(datetime.now(UTC), 100.0, 105.0, 98.0, 103.0, 1000.0)]

        for i in range(3):
            scenario = MarketScenario(
                name=f"scenario_{i}",
                description="Test",
                symbol="BTC/USDT",
                timeframe="1h",
                data_points=candles,
                expected_regime=MarketRegime.TRENDING_UP,
                metadata={},
            )
            dataset.add_scenario(scenario)

        names = dataset.list_scenarios()

        assert len(names) == 3
        assert "scenario_0" in names

    def test_filter_by_regime(self):
        """Filter scenarios by regime."""
        dataset = EvaluationDataset()
        candles = [OHLCV(datetime.now(UTC), 100.0, 105.0, 98.0, 103.0, 1000.0)]

        regimes = [MarketRegime.TRENDING_UP, MarketRegime.RANGING, MarketRegime.TRENDING_UP]

        for i, regime in enumerate(regimes):
            scenario = MarketScenario(
                name=f"scenario_{i}",
                description="Test",
                symbol="BTC/USDT",
                timeframe="1h",
                data_points=candles,
                expected_regime=regime,
                metadata={},
            )
            dataset.add_scenario(scenario)

        trending_scenarios = dataset.filter_by_regime(MarketRegime.TRENDING_UP)

        assert len(trending_scenarios) == 2

    def test_get_statistics(self):
        """Get dataset statistics."""
        dataset = EvaluationDataset()
        candles = [OHLCV(datetime.now(UTC), 100.0, 105.0, 98.0, 103.0, 1000.0)]

        scenario = MarketScenario(
            name="test",
            description="Test",
            symbol="BTC/USDT",
            timeframe="1h",
            data_points=candles,
            expected_regime=MarketRegime.TRENDING_UP,
            metadata={},
        )
        dataset.add_scenario(scenario)

        stats = dataset.get_statistics()

        assert stats["total_scenarios"] == 1
        assert "trending_up" in stats["regimes"]
        assert "BTC/USDT" in stats["symbols"]
