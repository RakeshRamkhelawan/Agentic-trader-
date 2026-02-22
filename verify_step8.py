#!/usr/bin/env python3
"""STAP 8: Frontend End-to-End Test"""

import asyncio
import aiohttp
import json

API_URL = "http://localhost:8003"
WS_URL = "ws://localhost:8003"

print('='*60)
print('STAP 8: Frontend End-to-End Verificatie')
print('='*60)

async def test_health():
    """Test 1: Health endpoint"""
    print('\n1. HEALTH ENDPOINT:')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/health", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f'   [OK] Health check: {data}')
                    return True
                else:
                    print(f'   [FAIL] Status: {resp.status}')
                    return False
    except Exception as e:
        print(f'   [FAIL] Error: {e}')
        return False

async def test_paper_trading_status():
    """Test 2: Paper Trading Status"""
    print('\n2. PAPER TRADING STATUS:')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/v1/paper-trading/status", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f'   [OK] Status: {json.dumps(data, indent=2)}')
                    return data
                else:
                    text = await resp.text()
                    print(f'   [FAIL] Status: {resp.status}, Response: {text}')
                    return None
    except Exception as e:
        print(f'   [FAIL] Error: {e}')
        return None

async def test_websocket():
    """Test 3: WebSocket Connection"""
    print('\n3. WEBSOCKET VERBINDING:')
    try:
        import aiohttp
        session = aiohttp.ClientSession()
        ws = await session.ws_connect(f"{WS_URL}/ws/paper-trading")
        
        # Wait for connected message
        msg = await ws.receive()
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            if data.get('type') == 'connected':
                print(f'   [OK] WebSocket connected: {data}')
                await ws.close()
                await session.close()
                return True
        
        await ws.close()
        await session.close()
        return False
    except Exception as e:
        print(f'   [FAIL] Error: {e}')
        return False

async def test_vedic_status():
    """Test 4: Vedic Status Endpoint"""
    print('\n4. VEDIC STATUS ENDPOINT:')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/v1/paper-trading/vedic-status", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f'   [OK] Vedic status: {json.dumps(data, indent=2)}')
                    return True
                else:
                    print(f'   [INFO] Status: {resp.status} - Endpoint mogelijk niet geimplementeerd')
                    return False
    except Exception as e:
        print(f'   [INFO] Error: {e}')
        return False

async def main():
    results = []
    
    results.append(('Health', await test_health()))
    status_data = await test_paper_trading_status()
    results.append(('Status', status_data is not None))
    results.append(('WebSocket', await test_websocket()))
    results.append(('Vedic Status', await test_vedic_status()))
    
    print('\n' + '='*60)
    print('STAP 8 RESULTAAT:')
    all_ok = all(r[1] for r in results)
    for name, ok in results:
        status = 'OK' if ok else 'FAIL'
        print(f'   [{status}] {name}')
    
    if all_ok:
        print('\nSTAP 8: SUCCESSVOL')
    else:
        print('\nSTAP 8: GEDEELTELIJK SUCCESSVOL')
    print('='*60)
    
    return all_ok

if __name__ == "__main__":
    asyncio.run(main())
