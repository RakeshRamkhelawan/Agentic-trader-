import asyncio
import os
import sys
from pathlib import Path

# Add project root to path for backend imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from backend.execution.exchange_adapter import ExchangeAdapter

async def test_connection():
    # Read API key from environment
    API_KEY = os.getenv("REVOLUT_API_KEY", "")
    PRIVATE_KEY_PATH = os.getenv("REVOLUT_PRIVATE_KEY_PATH", str(project_root / "revolut_private.pem"))
    SANDBOX = os.getenv("REVOLUT_SANDBOX", "false").lower() == "true"

    if not API_KEY:
        print("[ERROR] REVOLUT_API_KEY not found in .env file!")
        print("Add this to your .env file:")
        print('  REVOLUT_API_KEY="your_api_key_here"')
        print('  REVOLUT_PRIVATE_KEY_PATH="path/to/revolut_private.pem"')
        return

    if not Path(PRIVATE_KEY_PATH).exists():
        print(f"[ERROR] Private key file not found: {PRIVATE_KEY_PATH}")
        return

    base_url = "https://sandbox-revx.revolut.com" if SANDBOX else "https://revx.revolut.com"
    mode = "SANDBOX" if SANDBOX else "LIVE"
    print(f"Connecting to Revolut X ({mode})...")

    # Gebruik ExchangeAdapter, met de Revolut URL
    # Read private key content
    with open(PRIVATE_KEY_PATH, 'r') as f:
        private_key_pem = f.read()

    adapter = ExchangeAdapter(api_key=API_KEY, private_key_pem=private_key_pem, base_url=base_url)

    try:
        print("Fetching system configuration (currencies)...")
        # We voegen een tijdelijke methode toe aan de adapter of gebruiken de _request direct
        currencies = await adapter._request("GET", "/api/1.0/configuration/currencies")
        print(f"\n[SUCCESS] CONNECTION SUCCESSFUL!")
        print(f"Available currencies found: {len(currencies)}")

        # Laat de eerste 5 zien als check
        for c in currencies[:5]:
            print(f"- {c['code']} ({c['name']})")

    except Exception as e:
        print(f"\n[ERROR] Could not connect.")
        print(f"Details: {str(e)}")
    finally:
        await adapter.client.aclose()

if __name__ == "__main__":
    asyncio.run(test_connection())
