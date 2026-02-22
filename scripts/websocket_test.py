#!/usr/bin/env python3
"""
WebSocket Test Script

Tests WebSocket connectivity with and without authentication.

Usage:
    python scripts/websocket_test.py
    python scripts/websocket_test.py --public
    python scripts/websocket_test.py --url ws://localhost:8000/ws
"""

import asyncio
import websockets
import json
import sys
import argparse


async def test_websocket(url: str, token: str = None):
    """Test WebSocket connection."""
    print(f"Connecting to: {url}")
    
    try:
        # Build URL with token if provided
        full_url = url
        if token:
            full_url = f"{url}?token={token}"
        
        async with websockets.connect(full_url) as websocket:
            print("[PASS] Connected successfully")
            
            # Wait for connection confirmation
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"[INFO] Server response: {data.get('type', 'unknown')}")
                
                if data.get('type') == 'connected':
                    print(f"[INFO] Connection ID: {data.get('connection_id', 'N/A')[:8]}...")
                
                # Subscribe to a channel
                subscribe_msg = {
                    "type": "subscribe",
                    "channel": "ticker.BTC-EUR"
                }
                await websocket.send(json.dumps(subscribe_msg))
                print("[INFO] Subscribed to ticker.BTC-EUR")
                
                # Wait for messages
                print("[INFO] Waiting for messages (5 seconds)...")
                for _ in range(5):
                    try:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(msg)
                        print(f"[DATA] {data.get('type', 'message')}: {data.get('channel', '')}")
                    except asyncio.TimeoutError:
                        print("[INFO] No message received (timeout)")
                        
                # Unsubscribe
                unsubscribe_msg = {
                    "type": "unsubscribe",
                    "channel": "ticker.BTC-EUR"
                }
                await websocket.send(json.dumps(unsubscribe_msg))
                print("[INFO] Unsubscribed")
                
                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                pong = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"[INFO] Ping/Pong: {pong}")
                
            except asyncio.TimeoutError:
                print("[WARN] Timeout waiting for server message")
            
            print("[PASS] WebSocket test completed successfully")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[FAIL] Connection failed with status {e.status_code}")
        if e.status_code == 403:
            print("       Authentication required or CORS issue")
        return False
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test WebSocket connectivity")
    parser.add_argument("--url", default="ws://localhost:8000/ws", help="WebSocket URL")
    parser.add_argument("--public", action="store_true", help="Use public endpoint")
    parser.add_argument("--token", help="JWT token for authentication")
    
    args = parser.parse_args()
    
    # Use public endpoint if requested
    url = args.url
    if args.public:
        url = url.replace("/ws", "/ws/public")
        print("Using public endpoint (no auth required)")
    
    print("=" * 60)
    print("WebSocket Connection Test")
    print("=" * 60)
    print()
    
    try:
        success = asyncio.run(test_websocket(url, args.token))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[WARN] Test interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
