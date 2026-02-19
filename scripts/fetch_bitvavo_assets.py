#!/usr/bin/env python3
"""
Fetch all assets from Bitvavo exchange and export to CSV.

Usage:
    python scripts/fetch_bitvavo_assets.py
    
Output:
    - data/bitvavo_assets.csv
    - data/bitvavo_assets.json
"""

import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

import ccxt.async_support as ccxt


async def fetch_bitvavo_markets() -> List[Dict[str, Any]]:
    """Fetch all markets from Bitvavo using CCXT."""
    exchange = ccxt.bitvavo()

    try:
        print("[INFO] Fetching markets from Bitvavo...")
        await exchange.load_markets()

        markets = []
        for symbol, market in exchange.markets.items():
            markets.append(
                {
                    "symbol": symbol,
                    "baseAsset": market.get("base", ""),
                    "quoteAsset": market.get("quote", ""),
                    "status": "active" if market.get("active", True) else "inactive",
                    "type": market.get("type", "spot"),
                    "precision_price": market.get("precision", {}).get("price", 8),
                    "precision_amount": market.get("precision", {}).get("amount", 8),
                    "limits_min": market.get("limits", {})
                    .get("amount", {})
                    .get("min", 0),
                    "limits_max": market.get("limits", {})
                    .get("amount", {})
                    .get("max", None),
                }
            )

        print(f"[OK] Fetched {len(markets)} markets from Bitvavo")
        return markets

    finally:
        await exchange.close()


def extract_unique_assets(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract unique base assets from markets."""
    assets = {}

    for market in markets:
        base = market["baseAsset"]
        if base and base not in assets:
            assets[base] = {
                "symbol": base,
                "name": base,  # CCXT doesn't provide full names in markets
                "type": "crypto",
                "active": True,
            }

    return list(assets.values())


def save_to_csv(markets: List[Dict[str, Any]], filepath: Path):
    """Save markets to CSV file."""
    if not markets:
        print("[WARN] No markets to save")
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
    # Fetch markets
    markets = await fetch_bitvavo_markets()

    if not markets:
        print("[ERROR] No markets fetched")
        return

    # Extract unique assets
    unique_assets = extract_unique_assets(markets)
    print(f"[INFO] Found {len(unique_assets)} unique base assets")

    # Setup output directory
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    # Save markets CSV
    markets_csv = output_dir / "bitvavo_assets.csv"
    save_to_csv(markets, markets_csv)

    # Save unique assets CSV
    assets_csv = output_dir / "bitvavo_unique_assets.csv"
    save_to_csv(unique_assets, assets_csv)

    # Save JSON versions
    save_to_json(markets, output_dir / "bitvavo_assets.json")
    save_to_json(unique_assets, output_dir / "bitvavo_unique_assets.json")

    # Print summary
    print("\n[INFO] Summary:")
    print(f"   Total markets: {len(markets)}")
    print(f"   Unique assets: {len(unique_assets)}")
    print(f"   Quote currencies: {len(set(m['quoteAsset'] for m in markets))}")
    print("\n[OK] Done!")


if __name__ == "__main__":
    asyncio.run(main())
