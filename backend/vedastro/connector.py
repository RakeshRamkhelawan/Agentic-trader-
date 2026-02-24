"""
VedAstro Connector - Real Astronomical Data via Swiss Ephemeris

Provides high-performance Vedic astrology calculations using:
1. Swiss Ephemeris (pyswisseph) - industry standard, 100% local
2. Lahiri Ayanamsa for accurate Vedic positions
3. Real planetary positions (not mock data)

This replaces the previous C# pythonnet approach which had compilation issues.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Swiss Ephemeris - industry standard astronomical calculations
import swisseph as swe

logger = logging.getLogger(__name__)

# Set Lahiri Ayanamsa (standard for Vedic astrology)
swe.set_sid_mode(swe.SIDM_LAHIRI)


@dataclass
class VedAstroConfig:
    """Configuration for VedAstro connector."""

    cache_ttl: int = 3600  # seconds
    max_workers: int = 4
    lat: float = 40.7128  # Default: New York
    lon: float = -74.0060


class VedAstroConnector:
    """
    Real Vedic astrology calculations using Swiss Ephemeris.

    No mock data - all calculations use actual astronomical positions.
    """

    # Planet mappings to Swiss Ephemeris constants
    PLANETS = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.TRUE_NODE,  # Mean node is swe.MEAN_NODE
        "Ketu": swe.TRUE_NODE,  # Will be calculated as opposite of Rahu
    }

    # Zodiac signs
    SIGNS = [
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

    # Exaltation signs for planets
    EXALTATIONS = {
        "Sun": "Aries",
        "Moon": "Taurus",
        "Mars": "Capricorn",
        "Mercury": "Virgo",
        "Jupiter": "Cancer",
        "Venus": "Pisces",
        "Saturn": "Libra",
    }

    # Debilitation signs
    DEBILITATIONS = {
        "Sun": "Libra",
        "Moon": "Scorpio",
        "Mars": "Cancer",
        "Mercury": "Pisces",
        "Jupiter": "Capricorn",
        "Venus": "Virgo",
        "Saturn": "Aries",
    }

    # Sign lords
    SIGN_LORDS = {
        "Aries": "Mars",
        "Taurus": "Venus",
        "Gemini": "Mercury",
        "Cancer": "Moon",
        "Leo": "Sun",
        "Virgo": "Mercury",
        "Libra": "Venus",
        "Scorpio": "Mars",
        "Sagittarius": "Jupiter",
        "Capricorn": "Saturn",
        "Aquarius": "Saturn",
        "Pisces": "Jupiter",
    }

    # Nakshatras (27 lunar mansions)
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

    def __init__(self, config: VedAstroConfig | None = None):
        """
        Initialize VedAstro connector with Swiss Ephemeris.

        Args:
            config: VedAstro configuration
        """
        self.config = config or VedAstroConfig()
        self._cache: dict[str, Any] = {}
        self._transit_cache: dict[str, Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

        logger.info("VedAstro connector initialized with Swiss Ephemeris (Lahiri Ayanamsa)")

    def _datetime_to_jd(self, dt: datetime) -> float:
        """Convert Python datetime to Julian Day."""
        return swe.julday(
            dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        )

    def _get_sidereal_position(self, jd: float, planet: int) -> tuple:
        """
        Get sidereal (Vedic) position for a planet.

        Returns:
            (longitude, latitude, distance, speed)
        """
        # Calculate tropical position
        result = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)
        tropical_long = result[0][0]

        # Convert to sidereal (Lahiri ayanamsa already set)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        sidereal_long = (tropical_long - ayanamsa) % 360

        return sidereal_long, result[0][1], result[0][2], result[0][3]

    def _longitude_to_sign(self, longitude: float) -> str:
        """Convert longitude to zodiac sign."""
        sign_index = int(longitude / 30) % 12
        return self.SIGNS[sign_index]

    def _longitude_to_nakshatra(self, longitude: float) -> tuple:
        """
        Convert longitude to nakshatra and pada.

        Returns:
            (nakshatra_name, pada_number)
        """
        # Each nakshatra is 13°20' (13.333... degrees)
        nakshatra_index = int(longitude / (360 / 27)) % 27
        nakshatra = self.NAKSHATRAS[nakshatra_index]

        # Each pada is 3°20' (3.333... degrees)
        pada = int((longitude % (360 / 27)) / (360 / 108)) + 1

        return nakshatra, pada

    def _get_house(self, lagna_long: float, planet_long: float) -> int:
        """Calculate house position relative to lagna."""
        diff = (planet_long - lagna_long) % 360
        house = int(diff / 30) + 1
        return house

    def _is_retrograde(self, speed: float) -> bool:
        """Check if planet is retrograde based on speed."""
        return speed < 0

    async def calculate_kundli(
        self,
        symbol: str,
        birth_date: datetime,
        lat: float = 40.7128,
        lon: float = -74.0060,
        timezone_offset: int = -5,
    ) -> dict[str, Any]:
        """
        Calculate complete Kundli with real astronomical data.

        Args:
            symbol: Asset symbol (for caching)
            birth_date: Birth date/time
            lat: Latitude
            lon: Longitude
            timezone_offset: Timezone offset from UTC

        Returns:
            Kundli data with REAL planet positions, vargas, and lagna
        """
        cache_key = f"kundli:{symbol}:{birth_date.isoformat()}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Run calculation in thread pool (swe is not async)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor, self._compute_kundli, birth_date, lat, lon
        )

        self._cache[cache_key] = result
        return result

    def _compute_kundli(self, birth_date: datetime, lat: float, lon: float) -> dict[str, Any]:
        """Synchronous kundli calculation."""
        # Convert to Julian Day (UTC)
        jd = self._datetime_to_jd(birth_date)

        # Calculate Lagna (Ascendant)
        # swe.houses_ex calculates houses, ascendant is first house cusp
        houses = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
        lagna_long = houses[1][0]  # Ascendant longitude
        lagna_sign = self._longitude_to_sign(lagna_long)

        planets = {}
        vargas = {"D9": {}}  # Navamsa

        for planet_name, planet_id in self.PLANETS.items():
            # Special handling for Ketu (opposite of Rahu)
            if planet_name == "Ketu":
                rahu_long = planets.get("Rahu", {}).get("longitude", 0)
                longitude = (rahu_long + 180) % 360
                latitude = 0
                distance = 0
                speed = -planets.get("Rahu", {}).get("speed", 0)
            else:
                longitude, latitude, distance, speed = self._get_sidereal_position(jd, planet_id)

            sign = self._longitude_to_sign(longitude)
            house = self._get_house(lagna_long, longitude)
            nakshatra, pada = self._longitude_to_nakshatra(longitude)

            planets[planet_name] = {
                "longitude": longitude,
                "latitude": latitude,
                "sign": sign,
                "house": house,
                "nakshatra": nakshatra,
                "pada": pada,
                "retrograde": self._is_retrograde(speed),
                "exalted": self._is_exalted(planet_name, sign),
                "debilitated": self._is_debilitated(planet_name, sign),
                "speed": speed,
            }

            # Calculate D9 (Navamsa) position
            # Navamsa: each sign divided into 9 parts of 3°20' each
            navamsa_index = int((longitude % 30) / (30 / 9))
            # For fiery signs (Aries, Leo, Sag), navamsa starts from Aries
            # For earthy signs, from Cancer
            # For airy signs, from Libra
            # For watery signs, from Capricorn
            sign_elemental_start = {
                "Aries": 0,
                "Leo": 0,
                "Sagittarius": 0,
                "Taurus": 3,
                "Virgo": 3,
                "Capricorn": 3,
                "Gemini": 6,
                "Libra": 6,
                "Aquarius": 6,
                "Cancer": 9,
                "Scorpio": 9,
                "Pisces": 9,
            }
            navamsa_sign_index = (sign_elemental_start.get(sign, 0) + navamsa_index) % 12
            navamsa_sign = self.SIGNS[navamsa_sign_index]

            vargas["D9"][planet_name] = {
                "sign": navamsa_sign,
                "house": self._get_house(lagna_long, navamsa_sign_index * 30 + 15),
            }

        return {
            "planets": planets,
            "lagna": lagna_sign,
            "lagna_lord": self._get_lord(lagna_sign),
            "lagna_longitude": lagna_long,
            "vargas": vargas,
            "timestamp": birth_date.isoformat(),
            "location": {"lat": lat, "lon": lon},
            "ayanamsa": swe.get_ayanamsa_ut(jd),
        }

    async def calculate_transits(self, date: datetime, kundli: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate current transits vs birth chart.

        Args:
            date: Current date/time
            kundli: Birth chart (Kundli)

        Returns:
            Transit data with aspects and planetary states
        """
        cache_key = f"transit:{date.strftime('%Y%m%d%H')}"

        if cache_key in self._transit_cache:
            return self._transit_cache[cache_key]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor, self._compute_transits_sync, date, kundli
        )

        self._transit_cache[cache_key] = result

        # Limit cache size
        if len(self._transit_cache) > 100:
            oldest_key = next(iter(self._transit_cache))
            del self._transit_cache[oldest_key]

        return result

    def _compute_transits_sync(self, date: datetime, kundli: dict[str, Any]) -> dict[str, Any]:
        """Synchronous transit calculation."""
        jd = self._datetime_to_jd(date)

        # Get lagna from kundli or recalculate
        lagna_long = kundli.get("lagna_longitude", 0)

        transits = {
            "aspects": [],
            "retrograde_count": 0,
            "exalted_planets": [],
            "debilitated_planets": [],
            "current_positions": {},
        }

        birth_planets = kundli.get("planets", {})
        current_planets = {}

        for planet_name, planet_id in self.PLANETS.items():
            if planet_name == "Ketu":
                rahu_long = current_planets.get("Rahu", {}).get("longitude", 0)
                longitude = (rahu_long + 180) % 360
                speed = -current_planets.get("Rahu", {}).get("speed", 0)
            else:
                longitude, _, _, speed = self._get_sidereal_position(jd, planet_id)

            house = self._get_house(lagna_long, longitude)
            sign = self._longitude_to_sign(longitude)

            current_planets[planet_name] = {
                "longitude": longitude,
                "sign": sign,
                "house": house,
                "retrograde": self._is_retrograde(speed),
                "exalted": self._is_exalted(planet_name, sign),
                "debilitated": self._is_debilitated(planet_name, sign),
            }

        transits["current_positions"] = current_planets

        # Count retrogrades and dignities
        for planet, pos in current_planets.items():
            if pos.get("retrograde"):
                transits["retrograde_count"] += 1
            if pos.get("exalted"):
                transits["exalted_planets"].append(planet)
            if pos.get("debilitated"):
                transits["debilitated_planets"].append(planet)

        # Check aspects with birth chart
        for planet, curr_pos in current_planets.items():
            if planet in birth_planets:
                birth_pos = birth_planets[planet]
                birth_long = birth_pos.get("longitude", 0)
                curr_long = curr_pos["longitude"]

                angle = abs(curr_long - birth_long) % 360

                aspect_type = None
                orb = 0

                if angle <= 10 or angle >= 350:
                    aspect_type = "conjunction"
                    orb = min(angle, 360 - angle)
                elif 55 <= angle <= 65:
                    aspect_type = "sextile"
                    orb = abs(60 - angle)
                elif 85 <= angle <= 95:
                    aspect_type = "square"
                    orb = abs(90 - angle)
                elif 115 <= angle <= 125:
                    aspect_type = "trine"
                    orb = abs(120 - angle)
                elif 175 <= angle <= 185:
                    aspect_type = "opposition"
                    orb = abs(180 - angle)

                if aspect_type and orb <= 10:
                    transits["aspects"].append(
                        {
                            "planet": planet,
                            "type": aspect_type,
                            "angle": angle,
                            "orb": orb,
                            "birth_longitude": birth_long,
                            "current_longitude": curr_long,
                        }
                    )

        return transits

    def _is_exalted(self, planet: str, sign: str) -> bool:
        """Check if planet is exalted in sign."""
        return self.EXALTATIONS.get(planet) == sign

    def _is_debilitated(self, planet: str, sign: str) -> bool:
        """Check if planet is debilitated in sign."""
        return self.DEBILITATIONS.get(planet) == sign

    def _get_lord(self, sign: str) -> str:
        """Get lord of sign."""
        return self.SIGN_LORDS.get(sign, "Unknown")

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._cache.clear()
        self._transit_cache.clear()
        logger.info("VedAstro caches cleared")

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "kundli_cache_size": len(self._cache),
            "transit_cache_size": len(self._transit_cache),
            "mode": "pyswisseph",
        }
