from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import swisseph as swe

from backend.core.navagraha.models import (AspectType, GunaDistribution,
                                           NavagrahaState, PlanetaryAspect,
                                           PlanetName, PlanetState)


class EphemerisCalculator:
    PLANET_MAPPING = {
        PlanetName.SUN: swe.SUN,
        PlanetName.MOON: swe.MOON,
        PlanetName.MARS: swe.MARS,
        PlanetName.MERCURY: swe.MERCURY,
        PlanetName.JUPITER: swe.JUPITER,
        PlanetName.VENUS: swe.VENUS,
        PlanetName.SATURN: swe.SATURN,
        PlanetName.RAHU: swe.MEAN_NODE,
        PlanetName.KETU: swe.MEAN_NODE,
    }

    ASPECT_ANGLES = {
        AspectType.CONJUNCTION: (0.0, 8.0),
        AspectType.OPPOSITION: (180.0, 8.0),
        AspectType.TRINE: (120.0, 6.0),
        AspectType.SQUARE: (90.0, 6.0),
        AspectType.SEXTILE: (60.0, 4.0),
    }

    def __init__(self, ephemeris_path: Optional[str] = None):
        if ephemeris_path:
            swe.set_ephe_path(ephemeris_path)

        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def calculate_julian_day(self, dt: datetime) -> float:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0

        jd = swe.julday(year, month, day, hour)
        return jd

    def calculate_planet_position(
        self, planet_name: PlanetName, jd: float
    ) -> Tuple[float, float, float, float]:
        swe_planet = self.PLANET_MAPPING[planet_name]

        result, flag = swe.calc_ut(jd, swe_planet, swe.FLG_SWIEPH | swe.FLG_SPEED)

        if flag < 0:
            raise RuntimeError(
                f"Swiss Ephemeris calculation failed for {planet_name.value}: flag={flag}"
            )

        longitude_tropical = result[0]
        latitude = result[1]
        distance_au = result[2]
        speed = result[3]

        ayanamsa = swe.get_ayanamsa_ut(jd)
        longitude_sidereal = (longitude_tropical - ayanamsa) % 360.0

        if planet_name == PlanetName.KETU:
            longitude_sidereal = (longitude_sidereal + 180.0) % 360.0

        return longitude_sidereal, latitude, distance_au, speed

    def calculate_planet_state(
        self, planet_name: PlanetName, dt: datetime
    ) -> PlanetState:
        jd = self.calculate_julian_day(dt)
        longitude, latitude, distance_au, speed = self.calculate_planet_position(
            planet_name, jd
        )

        is_retrograde = speed < 0

        return PlanetState(
            name=planet_name,
            longitude=longitude,
            latitude=latitude,
            speed=speed,
            is_retrograde=is_retrograde,
            distance_au=distance_au,
            calculated_at=dt,
        )

    def calculate_all_planets(self, dt: datetime) -> Dict[PlanetName, PlanetState]:
        planets = {}
        for planet_name in PlanetName:
            planets[planet_name] = self.calculate_planet_state(planet_name, dt)

        rahu_lon = planets[PlanetName.RAHU].longitude
        ketu_lon = planets[PlanetName.KETU].longitude
        angle_diff = abs(rahu_lon - ketu_lon)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        if not (179.0 <= angle_diff <= 181.0):
            raise RuntimeError(
                f"Rahu-Ketu invariant violated: Rahu={rahu_lon:.4f}°, Ketu={ketu_lon:.4f}°, separation={angle_diff:.4f}° (expected ~180°)"
            )

        return planets

    def calculate_guna_distribution(
        self, planets: Dict[PlanetName, PlanetState], dt: datetime
    ) -> GunaDistribution:
        sattva_weights = {
            PlanetName.JUPITER: 0.30,
            PlanetName.MOON: 0.20,
            PlanetName.VENUS: 0.15,
            PlanetName.MERCURY: 0.10,
        }

        rajas_weights = {
            PlanetName.SUN: 0.25,
            PlanetName.MARS: 0.20,
            PlanetName.MERCURY: 0.10,
            PlanetName.RAHU: 0.15,
        }

        tamas_weights = {
            PlanetName.SATURN: 0.30,
            PlanetName.KETU: 0.15,
            PlanetName.MARS: 0.10,
        }

        def calculate_guna_score(weights: Dict[PlanetName, float]) -> float:
            score = 0.0
            for planet_name, weight in weights.items():
                planet = planets[planet_name]

                speed_factor = 1.0
                if planet.is_retrograde:
                    speed_factor = 0.7
                else:
                    speed_norm = abs(planet.speed) / 1.0
                    speed_factor = min(1.0, 0.5 + speed_norm * 0.5)

                score += weight * speed_factor

            return score

        sattva_raw = calculate_guna_score(sattva_weights)
        rajas_raw = calculate_guna_score(rajas_weights)
        tamas_raw = calculate_guna_score(tamas_weights)

        total = sattva_raw + rajas_raw + tamas_raw

        if total == 0:
            sattva = rajas = tamas = 1.0 / 3.0
        else:
            sattva = sattva_raw / total
            rajas = rajas_raw / total
            tamas = tamas_raw / total

        return GunaDistribution(
            sattva=sattva, rajas=rajas, tamas=tamas, calculated_at=dt
        )

    def calculate_aspects(
        self, planets: Dict[PlanetName, PlanetState]
    ) -> list[PlanetaryAspect]:
        aspects = []
        planet_list = list(planets.keys())

        for i, planet1_name in enumerate(planet_list):
            for planet2_name in planet_list[i + 1 :]:
                planet1 = planets[planet1_name]
                planet2 = planets[planet2_name]

                angle = abs(planet1.longitude - planet2.longitude)
                if angle > 180:
                    angle = 360 - angle

                for aspect_type, (ideal_angle, max_orb) in self.ASPECT_ANGLES.items():
                    orb = abs(angle - ideal_angle)

                    if orb <= max_orb:
                        is_applying = self._is_aspect_applying(
                            planet1, planet2, ideal_angle
                        )
                        strength = 1.0 - (orb / max_orb)

                        aspects.append(
                            PlanetaryAspect(
                                planet1=planet1_name,
                                planet2=planet2_name,
                                aspect_type=aspect_type,
                                angle=angle,
                                orb=orb,
                                is_applying=is_applying,
                                strength=strength,
                            )
                        )
                        break

        return aspects

    def _is_aspect_applying(
        self, planet1: PlanetState, planet2: PlanetState, ideal_angle: float
    ) -> bool:
        current_angle = abs(planet1.longitude - planet2.longitude)
        if current_angle > 180:
            current_angle = 360 - current_angle

        relative_speed = planet1.speed - planet2.speed

        if current_angle < ideal_angle:
            return relative_speed > 0
        else:
            return relative_speed < 0

    def calculate_rahu_kala(
        self, dt: datetime, location_lat: float, location_lon: float
    ) -> bool:
        day_of_week = dt.weekday()

        hour = dt.hour

        rahu_kala_hours = {
            0: (7, 9),
            1: (15, 17),
            2: (12, 14),
            3: (10, 12),
            4: (13, 15),
            5: (9, 11),
            6: (16, 18),
        }

        start_hour, end_hour = rahu_kala_hours.get(day_of_week, (0, 0))

        return start_hour <= hour < end_hour

    def calculate_navagraha_state(
        self,
        dt: datetime,
        location_lat: float,
        location_lon: float,
        current_dasha: Optional[PlanetName] = None,
    ) -> NavagrahaState:
        planets = self.calculate_all_planets(dt)
        guna_distribution = self.calculate_guna_distribution(planets, dt)
        aspects = self.calculate_aspects(planets)
        rahu_kala_active = self.calculate_rahu_kala(dt, location_lat, location_lon)

        if current_dasha is None:
            # Auto-calculate Dasha based on Moon's position
            from backend.core.navagraha.dasha import DashaCalculator

            moon_lon = planets[PlanetName.MOON].longitude
            current_dasha = DashaCalculator.get_current_mahadasha_lord(moon_lon)

        return NavagrahaState(
            planets=planets,
            guna_distribution=guna_distribution,
            aspects=aspects,
            rahu_kala_active=rahu_kala_active,
            current_dasha=current_dasha,
            calculated_at=dt,
            location_lat=location_lat,
            location_lon=location_lon,
        )
