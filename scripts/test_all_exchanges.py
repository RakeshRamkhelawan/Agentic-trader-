#!/usr/bin/env python3
"""
Test all exchange connections (Bitvavo & Revolut X)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_bitvavo():
    """Test Bitvavo connection."""
    from backend.execution.bitvavo_adapter import create_bitvavo_adapter
    
    print("="*70)
    print("TESTING BITVAVO CONNECTION")
    print("="*70)
    
    adapter = await create_bitvavo_adapter()
    if not adapter:
        print("[FAIL] Could not initialize Bitvavo")
        return False
    
    try:
        # Test balance
        balance = await adapter.fetch_balance()
        if balance:
            eur = balance.get('EUR', {}).get('total', 0)
            print(f"[OK] Balance fetched: EUR {eur:.2f}")
        
        # Test ticker
        ticker = await adapter.fetch_ticker("BTC/EUR")
        if ticker:
            print(f"[OK] BTC/EUR Price: EUR {ticker.get('last', 0):,.2f}")
        
        # Count pairs
        pairs = adapter.get_eur_pairs()
        print(f"[OK] Available EUR pairs: {len(pairs)}")
        
        print("[SUCCESS] Bitvavo connection OK")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    finally:
        await adapter.close()


async def test_revolut():
    """Test Revolut X connection."""
    import os
    from dotenv import load_dotenv
    from backend.execution.exchange_adapter import ExchangeAdapter
    
    load_dotenv(Path(__file__).parent.parent / ".env")
    
    print()
    print("="*70)
    print("TESTING REVOLUT X CONNECTION")
    print("="*70)
    
    api_key = os.getenv("REVOLUT_API_KEY")
    key_path = os.getenv("REVOLUT_PRIVATE_KEY_PATH")
    sandbox = os.getenv("REVOLUT_SANDBOX", "false").lower() == "true"
    
    if not api_key:
        print("[SKIP] REVOLUT_API_KEY not configured")
        return None
    
    if not Path(key_path).exists():
        print(f"[FAIL] Private key not found: {key_path}")
        return False
    
    try:
        with open(key_path, 'r') as f:
            private_key = f.read()
        
        base_url = "https://sandbox-revx.revolut.com" if sandbox else "https://revx.revolut.com"
        mode = "SANDBOX" if sandbox else "LIVE"
        
        print(f"Connecting to Revolut X ({mode})...")
        
        adapter = ExchangeAdapter(
            api_key=api_key,
            private_key_pem=private_key,
            base_url=base_url
        )
        
        # Test connection
        currencies = await adapter._request("GET", "/api/1.0/configuration/currencies")
        print(f"[OK] Connection successful")
        print(f"[OK] Available currencies: {len(currencies)}")
        
        print("[SUCCESS] Revolut X connection OK")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def main():
    print()
    print("="*70)
    print("EXCHANGE CONNECTION TEST SUITE")
    print("="*70)
    print()
    
    results = {}
    
    # Test Bitvavo
    results['bitvavo'] = await test_bitvavo()
    
    # Test Revolut
    results['revolut'] = await test_revolut()
    
    # Summary
    print()
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, result in results.items():
        if result is True:
            status = "OK"
        elif result is False:
            status = "FAILED"
        else:
            status = "NOT CONFIGURED"
        print(f"  {name:12} : {status}")
    
    print("="*70)
    
    # Return 0 if at least one works
    if any(r is True for r in results.values()):
        print("[READY] At least one exchange is configured correctly")
        return 0
    else:
        print("[WARNING] No exchanges configured - check your .env file")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
