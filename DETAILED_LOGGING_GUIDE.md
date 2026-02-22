# Detailed Agent Logging System

Complete insight into every agent action, decision, reasoning, and motivation during backtests.

---

## Overview

The detailed logging system provides comprehensive visibility into the agent decision-making process, from initial market analysis through to trade execution.

### Features

| Feature | Description |
|---------|-------------|
| **Agent Decisions** | Every agent's analysis, confidence, and reasoning |
| **Trade Executions** | Full trade details with P&L tracking |
| **Vedic Context** | Harmony scores, Rahu Kala, elemental prana |
| **Decision Chain** | How multiple agents reach consensus |
| **Performance Metrics** | Complete backtest statistics |

---

## Output Files

### 1. Detailed Text Log (`*_DETAILED_LOG.txt`)
Human-readable log with full reasoning for every decision.

### 2. Structured JSON (`*_STRUCTURED.json`)
Machine-readable data for analysis and visualization.

---

## Log Entry Types

### Agent Decision Entry
```
================================================================================
AGENT DECISION: TechnicalAnalyst_Alpha (TechnicalAnalysisAgent)
================================================================================
Timestamp:        2024-01-04T00:00:00+00:00
Symbol:           BTC
Decision:         BUY (confidence: 91.08%)

MARKET ANALYSIS:
  Price change: +3.11%. RSI at neutral levels. Volume above average.

TECHNICAL INDICATORS:
  rsi: 81.0800
  macd: 31.1000
  sma_20: 43261.9300
  sma_50: 41936.9100
  volume_ratio: 1.5725

FUNDAMENTAL FACTORS:
  • Network growth stable
  • No major news

SENTIMENT SCORE:  0.31

MOTIVATION:
  Primary:   Momentum signal triggered by +3.11% price move
  Secondary:
    • Volume confirmation
    • Support level test

RISK ASSESSMENT:  Normal volatility regime

VEDIC CONTEXT:
  Harmony Score:    0.84
  Rahu Kala:        Inactive
  Dominant Element: fire
  Prana Level:      0.78

EXECUTION PARAMETERS:
  Position Size:    0.1000
  Entry Price:      $44,179.92
  Stop Loss:        $41,970.92
  Take Profit:      $48,597.91
```

### Trade Execution Entry
```
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
TRADE EXECUTED: BUY BTC
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Timestamp:    2024-01-04T00:00:00+00:00
Quantity:     0.1000
Price:        $44,179.92
Total Value:  $4,417.99

ACCOUNT STATUS:
  Before Trade:  Cash: $5,582.01 | Portfolio: $10,000.00
  After Trade:   Cash: $5,582.01 | Portfolio: $10,000.00

EXECUTION QUALITY: Slippage: 0.0001 | Time: 133.69ms

DECISION CHAIN:
  1. TechnicalAnalyst_Alpha: BUY (confidence: 91.08%)
  2. RiskManager_Beta: APPROVE (confidence: 75.00%)
  3. SentimentAnalyzer_Gamma: BUY (confidence: 47.59%)

FINAL RATIONALE:
  Consensus: BUY based on Momentum signal triggered by +3.11% price move
```

### Vedic Context Entry
```
=======================================
VEDIC CONTEXT SNAPSHOT
=======================================
Timestamp:        2024-01-01T00:00:00+00:00
Market Regime:    neutral
Harmony Score:    0.67
Rahu Kala:        Inactive
Dominant Element: water
Navagraha:        Moon

Elemental Prana Levels:
  Earth (Value):   0.84
  Water (Flow):    0.89
  Fire (Momentum): 0.66
  Air (Volatility):0.75
  Ether (Sentiment):0.90
```

---

## Usage

### Run Backtest with Detailed Logging

```bash
# Basic usage
python scripts/backtest_detailed.py --symbols BTC ETH --start 2024-01-01 --end 2024-01-31

# Full portfolio with more capital
python scripts/backtest_detailed.py \
  --symbols BTC ETH SOL ADA DOT XRP LINK DOGE LTC XLM \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --capital 50000
```

### View Logs

```bash
# View detailed log
cat backtest_logs/backtest_detailed_20260220_144546_DETAILED_LOG.txt

# Search for specific trades
grep "TRADE EXECUTED" backtest_logs/*.txt

# Find all BUY decisions
grep -A 5 "Decision:.*BUY" backtest_logs/*.txt

# Find Rahu Kala warnings
grep "Rahu Kala.*ACTIVE" backtest_logs/*.txt
```

### Analyze JSON Data

```python
import json

with open('backtest_logs/backtest_detailed_xxx_STRUCTURED.json') as f:
    data = json.load(f)

# Get all agent decisions
for decision in data['agent_decisions']:
    print(f"{decision['agent_name']}: {decision['decision']} {decision['symbol']}")

# Get all trades
for trade in data['trades']:
    print(f"{trade['action']} {trade['symbol']} @ ${trade['price']:,.2f}")

# Performance summary
print(f"Return: {data['total_return_pct']:.2f}%")
print(f"Trades: {len(data['trades'])}")
```

---

## Agent Types

### 1. TechnicalAnalyst_Alpha
- **Type:** TechnicalAnalysisAgent
- **Focus:** Price action, indicators, volume
- **Indicators Used:** RSI, MACD, SMA(20), SMA(50), Volume
- **Decision Logic:** Momentum-based with threshold triggers

### 2. RiskManager_Beta
- **Type:** RiskManagementAgent
- **Focus:** Portfolio risk, position limits, drawdown
- **Checks:** Position count, cash ratio, Rahu Kala
- **Veto Power:** Can block any trade

### 3. SentimentAnalyzer_Gamma
- **Type:** SentimentAnalysisAgent
- **Focus:** Social sentiment, news, funding rates
- **Sources:** Twitter, News, Reddit, Funding rates
- **Decision Logic:** Sentiment score thresholds

---

## Decision Consolidation Logic

### Consensus Building
1. Each agent submits decision with confidence
2. Risk Manager can veto (BLOCK) any trade
3. Technical and Sentiment agents vote
4. Majority wins (weighted by confidence)

### Example Decision Chain
```
TechnicalAnalyst:  BUY (91% confidence)  →  Vote: BUY
RiskManager:       APPROVE (75%)         →  No veto
SentimentAnalyzer: BUY (48% confidence)  →  Vote: BUY

RESULT: BUY executed (consensus reached)
```

---

## Vedic Integration

### Rahu Kala Blocking
When Rahu Kala is active, the Risk Manager automatically blocks all new positions:
```
[!] RAHU KALA ACTIVE - Trading restricted
RiskManager: BLOCK - Rahu Kala active - no new positions
```

### Harmony Scoring
Each decision includes vedic harmony score (0-1):
- **> 0.8:** Optimal trading conditions
- **0.6-0.8:** Normal conditions
- **< 0.6:** Suboptimal - reduce position sizes

### Elemental Balance
Prana levels for each element guide strategy:
- **Earth (Value):** Long-term position sizing
- **Water (Flow):** Trend following strength
- **Fire (Momentum):** Short-term breakout trades
- **Air (Volatility):** Risk adjustment
- **Ether (Sentiment):** Market mood

---

## Performance Analysis

### Key Metrics Logged
- Total Return (%)
- Max Drawdown (%)
- Sharpe Ratio
- Win Rate
- Profit Factor
- Average Trade

### Agent Performance
Track each agent's contribution:
```
TechnicalAnalyst: 65% accuracy (when confidence > 80%)
RiskManager: Prevented 3 losses during Rahu Kala
SentimentAnalyzer: Early warning on sentiment shift
```

---

## Example Session Summary

```
================================================================================
BACKTEST SESSION SUMMARY
================================================================================
Session ID:       backtest_detailed_20260220_144546
Start Time:       2026-02-20T14:45:46.221005
End Time:         2026-02-20T14:45:46.477231

CONFIGURATION:
  Symbols:        BTC, ETH
  Date Range:     2024-01-01 to 2024-01-31
  Initial Capital: $10,000.00
  Strategy:       Multi-Agent Vedic Momentum

STATISTICS:
  Agent Decisions:  186
  Trades Executed:  18
  Vedic Snapshots:  7

PERFORMANCE:
  Final Capital:    $9,567.45
  Total Return:     -4.33%
  Max Drawdown:     6.70%
  Sharpe Ratio:     1.50
================================================================================
```

---

## Files Location

```
backtest_logs/
├── backtest_detailed_20260220_144546_DETAILED_LOG.txt   (Human-readable)
└── backtest_detailed_20260220_144546_STRUCTURED.json    (Machine-readable)
```

---

## Next Steps

### Visualization Ideas
1. **Decision Timeline:** Chart showing agent decisions over time
2. **Confidence Heatmap:** Agent confidence levels by symbol
3. **P&L Attribution:** Which agents contributed most to returns
4. **Vedic Overlay:** Harmony scores vs trade performance

### Enhancements
1. Add more agent types (MacroAgent, ValuationAgent)
2. Machine learning on decision patterns
3. Real-time alert system for live trading
4. Web dashboard for log analysis

---

*All trading in PAPER mode - No real orders executed*
