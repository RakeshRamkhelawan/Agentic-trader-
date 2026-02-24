"""
Navagraha Asset Affinity System
Maps planets to preferred assets based on Vedic principles
"""

from backend.config.asset_universe import FULL_ASSET_UNIVERSE

# ============================================================================
# PLANET ASSET AFFINITY MAPPING
# Based on Vedic astrology principles for trading
# ============================================================================

PLANET_ASSET_AFFINITY: dict[str, list[str]] = {
    "SUN": [
        # Authority, core trends, gold, large cap indices
        "BTC/EUR",  # Digital gold, dominant crypto
        "SPX500",  # Core US equity index
        "XAU/USD",  # Physical gold
        "GLD",  # Gold ETF
        "AAPL",  # Largest market cap
        "META",  # Social authority
    ],
    "MOON": [
        # Sentiment, cycles, silver, consumer staples
        "ETH/EUR",  # Emotional/crypto cycles
        "EUR/USD",  # Most traded forex pair (liquidity)
        "GBP/USD",  # Sentiment-driven
        "XAG/USD",  # Silver
        "NFLX",  # Entertainment/cycles
        "WMT",  # Consumer staples
        "NESN",  # Consumer goods
    ],
    "MARS": [
        # Aggression, momentum, energy, volatility
        "BTC/EUR",  # High volatility
        "SOL/EUR",  # Aggressive growth
        "OIL/USD",  # Energy
        "XOM",  # Energy sector
        "CVX",  # Energy sector
        "NVDA",  # High momentum
        "TSLA",  # Volatility
        "SHEL",  # Energy
        "TTE",  # Energy
    ],
    "MERCURY": [
        # Communication, speed, tech, quick trades
        "EUR/USD",  # Most liquid, quick moves
        "LINK/EUR",  # Oracle/communication
        "NAS100",  # Tech index
        "GOOGL",  # Information
        "AAPL",  # Communication devices
        "CRM",  # SaaS communication
        "ORCL",  # Database/communication
        "ASML",  # Tech infrastructure
        "AIR",  # Travel/communication
        "QQQ",  # Tech ETF
        "IWM",  # Quick small-cap moves
    ],
    "JUPITER": [
        # Wisdom, growth, expansion, large institutions
        "SPX500",  # Institutional benchmark
        "GER40",  # European blue chips
        "DOT/EUR",  # Governance/interoperability
        "XAU/USD",  # Store of value (wisdom)
        "MSFT",  # Enterprise/growth
        "UNH",  # Healthcare/growth
        "ROG",  # Pharma/growth
        "SPY",  # S&P ETF
        "VTI",  # Total market
    ],
    "VENUS": [
        # Value, attraction, luxury, beauty
        "ETH/EUR",  # Value settlement
        "EUR/GBP",  # European value pairs
        "XAG/USD",  # Precious (beauty)
        "JNJ",  # Healthcare/beauty
        "PFE",  # Healthcare
        "WMT",  # Consumer value
        "PG",  # Consumer goods
        "KO",  # Brand value
        "NESN",  # Consumer luxury
    ],
    "SATURN": [
        # Restriction, stability, discipline, structure
        "ADA/EUR",  # Academic/structured approach
        "GBP/USD",  # Conservative currency
        "USD/CHF",  # Safe haven
        "GER40",  # Structured German economy
        "JPM",  # Banking/discipline
        "BAC",  # Banking
        "WFC",  # Banking
        "GE",  # Industrial/discipline
        "CAT",  # Industrial
        "SAP",  # Enterprise structure
        "IBM",  # Conservative tech
        "ORCL",  # Enterprise
        "TLT",  # Long-term bonds
    ],
    "RAHU": [
        # Hype, bubbles, illusions, sudden changes
        # Note: Rahu Kala blocks trading, but these assets
        # resonate with Rahu's speculative nature
        "SOL/EUR",  # Hype cycles
        "DOT/EUR",  # New paradigm
        "NVDA",  # AI hype
        "TSLA",  # Meme stock energy
        "COIN",  # Crypto hype proxy
        "ROKU",  # Growth hype
        "SNOW",  # Tech hype
        "ZM",  # Pandemic boom/bust
    ],
    "KETU": [
        # Detachment, exits, spirituality, endings
        # Ketu assets are good for closing positions
        # Rather than opening - these mark cycle endings
        "BTC/EUR",  # When institutions exit
        "ETH/EUR",  # When DeFi matures
        "SPX500",  # Market tops
        "XAU/USD",  # Safe haven in crashes
        "TLT",  # Bonds when stocks peak
    ],
}


# ============================================================================
# Planet Trading Characteristics
# ============================================================================

PLANET_TRADING_STYLE: dict[str, dict] = {
    "SUN": {
        "style": "trend_following",
        "timeframe": "long_term",
        "risk_tolerance": "medium",
        "preferred_action": "position_hold",
    },
    "MOON": {
        "style": "sentiment_driven",
        "timeframe": "swing",
        "risk_tolerance": "medium_high",
        "preferred_action": "counter_trend",
    },
    "MARS": {
        "style": "momentum",
        "timeframe": "short_term",
        "risk_tolerance": "high",
        "preferred_action": "aggressive_entry",
    },
    "MERCURY": {
        "style": "scalping",
        "timeframe": "intraday",
        "risk_tolerance": "low",
        "preferred_action": "quick_flip",
    },
    "JUPITER": {
        "style": "value_growth",
        "timeframe": "long_term",
        "risk_tolerance": "medium",
        "preferred_action": "accumulate",
    },
    "VENUS": {
        "style": "value",
        "timeframe": "medium_term",
        "risk_tolerance": "low",
        "preferred_action": "buy_dips",
    },
    "SATURN": {
        "style": "disciplined",
        "timeframe": "very_long_term",
        "risk_tolerance": "very_low",
        "preferred_action": "hold",
    },
    "RAHU": {
        "style": "speculative",
        "timeframe": "very_short",
        "risk_tolerance": "very_high",
        "preferred_action": "avoid_or_contrarian",
    },
    "KETU": {
        "style": "exit_focused",
        "timeframe": "any",
        "risk_tolerance": "none",
        "preferred_action": "close_positions",
    },
}


# ============================================================================
# Core Functions
# ============================================================================


def get_favored_assets_for_planet(planet: str) -> list[str]:
    """
    Get assets that resonate with a specific planet.
    Called before each trading cycle to prioritize assets.
    """
    return PLANET_ASSET_AFFINITY.get(planet.upper(), [])


def get_planet_for_asset(symbol: str) -> str | None:
    """Find which planet has affinity with this asset"""
    for planet, symbols in PLANET_ASSET_AFFINITY.items():
        if symbol in symbols:
            return planet
    return None


def get_trading_style_for_planet(planet: str) -> dict:
    """Get recommended trading style for current planetary influence"""
    return PLANET_TRADING_STYLE.get(
        planet.upper(),
        {
            "style": "neutral",
            "timeframe": "medium",
            "risk_tolerance": "medium",
            "preferred_action": "hold",
        },
    )


def should_trade_asset(dominant_planet: str, symbol: str) -> bool:
    """
    Check if trading this asset aligns with dominant planet.
    Returns False if there's strong mismatch.
    """
    favored = get_favored_assets_for_planet(dominant_planet)

    # If in favored list - definitely trade
    if symbol in favored:
        return True

    # If Rahu dominant - avoid trading unless explicitly in Rahu list
    if dominant_planet == "RAHU":
        return symbol in favored

    # Default: allow trading but with reduced priority
    return True


def get_position_size_multiplier(planet: str) -> float:
    """
    Get position size adjustment based on planet.
    Saturn = conservative (0.5x), Mars = aggressive (1.5x)
    """
    multipliers = {
        "SUN": 1.0,
        "MOON": 1.1,
        "MARS": 1.5,
        "MERCURY": 0.9,
        "JUPITER": 1.2,
        "VENUS": 0.8,
        "SATURN": 0.5,
        "RAHU": 0.0,  # No trading during Rahu
        "KETU": 0.0,  # No new positions during Ketu
    }
    return multipliers.get(planet.upper(), 1.0)


def get_asset_priority_list(dominant_planet: str, secondary_planet: str | None = None) -> list[str]:
    """
    Get prioritized list of assets for current planetary configuration.
    Primary planet assets first, then secondary.
    """
    priorities = []

    # Primary planet assets (high priority)
    primary_assets = get_favored_assets_for_planet(dominant_planet)
    priorities.extend(primary_assets)

    # Secondary planet assets (medium priority)
    if secondary_planet:
        secondary_assets = get_favored_assets_for_planet(secondary_planet)
        for asset in secondary_assets:
            if asset not in priorities:
                priorities.append(asset)

    # Add remaining assets (low priority)
    all_symbols = [a.symbol for a in FULL_ASSET_UNIVERSE]
    for symbol in all_symbols:
        if symbol not in priorities:
            priorities.append(symbol)

    return priorities


def explain_planet_asset_connection(planet: str, symbol: str) -> str:
    """Get Vedic explanation for planet-asset connection"""
    connections = {
        (
            "SUN",
            "BTC/EUR",
        ): "Sun represents authority and digital gold - BTC as modern gold standard",
        ("SUN", "XAU/USD"): "Sun rules gold in Vedic astrology - direct correspondence",
        (
            "MOON",
            "ETH/EUR",
        ): "Moon rules water and cycles - ETH's ecosystem flows like tides",
        ("MOON", "XAG/USD"): "Moon rules silver - secondary precious metal",
        ("MARS", "OIL/USD"): "Mars rules energy and war - oil as energy commodity",
        ("MARS", "NVDA"): "Mars rules aggression and speed - NVDA's explosive growth",
        ("MERCURY", "EUR/USD"): "Mercury rules commerce and exchange - forex trading",
        ("MERCURY", "LINK/EUR"): "Mercury rules communication - LINK as oracle network",
        (
            "JUPITER",
            "DOT/EUR",
        ): "Jupiter rules governance and wisdom - DOT's interoperability",
        (
            "JUPITER",
            "SPX500",
        ): "Jupiter rules institutions and growth - institutional benchmark",
        (
            "VENUS",
            "ETH/EUR",
        ): "Venus rules value and beauty - ETH's elegant smart contracts",
        (
            "SATURN",
            "ADA/EUR",
        ): "Saturn rules structure and discipline - ADA's academic approach",
        ("SATURN", "GBP/USD"): "Saturn rules tradition - GBP's conservative nature",
    }

    return connections.get(
        (planet.upper(), symbol),
        f"{planet} influences {symbol} through Vedic resonance",
    )


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("NAVAGRAHA ASSET AFFINITY SYSTEM")
    print("=" * 70)

    # Example: Jupiter dominant
    dominant = "JUPITER"
    print(f"\nDominant Planet: {dominant}")
    print(f"Favored Assets: {get_favored_assets_for_planet(dominant)}")
    print(f"Trading Style: {get_trading_style_for_planet(dominant)}")
    print(f"Position Size Multiplier: {get_position_size_multiplier(dominant)}")

    # Check asset priority
    symbol = "DOT/EUR"
    can_trade = should_trade_asset(dominant, symbol)
    print(f"\nShould trade {symbol}? {can_trade}")
    print(f"Explanation: {explain_planet_asset_connection(dominant, symbol)}")

    # Get full priority list
    priorities = get_asset_priority_list(dominant, "MERCURY")
    print(f"\nTop 10 Priority Assets: {priorities[:10]}")

    print("=" * 70)
