
import asyncio
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv

load_dotenv()

async def check_bybit_variants():
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key:
        print("No Bybit key in .env")
        return

    configs = [
        {"name": "Bybit LIVE", "testnet": False},
        {"name": "Bybit TESTNET", "testnet": True}
    ]

    for config in configs:
        print(f"\n--- Testing {config['name']} ---")
        try:
            exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
            exchange.set_sandbox_mode(config['testnet'])
            balance = await exchange.fetch_balance()
            print(f"✅ SUCCESS on {config['name']}!")
            await exchange.close()
            return True
        except Exception as e:
            print(f"❌ FAILED on {config['name']}: {e}")

    return False

if __name__ == "__main__":
    asyncio.run(check_bybit_variants())
