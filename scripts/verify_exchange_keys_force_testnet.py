
import asyncio
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv

load_dotenv()

async def force_testnet_check():
    print("\n--- Checking Key against BYBIT TESTNET ---")
    api_key = os.getenv("BYBIT_API_KEY")
    secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key:
        print("No Key found.")
        return

    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': secret,
            'options': {'defaultType': 'linear'},
        })
        exchange.set_sandbox_mode(True) # FORCE TESTNET
        
        balance = await exchange.fetch_balance()
        print("✅ SUCCESS on TESTNET!")
        print(f"   Wallet Balance: {balance['total']}")
        
        await exchange.close()
    except Exception as e:
        print(f"❌ FAILED on TESTNET: {e}")

if __name__ == "__main__":
    asyncio.run(force_testnet_check())
