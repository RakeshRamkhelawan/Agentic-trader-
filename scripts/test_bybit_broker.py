
import asyncio
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv

load_dotenv()

async def test_bybit_with_broker():
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key:
        print("No Bybit key in .env")
        return

    # Broker IDs often used by Gainium or similar
    # Common ones: 'Gainium', 'Gainium_Broker', or leaving it to CCXT if it knows
    broker_ids = [None, 'Gainium', 'Gainium_EU']
    hostnames = ['bybit.com', 'bytick.com']
    account_types = ['spot', 'linear']

    for hostname in hostnames:
        for b_id in broker_ids:
            for acc_type in account_types:
                print(f"\n>>> Testing Host={hostname}, Broker={b_id}, Type={acc_type}")
                try:
                    config = {
                        'apiKey': api_key,
                        'secret': api_secret,
                        'enableRateLimit': True,
                        'hostname': hostname,
                        'options': {'defaultType': acc_type}
                    }
                    
                    exchange = ccxt.bybit(config)
                    
                    if b_id:
                        # V5 uses X-Referer header for broker identification
                        exchange.headers = {
                            'X-Referer': b_id
                        }
                    
                    # Try a simple private call (fetch balance)
                    balance = await exchange.fetch_balance()
                    print(f"✅ SUCCESS! Balance found.")
                    await exchange.close()
                    return True
                except Exception as e:
                    print(f"❌ FAILED: {str(e)[:100]}")
                    if exchange:
                        await exchange.close()

    return False

if __name__ == "__main__":
    asyncio.run(test_bybit_with_broker())
