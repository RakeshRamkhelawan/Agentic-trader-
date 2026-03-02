from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.navagraha.cache import NavagrahaCache
from backend.core.navagraha.models import NavagrahaState
from backend.core.navagraha.service import NavagrahaService


@pytest.fixture
def mock_cache_layer():
    with patch("backend.core.navagraha.cache.get_cache") as mock_get:
        mock_instance = AsyncMock()
        mock_get.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def navagraha_cache(mock_cache_layer):
    return NavagrahaCache()


@pytest.fixture
def mock_navagraha_state():
    # Helper to create a dummy state
    # We won't validate full content here, just need serialization checks
    # But NavagrahaState validation is strict, so we might mock the object itself
    # or create a minimal valid one.
    # Actually, let's just mock the object for service tests,
    # but for cache tests we need real object to test model_dump/validate.

    # We'll use the calculator to generate a real valid state for testing
    from backend.core.navagraha.ephemeris import EphemerisCalculator

    calc = EphemerisCalculator()
    return calc.calculate_navagraha_state(
        datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc), 28.6, 77.2
    )


@pytest.mark.asyncio
async def test_cache_key_generation(navagraha_cache):
    dt = datetime(2024, 1, 1, 12, 4, 30)  # Should round to 12:00
    key = navagraha_cache._generate_key(28.61, 77.21, dt)
    assert "202401011200" in key
    assert "28.61-77.21" in key

    dt2 = datetime(2024, 1, 1, 12, 7, 30)  # Should round to 12:05
    key2 = navagraha_cache._generate_key(28.61, 77.21, dt2)
    assert "202401011205" in key2


@pytest.mark.asyncio
async def test_set_state(navagraha_cache, mock_cache_layer, mock_navagraha_state):
    await navagraha_cache.set_state(mock_navagraha_state)

    # Verify set was called on underlying cache
    mock_cache_layer.set.assert_called_once()
    args = mock_cache_layer.set.call_args
    assert args[1]["ttl"] == 300  # Verify TTL

    # Verify data is serializable (dict)
    stored_data = args[0][1]
    assert isinstance(stored_data, dict)
    assert stored_data["location_lat"] == 28.6


@pytest.mark.asyncio
async def test_get_state_hit(navagraha_cache, mock_cache_layer, mock_navagraha_state):
    # Setup mock to return data
    mock_cache_layer.get.return_value = mock_navagraha_state.model_dump(mode="json")

    dt = mock_navagraha_state.calculated_at
    result = await navagraha_cache.get_state(28.6, 77.2, dt)

    assert result is not None
    assert isinstance(result, NavagrahaState)
    assert result.location_lat == 28.6


@pytest.mark.asyncio
async def test_get_state_miss(navagraha_cache, mock_cache_layer):
    mock_cache_layer.get.return_value = None

    dt = datetime.now(timezone.utc)
    result = await navagraha_cache.get_state(28.6, 77.2, dt)

    assert result is None


@pytest.mark.asyncio
async def test_service_cache_hit():
    # Service Integration Test
    mock_calc = MagicMock()
    mock_cache = AsyncMock()

    # Setup Cache Hit
    expected_state = "simulated_state"
    mock_cache.get_state.return_value = expected_state

    service = NavagrahaService(calculator=mock_calc, cache=mock_cache)

    result = await service.get_current_state(28.6, 77.2)

    assert result == expected_state
    mock_calc.calculate_navagraha_state.assert_not_called()


@pytest.mark.asyncio
async def test_service_cache_miss():
    # Service Integration Test
    mock_calc = MagicMock()
    mock_cache = AsyncMock()

    # Setup Cache Miss
    mock_cache.get_state.return_value = None

    # Setup Calculator Return
    # We invoke real calculator for the return value to be valid if strict typing is checked,
    # but for this unit test, a mock object is fine as long as logic holds.
    # However, service calls set_state which expects NavagrahaState if typed strictly?
    # Python is dynamic, so mock object is fine.
    simulated_state = AsyncMock(spec=NavagrahaState)
    mock_calc.calculate_navagraha_state.return_value = simulated_state

    service = NavagrahaService(calculator=mock_calc, cache=mock_cache)

    result = await service.get_current_state(28.6, 77.2)

    assert result == simulated_state
    mock_calc.calculate_navagraha_state.assert_called_once()
    mock_cache.set_state.assert_called_once_with(simulated_state)
