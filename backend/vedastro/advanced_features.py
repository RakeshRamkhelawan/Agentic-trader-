"""
Advanced Vedic Astrology Features
Implements: Yogas, Avastas, Pancha Pakshi, Muhurtha, Advanced Vargas
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PlanetState(Enum):
    """Planetary Avastas (States)"""

    EXALTED = "exalted"  # Uccha - 100% strength
    OWN_SIGN = "own_sign"  # Sva - 75% strength
    FRIEND_SIGN = "friend_sign"  # Mitra - 50% strength
    NEUTRAL = "neutral"  # Sama - 25% strength
    ENEMY_SIGN = "enemy_sign"  # Satru - 12.5% strength
    DEBILITATED = "debilitated"  # Neecha - 0% strength


@dataclass
class Yoga:
    """Vedic Yoga (Planetary Combination)"""

    name: str
    planets: List[str]
    strength: float  # 0-1
    description: str
    trading_significance: str


@dataclass
class Avasta:
    """Planetary State/Condition"""

    planet: str
    state: PlanetState
    strength_percent: float
    is_retrograde: bool
    is_combust: bool
    description: str


@dataclass
class PanchaPakshiData:
    """Pancha Pakshi (Five Birds) System"""

    birth_bird: str
    current_activity: str
    yama_bird: str
    is_favorable_period: bool
    strength: float


@dataclass
class MuhurthaData:
    """Electional Astrology - Favorable Times"""

    tithi: str
    tithi_type: str  # Nanda, Bhadra, Jaya, Rikta, Poorna
    nakshatra: str
    is_favorable: bool
    rating: float  # 0-10
    warnings: List[str]


@dataclass
class VargaChart:
    """Divisional Chart (Varga)"""

    division: str  # D1, D9, D10, etc.
    planets: Dict[str, Dict[str, Any]]
    ascendant: str
    significant_placements: List[str]


class AdvancedVedAstroFeatures:
    """
    Advanced Vedic Astrology calculations
    Extends EnhancedVedAstroConnector with deeper features
    """

    # Planet friendships (Vedic relationships)
    FRIENDSHIPS = {
        "Sun": {
            "friends": ["Moon", "Mars", "Jupiter"],
            "enemies": ["Venus", "Saturn"],
            "neutral": ["Mercury"],
        },
        "Moon": {
            "friends": ["Sun", "Mercury"],
            "enemies": [],
            "neutral": ["Mars", "Jupiter", "Venus", "Saturn"],
        },
        "Mars": {
            "friends": ["Sun", "Moon", "Jupiter"],
            "enemies": ["Mercury"],
            "neutral": ["Venus", "Saturn"],
        },
        "Mercury": {
            "friends": ["Sun", "Venus"],
            "enemies": ["Moon"],
            "neutral": ["Mars", "Jupiter", "Saturn"],
        },
        "Jupiter": {
            "friends": ["Sun", "Moon", "Mars"],
            "enemies": ["Mercury", "Venus"],
            "neutral": ["Saturn"],
        },
        "Venus": {
            "friends": ["Mercury", "Saturn"],
            "enemies": ["Sun", "Moon"],
            "neutral": ["Mars", "Jupiter"],
        },
        "Saturn": {
            "friends": ["Mercury", "Venus"],
            "enemies": ["Sun", "Moon", "Mars"],
            "neutral": ["Jupiter"],
        },
    }

    # Pancha Pakshi Birds
    PANCHA_PAKSHI_BIRDS = ["Vulture", "Owl", "Crow", "Cock", "Peacock"]

    # Bird activities by day/night
    BIRD_ACTIVITIES = {
        "Vulture": {"day": "eating", "night": "dying"},
        "Owl": {"day": "dying", "night": "eating"},
        "Crow": {"day": "walking", "night": "walking"},
        "Cock": {"day": "ruling", "night": "sleeping"},
        "Peacock": {"day": "sleeping", "night": "ruling"},
    }

    def __init__(self):
        self.signs = [
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

    # ==================== YOGAS (Planetary Combinations) ====================

    def calculate_all_yogas(self, kundli: Dict[str, Any]) -> List[Yoga]:
        """
        Calculate all major Vedic Yogas.
        Returns list of active yogas with trading significance.
        """
        yogas = []
        planets = kundli.get("planets", {})
        lagna_sign = kundli.get("lagna", "Aries")

        # 1. Gaja Kesari Yoga (Moon-Jupiter trine/conjunction)
        if self._check_gaja_kesari_yoga(planets):
            yogas.append(
                Yoga(
                    name="Gaja Kesari Yoga",
                    planets=["Moon", "Jupiter"],
                    strength=self._calculate_yoga_strength(
                        planets, ["Moon", "Jupiter"]
                    ),
                    description="Moon and Jupiter in mutual trine or conjunction - Wisdom, wealth, success",
                    trading_significance="EXCELLENT for trading - wisdom, intuition, and prosperity",
                )
            )

        # 2. Budha-Aditya Yoga (Sun-Mercury conjunction in same sign)
        if self._check_budha_aditya_yoga(planets):
            yogas.append(
                Yoga(
                    name="Budha-Aditya Yoga",
                    planets=["Sun", "Mercury"],
                    strength=self._calculate_yoga_strength(planets, ["Sun", "Mercury"]),
                    description="Sun and Mercury together - Intelligence, communication skills",
                    trading_significance="GOOD for analysis and quick decision making",
                )
            )

        # 3. Dhana Yoga (Wealth combinations)
        dhana_yogas = self._check_dhana_yogas(planets, lagna_sign)
        yogas.extend(dhana_yogas)

        # 4. Raja Yoga (Status/Power combinations)
        raja_yogas = self._check_raja_yogas(planets, lagna_sign)
        yogas.extend(raja_yogas)

        # 5. Chandra-Mangala Yoga (Moon-Mars conjunction)
        if self._check_chandra_mangala_yoga(planets):
            yogas.append(
                Yoga(
                    name="Chandra-Mangala Yoga",
                    planets=["Moon", "Mars"],
                    strength=self._calculate_yoga_strength(planets, ["Moon", "Mars"]),
                    description="Moon and Mars together - Courage, energy, but volatility",
                    trading_significance="CAUTION - High energy but emotional volatility in trading",
                )
            )

        # 6. Viparita Raja Yoga (6th/8th/12th lords in specific combinations)
        viparita = self._check_viparita_raja_yoga(planets, lagna_sign)
        if viparita:
            yogas.append(viparita)

        # 7. Pancha Mahapurusha Yogas (5 Great Person Yogas)
        mahapurusha = self._check_pancha_mahapurusha_yogas(planets)
        yogas.extend(mahapurusha)

        # 8. Lakshmi Yoga (9th lord in 9th or 10th, strong Venus)
        if self._check_lakshmi_yoga(planets, lagna_sign):
            yogas.append(
                Yoga(
                    name="Lakshmi Yoga",
                    planets=["Venus"],
                    strength=self._get_planet_strength(planets.get("Venus", {})),
                    description="Wealth and prosperity yoga",
                    trading_significance="EXCELLENT for financial gains and wealth accumulation",
                )
            )

        return sorted(yogas, key=lambda x: x.strength, reverse=True)

    def _check_gaja_kesari_yoga(self, planets: Dict) -> bool:
        """Moon and Jupiter in mutual kendra (1,4,7,10) or conjunction."""
        moon = planets.get("Moon", {})
        jupiter = planets.get("Jupiter", {})

        if not moon or not jupiter:
            return False

        moon_house = moon.get("house", 0)
        jupiter_house = jupiter.get("house", 0)

        # Check if in same house (conjunction) or kendra houses
        if moon_house == jupiter_house:
            return True

        # Check kendra relationship (4, 7, 10 houses apart)
        diff = abs(moon_house - jupiter_house)
        return diff in [3, 6, 9]  # 4th, 7th, 10th aspect

    def _check_budha_aditya_yoga(self, planets: Dict) -> bool:
        """Sun and Mercury in same sign."""
        sun = planets.get("Sun", {})
        mercury = planets.get("Mercury", {})

        if not sun or not mercury:
            return False

        return sun.get("sign") == mercury.get("sign")

    def _check_dhana_yogas(self, planets: Dict, lagna_sign: str) -> List[Yoga]:
        """Wealth producing combinations."""
        yogas = []

        # 2nd lord in kendra/trikona with benefits
        # 11th lord well placed
        # Venus-Jupiter connection

        venus = planets.get("Venus", {})
        jupiter = planets.get("Jupiter", {})

        if venus and jupiter:
            venus_house = venus.get("house", 0)
            jupiter_house = jupiter.get("house", 0)

            # Venus and Jupiter in mutual aspect or together
            if venus_house == jupiter_house or abs(venus_house - jupiter_house) in [
                3,
                6,
                9,
            ]:
                yogas.append(
                    Yoga(
                        name="Dhana Yoga (Venus-Jupiter)",
                        planets=["Venus", "Jupiter"],
                        strength=0.7,
                        description="Venus and Jupiter connected - Wealth and prosperity",
                        trading_significance="VERY GOOD for financial growth and investment success",
                    )
                )

        return yogas

    def _check_raja_yogas(self, planets: Dict, lagna_sign: str) -> List[Yoga]:
        """Power and status combinations."""
        yogas = []

        # Trine lords (1,5,9) in kendra (1,4,7,10) or vice versa
        # This is simplified - full implementation needs complete lordship calculations

        return yogas

    def _check_chandra_mangala_yoga(self, planets: Dict) -> bool:
        """Moon and Mars conjunction."""
        moon = planets.get("Moon", {})
        mars = planets.get("Mars", {})

        if not moon or not mars:
            return False

        return moon.get("sign") == mars.get("sign")

    def _check_viparita_raja_yoga(
        self, planets: Dict, lagna_sign: str
    ) -> Optional[Yoga]:
        """Difficult lords producing good results."""
        # Simplified check
        return None

    def _check_pancha_mahapurusha_yogas(self, planets: Dict) -> List[Yoga]:
        """Five great person yogas."""
        yogas = []

        # Ruchaka Yoga - Mars in kendra in own/exaltation sign
        mars = planets.get("Mars", {})
        if mars and mars.get("house") in [1, 4, 7, 10]:
            if mars.get("exalted") or mars.get("sign") in ["Aries", "Scorpio"]:
                yogas.append(
                    Yoga(
                        name="Ruchaka Yoga",
                        planets=["Mars"],
                        strength=0.8,
                        description="Mars strong in kendra - Courage, power, land/property",
                        trading_significance="GOOD for bold trading decisions and real estate",
                    )
                )

        # Bhadra Yoga - Mercury in kendra in own/exaltation
        mercury = planets.get("Mercury", {})
        if mercury and mercury.get("house") in [1, 4, 7, 10]:
            if mercury.get("exalted") or mercury.get("sign") in ["Gemini", "Virgo"]:
                yogas.append(
                    Yoga(
                        name="Bhadra Yoga",
                        planets=["Mercury"],
                        strength=0.8,
                        description="Mercury strong in kendra - Intelligence, communication",
                        trading_significance="EXCELLENT for analytical trading and data analysis",
                    )
                )

        # Hamsa Yoga - Jupiter in kendra in own/exaltation
        jupiter = planets.get("Jupiter", {})
        if jupiter and jupiter.get("house") in [1, 4, 7, 10]:
            if jupiter.get("exalted") or jupiter.get("sign") in [
                "Sagittarius",
                "Pisces",
            ]:
                yogas.append(
                    Yoga(
                        name="Hamsa Yoga",
                        planets=["Jupiter"],
                        strength=0.9,
                        description="Jupiter strong in kendra - Wisdom, wealth, righteousness",
                        trading_significance="EXCELLENT for long-term investment wisdom",
                    )
                )

        # Malavya Yoga - Venus in kendra in own/exaltation
        venus = planets.get("Venus", {})
        if venus and venus.get("house") in [1, 4, 7, 10]:
            if venus.get("exalted") or venus.get("sign") in ["Taurus", "Libra"]:
                yogas.append(
                    Yoga(
                        name="Malavya Yoga",
                        planets=["Venus"],
                        strength=0.85,
                        description="Venus strong in kendra - Luxury, wealth, vehicles",
                        trading_significance="EXCELLENT for luxury goods and beauty industry trades",
                    )
                )

        # Sasa Yoga - Saturn in kendra in own/exaltation
        saturn = planets.get("Saturn", {})
        if saturn and saturn.get("house") in [1, 4, 7, 10]:
            if saturn.get("exalted") or saturn.get("sign") in ["Capricorn", "Aquarius"]:
                yogas.append(
                    Yoga(
                        name="Sasa Yoga",
                        planets=["Saturn"],
                        strength=0.75,
                        description="Saturn strong in kendra - Power, authority, discipline",
                        trading_significance="GOOD for disciplined long-term trading strategies",
                    )
                )

        return yogas

    def _check_lakshmi_yoga(self, planets: Dict, lagna_sign: str) -> bool:
        """Venus strong and 9th lord well placed."""
        venus = planets.get("Venus", {})
        if not venus:
            return False

        # Simplified check - Venus in good dignity
        return (
            venus.get("exalted")
            or venus.get("own_sign")
            or venus.get("house") in [1, 5, 9]
        )

    def _calculate_yoga_strength(self, planets: Dict, yoga_planets: List[str]) -> float:
        """Calculate overall strength of a yoga based on planet strengths."""
        total_strength = 0
        for planet_name in yoga_planets:
            planet = planets.get(planet_name, {})
            total_strength += self._get_planet_strength(planet)

        return total_strength / len(yoga_planets) if yoga_planets else 0

    def _get_planet_strength(self, planet: Dict) -> float:
        """Get normalized planet strength (0-1)."""
        if not planet:
            return 0

        strength = 0.5  # Base

        if planet.get("exalted"):
            strength = 1.0
        elif planet.get("own_sign"):
            strength = 0.8
        elif planet.get("debilitated"):
            strength = 0.2

        # Retrograde reduces strength slightly
        if planet.get("retrograde"):
            strength *= 0.9

        return strength

    # ==================== AVASTAS (Planetary States) ====================

    def calculate_all_avastas(self, kundli: Dict[str, Any]) -> Dict[str, Avasta]:
        """
        Calculate Avastas (states) for all planets.
        Determines planetary strength and dignity.
        """
        avastas = {}
        planets = kundli.get("planets", {})

        for planet_name, planet_data in planets.items():
            avasta = self._calculate_single_avasta(planet_name, planet_data, planets)
            avastas[planet_name] = avasta

        return avastas

    def _calculate_single_avasta(
        self, planet_name: str, planet_data: Dict, all_planets: Dict
    ) -> Avasta:
        """Calculate Avasta for a single planet."""

        sign = planet_data.get("sign", "")
        house = planet_data.get("house", 0)
        is_retro = planet_data.get("retrograde", False)

        # Determine state
        if planet_data.get("exalted"):
            state = PlanetState.EXALTED
            strength = 100
            desc = f"{planet_name} is EXALTED in {sign} - Maximum strength"
        elif planet_data.get("debilitated"):
            state = PlanetState.DEBILITATED
            strength = 0
            desc = f"{planet_name} is DEBILITATED in {sign} - Minimum strength"
        elif self._is_in_own_sign(planet_name, sign):
            state = PlanetState.OWN_SIGN
            strength = 75
            desc = f"{planet_name} in OWN SIGN {sign} - Very strong"
        else:
            # Check friendship
            relationships = self.FRIENDSHIPS.get(planet_name, {})
            if sign and self._get_sign_lord(sign) in relationships.get("friends", []):
                state = PlanetState.FRIEND_SIGN
                strength = 50
                desc = f"{planet_name} in FRIENDLY sign {sign} - Moderate strength"
            elif sign and self._get_sign_lord(sign) in relationships.get("enemies", []):
                state = PlanetState.ENEMY_SIGN
                strength = 12.5
                desc = f"{planet_name} in ENEMY sign {sign} - Weak"
            else:
                state = PlanetState.NEUTRAL
                strength = 25
                desc = f"{planet_name} in NEUTRAL sign {sign} - Average strength"

        # Check combustion (within 8 degrees of Sun)
        is_combust = self._is_combust(planet_name, planet_data, all_planets)
        if is_combust:
            strength *= 0.5
            desc += " [COMBUST - weakened by proximity to Sun]"

        # Retrograde adjustment
        if is_retro:
            if state in [PlanetState.EXALTED, PlanetState.OWN_SIGN]:
                strength = min(
                    100, strength * 1.1
                )  # Stronger when retro in good dignity
            else:
                strength *= 0.9

        return Avasta(
            planet=planet_name,
            state=state,
            strength_percent=strength,
            is_retrograde=is_retro,
            is_combust=is_combust,
            description=desc,
        )

    def _is_in_own_sign(self, planet: str, sign: str) -> bool:
        """Check if planet is in its own sign."""
        own_signs = {
            "Sun": ["Leo"],
            "Moon": ["Cancer"],
            "Mars": ["Aries", "Scorpio"],
            "Mercury": ["Gemini", "Virgo"],
            "Jupiter": ["Sagittarius", "Pisces"],
            "Venus": ["Taurus", "Libra"],
            "Saturn": ["Capricorn", "Aquarius"],
        }
        return sign in own_signs.get(planet, [])

    def _get_sign_lord(self, sign: str) -> str:
        """Get the lord of a zodiac sign."""
        lords = {
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
        return lords.get(sign, "")

    def _is_combust(
        self, planet_name: str, planet_data: Dict, all_planets: Dict
    ) -> bool:
        """Check if planet is combust (within 8-15 degrees of Sun)."""
        if planet_name == "Sun":
            return False

        sun = all_planets.get("Sun", {})
        if not sun:
            return False

        sun_long = sun.get("longitude", 0)
        planet_long = planet_data.get("longitude", 0)

        diff = abs(sun_long - planet_long) % 360
        if diff > 180:
            diff = 360 - diff

        # Different combustion orbs for different planets
        orbs = {
            "Moon": 12,
            "Mars": 8,
            "Mercury": 8,
            "Jupiter": 11,
            "Venus": 10,
            "Saturn": 15,
        }
        return diff <= orbs.get(planet_name, 8)

    # ==================== PANCHA PAKSHI (Five Birds) ====================

    def calculate_pancha_pakshi(
        self, birth_nakshatra: str, current_time: datetime
    ) -> PanchaPakshiData:
        """
        Calculate Pancha Pakshi (Five Birds) system.
        Used for predicting favorable/unfavorable periods.
        """
        # Determine birth bird based on nakshatra
        bird_index = self._nakshatra_to_bird(birth_nakshatra)
        birth_bird = self.PANCHA_PAKSHI_BIRDS[bird_index]

        # Determine current activity based on day/night
        is_day = 6 <= current_time.hour < 18
        activity = self.BIRD_ACTIVITIES[birth_bird]["day" if is_day else "night"]

        # Determine Yama (5th part of day/night)
        yama_bird = self._calculate_yama_bird(birth_bird, current_time)

        # Favorable activities: Eating, Ruling, Walking
        # Unfavorable: Dying, Sleeping
        favorable_activities = ["eating", "ruling", "walking"]
        is_favorable = activity in favorable_activities

        # Calculate strength
        strength_map = {
            "eating": 1.0,
            "ruling": 0.9,
            "walking": 0.7,
            "sleeping": 0.4,
            "dying": 0.1,
        }
        strength = strength_map.get(activity, 0.5)

        return PanchaPakshiData(
            birth_bird=birth_bird,
            current_activity=activity,
            yama_bird=yama_bird,
            is_favorable_period=is_favorable,
            strength=strength,
        )

    def _nakshatra_to_bird(self, nakshatra: str) -> int:
        """Map nakshatra to bird (0-4)."""
        nakshatras = [
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

        try:
            index = nakshatras.index(nakshatra)
            # Each bird rules 5-6 nakshatras
            return (index // 6) % 5
        except ValueError:
            return 0

    def _calculate_yama_bird(self, birth_bird: str, current_time: datetime) -> str:
        """Calculate the bird ruling the current Yama (1/5th of day or night)."""
        is_day = 6 <= current_time.hour < 18

        if is_day:
            day_progress = (current_time.hour - 6) / 12
        else:
            if current_time.hour >= 18:
                day_progress = (current_time.hour - 18) / 12
            else:
                day_progress = (current_time.hour + 6) / 12

        yama_index = int(day_progress * 5) % 5

        # Birth bird determines sequence
        birth_index = self.PANCHA_PAKSHI_BIRDS.index(birth_bird)
        sequence = [(birth_index + i) % 5 for i in [0, 1, 4, 2, 3]]

        return self.PANCHA_PAKSHI_BIRDS[sequence[yama_index]]

    # ==================== MUHURTHA (Electional Astrology) ====================

    def calculate_muhurtha(
        self, date: datetime, kundli: Dict[str, Any]
    ) -> MuhurthaData:
        """
        Calculate Muhurtha - favorable/unfavorable time quality.
        """
        # Calculate Tithi (lunar day)
        tithi_num = self._calculate_tithi(date, kundli)
        tithi_name = self._tithi_name(tithi_num)
        tithi_type = self._tithi_type(tithi_num)

        # Get nakshatra
        moon_data = kundli.get("planets", {}).get("Moon", {})
        nakshatra = moon_data.get("nakshatra", "Ashwini")

        # Determine favorability
        is_favorable = tithi_type in ["Nanda", "Bhadra", "Jaya", "Poorna"]

        # Calculate rating
        rating = self._calculate_muhurtha_rating(tithi_type, nakshatra, kundli)

        # Generate warnings
        warnings = []
        if tithi_type == "Rikta":
            warnings.append("Rikta Tithi - Avoid new beginnings")

        return MuhurthaData(
            tithi=tithi_name,
            tithi_type=tithi_type,
            nakshatra=nakshatra,
            is_favorable=is_favorable,
            rating=rating,
            warnings=warnings,
        )

    def _calculate_tithi(self, date: datetime, kundli: Dict) -> int:
        """Calculate Tithi (lunar day) number 1-30."""
        # Simplified - would need accurate sun/moon longitudes
        sun_long = kundli.get("planets", {}).get("Sun", {}).get("longitude", 0)
        moon_long = kundli.get("planets", {}).get("Moon", {}).get("longitude", 0)

        diff = (moon_long - sun_long) % 360
        tithi = int(diff / 12) + 1  # Each tithi is 12 degrees
        return min(30, max(1, tithi))

    def _tithi_name(self, tithi_num: int) -> str:
        """Get name of tithi."""
        names = [
            "Pratipada",
            "Dwitiya",
            "Tritiya",
            "Chaturthi",
            "Panchami",
            "Shashthi",
            "Saptami",
            "Ashtami",
            "Navami",
            "Dashami",
            "Ekadashi",
            "Dwadashi",
            "Trayodashi",
            "Chaturdashi",
            "Purnima/Amavasya",
        ]
        if tithi_num <= 15:
            return names[min(tithi_num - 1, 14)]
        else:
            return names[min(tithi_num - 16, 14)]

    def _tithi_type(self, tithi_num: int) -> str:
        """Get tithi type (Nanda, Bhadra, Jaya, Rikta, Poorna)."""
        types = {
            "Nanda": [1, 6, 11, 16, 21, 26],
            "Bhadra": [2, 7, 12, 17, 22, 27],
            "Jaya": [3, 8, 13, 18, 23, 28],
            "Rikta": [4, 9, 14, 19, 24, 29],
            "Poorna": [5, 10, 15, 20, 25, 30],
        }

        for ttype, nums in types.items():
            if tithi_num in nums:
                return ttype
        return "Unknown"

    def _calculate_muhurtha_rating(
        self, tithi_type: str, nakshatra: str, kundli: Dict
    ) -> float:
        """Calculate overall Muhurtha rating 0-10."""
        base_rating = 5.0

        # Tithi type adjustment
        type_bonus = {"Nanda": 2, "Bhadra": 2, "Jaya": 1.5, "Poorna": 1, "Rikta": -3}
        base_rating += type_bonus.get(tithi_type, 0)

        # Check for favorable nakshatras
        favorable_nakshatras = [
            "Ashwini",
            "Rohini",
            "Pushya",
            "Uttara Phalguni",
            "Hasta",
            "Swati",
            "Anuradha",
            "Uttara Ashadha",
            "Shravana",
            "Dhanishta",
            "Uttara Bhadrapada",
            "Revati",
        ]
        if nakshatra in favorable_nakshatras:
            base_rating += 2

        return max(0, min(10, base_rating))

    # ==================== ADVANCED VARGAS ====================

    def calculate_all_vargas(self, kundli: Dict[str, Any]) -> Dict[str, VargaChart]:
        """
        Calculate all important Varga charts.
        """
        vargas = {}
        planets = kundli.get("planets", {})
        lagna_long = kundli.get("lagna_longitude", 0)

        # D1 - Rasi (already calculated)
        vargas["D1"] = self._create_varga_chart(
            "D1", planets, lagna_long, self._d1_position
        )

        # D9 - Navamsa (already in base connector, but add here for completeness)
        vargas["D9"] = self._create_varga_chart(
            "D9", planets, lagna_long, self._d9_position
        )

        # D10 - Dasamsa (Career/Status)
        vargas["D10"] = self._create_varga_chart(
            "D10", planets, lagna_long, self._d10_position
        )

        # D12 - Dwadasamsa (Parents/Family)
        vargas["D12"] = self._create_varga_chart(
            "D12", planets, lagna_long, self._d12_position
        )

        # D16 - Shodasamsa (Vehicles/Comforts)
        vargas["D16"] = self._create_varga_chart(
            "D16", planets, lagna_long, self._d16_position
        )

        # D20 - Vimshamsa (Spiritual)
        vargas["D20"] = self._create_varga_chart(
            "D20", planets, lagna_long, self._d20_position
        )

        # D24 - Chaturvimshamsa (Education)
        vargas["D24"] = self._create_varga_chart(
            "D24", planets, lagna_long, self._d24_position
        )

        # D27 - Bhamsha (Strength/Courage)
        vargas["D27"] = self._create_varga_chart(
            "D27", planets, lagna_long, self._d27_position
        )

        # D30 - Trimshamsha (Misfortunes)
        vargas["D30"] = self._create_varga_chart(
            "D30", planets, lagna_long, self._d30_position
        )

        # D40 - Khavedamsha (Auspicious results)
        vargas["D40"] = self._create_varga_chart(
            "D40", planets, lagna_long, self._d40_position
        )

        # D45 - Akshavedamsha (All general matters)
        vargas["D45"] = self._create_varga_chart(
            "D45", planets, lagna_long, self._d45_position
        )

        # D60 - Shashtyamsha (General results)
        vargas["D60"] = self._create_varga_chart(
            "D60", planets, lagna_long, self._d60_position
        )

        return vargas

    def _create_varga_chart(
        self, division: str, planets: Dict, lagna_long: float, position_func
    ) -> VargaChart:
        """Create a Varga chart using the given position function."""
        varga_planets = {}

        for planet_name, planet_data in planets.items():
            long = planet_data.get("longitude", 0)
            varga_sign_num = position_func(long)
            varga_sign = self.signs[varga_sign_num]

            varga_planets[planet_name] = {
                "sign": varga_sign,
                "longitude": (varga_sign_num * 30) + (long % 30),
            }

        # Calculate Varga Lagna
        varga_lagna_num = position_func(lagna_long)
        varga_lagna = self.signs[varga_lagna_num]

        # Find significant placements
        significant = self._find_significant_varga_placements(
            varga_planets, varga_lagna
        )

        return VargaChart(
            division=division,
            planets=varga_planets,
            ascendant=varga_lagna,
            significant_placements=significant,
        )

    def _d1_position(self, longitude: float) -> int:
        """D1 - Rasi (main chart)."""
        return int(longitude / 30) % 12

    def _d9_position(self, longitude: float) -> int:
        """D9 - Navamsa calculation."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        navamsa_in_sign = int(deg_in_sign / (30 / 9))

        # Elemental start for navamsa
        elemental_start = [0, 3, 6, 9, 0, 3, 6, 9, 0, 3, 6, 9][sign_num]
        return (elemental_start + navamsa_in_sign) % 12

    def _d10_position(self, longitude: float) -> int:
        """D10 - Dasamsa (Career)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        dasamsa = int(deg_in_sign / 3)  # 3 degrees each
        return (sign_num + dasamsa) % 12

    def _d12_position(self, longitude: float) -> int:
        """D12 - Dwadasamsa (Parents)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        dwadasamsa = int(deg_in_sign / 2.5)  # 2.5 degrees each
        return (sign_num + dwadasamsa) % 12

    def _d16_position(self, longitude: float) -> int:
        """D16 - Shodasamsa (Comforts)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        shodasamsa = int(deg_in_sign / 1.875)  # 1.875 degrees each
        return (sign_num + shodasamsa) % 12

    def _d20_position(self, longitude: float) -> int:
        """D20 - Vimshamsa (Spirituality)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        vimshamsa = int(deg_in_sign / 1.5)  # 1.5 degrees each
        return (sign_num + vimshamsa) % 12

    def _d24_position(self, longitude: float) -> int:
        """D24 - Chaturvimshamsa (Education)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        chaturvimshamsa = int(deg_in_sign / 1.25)  # 1.25 degrees each
        return (sign_num + chaturvimshamsa) % 12

    def _d27_position(self, longitude: float) -> int:
        """D27 - Bhamsha (Strength)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        bhamsha = int(deg_in_sign / (30 / 27))
        return (sign_num + bhamsha) % 12

    def _d30_position(self, longitude: float) -> int:
        """D30 - Trimshamsa (Misfortunes)."""
        deg_in_sign = longitude % 30
        # Complex Trimshamsa calculation based on sign type
        sign_num = int(longitude / 30)
        sign_type = sign_num % 3  # 0=moveable, 1=fixed, 2=dual

        if sign_type == 0:  # Moveable
            portions = [
                (0, 5, "Mars"),
                (5, 10, "Saturn"),
                (10, 18, "Jupiter"),
                (18, 25, "Mercury"),
                (25, 30, "Venus"),
            ]
        elif sign_type == 1:  # Fixed
            portions = [
                (0, 5, "Venus"),
                (5, 12, "Mercury"),
                (12, 20, "Jupiter"),
                (20, 25, "Saturn"),
                (25, 30, "Mars"),
            ]
        else:  # Dual
            portions = [
                (0, 5, "Mercury"),
                (5, 12, "Venus"),
                (12, 20, "Saturn"),
                (20, 25, "Mars"),
                (25, 30, "Jupiter"),
            ]

        for start, end, lord in portions:
            if start <= deg_in_sign < end:
                lords = {"Mars": 0, "Venus": 1, "Mercury": 2, "Jupiter": 3, "Saturn": 4}
                return (sign_num + lords.get(lord, 0)) % 12

        return sign_num

    def _d40_position(self, longitude: float) -> int:
        """D40 - Khavedamsha (Auspicious)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        khavedamsha = int(deg_in_sign / 0.75)  # 0.75 degrees each
        return (sign_num + khavedamsha) % 12

    def _d45_position(self, longitude: float) -> int:
        """D45 - Akshavedamsha (General)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        akshavedamsha = int(deg_in_sign / (2 / 3))  # 40/60 = 2/3 degree each
        return (sign_num + akshavedamsha) % 12

    def _d60_position(self, longitude: float) -> int:
        """D60 - Shashtyamsha (General results)."""
        sign_num = int(longitude / 30)
        deg_in_sign = longitude % 30
        shashtyamsha = int(deg_in_sign / 0.5)  # 0.5 degrees each
        return (sign_num + shashtyamsha) % 12

    def _find_significant_varga_placements(
        self, varga_planets: Dict, varga_lagna: str
    ) -> List[str]:
        """Find significant placements in Varga chart."""
        significant = []

        for planet, data in varga_planets.items():
            sign = data.get("sign", "")

            # Check if in own sign or exalted
            if self._is_in_own_sign(planet, sign):
                significant.append(f"{planet} in own sign {sign}")

            # Check if in Kendra (1,4,7,10) from Lagna
            lagna_idx = self.signs.index(varga_lagna)
            sign_idx = self.signs.index(sign)
            house_from_lagna = ((sign_idx - lagna_idx) % 12) + 1

            if house_from_lagna in [1, 4, 7, 10]:
                significant.append(f"{planet} in kendra (house {house_from_lagna})")

        return significant
