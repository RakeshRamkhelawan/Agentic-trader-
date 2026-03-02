import os
import sys
import traceback

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

try:
    from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge
except ImportError:
    print("Failed to import ZeroCopyBridge. checks sys.path.")
    sys.exit(1)


def test_bridge():
    print("Starting ZeroCopyBridge debug test...")

    bridge = None
    try:
        # 1. Create Bridge
        print("Creating bridge...")
        bridge = ZeroCopyBridge(max_symbols=10, create=True)
        print(f"Bridge created. SHM Name: {bridge.shm_name}, Size: {bridge.shm.size}")

        # 2. Write Intent
        symbol = "BTC/USD"
        print(f"Writing intent for {symbol}...")
        intent = TradingIntent(
            action=1,
            size=1.5,
            confidence=0.95,
            stop_loss=45000.0,
            take_profit=55000.0,
            max_hold_ms=60000,
            entry_price=50000.0,
            timestamp_ns=0,
        )
        bridge.write_intent(symbol, intent)
        print("Intent written.")

        # 3. Read Intent
        print(f"Reading intent for {symbol}...")
        read_intent = bridge.read_intent(symbol)

        if read_intent:
            print(f"Read success: Action={read_intent.action}, Size={read_intent.size}")
            if read_intent.action == 1 and read_intent.size == 1.5:
                print("Value verification PASSED.")
            else:
                print("Value verification FAILED.")
        else:
            print("Read returned None.")

    except Exception:
        print("An error occurred during the test:")
        traceback.print_exc()
    finally:
        if bridge:
            print("Closing bridge...")
            bridge.close()
            print("Bridge closed.")


if __name__ == "__main__":
    test_bridge()
