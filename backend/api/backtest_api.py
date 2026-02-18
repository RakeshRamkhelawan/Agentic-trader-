import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.backtesting.consciousness_strategy import ConsciousnessStrategy
from backend.backtesting.data_feed import MockDataFeed
from backend.backtesting.data_feed_historical import HistoricalCSVData
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.models import BacktestConfig, BacktestResult
from backend.backtesting.strategies.simple_ma import MovingAverageStrategy

router = APIRouter()


@router.post("/run", response_model=BacktestResult)
async def run_backtest(
    config: BacktestConfig,
    csv_path: Optional[str] = Query(
        None, description="Absolute path to a CSV file for HistoricalCSVData feed"
    ),
):
    """
    Run a backtest simulation.

    Supported strategies:
      - MovingAverage  (simple SMA crossover)
      - ConsciousnessStrategy (triple-layer consciousness architecture)

    Data feeds:
      - MockDataFeed (random walk, default)
      - HistoricalCSVData (when csv_path is provided)
    """
    try:
        # 1. Initialize Data Feed
        if csv_path and os.path.isfile(csv_path):
            data_feed = HistoricalCSVData(csv_path)
        else:
            data_feed = MockDataFeed()

        data_feed.load_data(config.symbols, config.start_date, config.end_date)

        # 2. Initialize Engine
        engine = BacktestEngine(data_feed, initial_capital=config.initial_capital)

        # 3. Initialize Strategy (factory pattern)
        if config.strategy_name == "MovingAverage":
            strategy = MovingAverageStrategy(engine.exchange)
        elif config.strategy_name == "ConsciousnessStrategy":
            strategy = ConsciousnessStrategy(engine.exchange)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown strategy: {config.strategy_name}"
            )

        # 4. Run Backtest
        result = await engine.run(strategy, config)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
