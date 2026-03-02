# Paper Trading Guide

Complete guide for paper trading with the Agentic Trader Platform.

## What is Paper Trading?

Paper trading simulates trades with virtual money against **real market prices**.

### Benefits
- ✅ Zero risk
- ✅ Test strategies with real data
- ✅ Validate execution logic
- ✅ Generate data for analysis

### Limitations
- ⚠️ No slippage simulation
- ⚠️ No market impact
- ⚠️ Always fills at quoted price

## Getting Started

### 1. Environment Setup

```bash
# Copy and edit .env
cp .env.example .env

# Required variables
TRADING_MODE=paper
BITVAVO_API_KEY=your_key
BITVAVO_API_SECRET=your_secret
```

### 2. Test Connection

```bash
python scripts/test_bitvavo_connection.py
```

### 3. Run Paper Trading

```bash
# Interactive mode
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR

# Auto-trade
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 20
```

## Interactive Commands

```
> buy 0.001        # Buy 0.001 BTC
> sell 0.001       # Sell 0.001 BTC
> balance          # Show balance
> status           # Show position
> auto N           # Auto-trade N times
> quit             # Exit
```

## Session Files

Sessions are automatically saved:

```
paper_trading_session_YYYYMMDD_HHMMSS.json
```

### File Structure

```json
{
  "session_id": "...",
  "timestamp": "2026-02-25T16:00:00",
  "exchange": "bitvavo",
  "trades": [
    {
      "timestamp": "...",
      "symbol": "BTC/EUR",
      "side": "buy",
      "amount": 0.001,
      "price": 45000.00,
      "pnl": 0
    }
  ],
  "summary": {
    "total_pnl": 125.50,
    "win_rate": 0.55
  }
}
```

## Best Practices

### Session Size
- **Quick test**: 10-20 trades
- **Strategy validation**: 50-100 trades
- **Statistical significance**: 500+ trades

### Market Conditions
- Test in different regimes (trending, ranging)
- Include volatile periods
- Test different times of day

### Data Analysis
- Compare to backtest results
- Check win rate consistency
- Analyze drawdown patterns

## Database Import

Import sessions to PostgreSQL:

```bash
python scripts/import_paper_trades.py --session paper_trading_session_*.json
```

## Comparison with Live Trading

| Aspect | Paper | Live |
|--------|-------|------|
| Risk | None | Real money |
| Slippage | None | 0.01-0.1% |
| Emotions | None | High impact |
| Fill rate | 100% | Market dependent |
| Latency | Low | Higher |

## Troubleshooting

### "No market data"
- Check API keys
- Verify exchange status
- Check internet

### "Session not saving"
- Check disk space
- Verify write permissions
