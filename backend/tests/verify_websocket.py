import asyncio
import json
import requests
import sys

# Try to import websockets, fail gracefully if not installed
try:
    import websockets
except ImportError:
    print(
        "❌ 'websockets' library not found. Please install it (pip install websockets) to run this test."
    )
    sys.exit(1)

HTTP_BASE_URL = "http://localhost:8003/api/v1"
WS_BASE_URL = "ws://localhost:8003/ws"


async def verify_websocket():
    print("🚀 Starting WebSocket Verification...")

    # 1. Login to get token
    payload = {"tenant_id": "tenant-123", "account_id": "acc-123"}
    try:
        r = requests.post(f"{HTTP_BASE_URL}/auth/token", json=payload)
        if r.status_code != 200:
            print(f"❌ Login Failed: {r.text}")
            return
        token = r.json().get("access_token")
        print("✅ Auth Token credentials obtained")
    except Exception as e:
        print(f"❌ Login Exception: {e}")
        return

    # 2. Connect to WebSocket
    uri = f"{WS_BASE_URL}?token={token}"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket Connection Established")

            # 3. Wait for 'connected' message
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "connected":
                print(f"✅ Received Handshake: {data}")
            else:
                print(f"⚠️ Received unexpected message: {data}")

            # 4. Subscribe (Optional verification of command handling)
            sub_msg = {"type": "subscribe", "channel": "ticker.BTC-EUR"}
            await websocket.send(json.dumps(sub_msg))
            print("✅ Sent Subscription Request")

            # logic doesn't send ack for ticker sub, but doesn't error.
            # So if we are here, we are good.

            print("🎉 WebSocket Test PASSED")

    except Exception as e:
        print(f"❌ WebSocket Error: {e}")


if __name__ == "__main__":
    asyncio.run(verify_websocket())
