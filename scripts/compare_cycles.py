#!/usr/bin/env python3
"""Compare cycle counting across versions"""
import json

print("=== CYCLE COUNTING COMPARISON ===\n")

# V10
print("V10 Full (2020-2026):")
try:
    with open("backtest_elemental_v10_full_2020_2026.json", "r") as f:
        data = json.load(f)
    cycles = data.get("elemental_cycles", 0)
    trades = data["total_trades"]
    print(f"  Cycles: {cycles:,}")
    print(f"  Trades: {trades}")
    print(
        f"  Execute rate: {trades/cycles*100:.2f}%" if cycles else "  Execute rate: N/A"
    )
except Exception as e:
    print(f"  Error: {e}")

print()

# V12
print("V12 Full (2020-2026):")
try:
    with open("backtest_elemental_v12_full_2020_2026_20250219_165337.json", "r") as f:
        data = json.load(f)
    cycles = data.get("elemental_cycles", 0)
    trades = data["total_trades"]
    print(f"  Cycles: {cycles:,}")
    print(f"  Trades: {trades}")
    print(
        f"  Execute rate: {trades/cycles*100:.2f}%" if cycles else "  Execute rate: N/A"
    )
except Exception as e:
    print(f"  Error: {e}")

print()

# V13
print("V13 Full (2020-2026):")
try:
    with open("backtest_v13_full_2020_2026_20260221_232310.json", "r") as f:
        data = json.load(f)
    cycles = data.get("elemental_cycles", 0)
    trades = data["total_trades"]
    print(f"  Cycles: {cycles:,}")
    print(f"  Trades: {trades}")
    print(
        f"  Execute rate: {trades/cycles*100:.2f}%" if cycles else "  Execute rate: N/A"
    )
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== ANALYSIS ===")
print("V10: ~4,427 cycles = realistic count of evaluations")
print("V12: 1,368 cycles = under-counted (too few)")
print("V13: 109,650 cycles = over-counted (all symbols every day)")
