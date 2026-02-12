
import asyncio
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv

# Load .env
load_dotenv()

async def verify_bybit():
    print("\n--- Verifying Bybit Keys ---")
    api_key = os.getenv("BYBIT_API_KEY")
    secret = os.getenv("BYBIT_API_SECRET")
    testnet = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    
    if not api_key or not secret:
        print("❌ BYBIT_API_KEY or BYBIT_API_SECRET missing.")
        return

    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': secret,
            'options': {'defaultType': 'linear'},
        })
        if testnet:
            exchange.set_sandbox_mode(True)
            print("ℹ️  Using Testnet")
        else:
            print("ℹ️  Using LIVE Environment")

        # Test Private Endpoint (Balance)
        balance = await exchange.fetch_balance()
        print("✅ Authentication Successful!")
        print(f"   Wallet Balance: {balance['total']}")
        
        await exchange.close()
    except Exception as e:
        print(f"❌ Bybit Verification Failed: {e}")

async def verify_kraken():
    print("\n--- Verifying Kraken Keys ---")
    api_key = os.getenv("KRAKEN_API_KEY")
    secret = os.getenv("KRAKEN_API_SECRET")
    
    if not api_key or not secret:
        print("⚠️  KRAKEN_API_KEY or KRAKEN_API_SECRET missing.")
        return

    try:
        exchange = ccxt.kraken({
            'apiKey': api_key,
            'secret': secret,
        })
        # Kraken doesn't have a standard sandbox/testnet accessible via API key usually, 
        # but let's try fetch_balance.
        
        balance = await exchange.fetch_balance()
        print("✅ Authentication Successful!")
        print(f"   Wallet Balance: {balance['total']}")
        
        await exchange.close()
    except Exception as e:
        print(f"❌ Kraken Verification Failed: {e}")

async def main():
    await verify_bybit()
    await verify_kraken()

if __name__ == "__main__":
    asyncio.run(main())
