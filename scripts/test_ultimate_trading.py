#!/usr/bin/env python3
"""Test ultimate paper trading system (short run)."""

import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from datetime import UTC, datetime
import uuid
import random


async def test():
    """Quick test of the system."""
    print("="*80)
    print("     ULTIMATE PAPER TRADING - QUICK TEST")
    print("="*80)
    print()

    # Test Bitvavo connection
    print("[TEST] Connecting to Bitvavo...")
    from backend.execution.bitvavo_adapter import BitvavoAdapter

    bitvavo = BitvavoAdapter()
    success = await bitvavo.initialize()

    if not success:
        print("[ERROR] Failed to connect to Bitvavo")
        return

    print("[OK] Connected to Bitvavo")

    # Get EUR pairs
    eur_pairs = bitvavo.get_eur_pairs()
    selected = eur_pairs[:20]  # Top 20
    print(f"[INFO] Selected {len(selected)} EUR pairs")
    print(f"       {', '.join(selected[:5])}...")
    print()

    # Initialize portfolio
    portfolio = ShadowPortfolioManager(initial_cash=10000.0)
    trades_executed = []

    # Fetch prices and trade
    print("[TRADING] Fetching prices and executing trades...")
    print()

    for i, symbol in enumerate(selected[:10]):  # Test with 10 symbols
        try:
            ticker = await bitvavo.fetch_ticker(symbol)
            if ticker and ticker.get('last'):
                price = ticker['last']
                portfolio.update_price(symbol, price)

                # Random buy/sell
                side = OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
                qty = 0.001

                order = OrderRequest(
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    order_type=OrderType.MARKET,
                    client_order_id=uuid.uuid4()
                )

                result = await portfolio.submit_order(order)

                if result.status.value == 'FILLED':
                    trades_executed.append({
                        'symbol': symbol,
                        'side': side.value,
                        'qty': qty,
                        'price': price,
                        'value': qty * price,
                    })
                    print(f"  [{i+1:2}] {side.value:4} {qty:.6f} {symbol:12} @ EUR {price:,.2f}")

                await asyncio.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  [SKIP] {symbol}: {e}")

    await bitvavo.close()

    # Summary
    print()
    print("="*80)
    print("     TEST COMPLETE")
    print("="*80)
    print(f"Trades executed: {len(trades_executed)}")

    balance = await portfolio.get_balance()
    print(f"Cash remaining: EUR {balance.get('EUR', 0):,.2f}")

    # Count positions
    positions = {k: v for k, v in balance.items() if k != 'EUR' and v > 0}
    print(f"Open positions: {len(positions)}")
    for sym, qty in list(positions.items())[:5]:
        print(f"  {sym}: {qty:.6f}")


if __name__ == "__main__":
    asyncio.run(test())
