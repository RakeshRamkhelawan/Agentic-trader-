import pandas as pd
import numpy as np
from typing import List, Dict
from backend.backtesting.models import BacktestMetrics

class MetricsCalculator:
    """Calculates financial performance metrics from equity curve."""
    
    @staticmethod
    def calculate(equity_curve: List[Dict], initial_capital: float) -> BacktestMetrics:
        if not equity_curve:
            return BacktestMetrics(
                total_return=0.0, cagr=0.0, sharpe_ratio=0.0, max_drawdown=0.0, win_rate=0.0, total_trades=0
            )
            
        df = pd.DataFrame(equity_curve)
        df['returns'] = df['equity'].pct_change().fillna(0)
        
        # Total Return
        final_equity = df['equity'].iloc[-1]
        total_return = (final_equity - initial_capital) / initial_capital
        
        # CAGR (Simplified assumption: daily data)
        days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days
        if days > 0:
            cagr = (final_equity / initial_capital) ** (365 / days) - 1
        else:
            cagr = 0.0
            
        # Sharpe Ratio (Assuming risk-free rate = 0 for crypto)
        # Annualized logic: sqrt(365) * mean / std
        mean_return = df['returns'].mean()
        std_return = df['returns'].std()
        
        if std_return == 0:
            sharpe = 0.0
        else:
            sharpe = (mean_return / std_return) * np.sqrt(365) # daily data assumption
            
        # Max Drawdown
        df['cummax'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['cummax']) / df['cummax']
        max_drawdown = df['drawdown'].min()
        
        return BacktestMetrics(
            total_return=round(total_return, 4),
            cagr=round(cagr, 4),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown=round(max_drawdown, 4),
            win_rate=0.0, # detailed trade analysis needed for this
            total_trades=0 # detailed trade analysis needed for this
        )
