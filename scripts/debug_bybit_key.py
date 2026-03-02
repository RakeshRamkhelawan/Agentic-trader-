
import os
from dotenv import load_dotenv

load_dotenv()

def debug_keys():
    print("\n--- Bybit Key Debugger ---")
    key = os.getenv("BYBIT_API_KEY")
    secret = os.getenv("BYBIT_API_SECRET")
    testnet_str = os.getenv("BYBIT_TESTNET", "true")

    print(f"BYBIT_TESTNET setting: '{testnet_str}'")

    if not key:
        print("❌ BYBIT_API_KEY is None or Empty")
    else:
        print(f"✅ BYBIT_API_KEY found.")
        print(f"   Length: {len(key)}")
        print(f"   First 4 chars: '{key[:4]}'")
        print(f"   Last 4 chars:  '{key[-4:]}'")
        # Check for whitespace
        if key.strip() != key:
            print("⚠️  WARNING: API Key has leading/trailing whitespace!")

    if not secret:
        print("❌ BYBIT_API_SECRET is None or Empty")
    else:
        print(f"✅ BYBIT_API_SECRET found.")
        print(f"   Length: {len(secret)}")
        # Check for whitespace
        if secret.strip() != secret:
            print("⚠️  WARNING: API Secret has leading/trailing whitespace!")

if __name__ == "__main__":
    debug_keys()
