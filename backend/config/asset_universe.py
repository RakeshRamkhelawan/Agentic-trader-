"""
Multi-Asset Universe Configuration
Vedic-aligned asset registry with elemental and Navagraha affinities
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict


class AssetClass(str, Enum):
    """Asset class categories"""
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITIES = "commodities"
    INDICES = "indices"
    EQUITIES = "equities"
    BONDS = "bonds"


@dataclass
class TradableAsset:
    """Complete asset definition with Vedic attributes"""
    symbol: str              # CCXT-compatible: "BTC/EUR", "EUR/USD"
    asset_class: AssetClass
    exchange: str            # "bitvavo", "ccxt:binance", "ccxt:oanda"
    min_qty: float
    tick_size: float
    vedic_element: str       # Primary elemental responsibility
    navagraha_affinity: str  # Resonant planet
    pip_value: float = 1.0   # For forex position sizing
    contract_size: float = 1.0  # For commodities/indices
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "asset_class": self.asset_class.value,
            "exchange": self.exchange,
            "min_qty": self.min_qty,
            "tick_size": self.tick_size,
            "vedic_element": self.vedic_element,
            "navagraha_affinity": self.navagraha_affinity,
        }


# ============================================================================
# FULL ASSET UNIVERSE - 50+ Assets across 6 classes
# ============================================================================

FULL_ASSET_UNIVERSE: List[TradableAsset] = [
    # ── CRYPTO (7) ─────────────────────────────────────────────────────
    TradableAsset("BTC/EUR",  AssetClass.CRYPTO,      "bitvavo",      0.0001, 0.01,   "fire",  "SUN"),
    TradableAsset("ETH/EUR",  AssetClass.CRYPTO,      "bitvavo",      0.001,  0.01,   "water", "MOON"),
    TradableAsset("SOL/EUR",  AssetClass.CRYPTO,      "bitvavo",      0.01,   0.001,  "fire",  "MARS"),
    TradableAsset("ADA/EUR",  AssetClass.CRYPTO,      "bitvavo",      1.0,    0.0001, "earth", "SATURN"),
    TradableAsset("XRP/EUR",  AssetClass.CRYPTO,      "bitvavo",      1.0,    0.0001, "water", "MERCURY"),
    TradableAsset("LINK/EUR", AssetClass.CRYPTO,      "bitvavo",      0.1,    0.001,  "air",   "MERCURY"),
    TradableAsset("DOT/EUR",  AssetClass.CRYPTO,      "bitvavo",      0.1,    0.001,  "ether", "JUPITER"),
    
    # ── FOREX (5) ──────────────────────────────────────────────────────
    TradableAsset("EUR/USD",  AssetClass.FOREX,       "ccxt:oanda",   1000,   0.00001, "air",   "MERCURY",  pip_value=10.0),
    TradableAsset("GBP/USD",  AssetClass.FOREX,       "ccxt:oanda",   1000,   0.00001, "earth", "SATURN",  pip_value=10.0),
    TradableAsset("USD/JPY",  AssetClass.FOREX,       "ccxt:oanda",   1000,   0.001,   "water", "MOON",    pip_value=1000.0),
    TradableAsset("EUR/GBP",  AssetClass.FOREX,       "ccxt:oanda",   1000,   0.00001, "air",   "VENUS",   pip_value=10.0),
    TradableAsset("USD/CHF",  AssetClass.FOREX,       "ccxt:oanda",   1000,   0.00001, "earth", "SATURN",  pip_value=10.0),
    
    # ── COMMODITIES (3) ───────────────────────────────────────────────
    TradableAsset("XAU/USD",  AssetClass.COMMODITIES, "ccxt:oanda",   0.01,   0.01,    "earth", "SUN"),     # Gold
    TradableAsset("XAG/USD",  AssetClass.COMMODITIES, "ccxt:oanda",   1.0,    0.001,   "water", "MOON"),    # Silver
    TradableAsset("OIL/USD",  AssetClass.COMMODITIES, "ccxt:oanda",   1.0,    0.01,    "fire",  "MARS"),    # WTI Oil
    
    # ── INDICES (3) ────────────────────────────────────────────────────
    TradableAsset("SPX500",   AssetClass.INDICES,     "ccxt:oanda",   0.1,    0.1,     "ether", "SUN",     contract_size=1.0),   # S&P500
    TradableAsset("NAS100",   AssetClass.INDICES,     "ccxt:oanda",   0.1,    0.1,     "fire",  "MERCURY", contract_size=1.0),   # Nasdaq
    TradableAsset("GER40",    AssetClass.INDICES,     "ccxt:oanda",   0.1,    0.1,     "earth", "SATURN",  contract_size=1.0),   # DAX
    
    # ── EQUITIES (35) ─────────────────────────────────────────────────
    # Tech Giants (Fire/Mercury)
    TradableAsset("AAPL",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MERCURY"),
    TradableAsset("MSFT",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "JUPITER"),
    TradableAsset("GOOGL",    AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "air",   "MERCURY"),
    TradableAsset("AMZN",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    TradableAsset("META",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "SUN"),
    TradableAsset("NVDA",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MARS"),
    TradableAsset("TSLA",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MARS"),
    
    # Financials (Earth/Saturn)
    TradableAsset("JPM",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    TradableAsset("BAC",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    TradableAsset("WFC",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    
    # Healthcare (Water/Venus)
    TradableAsset("JNJ",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "VENUS"),
    TradableAsset("PFE",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "VENUS"),
    TradableAsset("UNH",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "JUPITER"),
    
    # Energy (Fire/Mars)
    TradableAsset("XOM",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MARS"),
    TradableAsset("CVX",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MARS"),
    
    # Consumer (Earth/Venus)
    TradableAsset("WMT",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "VENUS"),
    TradableAsset("PG",       AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "VENUS"),
    TradableAsset("KO",       AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "VENUS"),
    
    # Industrials (Earth/Saturn)
    TradableAsset("GE",       AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    TradableAsset("CAT",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    
    # European
    TradableAsset("ASML",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "air",   "MERCURY"),
    TradableAsset("SAP",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    TradableAsset("NESN",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "VENUS"),
    TradableAsset("ROG",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "JUPITER"),
    TradableAsset("SHEL",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MARS"),
    TradableAsset("TTE",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MARS"),
    TradableAsset("AIR",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "air",   "MERCURY"),
    
    # Tech/SaaS
    TradableAsset("NFLX",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "water", "MOON"),
    TradableAsset("CRM",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "air",   "MERCURY"),
    TradableAsset("ADBE",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "SUN"),
    TradableAsset("ORCL",     AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    TradableAsset("IBM",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
    
    # ETFs (Ether/Jupiter)
    TradableAsset("SPY",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "ether", "JUPITER"),
    TradableAsset("QQQ",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "fire",  "MERCURY"),
    TradableAsset("IWM",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "air",   "MERCURY"),
    TradableAsset("VTI",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "ether", "JUPITER"),
    TradableAsset("GLD",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SUN"),
    TradableAsset("TLT",      AssetClass.EQUITIES,    "ccxt:alpaca",  1,      0.01,    "earth", "SATURN"),
]


# ============================================================================
# Asset Lookup Functions
# ============================================================================

def get_all_assets() -> List[TradableAsset]:
    """Get complete asset universe"""
    return FULL_ASSET_UNIVERSE


def get_assets_by_class(cls: AssetClass) -> List[TradableAsset]:
    """Filter assets by class"""
    return [a for a in FULL_ASSET_UNIVERSE if a.asset_class == cls]


def get_assets_by_element(element: str) -> List[TradableAsset]:
    """Filter assets by Vedic element"""
    return [a for a in FULL_ASSET_UNIVERSE if a.vedic_element == element]


def get_assets_by_navagraha(planet: str) -> List[TradableAsset]:
    """Filter assets by Navagraha affinity"""
    return [a for a in FULL_ASSET_UNIVERSE if a.navagraha_affinity == planet]


def get_asset_by_symbol(symbol: str) -> Optional[TradableAsset]:
    """Get single asset by symbol"""
    for asset in FULL_ASSET_UNIVERSE:
        if asset.symbol == symbol:
            return asset
    return None


def get_crypto_symbols() -> List[str]:
    """Get all crypto symbols"""
    return [a.symbol for a in FULL_ASSET_UNIVERSE if a.asset_class == AssetClass.CRYPTO]


def get_forex_symbols() -> List[str]:
    """Get all forex symbols"""
    return [a.symbol for a in FULL_ASSET_UNIVERSE if a.asset_class == AssetClass.FOREX]


def get_commodity_symbols() -> List[str]:
    """Get all commodity symbols"""
    return [a.symbol for a in FULL_ASSET_UNIVERSE if a.asset_class == AssetClass.COMMODITIES]


def get_index_symbols() -> List[str]:
    """Get all index symbols"""
    return [a.symbol for a in FULL_ASSET_UNIVERSE if a.asset_class == AssetClass.INDICES]


def get_equity_symbols() -> List[str]:
    """Get all equity symbols"""
    return [a.symbol for a in FULL_ASSET_UNIVERSE if a.asset_class == AssetClass.EQUITIES]


# ============================================================================
# Statistics
# ============================================================================

def get_universe_stats() -> Dict:
    """Get universe statistics"""
    stats = {
        "total_assets": len(FULL_ASSET_UNIVERSE),
        "by_class": {},
        "by_element": {},
        "by_navagraha": {}
    }
    
    for asset in FULL_ASSET_UNIVERSE:
        # By class
        cls = asset.asset_class.value
        stats["by_class"][cls] = stats["by_class"].get(cls, 0) + 1
        
        # By element
        elem = asset.vedic_element
        stats["by_element"][elem] = stats["by_element"].get(elem, 0) + 1
        
        # By navagraha
        planet = asset.navagraha_affinity
        stats["by_navagraha"][planet] = stats["by_navagraha"].get(planet, 0) + 1
    
    return stats


# Print stats when module loads
if __name__ == "__main__":
    stats = get_universe_stats()
    print("=" * 60)
    print("VEDIC ASSET UNIVERSE")
    print("=" * 60)
    print(f"Total Assets: {stats['total_assets']}")
    print("\nBy Asset Class:")
    for cls, count in stats["by_class"].items():
        print(f"  {cls}: {count}")
    print("\nBy Vedic Element:")
    for elem, count in stats["by_element"].items():
        print(f"  {elem}: {count}")
    print("\nBy Navagraha:")
    for planet, count in stats["by_navagraha"].items():
        print(f"  {planet}: {count}")
    print("=" * 60)
