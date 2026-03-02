import asyncio
import os

import msgpack
import redis.asyncio as redis
from dotenv import load_dotenv

from backend.core.config.settings import settings

load_dotenv()


async def test_e2e_market_data_flow():
    """
    E2E Test:
    1. Inject Market Tick into Redis Stream (market_events).
    2. Verify Trading Engine logs reception (Manual Check via docker logs) OR check if it triggers downstream.

    Since we don't have an easy way to spy on docker logs programmatically here without docker-py,
    we will just inject and report success of injection.
    The USER/Assistant must verify logs.
    """
    print(f"Connecting to Redis at {settings.REDIS_URL} (Override to 16379 for Host Test)")
    # Force 16379 for this test running on Host
    r = redis.from_url("redis://localhost:16379/0", decode_responses=False)

    # Inject 10 ticks to build history and trigger signal
    base_price = 50000.0
    stream_key = "market_events"

    print(f"Injecting 10 ticks to {stream_key} to trigger MVP Signal...")

    for i in range(10):
        # Spike price at the end to trigger BULLISH signal (>2%)
        current_price = base_price + (i * 10)
        if i >= 8:
            current_price = base_price * 1.05  # +5% spike

        tick = {
            "event_type": "ticker",
            "symbol": "BTC/E2E",
            "price": current_price,
            "last": current_price,
            "volume": 1.0,
            "timestamp": 1234567890 + i,
        }

        payload = msgpack.packb(tick, use_bin_type=True)
        await r.xadd(stream_key, {"data": payload})
        print(f"Injected tick {i+1}/10: {current_price}")
        await asyncio.sleep(0.1)

    print("✅ 10 Ticks Injected.")
    print("Waiting for SIGNAL in Redis stream...")

    # Read from stream to find the SIGNAL
    # We might need to listen for new messages ID > last_injected_id ?
    # Or just read typically.
    # We'll read from "$" (now) but since we injected, they are already there?
    # No, signal comes AFTER injection is processed by algo.

    # Let's read indefinitely for 5 seconds
    try:
        start_time = asyncio.get_event_loop().time()
        found_signal = False
        last_read_id = (
            "$"  # Start reading new messages (or should we read from 0-0 if we missed it?)
        )
        # Actually, if Orchestrator is fast, it might have published already.
        # Let's read from the beginning of time just in case, or a known ID.
        # Better: create a consumer group? Too complex for script.
        # Let's just read from "0-0" and filter for SIGNAL type appearing AFTER our timestamp?
        # Or just read from "$" BEFORE we start injection?
        # Too late for that.
        # But we injected ticks. The signal comes later.

        # Reset read ID to 0-0 to scan everything? Or just wait?
        # If we run this script, the orchestrator is running separately.
        # Orchestrator processes ticks.
        # We can just use "0-0" and look for "event_type": "SIGNAL".

        while asyncio.get_event_loop().time() - start_time < 10:
            streams = await r.xread({stream_key: last_read_id}, count=100, block=1000)
            if not streams:
                continue

            for stream_name, messages in streams:
                for message_id, data in messages:
                    last_read_id = message_id
                    payload = data.get(b"data") or data.get("data")
                    if payload:
                        try:
                            # Try to decode
                            event = msgpack.unpackb(payload, raw=False)
                            # Check event type
                            # SignalBridge wraps it in { "event_type": "SIGNAL", ... }
                            if event.get("event_type") == "SIGNAL":
                                print("🔥 FOUND SIGNAL IN REDIS STREAM! 🔥")
                                print(f"  Signal Data: {event.get('data')}")
                                found_signal = True
                                break
                        except Exception as e:
                            pass  # Ignore decode errors
            if found_signal:
                break

        if found_signal:
            print("✅ E2E TEST PASSED: Signal generated and published to Redis.")
        else:
            print("❌ E2E TEST FAILED: Timeout waiting for SIGNAL.")

    except Exception as e:
        print(f"Error reading stream: {e}")

    await r.aclose()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_e2e_market_data_flow())
    except Exception as e:
        print(f"❌ E2E Failed: {e}")
    finally:
        loop.close()
