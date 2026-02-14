import os
import asyncio
import httpx
import ccxt
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import sys

# Load .env
load_dotenv()

# Add project root to path for backend imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


async def test_deepseek():
    print("\n--- Testing DeepSeek LLM ---")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key or "your_" in api_key:
        print("❌ Skip: DeepSeek API Key not set properly.")
        return False

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'DeepSeek Connection OK'"}],
            max_tokens=10,
        )
        content = response.choices[0].message.content.strip()
        print(f"✅ DeepSeek Response: {content}")
        return True
    except Exception as e:
        print(f"❌ DeepSeek Error: {e}")
        return False


async def test_bybit():
    print("\n--- Testing Bybit (CCXT) ---")
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    use_eu = os.getenv("BYBIT_USE_EU", "false").lower() == "true"

    if not api_key or not api_secret:
        print("❌ Skip: Bybit credentials not set.")
        return False

    try:
        # If EU is enabled, use bybit.eu for better compatibility with V5
        hostname = "bybit.eu" if use_eu else "bybit.com"
        print(f"Using hostname: {hostname}")

        exchange = ccxt.bybit(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "hostname": hostname,
            }
        )
        exchange.set_sandbox_mode(testnet)

        # Test fetching balance
        balance = exchange.fetch_balance()
        print(
            f"✅ Bybit Connection OK. Total wallet balance keys: {len(balance['total'])}"
        )
        return True
    except Exception as e:
        print(f"❌ Bybit Error: {e}")
        return False


async def test_kraken():
    print("\n--- Testing Kraken (CCXT) ---")
    # Support both casings found in .env
    api_key = os.getenv("KRAKEN_API_KEY") or os.getenv("KRaken_API_KEY")
    api_secret = os.getenv("KRAKEN_API_SECRET") or os.getenv("KRaken_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Skip: Kraken credentials not set.")
        return False

    try:
        exchange = ccxt.kraken(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
            }
        )

        # Test fetching balance
        balance = exchange.fetch_balance()
        print(
            f"✅ Kraken Connection OK. Total wallet balance keys: {len(balance['total'])}"
        )
        return True
    except Exception as e:
        print(f"❌ Kraken Error: {e}")
        return False


async def test_revolut():
    print("\n--- Testing Revolut X ---")
    api_key = os.getenv("REVOLUT_API_KEY")
    private_key_path = os.getenv("REVOLUT_PRIVATE_KEY_PATH")

    if not api_key or not private_key_path:
        print("❌ Skip: Revolut credentials not set.")
        return False

    # Check if private key exists
    if not os.path.exists(private_key_path.strip('"').strip("'")):
        print(f"❌ Revolut Error: Private key file not found at {private_key_path}")
        return False

    try:
        # Simple health check or configuration fetch
        from backend.execution.exchange_adapter import ExchangeAdapter

        # Read the private key file
        pem_path = private_key_path.strip('"').strip("'")
        with open(pem_path, "r") as f:
            private_key_pem = f.read()

        adapter = ExchangeAdapter(
            api_key=api_key.strip('"').strip("'"),
            private_key_pem=private_key_pem,
            base_url="https://revx.revolut.com",
        )

        currencies = await adapter._request("GET", "/api/1.0/configuration/currencies")
        print(f"✅ Revolut X Connection OK. Currencies found: {len(currencies)}")
        await adapter.client.aclose()
        return True
    except Exception as e:
        print(f"❌ Revolut Error: {e}")
        return False


async def main():
    print("🚀 Starting Unified Provider Verification...")

    # Run tests
    results = await asyncio.gather(
        test_deepseek(),
        test_bybit(),
        test_kraken(),
        test_revolut(),
        return_exceptions=True,
    )

    print("\n" + "=" * 40)
    print("Final Verification Summary:")
    names = ["DeepSeek", "Bybit", "Kraken", "Revolut"]
    for name, res in zip(names, results):
        status = (
            "PASSED" if res is True else "FAILED" if res is False else f"ERROR: {res}"
        )
        print(f"{name:10}: {status}")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
