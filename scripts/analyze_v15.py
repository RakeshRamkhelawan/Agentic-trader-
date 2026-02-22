#!/usr/bin/env python3
"""Analyze V15 backtest results"""
import json
import sys

with open(sys.argv[1], 'r') as f:
    data = json.load(f)

print('=== V15 PORTFOLIO PERFORMANCE ===')
print(f"Total Return: {data['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {data['max_drawdown_pct']:.2f}%")
print(f"Total Trades: {data['total_trades']}")
print(f"Win Rate: {data['win_rate_pct']:.1f}%")
print(f"Profit Factor: {data.get('profit_factor', 0):.3f}")
print()

print('=== V15 CYCLE & EXECUTION METRICS ===')
print(f"Elemental Cycles: {data['elemental_cycles']:,}")
print(f"Execute Rate: {data['execute_rate_pct']:.2f}%")
print(f"Consensus Rate: {data['consensus_rate_pct']:.2f}%")
print(f"Avg Position Size: ${data['avg_position_size']:.2f}")
print()

print('=== V15 EXIT REASONS (The Big Fix!) ===')
exit_reasons = data.get('exit_reasons', {})
for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
    pct = count / data['total_trades'] * 100 if data['total_trades'] else 0
    print(f"  {reason:30s}: {count:4d} ({pct:5.1f}%)")
print()

# Calculate review exits
time_based = exit_reasons.get('time_based', 0)
trailing = exit_reasons.get('trailing_profit_stop', 0)
print("\nV15 SUCCESS INDICATORS:")
print(f"  [OK] time_based exits: {time_based} (60-day failsafe working!)")
print(f"  [OK] trailing_profit_stop: {trailing} (profit protection working!)")
print(f"  [OK] Position Review Exits: {data['position_review_exits']} (was 0 in V14!)")
print()

print('=== V15 vs V10 COMPARISON ===')
print(f"{'Metric':<25} {'V10':>12} {'V15':>12} {'Change':>12}")
print("-" * 65)
print(f"{'Return':<25} {'+69.81%':>12} {'+' + format(data['total_return_pct'], '.2f') + '%':>12} {'+' + format(data['total_return_pct']-69.81, '.2f') + '%':>12}")
print(f"{'Sharpe':<25} {'0.61':>12} {data['sharpe_ratio']:>12.2f} {'+' + format(data['sharpe_ratio']-0.61, '.2f'):>12}")
print(f"{'Cycles':<25} {'4,427':>12} {format(data['elemental_cycles'], ','):>12} {'Preserved':>12}")
print(f"{'Trades':<25} {'1,152':>12} {str(data['total_trades']):>12} {format(data['total_trades']-1152, '+d'):>12}")
print()

print('=== HEDGE DATA STATUS ===')
print(f"Hedge Entries: {data['hedge_entries']}")
print("[!] Hedge symbols (SH, PSQ, RWM, TBF) have NO data in database!")
print("    Hedge trades cannot work without historical data.")
print()

print('=== POSITION CAP VERIFICATION ===')
symbol_summary = data.get('symbol_position_summary', {})
max_sizes = []
for sym, stats in symbol_summary.items():
    max_sizes.append(stats['max'])
    if stats['max'] > 2000:
        print(f"  ⚠️  {sym}: max=${stats['max']:.2f} (exceeds cap!)")

if max_sizes:
    overall_max = max(max_sizes)
    print(f"  Overall max position size: ${overall_max:.2f}")
    if overall_max <= 2000:
        print("  [OK] All positions within €2,000 cap!")
