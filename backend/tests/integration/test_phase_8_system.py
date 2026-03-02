import asyncio
import logging
import os
import time
import traceback

import aiohttp
import pytest
import redis.asyncio as redis

# Configuration
# Run against local docker stack
WS_URL = os.getenv("WS_URL", "ws://localhost:8003/api/v1/ws/ws")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_phase_8_system")


@pytest.mark.asyncio
async def test_live_data_flow_e2e():
    """
    Verifies the entire Phase 8 End-to-End flow in a live environment.

    Flow:
    1. Connect to WebSocket & Subscribe to 'signals'.
    2. Inject Market Data (Series of ticks with a spike) into Redis.
    3. Listener (Orchestrator) -> ResearchAgent -> Signal -> Orchestrator -> RiskGuardian -> SignalBridge -> Redis -> API -> WebSocket.
    4. Client receives 'signal' (ORDER_VALIDATION_RESULT) via WebSocket.
    """

    logger.info("--- Starting System Integration Test (Phase 8) ---")

    # 1. Connect to WebSocket
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                logger.info("✅ WebSocket connected. Subscribing to signals...")
                await ws.send_json({"type": "subscribe", "channel": "signals"})

                # Consume validation response (if any) or just wait a bit
                # Wait for subscription confirmation? (Not implemented in backend, implied)
                logger.info("Waiting 1s for subscription...")
                await asyncio.sleep(1)

                # 2. Inject Market Data
                logger.info("Injecting market data spike...")
                await inject_market_data()
                logger.info("✅ Injection complete.")

                # 3. Wait for Signal
                logger.info("Waiting for SIGNAL via WS...")

                signal_received = False
                start_time = time.time()
                timeout = 15.0

                while time.time() - start_time < timeout:
                    try:
                        # Use receive_json with timeout
                        msg = await asyncio.wait_for(ws.receive_json(), timeout=1.0)

                        logger.info("Received WS Message: %s", msg)

                        # Validate Message Structure
                        # Expected: {"type": "signal", "channel": "signals", "data": {...}}
                        if msg.get("type") == "signal":
                            data = msg.get("data", {})
                            symbol = data.get("symbol")

                            # Check if it's our injected symbol
                            # Logic: verify_live_flow used BTC/LIVE
                            if symbol == "BTC/LIVE":
                                logger.info("✅ RECEIVED SIGNAL for BTC/LIVE!")

                                # Optional: Check confidence/side if available
                                # data keys: signal_id, agent_id, signal_type, confidence...
                                assert (
                                    data.get("agent_id") == "risk_guardian_v1"
                                )  # Or orchestrator proxy?
                                # Wait, SignalBridge uses agent_id from message.
                                # RiskGuardian returns ORDER_VALIDATION_RESULT.
                                # SignalBridge.emit_from_agent_message uses that.
                                # Let's just assert we got a signal for the symbol.

                                signal_received = True
                                break

                    except asyncio.TimeoutError:
                        continue  # loop check time
                    except Exception as e:
                        logger.error("Error receiving WS: %s", e)
                        break

                assert signal_received, "❌ Timed out waiting for SIGNAL via WebSocket."
                logger.info("✅ TEST PASSED: Full E2E Loop Verified.")

    except aiohttp.ClientError as e:
        pytest.fail(f"Could not connect to WebSocket: {e}")
    except Exception as e:
        pytest.fail(f"Test failed with error: {e}\n{traceback.format_exc()}")


async def inject_market_data():
    """Injects a price spike to trigger ResearchAgent."""
    r = redis.from_url(REDIS_URL, decode_responses=False)
    stream_key = "market_events"

    base_price = 60000.0
    symbol = "BTC/LIVE"

    import msgpack

    for i in range(10):
        price = base_price + (i * 10)
        # Spike at index 8
        if i >= 8:
            price = base_price * 1.05  # 5% jump (triggers >2% threshold)

        event = {
            "event_type": "trade",
            "symbol": symbol,
            "price": price,
            "volume": 0.5,
            "venue": "SIM",
            "timestamp": time.time(),
        }

        # Redis Stream Add
        await r.xadd(stream_key, {"data": msgpack.packb(event)})
        await asyncio.sleep(0.1)

    await r.aclose()


if __name__ == "__main__":
    # Allow running directly
    asyncio.run(test_live_data_flow_e2e())
