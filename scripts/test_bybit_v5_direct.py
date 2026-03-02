#!/usr/bin/env python3
"""
Direct Bybit V5 API test (zonder CCXT)
Test verschillende endpoints voor verschillende regio's
"""

import os
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_signature(timestamp: str, api_key: str, recv_window: str, query_string: str, secret: str) -> str:
    """
    Generate HMAC SHA256 signature for Bybit V5 API
    Format: timestamp + api_key + recv_window + query_string
    """
    param_str = f"{timestamp}{api_key}{recv_window}{query_string}"
    return hmac.new(
        secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def test_bybit_endpoint(base_url: str, api_key: str, api_secret: str, region_name: str):
    """Test een specifiek Bybit endpoint"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {region_name}")
    print(f"   Endpoint: {base_url}")
    print(f"{'='*60}")
    
    # V5 API authentication parameters
    timestamp = str(int(time.time() * 1000))
    recv_window = "5000"
    
    # Test 1: Get server time (public endpoint, no auth)
    try:
        print("\n📡 Test 1: Server Time (public endpoint)...")
        response = requests.get(f"{base_url}/v5/market/time", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server Time OK: {data}")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Get Wallet Balance (authenticated endpoint)
    try:
        print("\n🔐 Test 2: Wallet Balance (authenticated)...")
        
        # Build query string
        account_type = "UNIFIED"  # or "CONTRACT" for classic account
        query_string = f"accountType={account_type}"
        
        # Generate signature
        signature = generate_signature(timestamp, api_key, recv_window, query_string, api_secret)
        
        # Headers voor Bybit V5
        headers = {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-SIGN": signature,
            "X-BAPI-RECV-WINDOW": recv_window,
        }
        
        url = f"{base_url}/v5/account/wallet-balance?{query_string}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("retCode") == 0:
                print(f"   ✅ Wallet Balance OK!")
                print(f"   Result: {data.get('result', {})}")
                return True
            else:
                print(f"   ❌ API Error: {data.get('retCode')} - {data.get('retMsg')}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def main():
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    
    if not api_key or not api_secret:
        print("❌ BYBIT_API_KEY en BYBIT_API_SECRET moeten ingesteld zijn in .env")
        return
    
    print("🚀 Bybit V5 API Direct Test")
    print(f"   Testnet Mode: {testnet}")
    print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
    
    if testnet:
        endpoints = [
            ("https://api-testnet.bybit.com", "Testnet"),
        ]
    else:
        # Test verschillende mainnet endpoints
        endpoints = [
            ("https://api.bybit.nl", "Netherlands Mainnet"),
            ("https://api.bybit.com", "Global Mainnet"),
            ("https://api.bybit.eu", "EU Mainnet (beperkt)"),
        ]
    
    results = {}
    for base_url, region in endpoints:
        success = test_bybit_endpoint(base_url, api_key, api_secret, region)
        results[region] = success
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    for region, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {status} - {region}")
    
    # Recommendations
    print(f"\n{'='*60}")
    print("💡 AANBEVELINGEN")
    print(f"{'='*60}")
    
    if not any(results.values()):
        print("""
❌ Geen enkel endpoint werkt!

Mogelijke oorzaken:
1. API Keys zijn voor TESTNET maar je test MAINNET (of andersom)
2. API Keys hebben verkeerde permissies (zet "Contract" en "Wallet" aan)
3. IP adres is geblokkeerd (VS/China IP's worden geweigerd)
4. API Keys zijn verlopen of gerevoked

OPLOSSING:
• Ga naar https://www.bybit.com/app/user/api-management
• Maak NIEUWE API keys met:
  - Type: System-generated (HMAC)
  - Permissions: Account Transfer, Contract Trade, Spot Trade, Wallet
  - IP Restriction: "Unrestricted" (voor testing)
• Update je .env file
        """)
    elif results.get("Netherlands Mainnet"):
        print("""
✅ api.bybit.nl werkt het beste voor Nederlandse gebruikers!

Update je configuratie om dit endpoint te gebruiken.
        """)
    elif results.get("Global Mainnet"):
        print("""
✅ api.bybit.com werkt!

Dit is het standaard global endpoint.
        """)

if __name__ == "__main__":
    main()
