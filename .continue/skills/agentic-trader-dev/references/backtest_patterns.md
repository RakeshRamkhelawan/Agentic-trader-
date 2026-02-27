# Backtest Analysis Patterns

Common patterns for analyzing backtest results in the Agentic Trader Platform.

## File Naming Conventions

| Pattern | Description |
|---------|-------------|
| `elemental_backtest_*_harmony.csv` | Elemental harmony scores over time |
| `elemental_backtest_*_trades.csv` | Individual trade records |
| `elemental_backtest_*_symbols.csv` | Symbol metadata |
| `backtest_v{VERSION}_*.json` | Versioned backtest results (V13-V17+) |
| `paper_trading_session_*.json` | Live paper trading sessions |

## Key Metrics

### Performance Metrics
```python
{
    "total_return": float,        # Total % return
    "sharpe_ratio": float,        # Risk-adjusted return
    "max_drawdown": float,        # Max peak-to-trough decline
    "win_rate": float,            # % of profitable trades
    "total_trades": int,          # Total number of trades
    "profitable_trades": int,     # Number of winning trades
}
```

### Elemental Specific
```python
{
    "elemental_fire_score": float,    # 0-1 aggression level
    "elemental_water_score": float,   # 0-1 flow/adaptation
    "elemental_earth_score": float,   # 0-1 stability
    "elemental_air_score": float,     # 0-1 volatility sensitivity
}
```

## Common Analysis Queries

### Compare Two Backtests
```python
import json

def compare_backtest_files(file1, file2):
    with open(file1) as f:
        b1 = json.load(f)
    with open(file2) as f:
        b2 = json.load(f)
    
    return {
        'return_diff': b2['total_return'] - b1['total_return'],
        'sharpe_diff': b2['sharpe_ratio'] - b1['sharpe_ratio'],
        'trade_diff': b2['total_trades'] - b1['total_trades'],
    }
```

### Extract Top Performing Symbols
```python
import csv
from collections import defaultdict

def top_symbols(trades_csv, top_n=5):
    symbol_pnl = defaultdict(float)
    
    with open(trades_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol_pnl[row['symbol']] += float(row['pnl'])
    
    return sorted(symbol_pnl.items(), key=lambda x: x[1], reverse=True)[:top_n]
```

## Interpretation Guide

| Metric | Good | Bad | Action |
|--------|------|-----|--------|
| Sharpe > 1.5 | ✅ Excellent | ⚠️ < 1.0 | Adjust risk |
| Max DD < 10% | ✅ Safe | ⚠️ > 20% | Reduce size |
| Win Rate > 55% | ✅ Consistent | ⚠️ < 45% | Review signals |
| Return/Drawdown > 3 | ✅ Efficient | ⚠️ < 2 | Optimize entries |
