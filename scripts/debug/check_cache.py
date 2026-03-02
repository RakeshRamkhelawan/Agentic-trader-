#!/usr/bin/env python3
"""Check cache contents for debugging."""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
from backend.core.cache_layer import get_cache

async def check():
    cache = get_cache()

    print("Checking cache contents...")
    print("=" * 60)

    # Check markets:all
    all_markets = await cache.get('markets:all')
    if all_markets:
        print(f"\nmarkets:all has {len(all_markets)} items")
        for m in all_markets[:5]:
            print(f"  {m.get('symbol')}: price={m.get('price')}, exchange={m.get('exchange')}")
    else:
        print("\nmarkets:all is EMPTY")

    # Check exchange-specific caches
    for ex in ['kraken', 'revolut', 'bitvavo']:
        markets = await cache.get(f'markets:{ex}')
        if markets:
            print(f"\nmarkets:{ex} has {len(markets)} items")
            for m in markets[:3]:
                print(f"  {m.get('symbol')}: price={m.get('price')}")
        else:
            print(f"\nmarkets:{ex} is empty")

if __name__ == "__main__":
    asyncio.run(check())
