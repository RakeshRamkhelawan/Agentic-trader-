from typing import Dict, List

from backend.core.navagraha.models import PlanetName


class DashaCalculator:
    """
    Calculates the Vimshottari Dasha (or Nakshatra Lord) based on Moon's longitude.
    In the context of real-time trading state, 'Current Dasha' often refers to the
    ruling planet of the current Nakshatra (Transit Dasha or Nakshatra Lord).
    """

    NAKSHATRA_LORDS = [
        PlanetName.KETU,  # 0  Ashwini
        PlanetName.VENUS,  # 1  Bharani
        PlanetName.SUN,  # 2  Krittika
        PlanetName.MOON,  # 3  Rohini
        PlanetName.MARS,  # 4  Mrigashira
        PlanetName.RAHU,  # 5  Ardra
        PlanetName.JUPITER,  # 6  Punarvasu
        PlanetName.SATURN,  # 7  Pushya
        PlanetName.MERCURY,  # 8  Ashlesha
        PlanetName.KETU,  # 9  Magha
        PlanetName.VENUS,  # 10 Purva Phalguni
        PlanetName.SUN,  # 11 Uttara Phalguni
        PlanetName.MOON,  # 12 Hasta
        PlanetName.MARS,  # 13 Chitra
        PlanetName.RAHU,  # 14 Swati
        PlanetName.JUPITER,  # 15 Vishakha
        PlanetName.SATURN,  # 16 Anuradha
        PlanetName.MERCURY,  # 17 Jyeshtha
        PlanetName.KETU,  # 18 Mula
        PlanetName.VENUS,  # 19 Purva Ashadha
        PlanetName.SUN,  # 20 Uttara Ashadha
        PlanetName.MOON,  # 21 Shravana
        PlanetName.MARS,  # 22 Dhanishta
        PlanetName.RAHU,  # 23 Shatabhisha
        PlanetName.JUPITER,  # 24 Purva Bhadrapada
        PlanetName.SATURN,  # 25 Uttara Bhadrapada
        PlanetName.MERCURY,  # 26 Revati
    ]

    @staticmethod
    def get_nakshatra_index(longitude: float) -> int:
        """Calculates 0-26 index of the Nakshatra."""
        # 360 degrees / 27 Nakshatras = 13 deg 20 min = 13.3333... degrees per Nakshatra
        return int(longitude / 13.333333333333334)

    @classmethod
    def get_current_mahadasha_lord(cls, moon_longitude: float) -> PlanetName:
        """Returns the ruling planet of the current Nakshatra."""
        idx = cls.get_nakshatra_index(moon_longitude)
        # Handle edge case of 360.0 (though logic usually keeps < 360)
        if idx >= 27:
            idx = 0

        return cls.NAKSHATRA_LORDS[idx]
