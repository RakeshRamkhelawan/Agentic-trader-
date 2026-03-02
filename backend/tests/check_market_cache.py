import asyncio

from backend.core.cache_layer import get_cache


async def check_cache():
    cache = get_cache()
    await cache.connect()

    print("--- REVOLUT CACHE ---")
    rev_markets = await cache.get("markets:revolut")
    if rev_markets:
        print(f"Total Revolut symbols: {len(rev_markets)}")
        non_zero = sum(1 for m in rev_markets if m.get("price", 0) > 0)
        print(f"Symbols with non-zero price: {non_zero}")
        if rev_markets:
            print(f"Sample: {rev_markets[0]}")
    else:
        print("Revolut cache EMPTY")

    print("\n--- KRAKEN CACHE ---")
    krk_markets = await cache.get("markets:kraken")
    if krk_markets:
        print(f"Total Kraken symbols: {len(krk_markets)}")
        non_zero = sum(1 for m in krk_markets if m.get("price", 0) > 0)
        print(f"Symbols with non-zero price: {non_zero}")
        if krk_markets:
            print(f"Sample: {krk_markets[0]}")
    else:
        print("Kraken cache EMPTY")


if __name__ == "__main__":
    asyncio.run(check_cache())
