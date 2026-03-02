#!/usr/bin/env python3
"""Test Bitvavo connection and fetch real market data."""

import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.execution.bitvavo_adapter import BitvavoAdapter


async def test():
    print("="*70)
    print("     BITVAVO CONNECTION TEST")
    print("="*70)
    print()

    adapter = BitvavoAdapter()
    success = await adapter.initialize()

    if success:
        print("[OK] Connected to Bitvavo")
        print()

        # Get available pairs
        eur_pairs = adapter.get_eur_pairs()
        print(f"[INFO] Available EUR pairs: {len(eur_pairs)}")
        print(f"       {', '.join(eur_pairs[:5])}...")
        print()

        # Get BTC/EUR ticker
        print("[FETCH] Getting BTC/EUR ticker...")
        ticker = await adapter.fetch_ticker("BTC/EUR")
        if ticker:
            print(f"[DATA] BTC/EUR Last: EUR {ticker['last']:,.2f}")
            print(f"[DATA] Bid: EUR {ticker['bid']:,.2f}, Ask: EUR {ticker['ask']:,.2f}")
            print(f"[DATA] 24h Volume: {ticker['baseVolume']:,.4f} BTC")
            print(f"[DATA] 24h Change: {ticker['percentage']:.2f}%")
        else:
            print("[ERROR] Failed to fetch ticker")

        print()

        # Get orderbook
        print("[FETCH] Getting BTC/EUR orderbook...")
        orderbook = await adapter.fetch_order_book("BTC/EUR", limit=5)
        if orderbook:
            print("[DATA] Top 5 Bids (buyers):")
            for price, qty in orderbook['bids'][:5]:
                print(f"       EUR {price:,.2f} x {qty:.6f} BTC")
            print("[DATA] Top 5 Asks (sellers):")
            for price, qty in orderbook['asks'][:5]:
                print(f"       EUR {price:,.2f} x {qty:.6f} BTC")

        await adapter.close()
        print()
        print("[OK] Test completed successfully")
    else:
        print("[ERROR] Failed to connect to Bitvavo")
        print("[INFO] Check your BITVAVO_API_KEY and BITVAVO_API_SECRET in .env")


if __name__ == "__main__":
    asyncio.run(test())
