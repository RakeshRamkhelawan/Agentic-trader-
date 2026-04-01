import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.core.config.settings import settings
from backend.execution.exchange_adapter import ExchangeAdapter


async def dump_revolut():
    print(
        f"Checking Revolut credentials... API_KEY: {'set' if settings.REVOLUT_API_KEY else 'MISSING'}"
    )
    if not settings.REVOLUT_API_KEY:
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
        print("Fetching /api/1.0/configuration/pairs ...")
        # Direct request to see RAW data
        raw_data = await adapter._request("GET", "/api/1.0/configuration/pairs")
        print("Raw Data Sample (first 500 chars):")
        print(json.dumps(raw_data, indent=2)[:500])

        if isinstance(raw_data, list):
            print(f"Data is a LIST of {len(raw_data)} items")
            if len(raw_data) > 0:
                print(f"First item type: {type(raw_data[0])}")
                print(f"First item: {raw_data[0]}")
        elif isinstance(raw_data, dict):
            print(f"Data is a DICT with keys: {raw_data.keys()}")

    except Exception as e:
        print(f"Failed to dump Revolut data: {e}")


if __name__ == "__main__":
    asyncio.run(dump_revolut())
