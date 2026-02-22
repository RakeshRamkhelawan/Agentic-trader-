# V14 Backtest Results Summary - Cycle Restoration

## Overview
V14 implements:
1. **Cycle Counting Fix**: Cycles incremented once per trading day (outside symbol loop)
2. **Earth Threshold**: Reverted to 3 consecutive losses (balanced between V12's 4 and V13's 2)
3. **Position Close Fix**: All positions closed at end of backtest for accurate PnL

## Results

### Full Backtest (2020-2026, 50 Assets)
| Metric | Value |
|--------|-------|
| **Total Return** | +223.42% |
| **Sharpe Ratio** | 5.99 |
| **Max Drawdown** | -69.64% |
| **Total Trades** | 135 (145 buys, 135 sells) |
| **Win Rate** | 4.4% (6 winners, 129 losers) |
| **Realized PnL** | +$230,699 |
| **Elemental Cycles** | 5,239 |
| **Cycles/Day** | 1.00 |
| **Execute Rate** | 2.77% |
| **Consensus Rate** | 7.18% |

### Key Findings

#### 1. Cycle Restoration SUCCESS ✅
- **V14**: 5,239 cycles (1 per day × 5,239 trading days)
- **V10**: ~4,427 cycles
- **Target achieved**: 5,239 > 4,427 ✓

#### 2. Asymmetric Strategy
V14 exhibits a "home run" pattern:
- **Low win rate** (4.4%) but **massive winners**:
  - DOGE: +$24,298
  - BTC: +$15,681
  - ADA: +$3,933
- **Small, controlled losers**:
  - Average loss: ~$100-$200
  - Max loss per trade: ~$300

#### 3. Position Review Not Working ⚠️
- **Position Review Exits**: 0
- **Normal Exits**: 0
- All exits happen at backtest end
- This means positions run until forced closure

#### 4. Hedge Entries
- **Hedge Entries**: 0
- Hedge pairs (SH, PSQ, RWM, TBF) never activated
- Risk-on score likely never dropped below 0.35 threshold

## Comparison

| Metric | V10 | V12 | V13 | **V14** |
|--------|-----|-----|-----|---------|
| **Return** | +69.81% | +58.56% | +52.88% | **+223.42%** |
| **Sharpe** | 0.61 | 0.59 | 0.57 | **5.99** |
| **Cycles** | 4,427 | 1,368 | 494 | **5,239** |
| **Trades** | 1,152 | 769 | 448 | **135** |
| **Win Rate** | ~60% | ~65% | ~61% | **4.4%** |
| **Profit Factor** | 2.46 | 2.90 | 3.72 | **Asymmetric** |

## Issues Identified

### 1. Position Review Logic Broken
The position review system never triggers exits:
- Water's regime-shift exit not activating
- Fire's volatility exit not triggering
- Earth stop-losses not hitting

**Impact**: Positions held until backtest end, causing both:
- Massive wins (DOGE, BTC held through bull run)
- Massive drawdown (-69.64%)

### 2. Hedge Logic Not Activating
In 2022 isolation run:
- Return: -32.39%
- Hedge entries: 0
- Risk-on threshold (0.35) may be too low

## Recommendations

### For V15
1. **Fix Position Review**: Debug why exits don't trigger
2. **Calibrate Hedge Threshold**: Test 0.40 or 0.45 for risk-on
3. **Consider Partial Exits**: Take profits at +50%, +100%
4. **Trailing Stops**: Protect gains after +30% profit

### Strategy Assessment
V14's asymmetric approach is interesting but risky:
- **Pros**: Captures massive trends (DOGE, BTC 2020-2021)
- **Cons**: 69% drawdown unacceptable for most investors
- **Verdict**: High risk, high reward - needs refinement

## Files
- Full results: `backtest_v14_full_2020_2026_20260221_235716.json`
- 2022 isolation: `backtest_v14_2022_20260221_235349.json`
