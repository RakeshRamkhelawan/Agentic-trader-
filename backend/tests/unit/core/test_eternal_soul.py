import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.eternal_soul_service import EternalSoulService
from backend.core.navagraha.models import (
    GunaDistribution,
    NavagrahaState,
    PlanetName,
    PlanetState,
)
from backend.core.regime_detector import MarketRegime


@pytest.fixture
def mock_navagraha_state():
    return NavagrahaState(
        planets={
            PlanetName.SUN: PlanetState(
                name=PlanetName.SUN,
                longitude=0,
                latitude=0,
                speed=1,
                is_retrograde=False,
                calculated_at=datetime.now(),
            ),
            PlanetName.MOON: PlanetState(
                name=PlanetName.MOON,
                longitude=0,
                latitude=0,
                speed=13,
                is_retrograde=False,
                calculated_at=datetime.now(),
            ),
            PlanetName.MARS: PlanetState(
                name=PlanetName.MARS,
                longitude=0,
                latitude=0,
                speed=0.5,
                is_retrograde=False,
                calculated_at=datetime.now(),
            ),
            PlanetName.MERCURY: PlanetState(
                name=PlanetName.MERCURY,
                longitude=0,
                latitude=0,
                speed=1.5,
                is_retrograde=False,
                calculated_at=datetime.now(),
            ),
            PlanetName.JUPITER: PlanetState(
                name=PlanetName.JUPITER,
                longitude=0,
                latitude=0,
                speed=0.2,
                is_retrograde=False,
                calculated_at=datetime.now(),
            ),
            PlanetName.VENUS: PlanetState(
                name=PlanetName.VENUS,
                longitude=0,
                latitude=0,
                speed=1.2,
                is_retrograde=False,
                calculated_at=datetime.now(),
            ),
            PlanetName.SATURN: PlanetState(
                name=PlanetName.SATURN,
                longitude=0,
                latitude=0,
                speed=0.1,
                is_retrograde=False,
                calculated_at=datetime.now(),
            ),
            PlanetName.RAHU: PlanetState(
                name=PlanetName.RAHU,
                longitude=0,
                latitude=0,
                speed=-0.05,
                is_retrograde=True,
                calculated_at=datetime.now(),
            ),
            PlanetName.KETU: PlanetState(
                name=PlanetName.KETU,
                longitude=180,
                latitude=0,
                speed=-0.05,
                is_retrograde=True,
                calculated_at=datetime.now(),
            ),
        },
        guna_distribution=GunaDistribution(
            sattva=0.4, rajas=0.3, tamas=0.3, calculated_at=datetime.now()
        ),
        rahu_kala_active=True,
        calculated_at=datetime.now(),
        location_lat=0,
        location_lon=0,
    )


from datetime import datetime


@pytest.mark.asyncio
async def test_eternal_soul_start_stop():
    with (
        patch("backend.core.eternal_soul_service.redis.from_url") as mock_redis_cls,
        patch("backend.core.eternal_soul_service.NavagrahaService") as mock_navagraha_cls,
        patch("backend.core.eternal_soul_service.RegimeDetector") as mock_regime_cls,
    ):

        mock_redis = AsyncMock()
        mock_redis_cls.return_value = mock_redis

        # Mock instance methods to prevent failures
        mock_navagraha_instance = AsyncMock()
        mock_navagraha_cls.return_value = mock_navagraha_instance
        # Mocking async method get_current_state
        mock_navagraha_instance.get_current_state.return_value = MagicMock(rahu_kala_active=False)

        mock_regime_instance = MagicMock()
        mock_regime_cls.return_value = mock_regime_instance
        mock_regime_instance.detect.return_value = MarketRegime.BULL

        service = EternalSoulService()

        # Start
        await service.start()
        assert service.running is True
        mock_redis.ping.assert_called_once()
        assert service._task is not None

        # Stop
        await service.stop()
        assert service.running is False
        assert service._task.cancelled()
        mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_process_cycle(mock_navagraha_state):
    service = EternalSoulService()

    # Mock Redis
    service.redis_client = AsyncMock()

    # Mock NavagrahaService
    service.navagraha = AsyncMock()
    service.navagraha.get_current_state.return_value = mock_navagraha_state

    # Mock RegimeDetector
    service.regime_detector = MagicMock()
    service.regime_detector.detect.return_value = MarketRegime.BEAR

    # Run cycle
    context = await service.process_cycle()

    # Assertions
    assert context["rahu_kala_active"] is True
    assert context["market_regime"] == "BEAR"
    assert context["trading_gate_open"] is False  # Rahu Kala is active

    # Verify Redis calls
    service.redis_client.set.assert_called_once()
    call_args = service.redis_client.set.call_args
    assert call_args.args[0] == "soul:context"
    saved_context = json.loads(call_args.args[1])
    assert saved_context["rahu_kala_active"] is True
    # TTL should be passed as keyword argument 'ex'
    assert call_args.kwargs["ex"] == 90

    service.redis_client.publish.assert_called_once()
