# v10 Guardian Performance Comparison

## Results Summary

| Metric | v8 Baseline | v10 Guardian | Delta |
|--------|-------------|--------------|-------|
| **Total Trades** | 392 | 29 | -92.6% |
| **Win Rate** | 36.7% | 51.7% | +15.0% |
| **Total Return** | +7.7% | +1.2% | -6.5% |
| **Max Drawdown** | 19.3% | 0.9% | -18.4% |
| **Avg Hold Time** | 9.9 bars | ~8 bars | -1.9 |
| **Trades/Hour** | ~0.07 | ~0.005 | -92.9% |

## Key Findings

### 1. Quality Over Quantity Achieved
- **Win rate improved** from 36.7% to 51.7% (+15%)
- **Drawdown drastically reduced** from 19.3% to 0.9% (-95%)
- **Trade frequency reduced** by 92.6% (392 → 29 trades)

### 2. Filter Effectiveness
```
Total Decisions Checked:    33,932
Passed Filters:             50 (0.1%)
Rejected:                   33,882 (99.9%)
  - Harmony too low:        560
  - Confidence too low:     1,039
  - Max positions:          189
```

### 3. v10 Guardian Filters Applied
```python
MIN_HARMONY = 0.50      # (was: 0.693 avg in v8)
MIN_CONFIDENCE = 0.25   # (was: 0.368 avg in v8)
MAX_POSITIONS = 5
MAX_TRADES_PER_HOUR = 50
```

### 4. Risk-Adjusted Performance
| Metric | v8 | v10 |
|--------|-----|-----|
| Return/Max DD | 0.40 | 1.33 |
| Calmar Ratio | 0.40 | 1.33 |
| Risk Score | High | Very Low |

## Analysis

### What's Working:
1. **Dramatic drawdown reduction** - v10 filters prevent most losing trades
2. **Improved win rate** - Quality trades have better success rate
3. **Lower volatility** - Fewer trades = smoother equity curve

### What's Not Working:
1. **Too few trades** - 29 trades over 6 years is too conservative
2. **Lower absolute returns** - Missing many profitable opportunities
3. **Filters too strict** - Only 0.1% of decisions pass

## Recommended Adjustments

### For More Trades (Target: 80-120):
```python
MIN_HARMONY = 0.45      # Down from 0.50
MIN_CONFIDENCE = 0.20   # Down from 0.25
MAX_POSITIONS = 8       # Up from 5
```

### Expected Impact:
| Metric | Current | Target |
|--------|---------|--------|
| Trades | 29 | 100 |
| Win Rate | 51.7% | 45-50% |
| Return | +1.2% | +5-8% |
| Max DD | 0.9% | 5-8% |

## Implementation

### Run v10 Guardian:
```bash
python backend/scripts/run_v10_guardian_backtest.py
```

### Export Results:
```bash
python backend/core/audit/csv_exporter.py backend/data/audit_logs/audit_fdc58b9c_*.json
```

### Files Generated:
- `backend/data/audit_logs/audit_fdc58b9c_*.json` - Full audit trail
- `backend/data/backtest_results/v10_guardian_results.json` - Summary
- `backend/data/audit_csv/` - CSV exports for Excel

## Conclusion

v10 Guardian successfully demonstrates **quality over quantity** with:
- 51.7% win rate (vs 36.7% baseline)
- 0.9% max drawdown (vs 19.3% baseline)
- 95% risk reduction

However, filters need **slight relaxation** to achieve optimal trade frequency (80-120 trades) for better absolute returns while maintaining risk discipline.
