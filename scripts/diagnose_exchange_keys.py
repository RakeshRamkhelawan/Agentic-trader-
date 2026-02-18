#!/usr/bin/env python3
"""
Diagnose script voor exchange API key problemen
"""

import os

from dotenv import load_dotenv

load_dotenv()


def check_env_var(name):
    """Check of een environment variable correct is ingesteld"""
    value = os.getenv(name)
    if not value:
        print(f"❌ {name}: NIET INGESTELD")
        return False

    # Check voor veelvoorkomende fouten
    issues = []
    if value.startswith(" ") or value.endswith(" "):
        issues.append("bevat spaties aan begin/einde")
    if '"' in value or "'" in value:
        issues.append("bevat quotes (quotes niet nodig in .env)")
    if "your_" in value.lower() or "example" in value.lower():
        issues.append("bevat placeholder waarde")
    if len(value) < 10:
        issues.append("lijkt te kort")

    if issues:
        print(f"⚠️  {name}: POTENTIEEL PROBLEEM - {', '.join(issues)}")
        print(f"    Lengte: {len(value)} karakters")
        print(f"    Eerste 10 chars: {value[:10]}...")
        return False
    else:
        print(f"✅ {name}: OK (lengte {len(value)})")
        return True


def main():
    print("🔍 Exchange API Key Diagnose\n")
    print("=" * 50)

    # Bybit
    print("\n📊 BYBIT:")
    bybit_key_ok = check_env_var("BYBIT_API_KEY")
    bybit_secret_ok = check_env_var("BYBIT_API_SECRET")
    testnet = os.getenv("BYBIT_TESTNET", "false")
    use_eu = os.getenv("BYBIT_USE_EU", "false")
    print(f"   Testnet: {testnet}")
    print(f"   EU Server: {use_eu}")

    # Kraken
    print("\n🐙 KRAKEN:")
    kraken_key_ok = check_env_var("KRAKEN_API_KEY")
    kraken_secret_ok = check_env_var("KRAKEN_API_SECRET")

    # Revolut
    print("\n💳 REVOLUT:")
    check_env_var("REVOLUT_API_KEY")
    pem_path = os.getenv("REVOLUT_PRIVATE_KEY_PATH", "").strip('"').strip("'")
    if pem_path:
        from pathlib import Path

        if Path(pem_path).exists():
            print("✅ REVOLUT_PRIVATE_KEY_PATH: Bestand bestaat")
        else:
            print(f"❌ REVOLUT_PRIVATE_KEY_PATH: Bestand niet gevonden: {pem_path}")
    else:
        print("❌ REVOLUT_PRIVATE_KEY_PATH: NIET INGESTELD")

    print("\n" + "=" * 50)
    print("\n💡 AANBEVELINGEN:\n")

    if not bybit_key_ok or not bybit_secret_ok:
        print(
            """
🔸 BYBIT:
   1. Ga naar https://www.bybit.com/app/user/api-management
   2. Maak NIEUWE API keys aan (oude kunnen niet aangepast worden)
   3. Bij IP Restriction:
      - Als je een statisch IP/VPN hebt: voer dat IP in
      - Anders: Dit is een probleem - Bybit vereist vaak IP whitelisting
   4. Zet permissies: Wallet, Spot Trading
   5. Kopieer keys ZONDER extra spaties of quotes naar .env
        """
        )

    if not kraken_key_ok or not kraken_secret_ok:
        print(
            """
🔸 KRAKEN:
   1. Ga naar https://www.kraken.com/u/security/api
   2. Genereer nieuwe API key met permissions:
      - Query Funds
      - Query Open Orders & Trades
      - Query Closed Orders & Trades
      - Create & Modify Orders (optioneel)
   3. Kopieer de key PRECIES (let op: lang base64 formaat)
   4. Update .env ZONDER quotes of extra spaties
        """
        )

    print(
        """
🔸 IP ADRES PROBLEMEN (Bybit):
   Als Bybit weigert zonder IP whitelist:
   - Optie A: Gebruik VPN met statisch IP
   - Optie B: Server/Cloud met vast IP (AWS, Azure, etc.)
   - Optie C: Bybit Testnet proberen (BYBIT_TESTNET=true)
   - Optie D: Focus op Kraken + Revolut (die werkt al!)
    """
    )


if __name__ == "__main__":
    main()
