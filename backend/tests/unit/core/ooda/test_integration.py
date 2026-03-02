from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from backend.core.navagraha.models import GunaDistribution, NavagrahaState
from backend.core.system_identity import SystemIdentity


@pytest.fixture
def mock_navagraha_service():
    service = AsyncMock()
    return service


@pytest.fixture
def system_identity(mock_navagraha_service):
    # Patch NavagrahaService AND MemorySystem
    with (
        patch("backend.core.system_identity.NavagrahaService", return_value=mock_navagraha_service),
        patch("backend.core.system_identity.MemorySystem") as mock_memory_cls,
    ):

        mock_memory = mock_memory_cls.return_value
        mock_memory.recall.return_value = []  # No memories
        mock_memory.get_tendency.return_value = None
        mock_memory.store = AsyncMock()

        identity = SystemIdentity()
        identity.navagraha_service = mock_navagraha_service
        identity.memory_system = mock_memory
        return identity


@pytest.fixture
def base_market_data():
    return {
        "price_data": np.random.normal(100, 1, 100),
        "volume_data": np.random.normal(1000, 100, 100),
        "orderbook_imbalance": 0.2,
        "funding_rate": 0.01,
        "social_sentiment": 0.5,
    }


@pytest.fixture
def valid_planets():
    from backend.core.navagraha.models import PlanetName, PlanetState

    base_time = datetime.now(timezone.utc)
    planets = {}
    for name in PlanetName:
        speed = 1.0
        is_retro = False
        lon = 0.0

        if name in [PlanetName.RAHU, PlanetName.KETU]:
            speed = -0.05
            is_retro = True
            if name == PlanetName.RAHU:
                lon = 100.0
            else:
                lon = 280.0  # 180 deg apart

        planets[name] = PlanetState(
            name=name,
            longitude=lon,
            latitude=0,
            speed=speed,
            is_retrograde=is_retro,
            calculated_at=base_time,
        )
    return planets


@pytest.fixture
def mock_state_rahu_kala(valid_planets):
    dt = datetime.now(timezone.utc)
    return NavagrahaState(
        planets=valid_planets,
        guna_distribution=GunaDistribution(sattva=0.34, rajas=0.33, tamas=0.33, calculated_at=dt),
        aspects=[],
        rahu_kala_active=True,
        calculated_at=dt,
        location_lat=28.6,
        location_lon=77.2,
        current_dasha=None,
    )


@pytest.fixture
def mock_state_sattva(valid_planets):
    dt = datetime.now(timezone.utc)
    return NavagrahaState(
        planets=valid_planets,
        guna_distribution=GunaDistribution(sattva=0.8, rajas=0.1, tamas=0.1, calculated_at=dt),
        aspects=[],
        rahu_kala_active=False,
        calculated_at=dt,
        location_lat=28.6,
        location_lon=77.2,
        current_dasha=None,
    )


@pytest.mark.asyncio
async def test_rahu_kala_penalty(
    system_identity, mock_navagraha_service, base_market_data, mock_state_rahu_kala
):
    # Setup: Rahu Kala is Active
    mock_navagraha_service.get_current_state.return_value = mock_state_rahu_kala

    # Execute Cycle
    result = await system_identity.process_market_cycle(**base_market_data)

    # Verify: Coherence should be reduced.
    perception = result["perception"]
    assert perception["rahu_kala_active"] == True
    mock_navagraha_service.get_current_state.assert_called_once()


@pytest.mark.asyncio
async def test_sattva_boost(
    system_identity, mock_navagraha_service, base_market_data, mock_state_sattva
):
    # Setup: High Sattva
    mock_navagraha_service.get_current_state.return_value = mock_state_sattva

    # Execute Cycle
    result = await system_identity.process_market_cycle(**base_market_data)

    # Verify interaction.
    mock_navagraha_service.get_current_state.assert_called_once()
    assert result["perception"]["guna_context"]["sattva"] > 0.5
