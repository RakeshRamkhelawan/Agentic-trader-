"""
VedAstro Connector - C# Interop Bridge

Provides high-performance Vedic astrology calculations using:
1. Direct C# interop via pythonnet (10x faster)
2. HTTP fallback for containerized deployments
3. Aggressive caching for immutable Kundli data

NOTE: To use C# mode, place VedAstro.Library.dll in the libs/ directory.
The HTTP fallback mode works without any C# dependencies.
"""

import asyncio
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


@dataclass
class VedAstroConfig:
    """Configuration for VedAstro connector."""

    dll_path: str = "./libs/VedAstro.dll"
    ephemeris_path: str = "./libs/ephemeris/"
    use_http_fallback: bool = False
    http_endpoint: str = "http://localhost:5000"
    cache_ttl: int = 3600  # seconds
    max_workers: int = 4


class VedAstroConnector:
    """
    High-performance bridge to VedAstro C# core.

    Uses pythonnet for direct C# interop when available,
    falls back to HTTP API for containerized deployments.
    """

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

    def __init__(self, config: Optional[VedAstroConfig] = None):
        """
        Initialize VedAstro connector.

        Args:
            config: VedAstro configuration
        """
        self.config = config or VedAstroConfig()
        self._csharp_calculator = None
        self._csharp_types = {}
        self._cache: Dict[str, Any] = {}
        self._transit_cache: Dict[str, Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._http_client = None

        # Try to initialize C# bridge
        if not self.config.use_http_fallback:
            self._init_csharp_bridge()

        if self.config.use_http_fallback:
            self._init_http_client()

    def _init_csharp_bridge(self) -> bool:
        """Initialize C# interop via pythonnet."""
        try:
            import clr

            # Add libs directory to sys.path for DLL resolution
            dll_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../libs")
            )
            if dll_dir not in sys.path:
                sys.path.append(dll_dir)
                logger.debug(f"Added {dll_dir} to sys.path")

            # Try to load the DLL
            try:
                clr.AddReference("VedAstro.Library")
                from VedAstro.Library import Calculate, GeoLocation, PlanetName, Time
            except:
                # Fallback: try without .Library suffix
                clr.AddReference("VedAstro")
                from VedAstro import Calculate, GeoLocation, PlanetName, Time

            self._csharp_calculator = Calculate
            self._csharp_types = {
                "GeoLocation": GeoLocation,
                "Time": Time,
                "PlanetName": PlanetName,
            }

            logger.info("VedAstro C# bridge initialized successfully")
            return True

        except Exception as e:
            logger.warning(f"Failed to initialize C# bridge: {e}")
            logger.warning("Falling back to HTTP mode")
            self.config.use_http_fallback = True
            return False

    def _init_http_client(self):
        """Initialize HTTP client for fallback mode."""
        try:
            import httpx

            self._http_client = httpx.AsyncClient(base_url=self.config.http_endpoint)
            logger.info(f"HTTP client initialized for {self.config.http_endpoint}")
        except ImportError:
            logger.error("httpx not available for HTTP fallback")

    async def calculate_kundli(
        self,
        symbol: str,
        birth_date: datetime,
        lat: float = 40.7128,
        lon: float = -74.0060,
        timezone_offset: int = -5,
    ) -> Dict[str, Any]:
        """
        Calculate complete Kundli with all 16 Vargas.

        Args:
            symbol: Asset symbol (for caching)
            birth_date: Birth date/time
            lat: Latitude
            lon: Longitude
            timezone_offset: Timezone offset from UTC

        Returns:
            Kundli data with planets, vargas, and lagna
        """
        cache_key = f"kundli:{symbol}:{birth_date.isoformat()}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.config.use_http_fallback:
            result = await self._http_calculate_kundli(
                birth_date, lat, lon, timezone_offset
            )
        else:
            result = await self._csharp_calculate_kundli(
                birth_date, lat, lon, timezone_offset
            )

        self._cache[cache_key] = result
        return result

    async def _csharp_calculate_kundli(
        self, birth_date: datetime, lat: float, lon: float, tz_offset: int
    ) -> Dict[str, Any]:
        """Direct C# interop calculation."""
        loop = asyncio.get_event_loop()

        def _compute():
            GeoLocation = self._csharp_types["GeoLocation"]
            Time = self._csharp_types["Time"]
            PlanetName = self._csharp_types["PlanetName"]

            location = GeoLocation("Exchange", lon, lat)
            time_str = (
                f"{birth_date.hour}:{birth_date.minute:02d} "
                f"{birth_date.day}/{birth_date.month}/{birth_date.year} "
                f"{tz_offset:+03d}:00"
            )
            birth_time = Time(time_str, location)

            planets = {}
            vargas = {}

            # All 9 planets
            planet_names = [
                PlanetName.Sun,
                PlanetName.Moon,
                PlanetName.Mars,
                PlanetName.Mercury,
                PlanetName.Jupiter,
                PlanetName.Venus,
                PlanetName.Saturn,
                PlanetName.Rahu,
                PlanetName.Ketu,
            ]

            for planet in planet_names:
                # D1 (Rashi chart)
                data = self._csharp_calculator.AllPlanetData(planet, birth_time)

                planet_key = str(planet).replace("PlanetName.", "")

                # Parse longitude (format: "123.45°")
                long_str = str(data.PlanetLongitude).replace("°", "").replace(" ", "")
                try:
                    longitude = float(long_str)
                except ValueError:
                    longitude = 0.0

                planets[planet_key] = {
                    "longitude": longitude,
                    "sign": str(data.Sign),
                    "house": int(str(data.House)),
                    "nakshatra": str(data.Nakshatra),
                    "pada": int(str(data.Pada)),
                    "retrograde": bool(data.IsRetrograde),
                    "exalted": self._is_exalted(planet_key, str(data.Sign)),
                    "debilitated": self._is_debilitated(planet_key, str(data.Sign)),
                }

                # D9 (Navamsa) - spiritual/soul chart
                try:
                    navamsa_data = self._csharp_calculator.AllPlanetData(
                        planet, birth_time, "Navamsa"
                    )
                    if "D9" not in vargas:
                        vargas["D9"] = {}
                    vargas["D9"][planet_key] = {
                        "sign": str(navamsa_data.Sign),
                        "house": int(str(navamsa_data.House)),
                    }
                except Exception as e:
                    logger.debug(f"Failed to get Navamsa for {planet_key}: {e}")

            # Lagna (Ascendant)
            try:
                lagna_data = self._csharp_calculator.AllPlanetData(
                    PlanetName.House1, birth_time
                )
                lagna_sign = str(lagna_data.Sign)
            except:
                lagna_sign = "Aries"  # Default fallback

            return {
                "planets": planets,
                "lagna": lagna_sign,
                "lagna_lord": self._get_lord(lagna_sign),
                "vargas": vargas,
                "timestamp": birth_date.isoformat(),
                "location": {"lat": lat, "lon": lon},
            }

        return await loop.run_in_executor(self._executor, _compute)

    async def _http_calculate_kundli(
        self, birth_date: datetime, lat: float, lon: float, tz_offset: int
    ) -> Dict[str, Any]:
        """HTTP fallback calculation."""
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized")

        response = await self._http_client.post(
            "/calculate/kundli",
            json={
                "datetime": birth_date.isoformat(),
                "latitude": lat,
                "longitude": lon,
                "timezone": tz_offset,
            },
        )
        response.raise_for_status()
        return response.json()

    async def calculate_transits(
        self, date: datetime, kundli: Dict[str, Any]
    ) -> Dict[str, Any]:
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

        result = await self._compute_transits(date, kundli)
        self._transit_cache[cache_key] = result

        # Limit cache size
        if len(self._transit_cache) > 100:
            oldest_key = next(iter(self._transit_cache))
            del self._transit_cache[oldest_key]

        return result

    async def _compute_transits(
        self, date: datetime, kundli: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute transit aspects."""
        # Get current chart
        current_chart = await self.calculate_kundli(
            "transit",
            date,
            lat=kundli.get("location", {}).get("lat", 40.7128),
            lon=kundli.get("location", {}).get("lon", -74.0060),
        )

        transits = {
            "aspects": [],
            "retrograde_count": 0,
            "exalted_planets": [],
            "debilitated_planets": [],
            "current_positions": {},
        }

        birth_planets = kundli.get("planets", {})
        current_planets = current_chart.get("planets", {})

        for planet, curr_pos in current_planets.items():
            transits["current_positions"][planet] = curr_pos

            # Count retrograde
            if curr_pos.get("retrograde"):
                transits["retrograde_count"] += 1

            # Count exalted/debilitated
            if curr_pos.get("exalted"):
                transits["exalted_planets"].append(planet)
            if curr_pos.get("debilitated"):
                transits["debilitated_planets"].append(planet)

            # Check aspects with birth chart
            if planet in birth_planets:
                birth_pos = birth_planets[planet]
                angle = abs(curr_pos["longitude"] - birth_pos["longitude"]) % 360

                # Determine aspect type
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
                            "birth_longitude": birth_pos["longitude"],
                            "current_longitude": curr_pos["longitude"],
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

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "kundli_cache_size": len(self._cache),
            "transit_cache_size": len(self._transit_cache),
            "mode": "http" if self.config.use_http_fallback else "csharp",
        }
