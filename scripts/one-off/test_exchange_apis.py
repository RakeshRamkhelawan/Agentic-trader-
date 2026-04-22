"""
Test Bitvavo en Revolut X APIs voor Paper Trading Data
Tests public endpoints (geen auth nodig) en private endpoints (met auth)
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("EXCHANGE API TEST - Bitvavo & Revolut X")
print("=" * 80)
print()


async def test_bitvavo():
    """Test Bitvavo API"""
    print("\n" + "=" * 80)
    print("BITVAVO API TEST")
    print("=" * 80)

    # Import adapter
    from backend.execution.bitvavo_adapter import BitvavoAdapter

    adapter = BitvavoAdapter()

    # Test 1: Initialize (public endpoints work without auth)
    print("\n[TEST 1] Initialize Bitvavo...")
    try:
        success = await adapter.initialize()
        if success:
            print("  [OK] Bitvavo connected")
        else:
            print("  [WARN] Bitvavo init failed (credentials mogelijk ongeldig)")
            return
    except Exception as e:
        print(f"  [ERROR] {e}")
        return

    # Test 2: Get EUR pairs
    print("\n[TEST 2] Available EUR Trading Pairs...")
    try:
        eur_pairs = adapter.get_eur_pairs()
        print(f"  [OK] Found {len(eur_pairs)} EUR pairs")
        print(f"  Sample pairs: {eur_pairs[:10]}")

        # Save to file
        with open("bitvavo_eur_pairs.json", "w") as f:
            json.dump(eur_pairs, f, indent=2)
        print(f"  [SAVED] bitvavo_eur_pairs.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 3: Fetch ticker data
    print("\n[TEST 3] Fetch Ticker Data (BTC-EUR)...")
    try:
        ticker = await adapter.fetch_ticker("BTC-EUR")
        if ticker:
            print(f"  [OK] BTC-EUR ticker:")
            print(f"    Last: €{ticker.get('last', 'N/A')}")
            print(f"    Bid: €{ticker.get('bid', 'N/A')}")
            print(f"    Ask: €{ticker.get('ask', 'N/A')}")
            print(f"    Volume: {ticker.get('volume', 'N/A')}")
            print(f"    24h High: €{ticker.get('high', 'N/A')}")
            print(f"    24h Low: €{ticker.get('low', 'N/A')}")
            print(f"    24h Change: {ticker.get('percentage', 'N/A')}%")

            # Save to file
            with open("bitvavo_ticker_btc_eur.json", "w") as f:
                json.dump(ticker, f, indent=2, default=str)
            print(f"  [SAVED] bitvavo_ticker_btc_eur.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 4: Fetch multiple tickers
    print("\n[TEST 4] Fetch Multiple Tickers...")
    test_pairs = ["BTC-EUR", "ETH-EUR", "SOL-EUR", "XRP-EUR", "ADA-EUR"]
    ticker_data = {}

    for pair in test_pairs:
        try:
            ticker = await adapter.fetch_ticker(pair)
            if ticker:
                ticker_data[pair] = {
                    "last": ticker.get("last"),
                    "bid": ticker.get("bid"),
                    "ask": ticker.get("ask"),
                    "volume": ticker.get("volume"),
                    "change_24h": ticker.get("percentage")
                }
                print(f"  [OK] {pair}: €{ticker.get('last', 'N/A')}")
        except Exception as e:
            print(f"  [ERROR] {pair}: {e}")

    if ticker_data:
        with open("bitvavo_tickers_sample.json", "w") as f:
            json.dump(ticker_data, f, indent=2)
        print(f"  [SAVED] bitvavo_tickers_sample.json")

    # Test 5: Orderbook
    print("\n[TEST 5] Fetch Orderbook (BTC-EUR)...")
    try:
        orderbook = await adapter.fetch_order_book("BTC-EUR", limit=10)
        if orderbook:
            bids = orderbook.get("bids", [])[:5]
            asks = orderbook.get("asks", [])[:5]
            print(f"  [OK] Top 5 Bids:")
            for bid in bids:
                print(f"    Price: €{bid[0]}, Amount: {bid[1]} BTC")
            print(f"  [OK] Top 5 Asks:")
            for ask in asks:
                print(f"    Price: €{ask[0]}, Amount: {ask[1]} BTC")

            with open("bitvavo_orderbook_btc_eur.json", "w") as f:
                json.dump(orderbook, f, indent=2)
            print(f"  [SAVED] bitvavo_orderbook_btc_eur.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 6: Recent trades
    print("\n[TEST 6] Fetch Recent Trades (BTC-EUR)...")
    try:
        # Revolut X doesn't have fetch_recent_trades method in this adapter
        trades = []
        if trades:
            print(f"  [OK] Last {len(trades)} trades:")
            for trade in trades[:5]:
                side = "BUY" if trade.get("side") == "buy" else "SELL"
                print(f"    {side}: {trade.get('amount')} BTC @ €{trade.get('price')}")

            with open("bitvavo_trades_btc_eur.json", "w") as f:
                json.dump(trades, f, indent=2, default=str)
            print(f"  [SAVED] bitvavo_trades_btc_eur.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 7: OHLCV/Candles
    print("\n[TEST 7] Fetch OHLCV Candles (BTC-EUR, 1h)...")
    try:
        candles = await adapter.fetch_ohlcv("BTC-EUR", timeframe="1h", limit=24)
        if candles:
            print(f"  [OK] Last {len(candles)} candles:")
            for candle in candles[-3:]:
                print(f"    {candle[0]}: Open €{candle[1]}, High €{candle[2]}, Low €{candle[3]}, Close €{candle[4]}, Vol {candle[5]}")

            with open("bitvavo_candles_btc_eur.json", "w") as f:
                json.dump(candles, f, indent=2)
            print(f"  [SAVED] bitvavo_candles_btc_eur.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 8: Account info (requires auth)
    print("\n[TEST 8] Fetch Account Balance...")
    try:
        if adapter.api_key and adapter.api_secret:
            balance = await adapter.fetch_balance()
            print(f"  [OK] Account balance:")
            for asset, amount in balance.items():
                if amount > 0:
                    print(f"    {asset}: {amount}")

            with open("bitvavo_balance.json", "w") as f:
                json.dump(balance, f, indent=2)
            print(f"  [SAVED] bitvavo_balance.json")
        else:
            print("  [SKIP] No API credentials")
    except Exception as e:
        print(f"  [ERROR] {e}")

    await adapter.close()


async def test_revolut_x():
    """Test Revolut X API"""
    print("\n" + "=" * 80)
    print("REVOLUT X API TEST")
    print("=" * 80)

    try:
        from backend.exchange.integrations.revolut_x_client import RevolutXClient
    except ImportError:
        # Fallback: direct import
        import sys
        sys.path.insert(0, 'backend/exchange')
        from integrations.revolut_x_client import RevolutXClient

    api_key = os.getenv("REVOLUT_API_KEY")
    private_key_path = os.getenv("REVOLUT_PRIVATE_KEY_PATH")

    if not api_key:
        print("  [SKIP] REVOLUT_API_KEY not configured")
        return

    if not private_key_path or not os.path.exists(private_key_path):
        print(f"  [SKIP] Private key not found: {private_key_path}")
        return

    client = RevolutXClient(api_key=api_key, private_key_path=private_key_path)

    # Test 1: Connect
    print("\n[TEST 1] Connect to Revolut X...")
    try:
        connected = await client.connect()
        if connected:
            print("  [OK] Revolut X connected")
        else:
            print("  [ERROR] Connection failed")
            return
    except Exception as e:
        print(f"  [ERROR] {e}")
        return

    # Test 2: Get symbols
    print("\n[TEST 2] Available Trading Pairs...")
    try:
        symbols = await client.get_symbols()
        print(f"  [OK] Found {len(symbols)} trading pairs")
        print(f"  Sample pairs: {symbols[:10]}")

        with open("revolut_x_symbols.json", "w") as f:
            json.dump(symbols, f, indent=2)
        print(f"  [SAVED] revolut_x_symbols.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 3: Get ticker
    print("\n[TEST 3] Fetch Ticker (BTC-USD)...")
    try:
        ticker = await client.get_ticker("BTC-USD")
        if ticker:
            print(f"  [OK] BTC-USD ticker:")
            print(f"    Last: ${ticker.get('last', 'N/A')}")
            print(f"    Bid: ${ticker.get('bid', 'N/A')}")
            print(f"    Ask: ${ticker.get('ask', 'N/A')}")
            print(f"    Volume: {ticker.get('volume', 'N/A')}")

            with open("revolut_x_ticker_btc_usd.json", "w") as f:
                json.dump(ticker, f, indent=2, default=str)
            print(f"  [SAVED] revolut_x_ticker_btc_usd.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 4: Get orderbook
    print("\n[TEST 4] Fetch Orderbook (BTC-USD)...")
    try:
        orderbook = await client.get_orderbook("BTC-USD", limit=10)
        if orderbook:
            bids = orderbook.get("bids", [])[:5]
            asks = orderbook.get("asks", [])[:5]
            print(f"  [OK] Top 5 Bids:")
            for bid in bids:
                print(f"    Price: ${bid[0]}, Amount: {bid[1]} BTC")
            print(f"  [OK] Top 5 Asks:")
            for ask in asks:
                print(f"    Price: ${ask[0]}, Amount: {ask[1]} BTC")

            with open("revolut_x_orderbook_btc_usd.json", "w") as f:
                json.dump(orderbook, f, indent=2)
            print(f"  [SAVED] revolut_x_orderbook_btc_usd.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 5: Recent trades
    print("\n[TEST 5] Fetch Recent Trades (BTC-USD)...")
    try:
        trades = await client.get_recent_trades("BTC-USD", limit=10)
        if trades:
            print(f"  [OK] Last {len(trades)} trades:")
            for trade in trades[:5]:
                side = trade.get("side", "?").upper()
                print(f"    {side}: {trade.get('size', '?')} BTC @ ${trade.get('price', '?')}")

            with open("revolut_x_trades_btc_usd.json", "w") as f:
                json.dump(trades, f, indent=2, default=str)
            print(f"  [SAVED] revolut_x_trades_btc_usd.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 6: Account balance
    print("\n[TEST 6] Fetch Account Balance...")
    try:
        balance = await client.get_balance()
        if balance:
            print(f"  [OK] Account balance:")
            for asset, data in balance.items():
                if isinstance(data, dict) and data.get("available", 0) > 0:
                    print(f"    {asset}: {data['available']} (available)")

            with open("revolut_x_balance.json", "w") as f:
                json.dump(balance, f, indent=2)
            print(f"  [SAVED] revolut_x_balance.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # Test 7: Active orders
    print("\n[TEST 7] Fetch Active Orders...")
    try:
        orders = await client.get_active_orders()
        print(f"  [OK] Active orders: {len(orders)}")
        for order in orders[:3]:
            print(f"    {order.get('side')} {order.get('quantity')} {order.get('symbol')} @ {order.get('price', 'market')}")

        with open("revolut_x_active_orders.json", "w") as f:
            json.dump(orders, f, indent=2, default=str)
        print(f"  [SAVED] revolut_x_active_orders.json")
    except Exception as e:
        print(f"  [ERROR] {e}")

    await client.disconnect()


async def main():
    """Main test runner"""
    print(f"\nTest started at: {datetime.now()}")
    print(f"Python: {sys.version}")
    print()

    # Test Bitvavo
    await test_bitvavo()

    # Test Revolut X
    await test_revolut_x()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nAll data saved to JSON files for analysis.")


if __name__ == "__main__":
    asyncio.run(main())
