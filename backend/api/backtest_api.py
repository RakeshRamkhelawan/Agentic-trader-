from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from backend.backtesting.models import BacktestConfig, BacktestResult
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.data_feed import MockDataFeed
from backend.backtesting.strategies.simple_ma import MovingAverageStrategy

router = APIRouter()

@router.post("/run", response_model=BacktestResult)
async def run_backtest(config: BacktestConfig):
    """
    Run a backtest simulation.
    Currently supports 'MovingAverage' strategy with Mock Data.
    """
    try:
        # 1. Initialize Data Feed
        data_feed = MockDataFeed()
        data_feed.load_data(config.symbols, config.start_date, config.end_date)
        
        # 2. Initialize Engine
        engine = BacktestEngine(data_feed, initial_capital=config.initial_capital)
        
        # 3. Initialize Strategy
        # In a real app, successful strategies would be loaded dynamically or via factory
        if config.strategy_name == "MovingAverage":
            strategy = MovingAverageStrategy(engine.exchange)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {config.strategy_name}")
            
        # 4. Run Backtest
        result = await engine.run(strategy, config)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
