from datetime import datetime, timezone

import pytest

from backend.core.navagraha.ephemeris import EphemerisCalculator
from backend.core.navagraha.models import NavagrahaState, PlanetName


class TestEphemerisCalculator:

    @pytest.fixture
    def calculator(self):
        return EphemerisCalculator()

    def test_calculate_julian_day_known_epoch(self, calculator):
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd = calculator.calculate_julian_day(dt)

        expected_jd = 2451545.0
        assert abs(jd - expected_jd) < 0.001, f"Expected JD ~{expected_jd}, got {jd}"

    def test_calculate_julian_day_j2000(self, calculator):
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd = calculator.calculate_julian_day(dt)
        assert jd == pytest.approx(2451545.0, abs=0.001)

    def test_all_nine_planets_calculated(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)

        assert len(planets) == 9, f"Expected 9 planets, got {len(planets)}"

        for planet_name in PlanetName:
            assert planet_name in planets, f"Missing planet: {planet_name.value}"

    def test_rahu_always_retrograde(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        rahu_state = calculator.calculate_planet_state(PlanetName.RAHU, dt)

        assert rahu_state.is_retrograde is True, "Rahu must always be retrograde"
        assert (
            rahu_state.speed < 0
        ), f"Rahu speed must be negative, got {rahu_state.speed}"

    def test_ketu_always_retrograde(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        ketu_state = calculator.calculate_planet_state(PlanetName.KETU, dt)

        assert ketu_state.is_retrograde is True, "Ketu must always be retrograde"
        assert (
            ketu_state.speed < 0
        ), f"Ketu speed must be negative, got {ketu_state.speed}"

    def test_rahu_ketu_180_degree_opposition(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)

        rahu_lon = planets[PlanetName.RAHU].longitude
        ketu_lon = planets[PlanetName.KETU].longitude

        angle_diff = abs(rahu_lon - ketu_lon)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        assert 179.0 <= angle_diff <= 181.0, (
            f"Rahu-Ketu must be 180 degrees apart (±1 degree). "
            f"Rahu={rahu_lon:.4f} degrees, Ketu={ketu_lon:.4f} degrees, diff={angle_diff:.4f} degrees"
        )

    def test_planet_longitude_range(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)

        for planet_name, planet_state in planets.items():
            assert (
                0.0 <= planet_state.longitude < 360.0
            ), f"{planet_name.value} longitude out of range: {planet_state.longitude}"

    def test_planet_latitude_range(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)

        for planet_name, planet_state in planets.items():
            assert (
                -90.0 <= planet_state.latitude <= 90.0
            ), f"{planet_name.value} latitude out of range: {planet_state.latitude}"

    def test_retrograde_consistency(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)

        for planet_name, planet_state in planets.items():
            if planet_state.is_retrograde:
                assert (
                    planet_state.speed < 0
                ), f"{planet_name.value} marked retrograde but speed={planet_state.speed} >= 0"
            else:
                assert (
                    planet_state.speed >= 0
                ), f"{planet_name.value} not marked retrograde but speed={planet_state.speed} < 0"

    def test_guna_distribution_sums_to_one(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)
        guna = calculator.calculate_guna_distribution(planets, dt)

        total = guna.sattva + guna.rajas + guna.tamas
        assert (
            0.9999 <= total <= 1.0001
        ), f"Guna distribution must sum to 1.0, got {total}"

    def test_guna_distribution_non_negative(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)
        guna = calculator.calculate_guna_distribution(planets, dt)

        assert guna.sattva >= 0.0, f"Sattva cannot be negative: {guna.sattva}"
        assert guna.rajas >= 0.0, f"Rajas cannot be negative: {guna.rajas}"
        assert guna.tamas >= 0.0, f"Tamas cannot be negative: {guna.tamas}"

    def test_navagraha_state_complete(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        location_lat = 51.5074
        location_lon = -0.1278

        state = calculator.calculate_navagraha_state(dt, location_lat, location_lon)

        assert isinstance(state, NavagrahaState)
        assert len(state.planets) == 9
        assert state.guna_distribution is not None
        assert state.calculated_at == dt
        assert state.location_lat == location_lat
        assert state.location_lon == location_lon

    def test_aspects_calculated(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)
        aspects = calculator.calculate_aspects(planets)

        assert isinstance(aspects, list)

        for aspect in aspects:
            assert aspect.planet1 in PlanetName
            assert aspect.planet2 in PlanetName
            assert aspect.planet1 != aspect.planet2
            assert 0.0 <= aspect.angle < 360.0
            assert 0.0 <= aspect.orb <= 8.0
            assert 0.0 <= aspect.strength <= 1.0

    def test_rahu_kala_calculation(self, calculator):
        dt = datetime(2026, 2, 14, 15, 30, 0, tzinfo=timezone.utc)
        location_lat = 51.5074
        location_lon = -0.1278

        rahu_kala_active = calculator.calculate_rahu_kala(
            dt, location_lat, location_lon
        )

        assert isinstance(rahu_kala_active, bool)

    def test_benchmark_sun_position_vernal_equinox_2026(self, calculator):
        dt = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        sun_state = calculator.calculate_planet_state(PlanetName.SUN, dt)

        expected_sidereal = 335.66
        tolerance = 1.0

        assert abs(sun_state.longitude - expected_sidereal) < tolerance, (
            f"Sun at Vernal Equinox 2026 (sidereal Lahiri): Expected ~{expected_sidereal} degrees, "
            f"got {sun_state.longitude:.2f} degrees"
        )

    def test_benchmark_moon_fast_movement(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        moon_state = calculator.calculate_planet_state(PlanetName.MOON, dt)

        assert (
            abs(moon_state.speed) > 10.0
        ), f"Moon should move >10 degrees/day, got {moon_state.speed:.4f} degrees/day"

    def test_benchmark_jupiter_slow_movement(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        jupiter_state = calculator.calculate_planet_state(PlanetName.JUPITER, dt)

        assert (
            abs(jupiter_state.speed) < 0.5
        ), f"Jupiter should move <0.5 degrees/day, got {jupiter_state.speed:.4f} degrees/day"

    def test_trading_gate_closed_during_rahu_kala(self, calculator):
        dt = datetime(2026, 2, 17, 15, 30, 0, tzinfo=timezone.utc)
        location_lat = 51.5074
        location_lon = -0.1278

        state = calculator.calculate_navagraha_state(dt, location_lat, location_lon)

        if state.rahu_kala_active:
            assert (
                state.trading_gate_open is False
            ), "Trading gate must be closed during Rahu Kala"

    def test_trading_gate_closed_high_tamas(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        location_lat = 51.5074
        location_lon = -0.1278

        state = calculator.calculate_navagraha_state(dt, location_lat, location_lon)

        if state.guna_distribution.tamas > 0.6:
            assert (
                state.trading_gate_open is False
            ), "Trading gate must be closed when tamas > 0.6"

    def test_immutability_planet_state(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        planet_state = calculator.calculate_planet_state(PlanetName.SUN, dt)

        with pytest.raises(Exception):
            planet_state.longitude = 100.0

    def test_immutability_navagraha_state(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        state = calculator.calculate_navagraha_state(dt, 51.5074, -0.1278)

        with pytest.raises(Exception):
            state.rahu_kala_active = True

    def test_zodiac_sign_calculation(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        sun_state = calculator.calculate_planet_state(PlanetName.SUN, dt)

        zodiac_signs = [
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

        assert (
            sun_state.zodiac_sign in zodiac_signs
        ), f"Invalid zodiac sign: {sun_state.zodiac_sign}"

    def test_nakshatra_calculation(self, calculator):
        dt = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
        moon_state = calculator.calculate_planet_state(PlanetName.MOON, dt)

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

        assert (
            moon_state.nakshatra in nakshatras
        ), f"Invalid nakshatra: {moon_state.nakshatra}"


class TestEphemerisInvariants:

    @pytest.fixture
    def calculator(self):
        return EphemerisCalculator()

    @pytest.mark.parametrize(
        "year,month,day",
        [
            (2026, 1, 1),
            (2026, 6, 15),
            (2026, 12, 31),
            (2025, 3, 20),
            (2027, 9, 23),
        ],
    )
    def test_rahu_ketu_opposition_multiple_dates(self, calculator, year, month, day):
        dt = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)

        rahu_lon = planets[PlanetName.RAHU].longitude
        ketu_lon = planets[PlanetName.KETU].longitude
        angle_diff = abs(rahu_lon - ketu_lon)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        assert 179.0 <= angle_diff <= 181.0, (
            f"Date {year}-{month:02d}-{day:02d}: Rahu-Ketu opposition failed. "
            f"Rahu={rahu_lon:.4f} degrees, Ketu={ketu_lon:.4f} degrees, diff={angle_diff:.4f} degrees"
        )

    @pytest.mark.parametrize(
        "year,month,day",
        [
            (2026, 1, 1),
            (2026, 6, 15),
            (2026, 12, 31),
        ],
    )
    def test_guna_distribution_invariant_multiple_dates(
        self, calculator, year, month, day
    ):
        dt = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
        planets = calculator.calculate_all_planets(dt)
        guna = calculator.calculate_guna_distribution(planets, dt)

        total = guna.sattva + guna.rajas + guna.tamas
        assert (
            0.9999 <= total <= 1.0001
        ), f"Date {year}-{month:02d}-{day:02d}: Guna sum={total:.6f} (should be 1.0)"
