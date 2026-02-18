from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class Trade(BaseModel):
    """Record of an executed trade during backtest."""

    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0
    pnl: Optional[float] = None  # Realized PnL (for closing trades)


class Position(BaseModel):
    """Current holding in the portfolio."""

    symbol: str
    quantity: float
    average_price: float
    current_price: float
    unrealized_pnl: float


class BacktestConfig(BaseModel):
    """Configuration for a backtest run."""

    strategy_name: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    commission_rate: float = 0.001  # 0.1%
    timeframe: str = "1h"  # 1m, 1h, 1d


class BacktestMetrics(BaseModel):
    """Performance metrics."""

    total_return: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float
    win_rate: float
    total_trades: int


class BacktestResult(BaseModel):
    """Final output of a backtest."""

    config: BacktestConfig
    metrics: BacktestMetrics
    equity_curve: List[Dict[str, Any]]  # [{"time": ..., "equity": ...}]
    trades: List[Trade]
    logs: List[str] = []
