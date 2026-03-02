
import hmac
import hashlib
import time
import requests
import os
import socket
from dotenv import load_dotenv

# Load .env
load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BASE_URL = "https://api.bybit.eu"

# Force IPv4 helper
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(*args, **kwargs):
    responses = orig_getaddrinfo(*args, **kwargs)
    return [res for res in responses if res[0] == socket.AF_INET]

socket.getaddrinfo = getaddrinfo_ipv4

def generate_signature(timestamp, api_key, api_secret, recv_window, query_string=""):
    param_str = f"{timestamp}{api_key}{recv_window}{query_string}"
    signature = hmac.new(
        api_secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_bybit_ipv4_forced():
    print("=" * 60)
    print("BYBIT IPv4 FORCED TEST")
    print("=" * 60)

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
        print("Connecting via FORCED IPv4...")
        response = requests.get(endpoint, headers=headers, timeout=10)
        data = response.json()
        print(f"Response retCode: {data.get('retCode')}")
        print(f"Response retMsg: {data.get('retMsg')}")

        if data.get("retCode") == 0:
            print("\n✅ SUCCESS: Connection works when forcing IPv4!")
        else:
            print(f"\n❌ FAILED: Still getting {data.get('retCode')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bybit_ipv4_forced()
