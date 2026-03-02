
import hmac
import hashlib
import time
import requests
import os
from dotenv import load_dotenv

# Load .env to get the keys
load_dotenv()

# API credentials from .env
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

# BELANGRIJK: Gebruik api.bybit.eu voor EU accounts!
BASE_URL = "https://api.bybit.eu"

def generate_signature(timestamp, api_key, api_secret, recv_window, query_string=""):
    param_str = f"{timestamp}{api_key}{recv_window}{query_string}"
    signature = hmac.new(
        api_secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_bybit_eu():
    print("=" * 60)
    print("BYBIT EU API TEST SCRIPT (MANUAL)")
    print("=" * 60)
    
    if not API_KEY or not API_SECRET:
        print("❌ FOUT: Geen API_KEY of API_SECRET gevonden in .env")
        return

    print(f"API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
    print(f"Base URL: {BASE_URL}")
    print()

    # Genereer timestamp en signature
    timestamp = str(int(time.time() * 1000))
    recv_window = "5000"
    query_string = "accountType=UNIFIED"

    signature = generate_signature(timestamp, API_KEY, API_SECRET, recv_window, query_string)

    endpoint = f"{BASE_URL}/v5/account/wallet-balance?{query_string}"
    
    headers = {
        'X-BAPI-API-KEY': API_KEY,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-SIGN': signature,
        'X-BAPI-RECV-WINDOW': recv_window
    }

    try:
        print(f"Verbinding maken met {endpoint}...")
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        
        print("\nAPI Response:")
        print("-" * 60)
        import json
        print(json.dumps(data, indent=2))
        print("-" * 60)
        
        if data.get("retCode") == 0:
            print("\n✅ SUCCESS: Je API key werkt perfect op api.bybit.eu!")
        else:
            print(f"\n❌ FOUT: API weigert de verbinding (retCode: {data.get('retCode')})")
            print(f"Melding: {data.get('retMsg')}")
            
    except Exception as e:
        print(f"\n❌ CRASH: Fout tijdens het uitvoeren van de request: {e}")

if __name__ == "__main__":
    test_bybit_eu()
