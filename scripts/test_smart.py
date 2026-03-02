#!/usr/bin/env python3
"""Quick test of smart consciousness system"""

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
    for sym in ['BTC-EUR']:
        df = pd.read_pickle(data_dir / f'{sym}_1d_2020-2026_binance.pkl')
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, unit='ms')
        data[sym] = df
        print(f'Loaded {sym}: {len(df)} rows')
    
    engine = SmartConsciousnessBacktest(100000)
    print('\nRunning 30-day smart test...')
    results = await engine.run(data, days=30)
    
    print('\n=== RESULTS ===')
    print(f"Return: {results['total_return_pct']:+.2f}%")
    print(f"Trades: {results['total_trades']}")
    cache = results['cache_stats']
    print(f"API Calls: {cache['api_calls']}")
    print(f"Cache Hits: {cache['cache_hits']}")
    print(f"Hit Rate: {cache['cache_hit_rate']*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test())
