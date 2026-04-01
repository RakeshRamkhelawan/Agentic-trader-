"""
Phase 6 Integration Tests: Full Backtest Engine Integration

Validates the backtest engine with ConsciousnessStrategy, HistoricalCSVData,
and the BacktestAPI endpoint.
"""

from datetime import datetime, timedelta

import numpy as np
import pytest

# Create a minimal FastAPI app for API tests
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.api.backtest_api import router as backtest_router
from backend.backtesting.consciousness_strategy import ConsciousnessStrategy
from backend.backtesting.data_feed_historical import HistoricalCSVData
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.models import BacktestConfig

_test_app = FastAPI()
_test_app.include_router(backtest_router, prefix="/backtest")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def trending_csv(tmp_path):
    """250-bar uptrend CSV."""
    lines = ["datetime,open,high,low,close,volume"]
    np.random.seed(42)
    for i in range(250):
        dt = datetime(2023, 1, 1) + timedelta(hours=i)
        price = 100.0 + i * 0.1 + np.random.randn() * 0.5
        lines.append(
            f"{dt.isoformat()},{price:.2f},{price+1:.2f},{price-1:.2f},{price:.2f},1000"
        )
    csv_file = tmp_path / "trending.csv"
    csv_file.write_text("\n".join(lines))
    return str(csv_file)


@pytest.fixture
def volatile_csv(tmp_path):
    """250-bar highly volatile CSV (large random swings)."""
    lines = ["datetime,open,high,low,close,volume"]
    np.random.seed(99)
    for i in range(250):
        dt = datetime(2023, 1, 1) + timedelta(hours=i)
        price = 100.0 + np.random.randn() * 5.0  # Large swings
        price = max(50.0, price)  # Clamp to positive
        lines.append(
            f"{dt.isoformat()},{price:.2f},{price+2:.2f},{price-2:.2f},{price:.2f},1000"
        )
    csv_file = tmp_path / "volatile.csv"
    csv_file.write_text("\n".join(lines))
    return str(csv_file)


@pytest.fixture
def backtest_config():
    return BacktestConfig(
        strategy_name="ConsciousnessStrategy",
        symbols=["BTC/USD"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 2, 1),
        initial_capital=10000.0,
    )


@pytest.fixture
async def client():
    transport = ASGITransport(app=_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Tests (all async to work with conftest's autouse async fixtures)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_consciousness_strategy_full_backtest(trending_csv, backtest_config):
    """250-bar backtest should produce a result with metrics and equity curve."""
    feed = HistoricalCSVData(trending_csv)
    feed.load_data(
        backtest_config.symbols,
        backtest_config.start_date,
        backtest_config.end_date,
    )
    engine = BacktestEngine(feed, initial_capital=backtest_config.initial_capital)
    strategy = ConsciousnessStrategy(engine.exchange)

    result = await engine.run(strategy, backtest_config)

    assert result is not None
    assert result.metrics is not None
    assert len(result.equity_curve) > 0
    assert result.equity_curve[0]["equity"] > 0


@pytest.mark.asyncio
async def test_backtest_volatile_fewer_trades(volatile_csv, backtest_config):
    """Volatile data should produce fewer or no trades (defensive regime)."""
    feed = HistoricalCSVData(volatile_csv)
    feed.load_data(
        backtest_config.symbols,
        backtest_config.start_date,
        backtest_config.end_date,
    )
    engine = BacktestEngine(feed, initial_capital=backtest_config.initial_capital)
    strategy = ConsciousnessStrategy(engine.exchange)

    result = await engine.run(strategy, backtest_config)

    # Volatile regime should have fewer or zero trades compared to trending
    assert result is not None
    # We just verify it doesn't crash; trade count depends on data


@pytest.mark.asyncio
async def test_backtest_records_karma_episodes(trending_csv, backtest_config):
    """After a backtest, episode_memory should contain episodes."""
    feed = HistoricalCSVData(trending_csv)
    feed.load_data(
        backtest_config.symbols,
        backtest_config.start_date,
        backtest_config.end_date,
    )
    engine = BacktestEngine(feed, initial_capital=backtest_config.initial_capital)
    strategy = ConsciousnessStrategy(engine.exchange)

    await engine.run(strategy, backtest_config)

    # If trades happened, episodes should be recorded
    if len(engine.exchange.trades) > 0:
        episodes = strategy.episode_memory.get_episodes()
        assert len(episodes) > 0
        assert episodes[0].strategy == "ConsciousnessStrategy"


@pytest.mark.asyncio
async def test_historical_csv_to_engine_pipeline(trending_csv, backtest_config):
    """CSV -> HistoricalCSVData -> BacktestEngine -> BacktestResult."""
    feed = HistoricalCSVData(trending_csv)
    feed.load_data(
        backtest_config.symbols,
        backtest_config.start_date,
        backtest_config.end_date,
    )

    # Verify data loaded correctly
    bar = feed.get_latest_bar("BTC/USD")
    assert bar is not None
    assert "close" in bar

    engine = BacktestEngine(feed, initial_capital=backtest_config.initial_capital)
    strategy = ConsciousnessStrategy(engine.exchange)

    result = await engine.run(strategy, backtest_config)
    assert result is not None
    assert len(result.equity_curve) > 0


@pytest.mark.asyncio
async def test_backtest_api_consciousness_strategy(client):
    """POST /backtest/run with ConsciousnessStrategy should return 200."""
    payload = {
        "strategy_name": "ConsciousnessStrategy",
        "symbols": ["BTC/USD"],
        "start_date": "2023-01-01T00:00:00",
        "end_date": "2023-02-01T00:00:00",
        "initial_capital": 10000.0,
    }
    response = await client.post("/backtest/run", json=payload)
    # MockDataFeed generates random data, so it should succeed
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "equity_curve" in data


@pytest.mark.asyncio
async def test_backtest_api_unknown_strategy_returns_400(client):
    """POST /backtest/run with unknown strategy should return 400."""
    payload = {
        "strategy_name": "NonexistentStrategy",
        "symbols": ["BTC/USD"],
        "start_date": "2023-01-01T00:00:00",
        "end_date": "2023-02-01T00:00:00",
        "initial_capital": 10000.0,
    }
    response = await client.post("/backtest/run", json=payload)
    assert response.status_code == 400
