
import asyncio
import redis.asyncio as redis
import aiohttp
import msgpack
import time
import json
import logging

# Configuration
REDIS_URL = "redis://localhost:16379/0"
CLICKHOUSE_URL = "http://localhost:8123"
WS_URL = "ws://localhost:8003/api/v1/ws/ws"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_live_flow")

async def inject_market_data():
    """Injects a sequence of market ticks into Redis."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=False)
        stream_key = "market_events"
        base_price = 60000.0
        
        logger.info(f"Injecting 10 ticks into {stream_key}...")
        
        for i in range(10):
            # Create a localized spike to trigger a signal if logic allows
            price = base_price + (i * 10)
            if i >= 8:
                price = base_price * 1.05 # 5% spike
            
            tick = {
                "event_type": "trade", # Changed to trade to match price field
                "venue": "SIM",
                "symbol": "BTC/LIVE",
                "price": price,
                "size": 1.5,
                "side": "buy",
                "timestamp": time.time()
            }
            
            payload = msgpack.packb(tick, use_bin_type=True)
            await r.xadd(stream_key, {"data": payload})
            await asyncio.sleep(0.2)
            
        logger.info("✅ Injection complete.")
        await r.aclose()
        return True
    except Exception as e:
        logger.error(f"❌ Injection failed: {e}")
        return False

async def verify_websocket():
    """Connects to WebSocket and waits for a SIGNAL."""
    logger.info(f"Connecting to WebSocket: {WS_URL}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                logger.info("✅ WebSocket connected. Subscribing to signals...")
                await ws.send_json({"type": "subscribe", "channel": "signals"})
                
                logger.info("✅ Subscribed. Waiting for messages...")
                
                # Wait for up to 10 seconds
                start = time.time()
                while time.time() - start < 10:
                    try:
                        msg = await ws.receive(timeout=1.0)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            # Log what we get
                            # logger.info(f"Received WS Message: {data}")
                            
                            # Look for 'signal' type
                            if data.get("type") == "signal":
                                payload = data.get("data", {})
                                symbol = payload.get("symbol")
                                if symbol == "BTC/LIVE":
                                    logger.info(f"🔥 RECEIVED SIGNAL via WS: {payload.get('signal_type')} {symbol}")
                                    return True
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.error("❌ WebSocket closed unexpectedly.")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error("❌ WebSocket error.")
                            break
                    except asyncio.TimeoutError:
                        continue
                
                logger.warning("❌ Timeout waiting for SIGNAL via WS.")
                return False
    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")
        return False

async def main():
    logger.info("--- Starting Live Data Flow Verification ---")
    
    # 1. Start WebSocket Listener (Task)
    ws_task = asyncio.create_task(verify_websocket())
    
    # Give WS time to connect
    await asyncio.sleep(2)
    
    # 2. Inject Data
    injection_success = await inject_market_data()
    if not injection_success:
        logger.error("❌ Aborting due to injection failure.")
        return

    # 3. Wait for WS result
    ws_success = await ws_task
    
    # 4. Final Summary
    print("\n--- Summary ---")
    if ws_success:
        print("✅ LIVE DATA FLOW VERIFIED (Redis -> Orchestrator -> WebSocket)")
    else:
        print("❌ LIVE DATA FLOW FAILED (Check logs)")

if __name__ == "__main__":
    asyncio.run(main())
