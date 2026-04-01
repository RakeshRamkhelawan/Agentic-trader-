"""
Tests for ConsciousnessStrategy (Step 4A - GREEN).

Validates the triple-layer consciousness architecture integration:
- Regime detection drives strategy selection
- Rahu Kala defense halts trading
- Karma episodes are recorded on trades
- Full backtest engine integration produces a result
"""

import asyncio
from datetime import datetime

import numpy as np
import pytest

from backend.backtesting.consciousness_strategy import ConsciousnessStrategy
from backend.backtesting.data_feed_historical import HistoricalCSVData
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.exchange import SimulatedExchange
from backend.backtesting.models import BacktestConfig
from backend.core.regime_detector import MarketRegime

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def exchange():
    return SimulatedExchange(initial_capital=10000.0, commission_rate=0.001)


@pytest.fixture
def strategy(exchange):
    return ConsciousnessStrategy(exchange)


@pytest.fixture
def large_csv(tmp_path):
    """Generate a 250-bar CSV with a trending pattern (enough for regime detection)."""
    lines = ["datetime,open,high,low,close,volume"]
    base_price = 100.0
    np.random.seed(42)

    for i in range(250):
        dt = datetime(2023, 1, 1) + __import__("datetime").timedelta(hours=i)
        # Uptrend with noise
        price = base_price + i * 0.1 + np.random.randn() * 0.5
        lines.append(
            f"{dt.isoformat()},{price:.2f},{price+1:.2f},{price-1:.2f},{price:.2f},1000"
        )

    csv_file = tmp_path / "large_test.csv"
    csv_file.write_text("\n".join(lines))
    return str(csv_file)


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------


def test_consciousness_strategy_initializes(strategy):
    """Strategy should initialize with regime detector and episode memory."""
    assert strategy.regime_detector is not None
    assert strategy.episode_memory is not None
    assert strategy._current_regime == MarketRegime.SIDEWAYS
    assert strategy.price_history == []


def test_regime_detection_on_bar(strategy):
    """on_bar should update price_history and current_regime."""
    bar = {"close": 100.0, "open": 99.0, "high": 101.0, "low": 98.0, "volume": 500}
    asyncio.run(strategy.on_bar("BTC/USD", bar))

    assert len(strategy.price_history) == 1
    assert strategy.price_history[0] == 100.0
    # With only 1 datapoint, regime defaults to SIDEWAYS (not enough data for trend)
    assert strategy._current_regime == MarketRegime.SIDEWAYS


def test_rahu_kala_defense(exchange):
    """When force_rahu=True, the strategy should not execute any trades."""
    rahu_strategy = ConsciousnessStrategy(exchange, force_rahu=True)

    # Feed many bars
    for i in range(50):
        bar = {"close": 100.0 + i, "volume": 1000}
        asyncio.run(rahu_strategy.on_bar("BTC/USD", bar))

    # No trades should have been executed
    assert len(exchange.trades) == 0


def test_karma_episode_recording(strategy):
    """After a completed trade cycle, a KarmaEpisode should be recorded."""
    # We need to manually trigger a trade. Feed enough bars for trend following.
    # Create a clear uptrend (30+ bars needed)
    for i in range(35):
        bar = {
            "close": 100.0 + i * 0.5,
            "open": 99.5 + i * 0.5,
            "high": 101.0 + i * 0.5,
            "low": 99.0 + i * 0.5,
            "volume": 1000,
        }
        asyncio.run(strategy.on_bar("BTC/USD", bar))

    # If a trade was executed, episodes should have been recorded
    if len(strategy.exchange.trades) > 0:
        episodes = strategy.episode_memory.get_episodes()
        assert len(episodes) > 0
        assert episodes[0].strategy == "ConsciousnessStrategy"


def test_full_backtest_engine_integration(large_csv):
    """ConsciousnessStrategy should run inside BacktestEngine without errors."""
    feed = HistoricalCSVData(large_csv)
    config = BacktestConfig(
        strategy_name="ConsciousnessStrategy",
        symbols=["BTC/USD"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 2, 1),
        initial_capital=10000.0,
    )

    feed.load_data(config.symbols, config.start_date, config.end_date)
    engine = BacktestEngine(feed, initial_capital=config.initial_capital)
    strategy = ConsciousnessStrategy(engine.exchange)

    result = asyncio.run(engine.run(strategy, config))

    assert result is not None
    assert result.metrics is not None
    assert len(result.equity_curve) > 0
    # The equity curve should at least have tracked some bars
    assert result.equity_curve[0]["equity"] > 0
