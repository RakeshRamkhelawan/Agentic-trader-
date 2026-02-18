# Crypto Data Integration for Backtesting

## Overview

This document describes how to download historical crypto data and use it with the Agentic Trader backtesting engine.

## Quick Start

### 1. Download Historical Data

```bash
# Download BTC/USDT 1-hour candles for 2023
python -m backend.market_data.historical_data_fetcher \
    --exchange binance \
    --symbol BTC/USDT \
    --start 2023-01-01 \
    --end 2023-12-31 \
    --output data/historical/
```

### 2. Bulk Download Multiple Symbols

```bash
# Download all default symbols (BTC, ETH, SOL, etc.)
python scripts/download_historical_data.py --year 2023 --timeframe 1h

# Download specific symbols
python scripts/download_historical_data.py \
    --symbols BTC/USDT,ETH/USDT,SOL/USDT \
    --year 2024 \
    --timeframe 4h
```

### 3. Use in Backtest

```python
from datetime import datetime
from backend.backtesting.data_feed_historical import HistoricalCSVData
from backend.backtesting.engine import BacktestEngine

# Load data
data_feed = HistoricalCSVData("data/historical/binance/BTC_USDT_1h.csv")
data_feed.load_data(
    symbols=["BTC/USDT"],
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# Run backtest
engine = BacktestEngine(data_feed=data_feed, initial_capital=10000)
results = engine.run()
```

## Supported Exchanges

| Exchange | ID | Spot | Futures |
|----------|-----|------|---------|
| Binance | `binance` | ✅ | ✅ |
| Bybit | `bybit` | ✅ | ✅ |
| Kraken | `kraken` | ✅ | ❌ |
| Coinbase | `coinbase` | ✅ | ❌ |
| KuCoin | `kucoin` | ✅ | ✅ |

## Supported Timeframes

| Timeframe | Minutes | Use Case |
|-----------|---------|----------|
| 1m | 1 | High-frequency scalping |
| 5m | 5 | Short-term trades |
| 15m | 15 | Intraday |
| 30m | 30 | Swing trading |
| 1h | 60 | **Recommended** - Daily strategy |
| 4h | 240 | Multi-day positions |
| 1d | 1440 | Long-term trends |

## Data Format

Downloaded CSV files have these columns:

```csv
timestamp,open,high,low,close,volume,datetime
1609459200000,28923.00,29050.00,28750.00,29000.00,2500.50,2021-01-01 00:00:00
...
```

## Integration with Unified Consciousness

```python
from backend.orchestration.ooda_coordinator import OODALoopCoordinator
from backend.backtesting.data_feed_historical import HistoricalCSVData

# 1. Load historical data
data_feed = HistoricalCSVData("data/historical/binance/BTC_USDT_1h.csv")

# 2. Create OODA coordinator with consciousness integration
coordinator = OODALoopCoordinator(
    navagraha_service=navagraha_service,
    system_identity=system_identity,
    risk_orchestrator=risk_orchestrator,
)

# 3. Run backtest loop
while data_feed.next():
    bar = data_feed.get_latest_bar("BTC/USDT")
    
    # Process through consciousness pipeline
    result = await coordinator.run_cycle(
        symbol="BTC/USDT",
        current_price=bar["close"],
        strategy_id="trend_following"
    )
    
    if result["decision"] == "EXECUTE":
        # Execute paper trade
        pass
```

## Automation Script

Create a daily sync script:

```bash
#!/bin/bash
# scripts/daily_data_sync.sh

PAIRS=("BTC/USDT" "ETH/USDT" "SOL/USDT")
TIMEFRAMES=("1h" "4h" "1d")

for pair in "${PAIRS[@]}"; do
    for tf in "${TIMEFRAMES[@]}"; do
        python -m backend.market_data.historical_data_fetcher \
            --exchange binance \
            --symbol "$pair" \
            --timeframe "$tf" \
            --start $(date -d "-30 days" +%Y-%m-%d) \
            --end $(date +%Y-%m-%d) \
            --output data/historical/
    done
done
```

## Storage Recommendations

| Data Volume | Storage | Est. Size |
|-------------|---------|-----------|
| 1 symbol, 1 year, 1h | CSV | ~5 MB |
| 10 symbols, 1 year, 1h | CSV | ~50 MB |
| 10 symbols, 1 year, 1m | CSV | ~3 GB |
| All symbols, 3 years | ClickHouse | ~500 GB |

For production backtesting at scale, consider:
- **ClickHouse** for high-performance querying
- **Parquet** files for compressed storage
- **S3** for cloud storage with Athena

## Data Sources Reference

### Free CSV Downloads
- **CryptoDataDownload**: Direct CSV files (daily/hourly/minute)
- **Binance Public Data**: Monthly ZIP files since 2017
- **CoinMetrics**: CSV/JSON/Parquet export tool

### API Sources
- **CCXT Library**: 100+ exchanges via unified API
- **Binance API**: Free historical klines (1min+)
- **TwelveData**: Free tier with 1min OHLCV

## Troubleshooting

### Rate Limiting
If you hit rate limits:
```python
config.rate_limit_delay = 1.0  # Increase delay between requests
config.batch_size = 500       # Reduce batch size
```

### Resume Interrupted Downloads
The fetcher automatically resumes from existing files:
```bash
# Just re-run the same command
python scripts/download_historical_data.py --year 2023
```

### Test Mode
Test with single symbol before bulk download:
```bash
python scripts/download_historical_data.py --test --symbol BTC/USDT
```
