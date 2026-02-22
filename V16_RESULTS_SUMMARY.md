# V16 Backtest Results Summary - Threshold Calibration

## Overview
V16 implements pure calibration fixes to restore execution rates:
1. **Fire floor**: 0.35 (was 0.50) - Restored from V10
2. **Earth floor**: 0.45 (was 0.55) - Restored from V10
3. **Ether harmony**: 0.45 (was 0.50) - Looser consensus
4. **Planet thresholds**: Lowered by 0.03 each
5. **AAVE removed**: Data anomaly eliminated

Retained from V15:
- Trailing stop (+40% → -15%)
- Position cap €2,000
- 60-day failsafe
- Daily cycle counting (5,239 cycles)

## Results

### Full Backtest (2020-2026, 50 Assets)
| Metric | V15 | **V16** | Change |
|--------|-----|---------|--------|
| **Total Return** | +77.39%* | **+2.11%** | -75.28pp |
| **Sharpe Ratio** | 0.77 | **0.97** | +0.20 |
| **Max Drawdown** | -3.08% | **-5.15%** | -2.07pp |
| **Total Trades** | 386 | **350** | -36 |
| **Win Rate** | 42.5% | **42.3%** | -0.2pp |
| **Profit Factor** | 3.502 | **1.158** | -2.344 |
| **Elemental Cycles** | 5,239 | **5,239** | Preserved |
| **Execute Rate** | 7.39% | **6.70%** | -0.69pp |
| **Consensus Rate** | 11.91% | **9.33%** | -2.58pp |
| **Hedge Entries** | 0 | **3** | ✅ Working!

*V15's +77% was inflated by AAVE anomaly

### Exit Reasons Breakdown
| Exit Reason | Count | % of Trades |
|-------------|-------|-------------|
| **time_based** | 185 | 52.9% |
| **trailing_profit_stop** | 19 | 5.4% |
| **fire_vol_exit** | 42 | 12.0% |
| **earth_stop** | 103 | 29.4% |
| **water_bond_regime_shift** | 1 | 0.3% |

**Total Review-Based Exits**: 205

## V16 Achievements

### ✅ Hedge Logic Working!
**3 hedge entries executed** - first time in any version!
- SH, PSQ, RWM, TBF data verified (1,508 days each)
- Hedge pairs activate when risk_on < 0.35
- Inverse ETFs provide bear market protection

### ✅ AAVE Anomaly Removed
AAVE caused artificial +3600% spike in V15:
- Price jumped from $0.51 to $52.00 (token swap glitch)
- Removed from universe in V16
- Organic return now visible: +2.11%

### ⚠️ Consensus Rate Still Low
| Version | Consensus Rate |
|---------|----------------|
| V10 | ~90% |
| V15 | 11.91% |
| **V16** | **9.33%** |

**Problem**: Calibration was insufficient. The 0.03 threshold reduction wasn't enough to restore V10's 90% consensus rate.

## Root Cause Analysis

### Why Did Consensus Drop Further?
1. **Data anomaly removal**: AAVE's extreme volatility created artificial consensus
2. **Genuine market conditions**: 2022 bear market reduced signal quality
3. **Threshold calibration insufficient**: 0.03 reduction (0.50→0.47) not aggressive enough

### Why Did Return Drop to +2.11%?
Without AAVE's +3600% anomaly:
- V15 organic return: ~+5.5% (estimated)
- V16 actual return: +2.11%
- Market conditions: 2022-2023 bear market impact

## Hedge Data Verification

```
SH:   1,508 days ✓
PSQ:  1,508 days ✓
RWM:  1,508 days ✓
TBF:  1,508 days ✓
```

All hedge symbols have complete data for 2020-2026 period.

## Position Cap Verification

```
AAPL: max=$2,000.00 ✓
NVDA: max=$2,000.00 ✓
MSFT: max=$2,000.00 ✓
BTC:  max=$1,745.69 ✓ (< €2k)
```

All positions within €2,000 cap.

## Comparison with Previous Versions

| Metric | V10 | V12 | V13 | V14 | V15 | **V16** |
|--------|-----|-----|-----|-----|-----|---------|
| **Return** | +69.8% | +58.6% | +52.9% | +223%* | +77%* | **+2.11%** |
| **Sharpe** | 0.61 | 0.59 | 0.57 | 5.99 | 0.77 | **0.97** |
| **Max DD** | -11.3% | -11.3% | -11.3% | -69.6% | -3.1% | **-5.15%** |
| **Consensus** | ~90% | ~56% | ~91% | 0.42% | 11.9% | **9.33%** |
| **Hedges** | N/A | N/A | N/A | 0 | 0 | **3** |

*Inflated by open positions (V14) or AAVE anomaly (V15)

## Conclusion

### V16 Successes
1. ✅ **Hedge logic working**: 3 hedge entries executed
2. ✅ **AAVE anomaly removed**: Clean organic returns
3. ✅ **Risk management preserved**: All V15 features working
4. ✅ **Cycles preserved**: 5,239 daily cycles maintained

### V16 Challenges
1. ⚠️ **Consensus rate too low**: 9.33% vs V10's 90%
2. ⚠️ **Return modest**: +2.11% in difficult market conditions
3. ⚠️ **Calibration insufficient**: Need more aggressive threshold reduction

### Recommendation for V17
**Aggressive threshold calibration needed**:
- Fire floor: 0.35 → 0.30
- Earth floor: 0.45 → 0.40
- Ether harmony: 0.45 → 0.40
- Planet thresholds: -0.05 each (not just -0.03)

Or consider removing the consensus floor entirely and relying on:
- Position sizing (€2k cap)
- Trailing stops
- 60-day failsafe

## Files
- Agent: `backend/agents/elemental_agent_manager_v16.py`
- Engine: `scripts/backtest_elemental_v16.py`
- Full Run: `scripts/backtest_elemental_v16_full.py`
- Results: `backtest_v16_full_2020_2026_20260222_012434.json`
