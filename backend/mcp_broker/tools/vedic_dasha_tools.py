"""
Vedic Dasha MCP Tools - Planetary period analysis.

Exposes Vimshottari Dasha and other dasha systems as MCP tools.
"""

import logging
from datetime import datetime
from typing import Any

from backend.mcp_broker.resilience import circuit_breaker, vedastro_retry

logger = logging.getLogger(__name__)

# Dasha planet order and periods (years)
VIMSHOTTARI_PERIODS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

NAKSHATRA_LORDS = {
    "Ashwini": "Ketu",
    "Bharani": "Venus",
    "Krittika": "Sun",
    "Rohini": "Moon",
    "Mrigashira": "Mars",
    "Ardra": "Rahu",
    "Punarvasu": "Jupiter",
    "Pushya": "Saturn",
    "Ashlesha": "Mercury",
    "Magha": "Ketu",
    "Purva Phalguni": "Venus",
    "Uttara Phalguni": "Sun",
    "Hasta": "Moon",
    "Chitra": "Mars",
    "Swati": "Rahu",
    "Vishakha": "Jupiter",
    "Anuradha": "Saturn",
    "Jyeshtha": "Mercury",
    "Mula": "Ketu",
    "Purva Ashadha": "Venus",
    "Uttara Ashadha": "Sun",
    "Shravana": "Moon",
    "Dhanishta": "Mars",
    "Shatabhisha": "Rahu",
    "Purva Bhadrapada": "Jupiter",
    "Uttara Bhadrapada": "Saturn",
    "Revati": "Mercury",
}


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedic_calculate_vimshottari_dasha(
    birth_nakshatra: str, birth_nakshatra_pad: int, birth_date: str, ctx=None
) -> dict[str, Any]:
    """
    Calculate Vimshottari Dasha for a birth chart.

    Vimshottari Dasha is a 120-year planetary cycle system used in
    Vedic astrology to predict life events and timing.

    Args:
        birth_nakshatra: Birth nakshatra (lunar mansion) name
        birth_nakshatra_pad: Pada (quarter) 1-4
        birth_date: Birth date (ISO format: YYYY-MM-DD)
        ctx: MCP context for logging

    Returns:
        Dasha periods with timing and interpretations
    """
    if ctx:
        ctx.info(f"Calculating Vimshottari Dasha for {birth_nakshatra} pad {birth_nakshatra_pad}")

    try:
        # Validate inputs
        if birth_nakshatra not in NAKSHATRAS:
            return {
                "success": False,
                "error": f"Invalid nakshatra: {birth_nakshatra}. Valid: {', '.join(NAKSHATRAS[:5])}...",
            }

        if birth_nakshatra_pad < 1 or birth_nakshatra_pad > 4:
            return {"success": False, "error": "Nakshatra pad must be 1-4"}

        # Determine starting planet based on nakshatra lord
        start_planet = NAKSHATRA_LORDS.get(birth_nakshatra, "Moon")

        # Calculate balance of first dasha based on pad
        # Each pad = 3 degrees 20 minutes = 1/4 of nakshatra
        # Balance = (4 - pad + 1) / 4 * full_period
        balance_factor = (5 - birth_nakshatra_pad) / 4

        # Generate dasha sequence
        dasha_sequence = []
        planet_order = list(VIMSHOTTARI_PERIODS.keys())
        start_idx = planet_order.index(start_planet)

        # Reorder to start from birth planet
        ordered_planets = planet_order[start_idx:] + planet_order[:start_idx]

        # Calculate dates
        current_date = datetime.strptime(birth_date, "%Y-%m-%d")

        for planet in ordered_planets:
            period_years = VIMSHOTTARI_PERIODS[planet]

            # Apply balance factor only to first planet
            if planet == start_planet:
                effective_years = period_years * balance_factor
            else:
                effective_years = period_years

            end_date = current_date.replace(year=current_date.year + int(effective_years))

            dasha_sequence.append(
                {
                    "planet": planet,
                    "years": effective_years,
                    "start_date": current_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "interpretation": _get_dasha_interpretation(planet),
                }
            )

            current_date = end_date

        # Determine current dasha
        now = datetime.now()
        current_mahadasha = None
        for dasha in dasha_sequence:
            start = datetime.strptime(dasha["start_date"], "%Y-%m-%d")
            end = datetime.strptime(dasha["end_date"], "%Y-%m-%d")
            if start <= now <= end:
                current_mahadasha = dasha
                break

        if ctx:
            ctx.info(
                f"Dasha calculation complete. Current: {current_mahadasha['planet'] if current_mahadasha else 'Unknown'}"
            )

        return {
            "success": True,
            "result": {
                "birth_nakshatra": birth_nakshatra,
                "birth_pad": birth_nakshatra_pad,
                "starting_planet": start_planet,
                "current_mahadasha": current_mahadasha,
                "dasha_sequence": dasha_sequence[:9],  # Return all 9
                "total_cycle_years": 120,
            },
        }

    except Exception as e:
        logger.error(f"Vimshottari Dasha calculation failed: {e}")
        return {"success": False, "error": f"Calculation failed: {str(e)}"}


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedic_get_nakshatra_analysis(nakshatra: str, pada: int = 1, ctx=None) -> dict[str, Any]:
    """
    Get detailed analysis of a Nakshatra (lunar mansion).

    Args:
        nakshatra: Nakshatra name
        pada: Quarter (1-4), optional
        ctx: MCP context for logging

    Returns:
        Nakshatra characteristics and trading implications
    """
    if ctx:
        ctx.info(f"Analyzing nakshatra: {nakshatra}")

    try:
        if nakshatra not in NAKSHATRAS:
            return {
                "success": False,
                "error": f"Invalid nakshatra. Valid options: {', '.join(NAKSHATRAS)}",
            }

        lord = NAKSHATRA_LORDS.get(nakshatra, "Unknown")

        # Nakshatra characteristics for trading
        nakshatra_traits = {
            "Ashwini": {"nature": "Mobile", "quality": "Swift", "trading": "Good for quick trades"},
            "Bharani": {"nature": "Fixed", "quality": "Fierce", "trading": "Hold positions steady"},
            "Krittika": {
                "nature": "Fixed",
                "quality": "Sharp",
                "trading": "Good for cutting losses",
            },
            "Rohini": {"nature": "Fixed", "quality": "Soft", "trading": "Favorable for growth"},
            "Mrigashira": {
                "nature": "Soft",
                "quality": "Searching",
                "trading": "Research before trading",
            },
            "Ardra": {"nature": "Soft", "quality": "Intense", "trading": "Volatile periods"},
            "Punarvasu": {
                "nature": "Movable",
                "quality": "Renewal",
                "trading": "Good for recovery trades",
            },
            "Pushya": {
                "nature": "Fixed",
                "quality": "Nourishing",
                "trading": "Excellent for accumulation",
            },
            "Ashlesha": {"nature": "Soft", "quality": "Coiling", "trading": "Be cautious of traps"},
            "Magha": {
                "nature": "Fixed",
                "quality": "Royal",
                "trading": "Good for established positions",
            },
            "Purva Phalguni": {
                "nature": "Fixed",
                "quality": "Union",
                "trading": "Partnership favorable",
            },
            "Uttara Phalguni": {
                "nature": "Fixed",
                "quality": "Prosperity",
                "trading": "Good for long-term",
            },
            "Hasta": {
                "nature": "Movable",
                "quality": "Skill",
                "trading": "Technical analysis works well",
            },
            "Chitra": {
                "nature": "Movable",
                "quality": "Design",
                "trading": "Pattern recognition favorable",
            },
            "Swati": {
                "nature": "Movable",
                "quality": "Independent",
                "trading": "Contrarian strategies work",
            },
            "Vishakha": {
                "nature": "Movable",
                "quality": "Split",
                "trading": "Beware of indecision",
            },
            "Anuradha": {
                "nature": "Movable",
                "quality": "Devotion",
                "trading": "Stick to strategy",
            },
            "Jyeshtha": {
                "nature": "Movable",
                "quality": "Senior",
                "trading": "Respect market elders/trends",
            },
            "Mula": {"nature": "Fixed", "quality": "Root", "trading": "Find root causes of moves"},
            "Purva Ashadha": {
                "nature": "Fixed",
                "quality": "Invincible",
                "trading": "Strong momentum periods",
            },
            "Uttara Ashadha": {
                "nature": "Fixed",
                "quality": "Universal",
                "trading": "Broad market moves",
            },
            "Shravana": {
                "nature": "Movable",
                "quality": "Listening",
                "trading": "Pay attention to news",
            },
            "Dhanishta": {
                "nature": "Movable",
                "quality": "Wealth",
                "trading": "Good for wealth building",
            },
            "Shatabhisha": {
                "nature": "Movable",
                "quality": "Hundred",
                "trading": "Diversification favored",
            },
            "Purva Bhadrapada": {
                "nature": "Fixed",
                "quality": "Fiery",
                "trading": "Intense market moves",
            },
            "Uttara Bhadrapada": {
                "nature": "Fixed",
                "quality": "Water",
                "trading": "Emotional control needed",
            },
            "Revati": {"nature": "Soft", "quality": "Wealth", "trading": "Nurturing positions"},
        }

        traits = nakshatra_traits.get(
            nakshatra, {"nature": "Unknown", "quality": "Unknown", "trading": "Unknown"}
        )

        pada_traits = {
            1: "Dharma - Purpose/Righteousness. Focus on fundamental value.",
            2: "Artha - Wealth/Resources. Focus on financial gain.",
            3: "Kama - Desires/Pleasure. Focus on momentum/trends.",
            4: "Moksha - Liberation. Focus on exit/take profits.",
        }

        return {
            "success": True,
            "result": {
                "nakshatra": nakshatra,
                "pada": pada,
                "lord": lord,
                "nature": traits["nature"],
                "quality": traits["quality"],
                "trading_implication": traits["trading"],
                "pada_meaning": pada_traits.get(pada, "Unknown pada"),
                "symbolism": _get_nakshatra_symbolism(nakshatra),
                "best_for": _get_nakshatra_best_for(nakshatra),
            },
        }

    except Exception as e:
        logger.error(f"Nakshatra analysis failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedic_calculate_transits(
    date: str, symbols: list[str] | None = None, ctx=None
) -> dict[str, Any]:
    """
    Calculate planetary transits (Gochara) for a given date.

    Analyzes current planetary positions and their aspects to predict
    market conditions.

    Args:
        date: Date for transit calculation (YYYY-MM-DD)
        symbols: List of asset symbols to analyze (optional)
        ctx: MCP context for logging

    Returns:
        Transit analysis with trading predictions
    """
    if ctx:
        ctx.info(f"Calculating transits for {date}")

    try:
        # In production, this would use Swiss Ephemeris
        # For now, return mock data structure

        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        signs = [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]

        # Generate mock transit data
        # In production: Use actual ephemeris calculation
        transit_data = []

        import random

        random.seed(date)  # Deterministic for same date

        for planet in planets:
            sign_idx = random.randint(0, 11)
            degree = random.uniform(0, 30)

            transit_data.append(
                {
                    "planet": planet,
                    "sign": signs[sign_idx],
                    "degree": round(degree, 2),
                    "retrograde": random.random() < 0.1,  # 10% chance retrograde
                    "house": (sign_idx % 12) + 1,
                    "aspects": _calculate_mock_aspects(planet, sign_idx),
                }
            )

        # Calculate market prediction based on transits
        next((t for t in transit_data if t["planet"] == "Jupiter"), None)
        next((t for t in transit_data if t["planet"] == "Saturn"), None)

        market_sentiment = _analyze_market_sentiment(transit_data)

        if ctx:
            ctx.info(f"Transit analysis complete. Sentiment: {market_sentiment['overall']}")

        return {
            "success": True,
            "result": {
                "date": date,
                "planetary_positions": transit_data,
                "market_sentiment": market_sentiment,
                "key_aspects": _extract_key_aspects(transit_data),
                "favorable_for": market_sentiment["favorable_for"],
                "caution_for": market_sentiment["caution_for"],
                "symbols_analyzed": symbols or ["BTC", "ETH", "SPY"],
            },
        }

    except Exception as e:
        logger.error(f"Transit calculation failed: {e}")
        return {"success": False, "error": str(e)}


def _get_dasha_interpretation(planet: str) -> str:
    """Get trading interpretation for a dasha planet."""
    interpretations = {
        "Ketu": "Spiritual growth, detachment from material. Reduce positions.",
        "Venus": "Wealth accumulation, luxury. Good for growth stocks.",
        "Sun": "Authority, government influence. Watch regulatory news.",
        "Moon": "Emotional cycles, public sentiment. Follow crowd wisely.",
        "Mars": "Energy, aggression, conflict. High volatility period.",
        "Rahu": "Obsession, foreign influences. Beware of illusions.",
        "Jupiter": "Wisdom, expansion, luck. Excellent for growth.",
        "Saturn": "Restriction, discipline, lessons. Conservative approach.",
        "Mercury": "Communication, trading, intellect. Good for trading.",
    }
    return interpretations.get(planet, "Neutral period")


def _get_nakshatra_symbolism(nakshatra: str) -> str:
    """Get symbolic meaning of nakshatra."""
    symbolism = {
        "Ashwini": "Horse head - Speed, healing, beginnings",
        "Bharani": "Yoni - Bearance, nurturing, transformation",
        "Krittika": "Razor - Cutting, purification, criticism",
        "Rohini": "Chariot - Growth, fertility, stability",
        "Mrigashira": "Deer head - Searching, seeking, wandering",
        "Ardra": "Teardrop - Emotional intensity, storms",
        "Punarvasu": "Quiver of arrows - Renewal, return, repetition",
        "Pushya": "Flower - Nourishment, supporting, thriving",
        "Ashlesha": "Serpent - Coiling, binding, poisonous",
        "Magha": "Royal throne - Ancestors, power, prestige",
        "Purva Phalguni": "Front legs of bed - Union, creation, pleasure",
        "Uttara Phalguni": "Back legs of bed - Prosperity, patronage",
        "Hasta": "Hand - Skill, craftsmanship, grasping",
        "Chitra": "Jewel/Pearl - Design, architecture, illusion",
        "Swati": "Coral/Sapphire - Independence, self-going",
        "Vishakha": "Triumphant arch - Achievement, split nature",
        "Anuradha": "Arch of triumph - Devotion, friendship",
        "Jyeshtha": "Earring/Umbrella - Authority, seniority, protection",
        "Mula": "Root - Destruction, uprooting, foundation",
        "Purva Ashadha": "Elephant tusk/bed - Invincibility, victory",
        "Uttara Ashadha": "Elephant tusk - Universal achievement",
        "Shravana": "Ear - Listening, learning, gossip",
        "Dhanishta": "Drum - Wealth, music, rhythm",
        "Shatabhisha": "100 physicians - Healing, secrets, circles",
        "Purva Bhadrapada": "Front of funeral cot - Fire, purification",
        "Uttara Bhadrapada": "Back of funeral cot - Water, wisdom, finality",
        "Revati": "Drum/Fish - Wealth, nourishment, completion",
    }
    return symbolism.get(nakshatra, "Unknown")


def _get_nakshatra_best_for(nakshatra: str) -> list[str]:
    """Get what activities are best for this nakshatra."""
    best_for = {
        "Ashwini": ["Quick trades", "Starting new positions", "Healing portfolio"],
        "Bharani": ["Holding positions", "Transformation strategies", "Research"],
        "Krittika": ["Cutting losses", "Sharp entry/exit", "Analysis"],
        "Rohini": ["Long-term holdings", "Growth stocks", "Accumulation"],
        "Mrigashira": ["Searching opportunities", "Diversification", "Research"],
        "Ardra": ["Volatility trading", "Options", "Hedging"],
        "Punarvasu": ["Recovery trades", "Renewal strategies", "DCA"],
        "Pushya": ["Accumulation", "Nurturing positions", "Dividend stocks"],
        "Ashlesha": ["Defensive strategies", "Risk management", "Exits"],
        "Magha": ["Established positions", "Blue chips", "Authority plays"],
        "Purva Phalguni": ["Partnership trades", "Joint ventures", "Social trading"],
        "Uttara Phalguni": ["Long-term investments", "Prosperity plays", "ETFs"],
        "Hasta": ["Technical trading", "Pattern recognition", "Skill-based"],
        "Chitra": ["Design strategies", "Pattern trades", "Aesthetic plays"],
        "Swati": ["Contrarian trading", "Independent analysis", "Solo decisions"],
        "Vishakha": ["Scalping", "Quick decisions", "Ambition plays"],
        "Anuradha": ["Sticking to strategy", "Disciplined trading", "Devotion"],
        "Jyeshtha": ["Following trends", "Senior markets", "Respect momentum"],
        "Mula": ["Root cause analysis", "Fundamental plays", "Uprooting bad positions"],
        "Purva Ashadha": ["Momentum trading", "Invincible plays", "Strength"],
        "Uttara Ashadha": ["Universal plays", "Broad market", "Index funds"],
        "Shravana": ["News-based trading", "Listening to market", "Education"],
        "Dhanishta": ["Wealth building", "Rhythm trading", "Systematic"],
        "Shatabhisha": ["Diversification", "Portfolio balance", "Healing"],
        "Purva Bhadrapada": ["Intense plays", "Fire strategies", "Purification"],
        "Uttara Bhadrapada": ["Water plays", "Emotional control", "Wisdom"],
        "Revati": ["Nurturing", "Completion", "Final exits/entries"],
    }
    return best_for.get(nakshatra, ["General trading"])


def _calculate_mock_aspects(planet: str, sign_idx: int) -> list[dict]:
    """Calculate mock aspects for demonstration."""
    aspects = []

    # Different planets have different aspect patterns
    if planet in ["Mars", "Jupiter", "Saturn"]:
        # These planets cast special aspects
        aspect_signs = [(sign_idx + 4) % 12, (sign_idx + 7) % 12, (sign_idx + 8) % 12]
        for aspect_sign in aspect_signs:
            aspects.append(
                {"aspected_sign": aspect_sign, "aspect_type": f"{planet}_special", "orb": 5.0}
            )

    # All planets aspect 7th house (opposition)
    opposition = (sign_idx + 6) % 12
    aspects.append({"aspected_sign": opposition, "aspect_type": "opposition", "orb": 8.0})

    return aspects


def _analyze_market_sentiment(transit_data: list[dict]) -> dict[str, Any]:
    """Analyze market sentiment based on transits."""
    bullish_indicators = 0
    bearish_indicators = 0

    for planet in transit_data:
        # Simplified rules for demonstration
        if planet["planet"] == "Jupiter":
            if planet["sign"] in ["Cancer", "Sagittarius", "Pisces"]:
                bullish_indicators += 2
            elif planet["sign"] in ["Capricorn", "Gemini", "Virgo"]:
                bearish_indicators += 1

        if planet["planet"] == "Saturn":
            if planet["sign"] in ["Capricorn", "Aquarius", "Libra"]:
                bearish_indicators += 1
            elif planet["retrograde"]:
                bullish_indicators += 1  # Retrograde Saturn less restrictive

        if planet["planet"] == "Mars":
            if planet["sign"] in ["Aries", "Scorpio", "Capricorn"]:
                bullish_indicators += 1  # Strong Mars

    if bullish_indicators > bearish_indicators + 2:
        sentiment = "bullish"
    elif bearish_indicators > bullish_indicators + 2:
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    return {
        "overall": sentiment,
        "bullish_score": bullish_indicators,
        "bearish_score": bearish_indicators,
        "favorable_for": (
            ["growth stocks", "tech"] if sentiment == "bullish" else ["defensive", "utilities"]
        ),
        "caution_for": ["speculative"] if sentiment == "bearish" else ["aggressive shorts"],
    }


def _extract_key_aspects(transit_data: list[dict]) -> list[dict]:
    """Extract important aspects from transit data."""
    key_aspects = []

    # Find conjunctions (planets in same sign)
    positions = {}
    for planet in transit_data:
        sign = planet["sign"]
        if sign not in positions:
            positions[sign] = []
        positions[sign].append(planet["planet"])

    for sign, planets in positions.items():
        if len(planets) > 1:
            key_aspects.append(
                {
                    "type": "conjunction",
                    "planets": planets,
                    "sign": sign,
                    "significance": "high" if len(planets) > 2 else "medium",
                }
            )

    return key_aspects[:5]  # Return top 5
