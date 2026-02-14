import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.config.settings import settings
from backend.execution.exchange_adapter import ExchangeAdapter


async def t():
    print(f"Testing BTC-EUR with key: {settings.REVOLUT_API_KEY[:5]}...")
    if not settings.REVOLUT_API_KEY:
        print("No API Key found!")
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

    try:
        # Try BTC-EUR
        print("Requesting tickers?symbols=BTC-EUR")
        res = await adapter._request(
            "GET", "/api/1.0/tickers", params={"symbols": "BTC-EUR"}
        )
        print(f"Result for BTC-EUR: {res}")
    except Exception as e:
        print(f"Error for BTC-EUR: {e}")

    try:
        # Try BTCEUR just in case
        print("Requesting tickers?symbols=BTCEUR")
        res = await adapter._request(
            "GET", "/api/1.0/tickers", params={"symbols": "BTCEUR"}
        )
        print(f"Result for BTCEUR: {res}")
    except Exception as e:
        print(f"Error for BTCEUR: {e}")


if __name__ == "__main__":
    asyncio.run(t())
