"""
Enhanced VedAstro Connector - Swiss Ephemeris + Advanced Vedic Features

Extends the base connector with:
1. Ashtakavarga (Bindu scoring)
2. Vimshottari Dasha
3. Sahams (Financial points)
4. Enhanced Gochara with obstructies
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import swisseph as swe

from .connector import VedAstroConfig, VedAstroConnector

logger = logging.getLogger(__name__)


@dataclass
class DashaInfo:
    """Vimshottari Dasha information."""

    mahadasha_lord: str
    mahadasha_start: datetime
    mahadasha_end: datetime
    antardasha_lord: str
    antardasha_start: datetime
    antardasha_end: datetime
    pratyantardasha_lord: str


class EnhancedVedAstroConnector(VedAstroConnector):
    """
    Enhanced connector with advanced Vedic features.
    """

    # Vimshottari Dasha planet years
    DASHA_YEARS = {
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

    DASHA_SEQUENCE = [
        "Ketu",
        "Venus",
        "Sun",
        "Moon",
        "Mars",
        "Rahu",
        "Jupiter",
        "Saturn",
        "Mercury",
    ]

    # Ashtakavarga - Benefic positions for each planet
    # Format: Planet: {SignIndex: [benefic_house_positions_from_planet]}
    ASHTAKAVARGA_POINTS = {
        "Sun": {
            0: [1, 2, 4, 7, 8, 9, 10, 11],
            1: [1, 2, 4, 7, 8, 9, 10, 11],
            2: [3, 5, 6, 10],
            3: [3, 5, 6, 10],
            4: [1, 2, 4, 7, 8, 9, 10, 11],
            5: [3, 5, 6, 10],
            6: [3, 5, 6, 10],
            7: [1, 2, 4, 7, 8, 9, 10, 11],
            8: [1, 2, 4, 7, 8, 9, 10, 11],
            9: [1, 2, 4, 7, 8, 9, 10, 11],
            10: [3, 5, 6, 10],
            11: [1, 2, 4, 7, 8, 9, 10, 11],
        },
        "Moon": {
            0: [1, 3, 6, 7, 10, 11],
            1: [1, 3, 6, 7, 10, 11],
            2: [2, 3, 5, 6, 9, 10, 11],
            3: [1, 3, 6, 7, 10, 11],
            4: [1, 3, 6, 7, 10, 11],
            5: [2, 3, 5, 6, 9, 10, 11],
            6: [2, 3, 5, 6, 9, 10, 11],
            7: [1, 3, 6, 7, 10, 11],
            8: [1, 3, 6, 7, 10, 11],
            9: [1, 3, 6, 7, 10, 11],
            10: [2, 3, 5, 6, 9, 10, 11],
            11: [1, 3, 6, 7, 10, 11],
        },
        "Mars": {
            0: [1, 2, 4, 7, 8, 10, 11],
            1: [1, 2, 4, 7, 8, 10, 11],
            2: [3, 5, 6, 9, 10, 11],
            3: [3, 5, 6, 9, 10, 11],
            4: [1, 2, 4, 7, 8, 10, 11],
            5: [3, 5, 6, 9, 10, 11],
            6: [3, 5, 6, 9, 10, 11],
            7: [1, 2, 4, 7, 8, 10, 11],
            8: [1, 2, 4, 7, 8, 10, 11],
            9: [1, 2, 4, 7, 8, 10, 11],
            10: [3, 5, 6, 9, 10, 11],
            11: [1, 2, 4, 7, 8, 10, 11],
        },
        "Mercury": {
            0: [1, 3, 5, 6, 9, 10, 11, 12],
            1: [1, 3, 5, 6, 9, 10, 11, 12],
            2: [2, 4, 6, 8, 10, 11],
            3: [2, 4, 6, 8, 10, 11],
            4: [1, 3, 5, 6, 9, 10, 11, 12],
            5: [2, 4, 6, 8, 10, 11],
            6: [2, 4, 6, 8, 10, 11],
            7: [1, 3, 5, 6, 9, 10, 11, 12],
            8: [1, 3, 5, 6, 9, 10, 11, 12],
            9: [1, 3, 5, 6, 9, 10, 11, 12],
            10: [2, 4, 6, 8, 10, 11],
            11: [1, 3, 5, 6, 9, 10, 11, 12],
        },
        "Jupiter": {
            0: [1, 2, 3, 4, 7, 8, 9, 10, 11],
            1: [1, 2, 3, 4, 7, 8, 9, 10, 11],
            2: [2, 5, 7, 9, 11],
            3: [2, 5, 7, 9, 11],
            4: [1, 2, 3, 4, 7, 8, 9, 10, 11],
            5: [2, 5, 7, 9, 11],
            6: [2, 5, 7, 9, 11],
            7: [1, 2, 3, 4, 7, 8, 9, 10, 11],
            8: [1, 2, 3, 4, 7, 8, 9, 10, 11],
            9: [1, 2, 3, 4, 7, 8, 9, 10, 11],
            10: [2, 5, 7, 9, 11],
            11: [1, 2, 3, 4, 7, 8, 9, 10, 11],
        },
        "Venus": {
            0: [1, 2, 3, 4, 5, 8, 9, 10, 11],
            1: [1, 2, 3, 4, 5, 8, 9, 10, 11],
            2: [3, 5, 6, 9, 10, 11, 12],
            3: [3, 5, 6, 9, 10, 11, 12],
            4: [1, 2, 3, 4, 5, 8, 9, 10, 11],
            5: [3, 5, 6, 9, 10, 11, 12],
            6: [3, 5, 6, 9, 10, 11, 12],
            7: [1, 2, 3, 4, 5, 8, 9, 10, 11],
            8: [1, 2, 3, 4, 5, 8, 9, 10, 11],
            9: [1, 2, 3, 4, 5, 8, 9, 10, 11],
            10: [3, 5, 6, 9, 10, 11, 12],
            11: [1, 2, 3, 4, 5, 8, 9, 10, 11],
        },
        "Saturn": {
            0: [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
            1: [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
            2: [3, 5, 6, 10, 11, 12],
            3: [3, 5, 6, 10, 11, 12],
            4: [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
            5: [3, 5, 6, 10, 11, 12],
            6: [3, 5, 6, 10, 11, 12],
            7: [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
            8: [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
            9: [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
            10: [3, 5, 6, 10, 11, 12],
            11: [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
        },
    }

    def __init__(self, config: VedAstroConfig | None = None):
        super().__init__(config)
        self._dasha_cache: dict[str, Any] = {}
        self._ashtaka_cache: dict[str, Any] = {}
        logger.info("Enhanced VedAstro connector initialized")

    # ==================== ASHTAKAVARGA ====================

    def calculate_ashtakavarga(self, kundli: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate Ashtakavarga (bindu scoring) for all planets.

        Returns Bhinnashtakavarga (individual) and Sarvashtakavarga (total).
        """
        cache_key = f"ashtaka:{kundli.get('timestamp', '')}"
        if cache_key in self._ashtaka_cache:
            return self._ashtaka_cache[cache_key]

        planets = kundli.get("planets", {})
        lagna_sign_idx = self.SIGNS.index(kundli.get("lagna", "Aries"))

        # Bhinnashtakavarga - individual planet scores
        bhinnashtaka = {}
        sarvashtaka = {sign: 0 for sign in self.SIGNS}

        for planet_name in [
            "Sun",
            "Moon",
            "Mars",
            "Mercury",
            "Jupiter",
            "Venus",
            "Saturn",
        ]:
            if planet_name not in planets:
                continue

            planet_data = planets[planet_name]
            self.SIGNS.index(planet_data["sign"])

            # Get benefic positions for this planet from each sign
            planet_scores = {sign: 0 for sign in self.SIGNS}

            # Calculate from each sign's perspective
            for sign_idx, sign_name in enumerate(self.SIGNS):
                benefic_positions = self.ASHTAKAVARGA_POINTS.get(planet_name, {}).get(sign_idx, [])

                # Check each house position from this sign
                for house_pos in range(1, 13):
                    house_sign_idx = (sign_idx + house_pos - 1) % 12
                    house_sign = self.SIGNS[house_sign_idx]

                    # If planet is in a benefic house from this sign
                    if house_pos in benefic_positions:
                        # Check if any planet (including self) is in this sign
                        for p_name, p_data in planets.items():
                            if p_data["sign"] == house_sign:
                                planet_scores[house_sign] = 1
                                break

                        # Lagna also contributes
                        if lagna_sign_idx == house_sign_idx:
                            planet_scores[house_sign] = 1

            bhinnashtaka[planet_name] = planet_scores

            # Add to Sarvashtakavarga
            for sign, score in planet_scores.items():
                sarvashtaka[sign] += score

        result = {
            "bhinnashtaka": bhinnashtaka,
            "sarvashtaka": sarvashtaka,
            "total_bindu": sum(sarvashtaka.values()),
        }

        self._ashtaka_cache[cache_key] = result
        return result

    def get_gochara_bindu(
        self, birth_kundli: dict[str, Any], current_date: datetime, planet: str
    ) -> int:
        """
        Get Ashtakavarga bindu for transit (Gochara).
        Returns bindu score for planet's current position.
        """
        ashtaka = self.calculate_ashtakavarga(birth_kundli)

        # Get current transit position
        jd = self._datetime_to_jd(current_date)
        if planet == "Ketu":
            rahu_long = self._get_sidereal_position(jd, swe.TRUE_NODE)[0]
            longitude = (rahu_long + 180) % 360
        else:
            longitude = self._get_sidereal_position(jd, self.PLANETS[planet])[0]

        sign = self._longitude_to_sign(longitude)

        # Get bindu from Moon's Ashtakavarga (standard for Gochara)
        birth_kundli.get("planets", {}).get("Moon", {}).get("sign", "Aries")
        bhinnashtaka = ashtaka.get("bhinnashtaka", {})

        return bhinnashtaka.get(planet, {}).get(sign, 0)

    # ==================== VIMSHOTTARI DASHA ====================

    def calculate_vimshottari_dasha(
        self, kundli: dict[str, Any], reference_date: datetime | None = None
    ) -> DashaInfo:
        """
        Calculate Vimshottari Dasha based on Moon's position at birth.

        Returns current Mahadasha, Antardasha, and Pratyantardasha.
        """
        cache_key = f"dasha:{kundli.get('timestamp', '')}:{reference_date.isoformat() if reference_date else 'now'}"
        if cache_key in self._dasha_cache:
            return self._dasha_cache[cache_key]

        moon_data = kundli.get("planets", {}).get("Moon", {})
        moon_nakshatra = moon_data.get("nakshatra", "Ashwini")
        moon_data.get("pada", 1)

        # Nakshatra lords (same order as DASHA_SEQUENCE)
        nakshatra_lords = [
            "Ketu",
            "Venus",
            "Sun",
            "Moon",
            "Mars",
            "Rahu",
            "Jupiter",
            "Saturn",
            "Mercury",
        ] * 3  # 27 nakshatras

        nakshatra_index = self.NAKSHATRAS.index(moon_nakshatra)
        birth_lord = nakshatra_lords[nakshatra_index]

        # Calculate balance of dasha at birth
        # Each nakshatra is 13°20' = 800 minutes of arc
        # Pada is 1/4 of nakshatra = 3°20' = 200 minutes

        # Moon's longitude within nakshatra
        moon_long = moon_data.get("longitude", 0)
        nakshatra_start = nakshatra_index * (360 / 27)
        moon_in_nakshatra = (moon_long - nakshatra_start) % (360 / 27)

        # Portion remaining in birth dasha
        portion_remaining = 1 - (moon_in_nakshatra / (360 / 27))
        birth_dasha_years = self.DASHA_YEARS[birth_lord]
        balance_at_birth = portion_remaining * birth_dasha_years

        # Calculate reference date (default: now)
        ref_date = reference_date or datetime.now()
        birth_date = datetime.fromisoformat(kundli.get("timestamp", ref_date.isoformat()))
        years_elapsed = (ref_date - birth_date).days / 365.25

        # Find current Mahadasha
        years_accounted = 0
        current_maha_index = self.DASHA_SEQUENCE.index(birth_lord)

        # Account for balance at birth
        years_accounted = balance_at_birth
        if years_elapsed <= years_accounted:
            mahadasha_lord = birth_lord
            maha_start = birth_date
            maha_end = birth_date + timedelta(days=balance_at_birth * 365.25)
        else:
            years_remaining = years_elapsed - years_accounted
            while years_remaining > 0:
                current_maha_index = (current_maha_index + 1) % 9
                lord = self.DASHA_SEQUENCE[current_maha_index]
                lord_years = self.DASHA_YEARS[lord]

                if years_remaining <= lord_years:
                    mahadasha_lord = lord
                    maha_start = ref_date - timedelta(days=years_remaining * 365.25)
                    maha_end = maha_start + timedelta(days=lord_years * 365.25)
                    break
                years_remaining -= lord_years
            else:
                mahadasha_lord = self.DASHA_SEQUENCE[current_maha_index]
                maha_start = ref_date
                maha_end = ref_date + timedelta(days=self.DASHA_YEARS[mahadasha_lord] * 365.25)

        # Calculate Antardasha (Bhukti)
        antardasha = self._calculate_antardasha(mahadasha_lord, maha_start, maha_end, ref_date)

        result = DashaInfo(
            mahadasha_lord=mahadasha_lord,
            mahadasha_start=maha_start,
            mahadasha_end=maha_end,
            antardasha_lord=antardasha[0],
            antardasha_start=antardasha[1],
            antardasha_end=antardasha[2],
            pratyantardasha_lord=antardasha[3],
        )

        self._dasha_cache[cache_key] = result
        return result

    def _calculate_antardasha(
        self,
        maha_lord: str,
        maha_start: datetime,
        maha_end: datetime,
        ref_date: datetime,
    ) -> tuple[str, datetime, datetime, str]:
        """Calculate Antardasha within Mahadasha."""
        self.DASHA_YEARS[maha_lord]
        total_days = (maha_end - maha_start).days

        start_index = self.DASHA_SEQUENCE.index(maha_lord)

        days_accounted = 0
        for i in range(9):
            lord_index = (start_index + i) % 9
            lord = self.DASHA_SEQUENCE[lord_index]
            # Antardasha proportion = sub-lord years / 120 * maha years
            antardasha_days = (self.DASHA_YEARS[lord] / 120) * total_days

            ant_start = maha_start + timedelta(days=days_accounted)
            ant_end = ant_start + timedelta(days=antardasha_days)

            if ant_start <= ref_date < ant_end:
                # Calculate Pratyantardasha
                praty_lord = self._calculate_pratyantardasha(lord, ant_start, ant_end, ref_date)
                return (lord, ant_start, ant_end, praty_lord)

            days_accounted += antardasha_days

        return (maha_lord, maha_start, maha_end, maha_lord)

    def _calculate_pratyantardasha(
        self, anta_lord: str, ant_start: datetime, ant_end: datetime, ref_date: datetime
    ) -> str:
        """Calculate Pratyantardasha lord."""
        anta_days = (ant_end - ant_start).days
        start_index = self.DASHA_SEQUENCE.index(anta_lord)

        praty_days = anta_days / 9
        for i in range(9):
            lord_index = (start_index + i) % 9
            lord = self.DASHA_SEQUENCE[lord_index]
            praty_start = ant_start + timedelta(days=i * praty_days)
            praty_end = praty_start + timedelta(days=praty_days)

            if praty_start <= ref_date < praty_end:
                return lord

        return anta_lord

    # ==================== SAHAMS ====================

    def calculate_artha_saham(self, kundli: dict[str, Any]) -> float:
        """
        Calculate Artha Saham (financial prosperity point).
        Formula: Lagna + Saturn - Mars (at sunrise)
        """
        lagna_long = kundli.get("lagna_longitude", 0)
        planets = kundli.get("planets", {})
        saturn_long = planets.get("Saturn", {}).get("longitude", 0)
        mars_long = planets.get("Mars", {}).get("longitude", 0)

        artha_saham = (lagna_long + saturn_long - mars_long) % 360
        return artha_saham

    def calculate_all_sahams(self, kundli: dict[str, Any]) -> dict[str, float]:
        """
        Calculate all important Sahams.
        """
        lagna_long = kundli.get("lagna_longitude", 0)
        planets = kundli.get("planets", {})

        saturn_long = planets.get("Saturn", {}).get("longitude", 0)
        mars_long = planets.get("Mars", {}).get("longitude", 0)
        mercury_long = planets.get("Mercury", {}).get("longitude", 0)
        jupiter_long = planets.get("Jupiter", {}).get("longitude", 0)
        venus_long = planets.get("Venus", {}).get("longitude", 0)
        sun_long = planets.get("Sun", {}).get("longitude", 0)
        moon_long = planets.get("Moon", {}).get("longitude", 0)

        return {
            "artha": (lagna_long + saturn_long - mars_long) % 360,  # Wealth
            "labha": (lagna_long + saturn_long - mercury_long) % 360,  # Profit/Gain
            "karyasiddhi": (lagna_long + jupiter_long - mercury_long) % 360,  # Success
            "vivaha": (lagna_long + venus_long - sun_long) % 360,  # Partnerships
            "rajya": (lagna_long + sun_long - moon_long) % 360,  # Status/Authority
            "punya": (lagna_long + mars_long - moon_long) % 360,  # Fortune
        }

    def is_saham_transit_favorable(
        self, saham_name: str, saham_long: float, transits: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Check if transit is favorable for a specific Saham.
        """
        saham_sign = self._longitude_to_sign(saham_long)
        saham_house = int(saham_long / 30) + 1

        favorable_aspects = []

        for planet, pos in transits.get("current_positions", {}).items():
            planet_long = pos.get("longitude", 0)
            pos.get("sign", "")

            # Conjunction with Saham
            angle = abs(planet_long - saham_long) % 360
            if angle <= 10 or angle >= 350:
                favorable_aspects.append(
                    {
                        "planet": planet,
                        "aspect": "conjunction",
                        "strength": "strong" if pos.get("exalted") else "normal",
                    }
                )

            # Trine to Saham (120°)
            elif 110 <= angle <= 130:
                favorable_aspects.append(
                    {"planet": planet, "aspect": "trine", "strength": "supportive"}
                )

        return {
            "saham": saham_name,
            "longitude": saham_long,
            "sign": saham_sign,
            "house": saham_house,
            "favorable_aspects": favorable_aspects,
            "is_favorable": len(favorable_aspects) > 0,
        }

    # ==================== ENHANCED TRANSIT ====================

    def calculate_gochara_with_obstructions(
        self, birth_kundli: dict[str, Any], current_date: datetime
    ) -> dict[str, Any]:
        """
        Enhanced Gochara with Vedhanka (obstructions).
        """
        moon_sign = birth_kundli.get("planets", {}).get("Moon", {}).get("sign", "Aries")
        moon_sign_idx = self.SIGNS.index(moon_sign)

        jd = self._datetime_to_jd(current_date)

        gochara = {
            "moon_sign": moon_sign,
            "transits": {},
            "favorable_houses": [],
            "unfavorable_houses": [],
        }

        # Standard Gochara favorable positions from Moon
        gochara_map = {
            "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
            "Moon": [1, 3, 6, 7, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [1, 2, 3, 4, 7, 8, 9, 10, 11],
            "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn": [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
            "Rahu": [1, 2, 3, 5, 6, 10, 11, 12],
            "Ketu": [1, 2, 4, 6, 7, 8, 10, 11],
        }

        for planet in [
            "Sun",
            "Moon",
            "Mars",
            "Mercury",
            "Jupiter",
            "Venus",
            "Saturn",
            "Rahu",
            "Ketu",
        ]:
            if planet == "Ketu":
                rahu_long = self._get_sidereal_position(jd, swe.TRUE_NODE)[0]
                longitude = (rahu_long + 180) % 360
            else:
                longitude = self._get_sidereal_position(jd, self.PLANETS[planet])[0]

            sign = self._longitude_to_sign(longitude)
            sign_idx = self.SIGNS.index(sign)

            # House from Moon
            house_from_moon = ((sign_idx - moon_sign_idx) % 12) + 1

            # Check if favorable
            is_favorable = house_from_moon in gochara_map.get(planet, [])

            # Get Ashtakavarga bindu
            bindu = self.get_gochara_bindu(birth_kundli, current_date, planet)

            gochara["transits"][planet] = {
                "sign": sign,
                "house_from_moon": house_from_moon,
                "is_favorable": is_favorable,
                "bindu": bindu,
                "strength": ("strong" if bindu >= 4 else "medium" if bindu >= 2 else "weak"),
            }

            if is_favorable and bindu >= 3:
                gochara["favorable_houses"].append(
                    {"planet": planet, "house": house_from_moon, "bindu": bindu}
                )
            elif not is_favorable or bindu < 2:
                gochara["unfavorable_houses"].append(
                    {"planet": planet, "house": house_from_moon, "bindu": bindu}
                )

        return gochara

    # ==================== TRADING SPECIFIC ====================

    def calculate_trading_strength(
        self, kundli: dict[str, Any], current_date: datetime
    ) -> dict[str, Any]:
        """
        Calculate overall trading strength based on multiple factors.
        """
        # Get all components
        dasha = self.calculate_vimshottari_dasha(kundli, current_date)
        ashtaka = self.calculate_ashtakavarga(kundli)
        sahams = self.calculate_all_sahams(kundli)

        # Calculate Artha Saham transit
        jd = self._datetime_to_jd(current_date)
        transits = {"current_positions": {}}
        for planet_name, planet_id in self.PLANETS.items():
            if planet_name == "Ketu":
                continue
            longitude = self._get_sidereal_position(jd, planet_id)[0]
            transits["current_positions"][planet_name] = {"longitude": longitude}

        artha_analysis = self.is_saham_transit_favorable("artha", sahams["artha"], transits)

        # Scoring
        score = 0

        # Dasha lords (40 points)
        benefic_planets = ["Jupiter", "Venus", "Mercury", "Moon"]
        if dasha.mahadasha_lord in benefic_planets:
            score += 20
        if dasha.antardasha_lord in benefic_planets:
            score += 15
        if dasha.pratyantardasha_lord in benefic_planets:
            score += 5

        # Artha Saham (30 points)
        if artha_analysis["is_favorable"]:
            score += 30

        # Ashtakavarga (30 points)
        sarva = ashtaka.get("sarvashtaka", {})
        avg_bindu = sum(sarva.values()) / 12 if sarva else 0
        score += min(30, avg_bindu * 3)

        return {
            "overall_score": score,
            "rating": (
                "excellent"
                if score >= 80
                else "good" if score >= 60 else "moderate" if score >= 40 else "weak"
            ),
            "dasha": {
                "mahadasha": dasha.mahadasha_lord,
                "antardasha": dasha.antardasha_lord,
                "pratyantardasha": dasha.pratyantardasha_lord,
            },
            "artha_saham": artha_analysis,
            "ashtakavarga_avg": avg_bindu,
            "recommendation": (
                "strong_buy"
                if score >= 75
                else "buy" if score >= 55 else "hold" if score >= 40 else "avoid"
            ),
        }
