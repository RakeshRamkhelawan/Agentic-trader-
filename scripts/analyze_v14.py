#!/usr/bin/env python3
"""Analyze V14 backtest results"""
import json
import sys

with open(sys.argv[1], 'r') as f:
    data = json.load(f)

print('=== V14 PORTFOLIO PERFORMANCE ===')
print(f"Total Return: {data['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {data['max_drawdown_pct']:.2f}%")
print(f"Total Trades: {data['total_trades']}")
print(f"Win Rate: {data['win_rate_pct']:.1f}%")
print(f"Profit Factor: {data['profit_factor']:.3f}")
print()

print('=== CYCLE & AGENT METRICS ===')
print(f"Elemental Cycles: {data['elemental_cycles']:,}")
print(f"Execute Rate: {data['execute_rate_pct']:.2f}%")
print(f"Consensus Rate: {data['consensus_rate_pct']:.2f}%")
print(f"Avg Position Size: ${data['avg_position_size']:.2f}")
print()

# Calculate days
days = len(data['equity_curve'])
print(f"Trading Days: {days}")
print(f"Cycles per Day: {data['elemental_cycles']/days:.2f}")
print()

print('=== AGENT CONFIDENCES ===')
for agent in ['fire', 'water', 'air', 'earth', 'ether']:
    if agent in data['agent_stats']:
        stats = data['agent_stats'][agent]
        print(f"{agent.upper():8} avg={stats['avg_confidence']:.3f} samples={stats['samples']}")
print()

# Symbol analysis
print('=== SYMBOL TRADE COUNTS (Top 15) ===')
symbol_counts = {}
for t in data['trades']:
    if t['action'] == 'BUY':
        sym = t['symbol']
        symbol_counts[sym] = symbol_counts.get(sym, 0) + 1

sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
for sym, count in sorted_symbols[:15]:
    print(f"  {sym:8} {count} trades")
print()

print('=== HEDGE STATS ===')
print(f"Hedge Entries: {data['hedge_entries']}")
print(f"Position Review Exits: {data['position_review_exits']}")
print()

print('=== COMPARISON ===')
print("V10: 4,427 cycles -> 1,152 trades (+69.81%)")
print(f"V14: {data['elemental_cycles']:,} cycles -> {data['total_trades']} trades ({data['total_return_pct']:+.2f}%)")
print(f"Efficiency: {data['total_trades']/data['elemental_cycles']*100:.2f}% of cycles become trades")
