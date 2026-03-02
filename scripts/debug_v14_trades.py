#!/usr/bin/env python3
"""Debug V14 trade issues"""
import json

with open('backtest_v14_full_2020_2026_20260221_235330.json', 'r') as f:
    data = json.load(f)

# Check trades
trades = data['trades']
print(f'Total trades: {len(trades)}')
buys = [t for t in trades if t['action'] == 'BUY']
sells = [t for t in trades if t['action'] == 'SELL']
print(f'Buys: {len(buys)}, Sells: {len(sells)}')

# Check winners/losers
winners = [t for t in sells if t.get('is_winner')]
losers = [t for t in sells if not t.get('is_winner')]
print(f'Winners: {len(winners)}, Losers: {len(losers)}')

# Sample trades
print()
print('Sample SELL trades:')
for t in sells[:10]:
    print(f"  {t['symbol']}: PnL={t.get('realized_pnl')}, is_winner={t.get('is_winner')}")

# Check for None values
print()
print('Checking for None values in is_winner:')
none_winner = [t for t in sells if t.get('is_winner') is None]
print(f'SELL trades with is_winner=None: {len(none_winner)}')

# Total PnL
total_pnl = sum(t.get('realized_pnl', 0) for t in sells if t.get('realized_pnl'))
print(f'\nTotal realized PnL from SELL trades: ${total_pnl:,.2f}')

# Check position review exits
print(f"\nPosition Review Exits: {data['position_review_exits']}")
print(f"Normal Exits: {data['normal_exits']}")
