#!/usr/bin/env python3
"""Debug V13 cycle counting"""
import json

with open('backtest_v13_full_2020_2026_20260221_232310.json', 'r') as f:
    data = json.load(f)

print("=== V13 CYCLE ANALYSIS ===")
print(f"Total trading days: 2193")
print(f"Symbols: {len(data['symbols'])}")
print(f"Elemental cycles: {data['elemental_cycles']:,}")
print(f"Total trades: {data['total_trades']}")
print(f"Execute rate: {data['execute_rate_pct']:.4f}%")
print(f"Consensus rate: {data['consensus_rate_pct']:.4f}%")
print()

# Calculate expected cycles
symbols = len(data['symbols'])
days = 2193
expected_max = symbols * days
print(f"Expected max cycles (if all symbols every day): {expected_max:,}")
print(f"Actual / Expected: {data['elemental_cycles'] / expected_max * 100:.2f}%")
print()

# Work backwards from trades
trades = data['total_trades']
execute_rate = data['execute_rate_pct'] / 100
if execute_rate > 0:
    implied_cycles = trades / execute_rate
    print(f"Implied cycles from trades: {implied_cycles:,.0f}")
    print(f"Implied cycles per day: {implied_cycles / days:.1f}")
print()

# Compare with V12
print("=== COMPARISON ===")
print("V12 Full: 1,368 cycles for 769 trades = 56% execute rate")
print("V13 Full: 109,650 cycles for 448 trades = 0.41% execute rate")
print()
print("V12 Smoke: ~36 cycles for 31 trades = 86% execute rate")
print("V13 Smoke: ~34 cycles for 31 trades = 91% execute rate")
