import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.config.settings import settings
from backend.execution.exchange_adapter import ExchangeAdapter


async def test_formats():
    print("Testing Revolut Ticker Formats...")

    if not (settings.REVOLUT_API_KEY and settings.REVOLUT_PRIVATE_KEY):
        print("Error: Revolut credentials missing in settings.")
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

    formats = ["BTC/EUR", "BTC-EUR", "BTCEUR"]

    for fmt in formats:
        print(f"\nTesting format: {fmt}")
        try:
            # We use _request directly to bypass any logic in get_ticker/get_tickers
            response = await adapter._request("GET", "/api/1.0/tickers", params={"symbols": fmt})
            print(f"Success! Response: {response}")
        except Exception as e:
            print(f"Failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_formats())
