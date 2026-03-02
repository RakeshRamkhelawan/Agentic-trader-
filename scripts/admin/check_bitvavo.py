#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app')

import ccxt.async_support as ccxt
from backend.core.config.settings import settings

async def test():
    exchange = ccxt.bitvavo({
        'apiKey': settings.BITVAVO_API_KEY,
        'secret': settings.BITVAVO_API_SECRET,
    })
    
    try:
        await exchange.load_markets()
        tickers = await exchange.fetch_tickers(['BTC/EUR', 'ETH/EUR', 'SOL/EUR', 'ADA/EUR', 'DOT/EUR'])
        print('Raw tickers from Bitvavo:')
        for symbol, data in tickers.items():
            print(f'  {symbol}:')
            print(f'    last: {data.get("last")}')
            print(f'    percentage: {data.get("percentage")}')
            print(f'    change: {data.get("change")}')
            print()
    finally:
        await exchange.close()

asyncio.run(test())
