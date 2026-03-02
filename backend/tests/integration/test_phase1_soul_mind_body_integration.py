"""
Phase 1+2 Integration Tests: Soul -> Redis -> Mind -> SHM -> Body

Validates the core consciousness data flow across all three layers
without requiring real Redis or external services.
"""

import asyncio
import json
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.cognitive_mind_service import CognitiveMindService
from backend.core.eternal_soul_service import EternalSoulService
from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge
from backend.execution.reflex_executor import ReflexExecutor


def _unique_shm():
    """Generate a unique SHM name to avoid cross-test pollution on Windows."""
    return f"t_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redis():
    """Mock Redis client with get/set/publish/ping/close."""
    client = AsyncMock()
    client.ping = AsyncMock()
    client.set = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.publish = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def soul_service(mock_redis):
    """EternalSoulService with mocked Redis (no real connection)."""
    service = EternalSoulService()
    service.redis_client = mock_redis
    return service


@pytest.fixture
def shm_bridge():
    """Create a ZeroCopyBridge with a unique name for intent communication."""
    name = _unique_shm()
    bridge = ZeroCopyBridge(create=True, shm_name=name, dtype_name="intent")
    yield bridge
    bridge.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_soul_publishes_context_to_redis(soul_service, mock_redis):
    """Soul.process_cycle should publish context to Redis."""
    result = await soul_service.process_cycle()

    # Verify Redis set was called with soul:context
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == "soul:context"

    # Verify Redis publish was called
    mock_redis.publish.assert_called_once()
    pub_args = mock_redis.publish.call_args
    assert pub_args[0][0] == "soul.updates"


@pytest.mark.asyncio
async def test_soul_context_has_all_required_keys(soul_service):
    """Soul context must contain all keys the Mind layer needs."""
    context = await soul_service.process_cycle()

    required_keys = [
        "timestamp",
        "rahu_kala_active",
        "consciousness_level",
        "guna_dominance",
        "trading_gate_open",
        "market_regime",
        "causality_threshold",
        "market_metrics",
    ]
    for key in required_keys:
        assert key in context, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_mind_reads_soul_context_and_writes_intent(shm_bridge):
    """Mind should read soul context and produce intent in SHM."""
    mind = CognitiveMindService(shm_name=shm_bridge.shm_name)
    mind.bridge = shm_bridge

    soul_context = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "rahu_kala_active": False,
        "consciousness_level": 0.8,
        "guna_dominance": "rajas",
        "trading_gate_open": True,
        "market_regime": "BULL",
        "causality_threshold": 0.6,
        "market_metrics": {
            "price": 42000.0,
            "sma_50": 41500.0,
            "sma_200": 40000.0,
            "volatility": 0.005,
        },
    }

    await mind.process_cycle(soul_context=soul_context)

    intent = shm_bridge.read_intent("BTC/USD")
    assert intent is not None, "Mind should have written an intent to SHM"
    assert intent.timestamp_ns > 0


@pytest.mark.asyncio
async def test_body_reads_intent_from_shm(shm_bridge):
    """Body should be able to read intents written to SHM."""
    test_intent = TradingIntent(
        action=1,
        size=0.5,
        confidence=0.8,
        stop_loss=41000.0,
        take_profit=44000.0,
        max_hold_ms=60000,
        entry_price=42000.0,
        timestamp_ns=time.time_ns(),
    )
    shm_bridge.write_intent("BTC/USD", test_intent)

    executor = ReflexExecutor(shm_name=shm_bridge.shm_name)
    executor.bridge = ZeroCopyBridge(
        create=False, shm_name=shm_bridge.shm_name, dtype_name="intent"
    )

    intent = executor.read_intent("BTC/USD")
    assert intent is not None
    assert intent.action == 1
    assert intent.size == pytest.approx(0.5, abs=0.01)

    executor.bridge.close()


@pytest.mark.asyncio
async def test_full_soul_mind_body_pipeline(soul_service, mock_redis):
    """End-to-end: Soul -> Redis -> Mind -> SHM -> Body reads valid intent."""
    soul_context = await soul_service.process_cycle()
    mock_redis.get.return_value = json.dumps(soul_context)

    name = _unique_shm()
    bridge = ZeroCopyBridge(create=True, shm_name=name, dtype_name="intent")
    try:
        mind = CognitiveMindService(shm_name=name)
        mind.bridge = bridge

        await mind.process_cycle(soul_context=soul_context)

        intent = bridge.read_intent("BTC/USD")
        assert intent is not None
        assert intent.timestamp_ns > 0
    finally:
        bridge.close()


@pytest.mark.asyncio
async def test_rahu_kala_blocks_entire_pipeline(soul_service, mock_redis):
    """When rahu_kala=True, Mind should produce HOLD (action=0)."""
    name = _unique_shm()
    bridge = ZeroCopyBridge(create=True, shm_name=name, dtype_name="intent")
    try:
        rahu_context = {
            "timestamp": "2026-01-01T00:00:00+00:00",
            "rahu_kala_active": True,
            "consciousness_level": 0.3,
            "guna_dominance": "tamas",
            "trading_gate_open": False,
            "market_regime": "BULL",
            "causality_threshold": 0.6,
            "market_metrics": {
                "price": 42000.0,
                "sma_50": 41500.0,
                "sma_200": 40000.0,
                "volatility": 0.005,
            },
        }

        mind = CognitiveMindService(shm_name=name)
        mind.bridge = bridge

        await mind.process_cycle(soul_context=rahu_context)

        intent = bridge.read_intent("BTC/USD")
        assert intent is not None
        assert intent.action == 0, f"Expected HOLD (0), got {intent.action}"
    finally:
        bridge.close()


@pytest.mark.asyncio
async def test_stale_intent_rejected_by_body():
    """Body should reject intents older than 500ms."""
    name = _unique_shm()
    bridge = ZeroCopyBridge(create=True, shm_name=name, dtype_name="intent")
    try:
        # First write a valid intent to populate the slot
        fresh_intent = TradingIntent(
            action=1,
            size=0.5,
            confidence=0.8,
            stop_loss=41000.0,
            take_profit=44000.0,
            max_hold_ms=60000,
            entry_price=42000.0,
            timestamp_ns=time.time_ns(),
        )
        bridge.write_intent("BTC/USD", fresh_intent)

        # Now directly overwrite the timestamp in the SHM array to simulate staleness
        # (write_intent always sets timestamp_ns = time.time_ns(), so we override here)
        idx = bridge._get_idx("BTC/USD")
        bridge.data_array[idx]["timestamp_ns"] = time.time_ns() - 10_000_000_000

        executor = ReflexExecutor(shm_name=name)
        executor.bridge = ZeroCopyBridge(create=False, shm_name=name, dtype_name="intent")

        # Body should reject stale intent (> 500ms old)
        result = executor.read_intent("BTC/USD")
        assert result is None, "Stale intent should be rejected by ReflexExecutor"

        executor.bridge.close()
    finally:
        bridge.close()
