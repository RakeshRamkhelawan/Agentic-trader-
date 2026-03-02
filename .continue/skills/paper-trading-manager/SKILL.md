---
name: paper-trading-manager
description: Manage paper trading sessions with real market data from Bitvavo and Revolut. Use when starting paper trading sessions, comparing session results, analyzing P&L, or importing trades to database. Triggers include "paper trading", "start session", "compare sessions", "paper trade", "Bitvavo paper", "Revolut paper", "session P&L", "import paper trades", "realtime paper trading".
---

# Paper Trading Manager Skill

Manage paper trading sessions with real market data.

## Overview

Paper trading simulates trades with "fake" money against **real market prices**. Ideal for testing strategies without risk.

## Quick Start

### Start a Session

```bash
# Interactive mode
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR

# Auto-trade 20 trades
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 20

# Multi-asset
python scripts/realtime_paper_trading.py --exchange bitvavo --symbols BTC/EUR,ETH/EUR,SOL/EUR --auto 50
```

### Use the Manager

```bash
# Start new session
python .continue/skills/paper-trading-manager/scripts/paper_manager.py start --exchange bitvavo --assets BTC,ETH --auto 30

# List all sessions
python .continue/skills/paper-trading-manager/scripts/paper_manager.py list

# Compare two sessions
python .continue/skills/paper-trading-manager/scripts/paper_manager.py compare 20260219_225626 20260220_085444

# Show session details
python .continue/skills/paper-trading-manager/scripts/paper_manager.py show latest

# Import to database
python .continue/skills/paper-trading-manager/scripts/paper_manager.py import 20260219_225626
```

## Session Commands

When running interactive mode:

```
> buy 0.001        # Buy 0.001 BTC
> sell 0.001       # Sell 0.001 BTC
> balance          # Show current balance
> status           # Show price and position
> auto 20          # Auto-trade 20 trades
> quit             # Exit and save session
```

## Session Files

Sessions are saved as:

```
paper_trading_session_{YYYYMMDD}_{HHMMSS}.json
real_paper_session_{YYYYMMDD}_{HHMMSS}.json
```

Each file contains:
- Trade history
- P&L calculations
- Market data snapshots
- Session metadata

## CLI Reference

```bash
# Start new session
python scripts/paper_manager.py start \
    --exchange bitvavo \
    --assets BTC/EUR,ETH/EUR \
    --auto 50 \
    --duration 60

# List sessions
python scripts/paper_manager.py list --limit 10 --format table

# Show session details
python scripts/paper_manager.py show latest --trades --chart

# Compare sessions
python scripts/paper_manager.py compare session1 session2 --metrics pnl,winrate,trades

# Export to CSV
python scripts/paper_manager.py export latest --format csv --output trades.csv

# Import to database
python scripts/paper_manager.py import session_id --db postgresql://...

# Delete old sessions
python scripts/paper_manager.py cleanup --older-than 30 --dry-run
```

## Configuration

### Environment (.env)

```env
# Trading Mode (CRITICAL!)
TRADING_MODE=paper

# Bitvavo API
BITVAVO_API_KEY=your_key
BITVAVO_API_SECRET=your_secret
BITVAVO_SANDBOX=false

# Revolut X API (optional)
REVOLUT_API_KEY=your_key
REVOLUT_PRIVATE_KEY_PATH=./revolut_private.pem
```

### Available Exchanges

| Exchange | Data Quality | Pairs | Notes |
|----------|--------------|-------|-------|
| Bitvavo | ⭐⭐⭐ Real | 437+ EUR | Recommended |
| Revolut | ⭐⭐⭐ Real | 100+ | UK/EU focus |

## Session Analysis

### P&L Metrics

```python
from scripts.paper_manager import analyze_session

result = analyze_session('paper_trading_session_20260219_225626.json')

print(f"Total P&L: €{result['total_pnl']:.2f}")
print(f"Win Rate: {result['win_rate']:.1f}%")
print(f"Trades: {result['total_trades']}")
print(f"Avg Trade: €{result['avg_trade_pnl']:.2f}")
```

### Compare Sessions

```python
from scripts.paper_manager import compare_sessions

comparison = compare_sessions(
    session1='paper_trading_session_20260219.json',
    session2='paper_trading_session_20260220.json'
)

# Shows: P&L diff, trade count diff, strategy improvements
```

## Database Import

### PostgreSQL

```bash
python scripts/paper_manager.py import session_id \
    --db postgresql://user:pass@localhost/trader
```

### Tables Created

```sql
-- paper_trades table
CREATE TABLE paper_trades (
    id UUID PRIMARY KEY,
    session_id VARCHAR(50),
    timestamp TIMESTAMP,
    symbol VARCHAR(20),
    side VARCHAR(10),  -- buy/sell
    amount DECIMAL,
    price DECIMAL,
    pnl DECIMAL,
    metadata JSONB
);

-- paper_sessions table
CREATE TABLE paper_sessions (
    id VARCHAR(50) PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_pnl DECIMAL,
    total_trades INTEGER,
    win_rate DECIMAL,
    config JSONB
);
```

## Best Practices

### 1. Session Duration
- **Short tests**: 10-50 trades
- **Strategy validation**: 100+ trades
- **Full backtest equivalent**: 1000+ trades

### 2. Asset Selection
- Start with BTC/EUR (most liquid)
- Add ETH/EUR for correlation
- Expand to SOL, ADA for diversity

### 3. Data Recording
- Always save session files
- Import to database for analysis
- Export CSV for Excel analysis

### 4. Comparison
- Compare to backtest results
- Check if live behavior matches simulation
- Validate execution logic

## Troubleshooting

### "No market data"
- Check API keys in .env
- Verify exchange status
- Check internet connection

### "Insufficient balance"
- Paper trading starts with €10,000 fake
- Check position sizes

### "Session not saving"
- Check write permissions
- Verify disk space

## References

- `references/paper_trading_guide.md` - Complete guide
- `references/session_analysis.md` - Analysis patterns
- `PAPER_TRADING_GUIDE.md` - Original documentation
