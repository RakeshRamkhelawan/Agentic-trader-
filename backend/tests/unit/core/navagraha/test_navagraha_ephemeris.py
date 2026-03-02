from datetime import datetime, timezone

import pytest

from backend.core.navagraha.ephemeris import EphemerisCalculator
from backend.core.navagraha.models import NavagrahaState, PlanetName


@pytest.fixture
def calculator():
    return EphemerisCalculator()


@pytest.fixture
def known_date():
    # January 1st, 2024, 12:00 UTC
    return datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def location():
    # New Delhi
    return (28.6139, 77.2090)


def test_ephemeris_state_generation(calculator, known_date, location):
    """Test 1: Generate state for a known date/time."""
    state = calculator.calculate_navagraha_state(
        dt=known_date, location_lat=location[0], location_lon=location[1]
    )

    assert isinstance(state, NavagrahaState)
    assert state.calculated_at == known_date
    assert state.location_lat == location[0]
    assert state.location_lon == location[1]


def test_nine_planets_returned(calculator, known_date, location):
    """Test 2: Verify exactly 9 planets are returned."""
    state = calculator.calculate_navagraha_state(
        dt=known_date, location_lat=location[0], location_lon=location[1]
    )

    assert len(state.planets) == 9
    assert all(p in state.planets for p in PlanetName)


def test_rahu_always_retrograde(calculator, known_date, location):
    """Test 3: Verify Rahu is always Retrograde."""
    state = calculator.calculate_navagraha_state(
        dt=known_date, location_lat=location[0], location_lon=location[1]
    )

    rahu = state.planets[PlanetName.RAHU]
    ketu = state.planets[PlanetName.KETU]

    assert rahu.is_retrograde is True
    assert ketu.is_retrograde is True

    # Also verify speed is negative
    assert rahu.speed < 0
    assert ketu.speed < 0


def test_planet_positions_range(calculator, known_date, location):
    """Test 4: Verify positions are within [0, 360)."""
    state = calculator.calculate_navagraha_state(
        dt=known_date, location_lat=location[0], location_lon=location[1]
    )

    for planet in state.planets.values():
        assert 0.0 <= planet.longitude < 360.0
        assert -90.0 <= planet.latitude <= 90.0


def test_rahu_ketu_invariant(calculator, known_date, location):
    """Verify Rahu and Ketu are 180 degrees apart."""
    state = calculator.calculate_navagraha_state(
        dt=known_date, location_lat=location[0], location_lon=location[1]
    )

    rahu = state.planets[PlanetName.RAHU]
    ketu = state.planets[PlanetName.KETU]

    diff = abs(rahu.longitude - ketu.longitude)
    if diff > 180:
        diff = 360 - diff

    assert 179.0 <= diff <= 181.0


def test_guna_distribution_sum(calculator, known_date, location):
    """Verify Guna distribution sums to exactly 1.0."""
    state = calculator.calculate_navagraha_state(
        dt=known_date, location_lat=location[0], location_lon=location[1]
    )

    total = (
        state.guna_distribution.sattva
        + state.guna_distribution.rajas
        + state.guna_distribution.tamas
    )

    assert 0.9999 <= total <= 1.0001


def test_dasha_calculation(calculator, known_date, location):
    """Verify Dasha is calculated based on Moon position."""
    state = calculator.calculate_navagraha_state(
        dt=known_date, location_lat=location[0], location_lon=location[1]
    )

    assert state.current_dasha is not None
    assert isinstance(state.current_dasha, PlanetName)

    # Verify correspondence with Moon longitude
    from backend.core.navagraha.dasha import DashaCalculator

    moon_lon = state.planets[PlanetName.MOON].longitude
    expected_dasha = DashaCalculator.get_current_mahadasha_lord(moon_lon)

    assert state.current_dasha == expected_dasha
