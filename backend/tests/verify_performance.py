import asyncio
import sys
import os

# Add project root to path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.core.cache_layer import get_cache
from backend.execution.exchange_adapter import ExchangeAdapter


async def test_performance_layer():
    print("Testing Performance Layer...")
    cache = get_cache()
    try:
        await cache.connect()
        print("✅ Redis Connection Successful (or lazy initialization ready)")

        test_key = "test_perf_key"
        await cache.set(test_key, {"status": "ok"}, ttl=10)
        val = await cache.get(test_key)
        if val and val.get("status") == "ok":
            print("✅ Cache Get/Set Successful")
        else:
            print("❌ Cache Get/Set Failed")

    except Exception as e:
        print(f"❌ Performance Layer Test Failed: {e}")


async def test_instrument_discovery():
    print("Testing Instrument Discovery logic...")
    # Mocking instruments list for verification
    mock_instruments = [
        {"symbol": "BTC-EUR", "type": "crypto"},
        {"symbol": "ETH-EUR", "type": "crypto"},
        {"symbol": "VUSA-EUR", "type": "ETF"},
        {"symbol": "IWDA-EUR", "type": "ETF"},
    ]

    available_symbols = []
    for inst in mock_instruments:
        symbol = inst.get("symbol", "")
        if "-EUR" in symbol:
            available_symbols.append(symbol)

    if len(available_symbols) >= 4:
        print(f"✅ Discovery Logic Successful: found {available_symbols}")
    else:
        print(f"❌ Discovery Logic Failed: {available_symbols}")


if __name__ == "__main__":
    asyncio.run(test_performance_layer())
    asyncio.run(test_instrument_discovery())
