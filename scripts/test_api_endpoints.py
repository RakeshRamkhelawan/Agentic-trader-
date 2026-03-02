#!/usr/bin/env python3
"""
API Endpoint Test Suite

Tests all FastAPI endpoints and WebSocket connections.

Usage:
    python scripts/test_api_endpoints.py
    python scripts/test_api_endpoints.py --verbose
"""

import asyncio
import aiohttp
import sys
from datetime import datetime

API_BASE = "http://localhost:8000"


async def test_health():
    """Test health endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/api/v1/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"  Status: {data.get('status')}")
                print(f"  Version: {data.get('version')}")
                return True
            return False


async def test_markets():
    """Test markets endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/api/v1/trading/markets") as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list):
                    print(f"  Assets: {len(data)}")
                    if len(data) > 0:
                        print(f"  First asset: {data[0].get('symbol', 'N/A')}")
                    return True
            return False


async def test_agents():
    """Test agents status endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/api/v1/agents/status") as resp:
            if resp.status == 200:
                data = await resp.json()
                agents = data.get('agents', {})
                print(f"  Agents: {len(agents)}")
                for name, info in list(agents.items())[:3]:
                    print(f"    - {name}: {info.get('type', 'unknown')}")
                return True
            return False


async def test_navagraha():
    """Test navagraha state endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/api/v1/navagraha/current-state") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"  Dasha: {data.get('current_dasha', 'N/A')}")
                print(f"  Trading Gate: {'Open' if data.get('trading_gate_open') else 'Closed'}")
                return True
            return False


async def test_ooda():
    """Test OODA cycle endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/api/v1/ooda/current-cycle") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"  Phase: {data.get('phase', 'N/A')}")
                print(f"  Coherence: {data.get('coherence', 0):.2f}")
                return True
            return False


async def test_websocket():
    """Test WebSocket connection."""
    import aiohttp
    
    try:
        session = aiohttp.ClientSession()
        ws = await session.ws_connect(f"{API_BASE.replace('http', 'ws')}/ws")
        
        # Subscribe to ticker
        await ws.send_json({"type": "subscribe", "channel": "ticker.BTC-EUR"})
        
        # Wait for response
        msg = await asyncio.wait_for(ws.receive(), timeout=5)
        
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = msg.json()
            print(f"  Connected: {data.get('type')}")
            print(f"  Connection ID: {data.get('connection_id', 'N/A')[:8]}...")
        
        await ws.close()
        await session.close()
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


async def run_tests():
    """Run all API tests."""
    print("=" * 60)
    print("API ENDPOINT TEST SUITE")
    print("=" * 60)
    print(f"Base URL: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Health Check", test_health),
        ("Markets", test_markets),
        ("Agents", test_agents),
        ("Navagraha", test_navagraha),
        ("OODA Cycle", test_ooda),
        ("WebSocket", test_websocket),
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"[TEST] {name}")
        try:
            result = await asyncio.wait_for(test_func(), timeout=10)
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status}")
            results.append((name, result))
        except Exception as e:
            print(f"  [FAIL] {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print()
    print(f"Passed: {passed}/{len(results)}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
