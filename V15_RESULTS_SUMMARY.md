# V15 Backtest Results Summary - Risk Management & Profit Protection

## Overview
V15 implements all 5 priorities from the Masterprompt:
1. ✅ **Trailing Stop**: +40% activates, -15% from peak closes position
2. ✅ **Position Cap**: Hard €2,000 limit regardless of portfolio size
3. ✅ **60-Day Failsafe**: Time-based exit restored from V10
4. ✅ **Fixed Counters**: Position review exits properly tracked (222 exits!)
5. ✅ **Hedge Validation**: Data availability check at startup

## Results

### Full Backtest (2020-2026, 50 Assets)
| Metric | V15 Result |
|--------|-----------|
| **Total Return** | **+77.39%** |
| **Sharpe Ratio** | **0.77** |
| **Max Drawdown** | **-3.08%** |
| **Total Trades** | 386 |
| **Win Rate** | 42.5% |
| **Profit Factor** | 3.502 |
| **Elemental Cycles** | 5,239 |
| **Execute Rate** | 7.39% |
| **Consensus Rate** | 11.91% |
| **Avg Position Size** | $1,479 |
| **Position Review Exits** | **222** |

### Exit Reasons Breakdown (V15's Big Fix!)
| Exit Reason | Count | % of Trades |
|-------------|-------|-------------|
| **time_based** | 195 | 50.5% |
| **trailing_profit_stop** | 26 | 6.7% |
| **fire_vol_exit** | 54 | 14.0% |
| **earth_stop** | 110 | 28.5% |
| **water_bond_regime_shift** | 1 | 0.3% |

**Total Review-Based Exits**: 222 (was 0 in V14!)

## V15 Success Indicators

### ✅ Trailing Stop Working
26 positions closed by trailing profit stop:
- Activated at +40% unrealized gain
- Closed when price dropped 15% from peak
- Protected parabolic wins (DOGE, BTC, etc.)

### ✅ 60-Day Failsafe Restored
195 positions closed by time-based exit:
- Prevents indefinite position holding
- Forces portfolio turnover
- Reduces catastrophic drawdown risk

### ✅ Position Cap Enforced
All positions max at exactly $2,000.00:
- Prevents runaway position sizing
- Controls portfolio concentration
- Limits single-trade risk

### ✅ Cycles Preserved
Elemental cycles maintained at 5,239:
- Daily evaluation cycle intact
- No regression from V14 fix
- Proper cycle counting verified

## Comparison with Previous Versions

| Metric | V10 | V12 | V13 | V14 | **V15** |
|--------|-----|-----|-----|-----|---------|
| **Return** | +69.81% | +58.56% | +52.88% | +223.42%* | **+77.39%** |
| **Sharpe** | 0.61 | 0.59 | 0.57 | 5.99 | **0.77** |
| **Max DD** | -11.31% | -11.31% | -11.31% | -69.64% | **-3.08%** |
| **Cycles** | 4,427 | 1,368 | 494 | 5,239 | **5,239** |
| **Review Exits** | ? | ? | ? | 0 | **222** |
| **Position Cap** | ❌ | ❌ | ❌ | ❌ | **✅ €2k** |
| **Trailing Stop** | ❌ | ❌ | ❌ | ❌ | **✅** |

*V14's +223% was inflated by open positions; realized PnL was negative

## Critical Finding: Hedge Data Missing

**Hedge symbols have NO data in database:**
- SH (S&P 500 Inverse): 0 days
- PSQ (Nasdaq Inverse): 0 days
- RWM (Russell 2000 Inverse): 0 days
- TBF (Treasury Inverse): 0 days

**Impact**: Hedge pairs cannot function without historical data.
**Solution**: Import hedge ETF data from Yahoo Finance or similar source.

## Position Cap Verification

**All positions within €2,000 cap:**
```
BTC      avg=$1,203.95, max=$1,745.68, n=6
ETH      avg=$1,161.30, max=$1,568.94, n=8
AAPL     avg=$1,963.62, max=$2,000.00, n=7
NVDA     avg=$1,914.44, max=$2,000.00, n=6
MSFT     avg=$1,989.80, max=$2,000.00, n=6
```

## Risk Metrics Improved Dramatically

| Risk Metric | V14 | V15 | Improvement |
|-------------|-----|-----|-------------|
| Max Drawdown | -69.64% | **-3.08%** | 95.6% better |
| Win Rate | 4.4% | **42.5%** | 9.7x better |
| Profit Factor | 0.007 | **3.502** | 500x better |
| Avg Position | Variable | **≤€2k** | Controlled |

## Conclusion

### V15 Achievements
1. **Drawdown Control**: From -69.64% to -3.08%
2. **Profit Protection**: 26 trailing stops activated
3. **Forced Turnover**: 195 time-based exits
4. **Risk Management**: All positions capped at €2k
5. **Cycle Preservation**: 5,239 cycles maintained

### Trade-offs
- **Lower Return**: +77% vs V14's inflated +223%
- **Fewer Trades**: 386 vs V10's 1,152
- **But**: Sustainable, reproducible, lower risk

### Recommendation
V15 is **production-ready** from a risk management perspective. The only missing piece is hedge data import for bear market protection.

## Files
- Full results: `backtest_v15_full_2020_2026_20260222_002942.json`
- Smoke test: `backtest_v15_smoke_20260222_002908.json`
- Agent: `backend/agents/elemental_agent_manager_v15.py`
- Engine: `scripts/backtest_elemental_v15.py`
