#!/usr/bin/env python3
"""60-day multi-symbol test"""

import asyncio
import sys
sys.path.insert(0, '/app')

from scripts.smart_consciousness_backtest import SmartConsciousnessBacktest
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test():
    data_dir = Path('/app/data/historical_6year')
    data = {}

    for sym in ['BTC-EUR', 'ETH-EUR']:
        df = pd.read_pickle(data_dir / f'{sym}_1d_2020-2026_binance.pkl')
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        data[sym] = df
        print(f'Loaded {sym}: {len(df)} rows')

    engine = SmartConsciousnessBacktest(100000)
    print('\nRunning 60-day multi-symbol test...')
    results = await engine.run(data, days=60)

    print('\n' + '='*50)
    print('RESULTS')
    print('='*50)
    print(f"Return: {results['total_return_pct']:+.2f}%")
    print(f"Trades: {results['total_trades']}")
    cache = results['cache_stats']
    print(f"API Calls: {cache['api_calls']}")
    print(f"Cache Hits: {cache['cache_hits']}")
    print(f"Hit Rate: {cache['cache_hit_rate']*100:.1f}%")

    # Show guna distribution
    if results.get('guna_distribution'):
        print('\nGuna Distribution:')
        for guna, count in results['guna_distribution'].items():
            print(f"  {guna}: {count}")

if __name__ == "__main__":
    asyncio.run(test())
