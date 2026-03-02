
import asyncio
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv

load_dotenv()

async def check_bybit_endpoints():
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key:
        print("No Bybit key in .env")
        return

    # Variants to test
    variants = [
        {"name": "Default (bybit.com)", "hostname": "bybit.com"},
        {"name": "EU (bytick.com)", "hostname": "bytick.com"},
    ]

    for v in variants:
        print(f"\n--- Testing {v['name']} ---")
        try:
            exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'hostname': v['hostname']
            })
            balance = await exchange.fetch_balance()
            print(f"✅ SUCCESS on {v['name']}!")
            await exchange.close()
            return True
        except Exception as e:
            print(f"❌ FAILED on {v['name']}: {e}")

    return False

if __name__ == "__main__":
    asyncio.run(check_bybit_endpoints())
