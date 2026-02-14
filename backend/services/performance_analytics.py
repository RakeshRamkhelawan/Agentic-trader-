from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trade_count: int


class PerformanceAnalytics:
    """
    Calculates trading performance metrics from equity curves and trade lists.
    """

    def calculate_metrics(
        self, equity_curve: List[float], trades: List[Dict]
    ) -> PerformanceMetrics:
        """
        Calculates standard metrics.
        equity_curve: List of portfolio values over time (e.g. daily or hourly)
        trades: List of trade dictionaries {'pnl': float, ...}
        """
        if not equity_curve:
            return PerformanceMetrics(0, 0, 0, 0, 0)

        # 1. Total Return
        start_equity = equity_curve[0]
        end_equity = equity_curve[-1]
        total_ret = (
            (end_equity - start_equity) / start_equity if start_equity > 0 else 0
        )

        # 2. Sharpe Ratio (assuming daily data for simplicity, usually needs resampling)
        # Using numpy for vector operations
        returns = pd.Series(equity_curve).pct_change().dropna()
        if len(returns) > 1 and returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized
        else:
            sharpe = 0.0

        # 3. Max Drawdown
        peaks = pd.Series(equity_curve).cummax()
        drawdowns = (pd.Series(equity_curve) - peaks) / peaks
        max_dd = drawdowns.min()  # negative value

        # 4. Win Rate
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0.0

        return PerformanceMetrics(
            total_return=total_ret,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            trade_count=len(trades),
        )
