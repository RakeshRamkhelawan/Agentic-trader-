#!/usr/bin/env python3
"""
Fetch all assets from Revolut X.

Revolut X doesn't have a public API like Bitvavo, but we can:
1. Try CCXT (if supported)
2. Use their internal API endpoints found via browser dev tools
3. Fallback to manual import

Usage:
    python scripts/fetch_revolut_assets.py

Output:
    - data/revolutx_assets.csv
    - data/revolutx_assets.json
"""

import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

import httpx

# Revolut X API endpoints (found via browser dev tools)
# These are internal endpoints and may change
REVOLUT_API_BASE = "https://app.revolut.com/api"
TOKEN_LIST_ENDPOINT = "https://app.revolut.com/api/crypto/trading/token-list"


async def fetch_revolut_assets_via_ccxt() -> Optional[List[Dict[str, Any]]]:
    """Try to fetch assets using CCXT."""
    try:
        import ccxt.async_support as ccxt

        # Check if revolut is supported
        if hasattr(ccxt, "revolut"):
            exchange = ccxt.revolut()
            await exchange.load_markets()

            markets = []
            for symbol, market in exchange.markets.items():
                markets.append(
                    {
                        "symbol": symbol,
                        "baseAsset": market.get("base", ""),
                        "quoteAsset": market.get("quote", ""),
                        "status": "active"
                        if market.get("active", True)
                        else "inactive",
                    }
                )

            await exchange.close()
            return markets
    except Exception as e:
        print(f"[WARN] CCXT not available for Revolut: {e}")

    return None


async def fetch_revolut_assets_via_api() -> Optional[List[Dict[str, Any]]]:
    """
    Fetch assets from Revolut's internal API.
    Note: This may require authentication or may be rate-limited.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try the public token list endpoint
            response = await client.get(
                TOKEN_LIST_ENDPOINT,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )

            if response.status_code == 200:
                data = response.json()
                print("[OK] Fetched data from Revolut API")

                # Parse the response (structure may vary)
                markets = []
                if isinstance(data, list):
                    for item in data:
                        markets.append(
                            {
                                "symbol": item.get("symbol", ""),
                                "baseAsset": item.get(
                                    "baseAsset", item.get("symbol", "").split("-")[0]
                                ),
                                "quoteAsset": item.get(
                                    "quoteAsset",
                                    item.get("symbol", "").split("-")[1]
                                    if "-" in item.get("symbol", "")
                                    else "",
                                ),
                                "name": item.get("name", ""),
                                "status": item.get("status", "active"),
                            }
                        )
                elif isinstance(data, dict) and "tokens" in data:
                    for item in data["tokens"]:
                        markets.append(
                            {
                                "symbol": item.get("symbol", ""),
                                "baseAsset": item.get("baseAsset", ""),
                                "quoteAsset": item.get("quoteAsset", ""),
                                "name": item.get("name", ""),
                                "status": item.get("status", "active"),
                            }
                        )

                return markets
            else:
                print(f"[WARN] Revolut API returned status {response.status_code}")

    except Exception as e:
        print(f"[WARN] Could not fetch from Revolut API: {e}")

    return None


def load_manual_revolut_assets() -> List[Dict[str, Any]]:
    """
    Load manually collected Revolut X assets.
    These were collected from the Revolut X web interface.
    """
    # Common assets available on Revolut X (as of 2024)
    # This is a fallback list - users should update via browser dev tools
    assets = [
        # Major pairs available on Revolut X
        {
            "symbol": "BTC-EUR",
            "baseAsset": "BTC",
            "quoteAsset": "EUR",
            "name": "Bitcoin",
            "status": "active",
        },
        {
            "symbol": "ETH-EUR",
            "baseAsset": "ETH",
            "quoteAsset": "EUR",
            "name": "Ethereum",
            "status": "active",
        },
        {
            "symbol": "SOL-EUR",
            "baseAsset": "SOL",
            "quoteAsset": "EUR",
            "name": "Solana",
            "status": "active",
        },
        {
            "symbol": "ADA-EUR",
            "baseAsset": "ADA",
            "quoteAsset": "EUR",
            "name": "Cardano",
            "status": "active",
        },
        {
            "symbol": "DOT-EUR",
            "baseAsset": "DOT",
            "quoteAsset": "EUR",
            "name": "Polkadot",
            "status": "active",
        },
        {
            "symbol": "XRP-EUR",
            "baseAsset": "XRP",
            "quoteAsset": "EUR",
            "name": "XRP",
            "status": "active",
        },
        {
            "symbol": "LINK-EUR",
            "baseAsset": "LINK",
            "quoteAsset": "EUR",
            "name": "Chainlink",
            "status": "active",
        },
        {
            "symbol": "DOGE-EUR",
            "baseAsset": "DOGE",
            "quoteAsset": "EUR",
            "name": "Dogecoin",
            "status": "active",
        },
        {
            "symbol": "LTC-EUR",
            "baseAsset": "LTC",
            "quoteAsset": "EUR",
            "name": "Litecoin",
            "status": "active",
        },
        {
            "symbol": "XLM-EUR",
            "baseAsset": "XLM",
            "quoteAsset": "EUR",
            "name": "Stellar",
            "status": "active",
        },
    ]

    print(
        "[WARN] Using fallback asset list. For complete list, use browser dev tools method."
    )
    print(
        "   See: https://github.com/RakeshRamkhelawan/Agentic-trader-/blob/main/scripts/README.md"
    )

    return assets


def extract_unique_assets(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract unique base assets from markets."""
    assets = {}

    for market in markets:
        base = market.get("baseAsset", "")
        if base and base not in assets:
            assets[base] = {
                "symbol": base,
                "name": market.get("name", base),
                "type": "crypto",
                "active": market.get("status") == "active",
            }

    return list(assets.values())


def save_to_csv(markets: List[Dict[str, Any]], filepath: Path):
    """Save markets to CSV file."""
    if not markets:
        print("⚠️ No markets to save")
        return

    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=markets[0].keys())
        writer.writeheader()
        writer.writerows(markets)

    print(f"[OK] Saved {len(markets)} markets to {filepath}")


def save_to_json(data: Any, filepath: Path):
    """Save data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved to {filepath}")


async def main():
    """Main function."""
    print("[INFO] Fetching Revolut X assets...\n")

    markets = None

    # Try CCXT first
    print("[1/3] Trying CCXT...")
    markets = await fetch_revolut_assets_via_ccxt()

    # Try direct API if CCXT fails
    if not markets:
        print("\n[2/3] Trying direct API...")
        markets = await fetch_revolut_assets_via_api()

    # Fallback to manual list
    if not markets:
        print("\n[3/3] Using fallback asset list...")
        markets = load_manual_revolut_assets()

    if not markets:
        print("[ERROR] Could not fetch any assets")
        return

    # Extract unique assets
    unique_assets = extract_unique_assets(markets)
    print(f"\n[INFO] Found {len(unique_assets)} unique base assets")

    # Setup output directory
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    # Save markets CSV
    markets_csv = output_dir / "revolutx_assets.csv"
    save_to_csv(markets, markets_csv)

    # Save unique assets CSV
    assets_csv = output_dir / "revolutx_unique_assets.csv"
    save_to_csv(unique_assets, assets_csv)

    # Save JSON versions
    save_to_json(markets, output_dir / "revolutx_assets.json")
    save_to_json(unique_assets, output_dir / "revolutx_unique_assets.json")

    # Print summary
    print("\n[INFO] Summary:")
    print(f"   Total markets: {len(markets)}")
    print(f"   Unique assets: {len(unique_assets)}")
    print(f"   Quote currencies: {len(set(m.get('quoteAsset', '') for m in markets))}")
    print("\n[OK] Done!")
    print("\n[TIP] For the complete asset list, use browser dev tools:")
    print("   1. Open Revolut X in browser")
    print("   2. Open Network tab (F12)")
    print("   3. Look for 'token-list' or 'markets' API calls")
    print("   4. Copy the JSON response and save to data/revolutx_manual.json")


if __name__ == "__main__":
    asyncio.run(main())
