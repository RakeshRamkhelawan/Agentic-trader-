"""
Market Sync Task - Periodic background synchronization of market data to Redis.
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.core.cache_layer import get_cache
from backend.execution.exchange_adapter import ExchangeAdapter
from backend.core.config.settings import settings
import ccxt.async_support as ccxt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_kraken(cache):
    """Sync public Kraken tickers."""
    try:
        exchange = ccxt.kraken()
        logger.info("Syncing Kraken tickers...")
        # Default interesting symbols
        symbols = [
            "BTC/EUR",
            "ETH/EUR",
            "SOL/EUR",
            "ADA/EUR",
            "DOT/EUR",
            "XRP/EUR",
            "LINK/EUR",
            "DOGE/EUR",
        ]
        tickers = await exchange.fetch_tickers(symbols)

        markets_data = []
        for symbol, ticker in tickers.items():
            markets_data.append(
                {
                    "symbol": symbol.replace("/", "-"),
                    "name": symbol.split("/")[0],
                    "price": ticker.get("last", 0.0),
                    "change": ticker.get("percentage", 0.0),
                    "volume": f"{ticker.get('baseVolume', 0.0) or 0.0:.2f}",
                    "favorite": False,
                }
            )

        await cache.set("markets:kraken", markets_data, ttl=60)
        await exchange.close()
        logger.info(f"Synced {len(markets_data)} symbols from Kraken")
    except Exception as e:
        logger.error(f"Kraken sync failed: {e}")


async def sync_revolut(cache):
    """Sync Revolut instruments and tickers."""
    try:

        # Using system credentials for background sync if available
        if not (settings.REVOLUT_API_KEY and settings.REVOLUT_PRIVATE_KEY):
            logger.warning("Revolut system credentials missing. Skipping Revolut sync.")
            return

        adapter = ExchangeAdapter(
            api_key=settings.REVOLUT_API_KEY,
            private_key_pem=settings.REVOLUT_PRIVATE_KEY,
            base_url=(
                "https://revx.revolut.com"
                if not settings.REVOLUT_SANDBOX
                else "https://sandbox-revx.revolut.com"
            ),
        )
        logger.info("Syncing Revolut instruments...")

        instruments = await adapter.get_instruments()
        # Cache the raw instruments for internal service use
        await cache.set_instruments(instruments, "revolut")

        markets_data = []
        # Instruments in Revolut dictionary: {"BTC/EUR": {...}, ...}
        # Iterate over items to get both symbol and detail
        if isinstance(instruments, dict):
            items = instruments.items()
        elif isinstance(instruments, list):
            # Fallback if it's a list (some adapters might normalize it)
            items = [
                (inst if isinstance(inst, str) else inst.get("symbol"), inst)
                for inst in instruments
            ]
        else:
            logger.error(f"Unexpected instruments format: {type(instruments)}")
            return

        for sym, detail in items:
            # Flexible separator check (Revolut uses /, others might use -)
            if any(x in sym.upper() for x in ["/EUR", "-EUR", "BTCEUR", "ETHEUR"]):
                # Normalize symbol for frontend
                display_symbol = sym.replace("/", "-")

                # Extract meta-data if detail is a dict
                name = sym.split("/")[0].split("-")[0]
                if isinstance(detail, dict):
                    name = detail.get("base", name)

                markets_data.append(
                    {
                        "symbol": display_symbol,
                        "raw_symbol": sym,  # Keep for ticker lookup
                        "name": name,
                        "price": 0.0,
                        "change": 0.0,
                        "volume": "0",
                        "favorite": False,
                    }
                )

        if markets_data:
            # EXCLUDE TOXIC SYMBOLS that cause bulk API failures (400 Bad Request)
            blacklist = ["RNDR/EUR", "FTM/EUR", "USDT/EUR", "EOS/EUR"]
            filtered_markets = [
                m for m in markets_data if m["raw_symbol"] not in blacklist
            ]

            # Fetch real prices in bulk for valid symbols
            raw_symbols = [m["raw_symbol"] for m in filtered_markets]
            logger.info(
                f"Fetching tickers for {len(raw_symbols)} Revolut symbols (excluded {len(blacklist)} toxic)..."
            )
            tickers = await adapter.get_tickers(raw_symbols)

            # NEW: Store ticks to DB for history
            from backend.services.trading_service import get_trading_service
            from datetime import datetime

            trading_service = get_trading_service()
            current_time = datetime.utcnow()

            ticks_to_save = []
            for sym, ticker_data in tickers.items():
                if ticker_data:
                    ticks_to_save.append(
                        {
                            "symbol": sym,  # e.g. BTC/EUR
                            "timestamp": current_time,
                            "price": ticker_data.get("last", 0.0),
                            "volume": ticker_data.get("volume_24h", 0.0),
                            "side": "last",  # It's a last price
                            "seq": 0,
                        }
                    )
            if ticks_to_save:
                await trading_service.store_market_ticks_bulk(ticks_to_save)

            # NEW: Fetch 24h reference prices to calc change if API is missing it
            ref_prices = {}
            try:
                ref_prices = await trading_service.get_24h_reference_prices(raw_symbols)
            except Exception as e:
                logger.error(f"Failed to get ref prices: {e}")

            matched_count = 0
            for m in markets_data:
                # If cached from previous run or skipped, price remains 0.0
                if m["raw_symbol"] in blacklist:
                    continue

                ticker = tickers.get(m["raw_symbol"])
                if ticker:
                    price = ticker.get("last", 0.0)
                    change = ticker.get("change_24h", 0.0)
                    volume = ticker.get("volume_24h", 0.0)

                    # Calculate change from DB if API is 0.0
                    if change == 0.0 and price > 0:
                        ref_price = ref_prices.get(m["raw_symbol"])
                        if ref_price and ref_price > 0:
                            change = ((price - ref_price) / ref_price) * 100
                            # Cap it to avoid crazy spikes if bad data
                            if abs(change) > 500:
                                change = 0.0

                    m["price"] = price
                    m["change"] = change
                    m["volume"] = f"{volume:.2f}"
                    matched_count += 1

                # Remove raw_symbol before caching
                # Note: We need to keep raw_symbol until the end of loop if we were debugging
                # but here we can just pop it when serializing or just leave it (it's internal)

            # Remove raw_symbol for cache compliance if needed, or just let it be extra data
            for m in markets_data:
                if "raw_symbol" in m:
                    del m["raw_symbol"]

            await cache.set("markets:revolut", markets_data, ttl=300)
            logger.info(
                f"Synced {len(markets_data)} symbols from Revolut ({matched_count} updated live)"
            )
        else:
            logger.warning("No EUR symbols found in Revolut instruments")
    except Exception as e:
        logger.error(f"Revolut sync failed: {e}")


async def main():
    cache = get_cache()
    await cache.connect()

    logger.info("Starting Market Sync Task...")
    while True:
        # Run syncs in parallel
        await asyncio.gather(sync_kraken(cache), sync_revolut(cache))
        # Sleep for a interval (e.g., 30 seconds)
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
