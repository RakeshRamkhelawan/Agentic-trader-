"""
Simplified Exchange API Test
Tests what data we can get for paper trading
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("EXCHANGE API DATA COLLECTION TEST")
print("=" * 80)
print()


async def test_bitvavo():
    """Test Bitvavo API - what data can we get for paper trading?"""
    print("\n" + "=" * 80)
    print("BITVAVO - Data Available for Paper Trading")
    print("=" * 80)

    from backend.execution.bitvavo_adapter import BitvavoAdapter

    adapter = BitvavoAdapter()

    # Connect
    print("\n[1] Connecting to Bitvavo...")
    success = await adapter.initialize()
    if not success:
        print("  [ERROR] Failed to connect")
        return
    print("  [OK] Connected")

    # Get all EUR pairs
    print("\n[2] Getting EUR Trading Pairs...")
    eur_pairs = adapter.get_eur_pairs()
    print(f"  [OK] Total EUR pairs: {len(eur_pairs)}")
    print(f"  Sample: {', '.join(eur_pairs[:15])}")

    # Save full list
    with open("bitvavo_all_eur_pairs.json", "w") as f:
        json.dump(eur_pairs, f, indent=2)
    print(f"  [SAVED] bitvavo_all_eur_pairs.json ({len(eur_pairs)} pairs)")

    # Get ticker data for top pairs
    print("\n[3] Getting Real-Time Prices (Top 20)...")
    top_pairs = ["BTC-EUR", "ETH-EUR", "SOL-EUR", "XRP-EUR", "ADA-EUR",
                 "DOT-EUR", "LINK-EUR", "AVAX-EUR", "ATOM-EUR", "LTC-EUR",
                 "UNI-EUR", "AAVE-EUR", "SUI-EUR", "OP-EUR", "ARB-EUR",
                 "MATIC-EUR", "DOGE-EUR", "SHIB-EUR", "TRX-EUR", "BCH-EUR"]

    prices = {}
    for pair in top_pairs:
        try:
            ticker = await adapter.fetch_ticker(pair)
            if ticker:
                prices[pair] = {
                    "last": ticker.get("last"),
                    "bid": ticker.get("bid"),
                    "ask": ticker.get("ask"),
                    "high_24h": ticker.get("high"),
                    "low_24h": ticker.get("low"),
                    "change_24h_pct": ticker.get("percentage"),
                    "volume_24h": ticker.get("baseVolume"),
                    "timestamp": datetime.now().isoformat()
                }
                print(f"  {pair}: €{ticker.get('last', 'N/A')} ({ticker.get('percentage', 0):.2f}%)")
        except Exception as e:
            print(f"  [ERROR] {pair}: {e}")

    with open("bitvavo_prices_snapshot.json", "w") as f:
        json.dump(prices, f, indent=2)
    print(f"  [SAVED] bitvavo_prices_snapshot.json ({len(prices)} pairs)")

    # Get OHLCV data
    print("\n[4] Getting OHLCV/Candle Data...")
    try:
        # 1 hour candles, last 24 hours
        ohlcv = await adapter.fetch_ohlcv("BTC-EUR", timeframe="1h", limit=24)
        if ohlcv:
            print(f"  [OK] Got {len(ohlcv)} hourly candles for BTC-EUR")
            print(f"  Latest: Open=€{ohlcv[-1][1]}, High=€{ohlcv[-1][2]}, Low=€{ohlcv[-1][3]}, Close=€{ohlcv[-1][4]}")

            # Save in readable format
            candles = []
            for c in ohlcv:
                candles.append({
                    "timestamp": c[0],
                    "open": c[1],
                    "high": c[2],
                    "low": c[3],
                    "close": c[4],
                    "volume": c[5]
                })

            with open("bitvavo_btc_eur_ohlcv_1h.json", "w") as f:
                json.dump(candles, f, indent=2)
            print(f"  [SAVED] bitvavo_btc_eur_ohlcv_1h.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Get orderbook
    print("\n[5] Getting Order Book (Market Depth)...")
    try:
        ob = await adapter.fetch_order_book("BTC-EUR", limit=10)
        if ob:
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            print(f"  [OK] Orderbook: {len(bids)} bids, {len(asks)} asks")
            print(f"  Best Bid: €{bids[0][0]} ({bids[0][1]} BTC)")
            print(f"  Best Ask: €{asks[0][0]} ({asks[0][1]} BTC)")
            print(f"  Spread: €{asks[0][0] - bids[0][0]:.2f}")

            with open("bitvavo_btc_eur_orderbook.json", "w") as f:
                json.dump(ob, f, indent=2)
            print(f"  [SAVED] bitvavo_btc_eur_orderbook.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Get account balance
    print("\n[6] Getting Account Balance...")
    try:
        balance = await adapter.fetch_balance()
        if balance:
            print(f"  [OK] Account balance retrieved:")
            for asset, data in balance.items():
                if isinstance(data, dict):
                    free = data.get("free", 0)
                    used = data.get("used", 0)
                    total = data.get("total", 0)
                    if total > 0:
                        print(f"    {asset}: {free} free, {used} used (total: {total})")

            with open("bitvavo_balance.json", "w") as f:
                json.dump(balance, f, indent=2, default=str)
            print(f"  [SAVED] bitvavo_balance.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    await adapter.close()
    print("\n  [OK] Bitvavo connection closed")


async def test_revolut_x_simple():
    """Test Revolut X API with direct import"""
    print("\n" + "=" * 80)
    print("REVOLUT X - Data Available for Paper Trading")
    print("=" * 80)

    # Direct import to avoid circular imports
    import importlib.util
    spec = importlib.util.spec_from_file_location("revolut_x_client",
                                                  "backend/exchange/integrations/revolut_x_client.py")
    revolut_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revolut_module)
    RevolutXClient = revolut_module.RevolutXClient

    api_key = os.getenv("REVOLUT_API_KEY")
    private_key_path = os.getenv("REVOLUT_PRIVATE_KEY_PATH")

    if not api_key or not private_key_path:
        print("  [SKIP] Revolut X credentials not configured")
        return

    if not os.path.exists(private_key_path):
        print(f"  [SKIP] Private key not found: {private_key_path}")
        return

    client = RevolutXClient(api_key=api_key, private_key_path=private_key_path)

    # Connect
    print("\n[1] Connecting to Revolut X...")
    try:
        connected = await client.connect()
        if not connected:
            print("  [ERROR] Connection failed")
            return
        print("  [OK] Connected")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return

    # Get symbols
    print("\n[2] Getting Trading Pairs...")
    try:
        symbols = await client.get_symbols()
        print(f"  [OK] Total pairs: {len(symbols)}")
        print(f"  Sample: {', '.join(symbols[:15])}")

        with open("revolut_x_all_symbols.json", "w") as f:
            json.dump(symbols, f, indent=2)
        print(f"  [SAVED] revolut_x_all_symbols.json ({len(symbols)} pairs)")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Get ticker for BTC
    print("\n[3] Getting Real-Time Prices...")
    test_symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD"]
    prices = {}
    for symbol in test_symbols:
        try:
            ticker = await client.get_ticker(symbol)
            if ticker:
                prices[symbol] = {
                    "last": ticker.get("last"),
                    "bid": ticker.get("bid"),
                    "ask": ticker.get("ask"),
                    "timestamp": datetime.now().isoformat()
                }
                print(f"  {symbol}: ${ticker.get('last', 'N/A')}")
        except Exception as e:
            print(f"  [ERROR] {symbol}: {e}")

    with open("revolut_x_prices_snapshot.json", "w") as f:
        json.dump(prices, f, indent=2)
    print(f"  [SAVED] revolut_x_prices_snapshot.json ({len(prices)} pairs)")

    # Get orderbook
    print("\n[4] Getting Order Book...")
    try:
        ob = await client.get_orderbook("BTC-USD", limit=10)
        if ob:
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            print(f"  [OK] Orderbook: {len(bids)} bids, {len(asks)} asks")
            if bids and asks:
                print(f"  Best Bid: ${bids[0][0]} ({bids[0][1]} BTC)")
                print(f"  Best Ask: ${asks[0][0]} ({asks[0][1]} BTC)")

            with open("revolut_x_btc_usd_orderbook.json", "w") as f:
                json.dump(ob, f, indent=2)
            print(f"  [SAVED] revolut_x_btc_usd_orderbook.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Get balance
    print("\n[5] Getting Account Balance...")
    try:
        balance = await client.get_balance()
        if balance:
            print(f"  [OK] Balance retrieved:")
            # Print structure
            if isinstance(balance, dict):
                for k, v in list(balance.items())[:5]:
                    print(f"    {k}: {v}")

            with open("revolut_x_balance.json", "w") as f:
                json.dump(balance, f, indent=2, default=str)
            print(f"  [SAVED] revolut_x_balance.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Get active orders
    print("\n[6] Getting Active Orders...")
    try:
        orders = await client.get_active_orders()
        print(f"  [OK] Active orders: {len(orders)}")
        for order in orders[:3]:
            print(f"    {order.get('side')} {order.get('quantity')} {order.get('symbol')}")

        with open("revolut_x_active_orders.json", "w") as f:
            json.dump(orders, f, indent=2, default=str)
        print(f"  [SAVED] revolut_x_active_orders.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    await client.disconnect()
    print("\n  [OK] Revolut X connection closed")


async def main():
    print(f"\nTest started: {datetime.now()}")
    print(f"Python: {sys.version}\n")

    # Test Bitvavo
    await test_bitvavo()

    # Test Revolut X
    await test_revolut_x_simple()

    print("\n" + "=" * 80)
    print("TEST COMPLETE - All data saved to JSON files")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
