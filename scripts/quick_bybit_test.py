#!/usr/bin/env python3
"""Quick Bybit key test"""
import os
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")
testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

print(f"🔑 API Key: {api_key}")
print(f"🧪 Testnet: {testnet}")

base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"

# Test 1: Public endpoint
print(f"\n📡 Testing {base_url}...")
try:
    resp = requests.get(f"{base_url}/v5/market/time", timeout=10)
    if resp.status_code == 200:
        print(f"✅ Server reachable: {resp.json()}")
    else:
        print(f"❌ Failed: {resp.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Auth endpoint
print(f"\n🔐 Testing authentication...")
timestamp = str(int(time.time() * 1000))
recv_window = "5000"
query_string = "accountType=UNIFIED"

param_str = f"{timestamp}{api_key}{recv_window}{query_string}"
signature = hmac.new(
    api_secret.encode('utf-8'),
    param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

headers = {
    "X-BAPI-API-KEY": api_key,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-SIGN": signature,
    "X-BAPI-RECV-WINDOW": recv_window,
}

try:
    url = f"{base_url}/v5/account/wallet-balance?{query_string}"
    resp = requests.get(url, headers=headers, timeout=10)
    data = resp.json()
    
    if data.get("retCode") == 0:
        print(f"✅ BYBIT WERKT! Balance gevonden!")
        print(f"   Result: {data.get('result')}")
    else:
        print(f"❌ Error: {data.get('retCode')} - {data.get('retMsg')}")
except Exception as e:
    print(f"❌ Exception: {e}")
