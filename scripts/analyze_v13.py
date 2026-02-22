#!/usr/bin/env python3
"""Analyze V13 backtest results"""
import json
import sys

with open(sys.argv[1], 'r') as f:
    data = json.load(f)

print('=== V13 PORTFOLIO PERFORMANCE ===')
print(f"Total Return: {data['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {data['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {data['max_drawdown_pct']:.2f}%")
print(f"Total Trades: {data['total_trades']}")
print(f"Win Rate: {data['win_rate_pct']:.1f}%")
print(f"Profit Factor: {data['profit_factor']:.3f}")
print()

print('=== CYCLE & AGENT METRICS ===')
print(f"Elemental Cycles: {data['elemental_cycles']:,}")
print(f"Agent Samples (consensus): {data['agent_stats']['ether']['samples']}")
print(f"Execute Rate: {data['execute_rate_pct']:.2f}%")
print(f"Consensus Rate: {data['consensus_rate_pct']:.2f}%")
print(f"Avg Position Size: ${data['avg_position_size']:.2f}")
print()

# Calculate actual execute rate
trades = data['total_trades']
cycles = data['elemental_cycles']
consensus = data['agent_stats']['ether']['samples']
print(f"Actual: {trades} trades / {consensus} consensus = {trades/consensus*100:.1f}% execution of consensus")
print(f"Actual: {consensus} consensus / {cycles} cycles = {consensus/cycles*100:.2f}% consensus rate")
print()

print('=== AGENT CONFIDENCES ===')
for agent in ['fire', 'water', 'air', 'earth', 'ether']:
    stats = data['agent_stats'][agent]
    print(f"{agent.upper():8} avg={stats['avg_confidence']:.3f} samples={stats['samples']}")
print()

print('=== SYMBOL TRADE COUNTS (Top 10) ===')
symbol_counts = {}
for t in data['trades']:
    if t['action'] == 'BUY':
        sym = t['symbol']
        symbol_counts[sym] = symbol_counts.get(sym, 0) + 1

sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
for sym, count in sorted_symbols[:10]:
    print(f"  {sym:8} {count} trades")
print()

print('=== HEDGE STATS ===')
print(f"Hedge Entries: {data['hedge_entries']}")
print(f"Position Review Exits: {data['position_review_exits']}")
print(f"Normal Exits: {data['normal_exits']}")
