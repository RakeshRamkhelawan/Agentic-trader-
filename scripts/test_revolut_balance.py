import asyncio
import os
import json
import re
import sys
from pathlib import Path

# Add project root to path for backend imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from backend.execution.exchange_adapter import ExchangeAdapter # Aangepast naar ExchangeAdapter
from backend.core.config.settings import settings # Nieuw: voor Revolut host

async def test_connection():
    # De API key moet uit een .env file komen of hier handmatig worden ingevuld voor testdoeleinden
    API_KEY = os.getenv("REVOLUT_API_KEY", "JOUW_API_KEY_HIER")

    # Path calculation for pem file
    default_pem_path = str(project_root / "revolut_private.pem")
    PRIVATE_KEY_PATH = os.getenv("REVOLUT_PRIVATE_KEY_PATH", default_pem_path)

    if API_KEY == "JOUW_API_KEY_HIER":
        print("Fout: Vul eerst je API Key in het script of in een .env bestand in!")
        return

    print(f"Verbinding maken met Exchange (Revolut X)...")

    adapter = ExchangeAdapter(
        api_key=API_KEY,
        private_key_path=PRIVATE_KEY_PATH,
        base_url="https://revx.revolut.com" # Of settings.REVOLUT_BASE_URL als die bestaat
    )

    try:
        print("Saldo ophalen...")
        balances = await adapter.get_balance()

        print("\n--- Jouw Revolut X Saldo ---")
        if not balances:
            print("Geen saldo gevonden (of alle wallets zijn leeg).")
        for currency, amount in balances.items():
            if amount > 0:
                print(f"{currency}: {amount}")
        print("----------------------------")
        print("\n✅ ALLES WERKT!")

    except Exception as e:
        print(f"\n❌ FOUT: {str(e)}")
    finally:
        await adapter.client.aclose()

if __name__ == "__main__":
    asyncio.run(test_connection())
