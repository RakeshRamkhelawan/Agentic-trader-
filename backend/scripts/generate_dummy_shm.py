import math
import os
import random
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge


def run_generator():
    # 1. Create Market Data Writer
    try:
        market_bridge = ZeroCopyBridge(
            create=True, shm_name="market_data_v2", dtype_name="market", max_symbols=100
        )
        print("[OK] Created 'market_data_v2' SHM", flush=True)
    except Exception as e:
        print(f"[ERR] Failed to create 'market_data_v2': {e}", flush=True)
        return

    # 2. Create Trading Intent Writer
    try:
        intent_bridge = ZeroCopyBridge(
            create=True,
            shm_name="trading_intents_v2",
            dtype_name="intent",
            max_symbols=100,
        )
        print("[OK] Created 'trading_intents_v2' SHM", flush=True)
    except Exception as e:
        print(f"[ERR] Failed to create 'trading_intents_v2': {e}", flush=True)
        market_bridge.close()
        return

    print("Starting Data Loop (600s)...", flush=True)
    start_time = time.time()

    symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]

    try:
        while time.time() - start_time < 600:
            t = time.time()
            ts_ns = int(t * 1e9)

            try:
                # Update Market Data
                for sym in symbols:
                    base_price = 50000 if "BTC" in sym else (3000 if "ETH" in sym else 100)
                    volatility = 0.001
                    price = base_price * (
                        1 + math.sin(t) * volatility + random.gauss(0, volatility / 10)
                    )

                    market_bridge.write_market_data(
                        symbol=sym,
                        bid=price - 0.5,
                        ask=price + 0.5,
                        last=price,
                        bid_size=1000.0,
                        ask_size=1000.0,
                    )

                # Update Intents (less frequent)
                if int(t * 10) % 5 == 0:  # Every 0.5s
                    for sym in symbols:
                        action = 1 if math.sin(t) > 0 else -1
                        intent = TradingIntent(
                            action=action,
                            size=1.0,
                            confidence=0.95,
                            stop_loss=0.0,
                            take_profit=0.0,
                            max_hold_ms=0,
                            entry_price=0.0,
                            timestamp_ns=ts_ns,
                        )
                        intent_bridge.write_intent(sym, intent)
            except Exception as loop_e:
                print(f"[ERR] Loop Error: {loop_e}", flush=True)
                time.sleep(1)

            time.sleep(0.01)  # 100Hz

    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        print("Closing bridges...")
        market_bridge.close()
        intent_bridge.close()
        # Unlink is dangerous if monitor is reading, but for test it's fine.
        # Ideally we let OS cleanup or explicit unlink separate script.
        # market_bridge.unlink()
        # intent_bridge.unlink()


if __name__ == "__main__":
    run_generator()
