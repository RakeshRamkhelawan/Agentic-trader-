import asyncio
import json
import uuid
from unittest.mock import AsyncMock

import pytest

from backend.core.zero_copy_bridge import ZeroCopyBridge

# Skip tests if reflex_executor imports fail (shadow_portfolio was removed in Week 8)
pytest.importorskip("backend.execution.reflex_executor")

from datetime import UTC

from backend.execution.reflex_executor import ReflexExecutor


@pytest.fixture
def unique_shm_name():
    return f"test_integ_{uuid.uuid4().hex}"


@pytest.mark.asyncio
async def test_mind_to_body_flow(unique_shm_name):
    """
    Test complete flow: CognitiveMind -> ZeroCopyBridge -> ReflexExecutor

    Validates:
    - Mind kan besluiten nemen
    - Bridge kan serialized besluiten naar SHM schrijven
    - Body (ReflexExecutor) kan besluiten lezen en ACK terugsturen
    """
    # Setup ZeroCopyBridge
    bridge = ZeroCopyBridge(
        shm_name=unique_shm_name,
        shm_size=65536,
        max_chunk_size=32768,
    )

    await bridge.connect()

    try:
        # Setup ReflexExecutor (Body) - mocks exchange
        mock_exchange = AsyncMock()
        mock_exchange.submit_order = AsyncMock(return_value={"order_id": "test-123"})

        body = ReflexExecutor(
            exchange_interface=mock_exchange,
            shm_name=unique_shm_name,
            poll_interval_ms=10,  # Fast polling for test
        )

        # Start body executor in background
        body_task = asyncio.create_task(body.run())

        # Simulate CognitiveMind decision
        decision = {
            "action": "BUY",
            "symbol": "BTC-EUR",
            "quantity": 1.0,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Write decision via Bridge (Mind side)
        decision_bytes = json.dumps(decision).encode("utf-8")
        await bridge.write_chunk(decision_bytes, is_final=True)

        # Wait for body to process
        await asyncio.sleep(0.1)

        # Verify body processed the order
        mock_exchange.submit_order.assert_called_once()
        call_args = mock_exchange.submit_order.call_args[0][0]
        assert call_args["action"] == "BUY"
        assert call_args["symbol"] == "BTC-EUR"

        # Verify ACK was written back
        ack_chunk = await bridge.read_chunk()
        assert ack_chunk is not None
        ack = json.loads(ack_chunk.decode("utf-8"))
        assert ack["status"] == "ACK"
        assert ack["order_id"] == "test-123"

    finally:
        # Cleanup
        body.stop()
        body_task.cancel()
        try:
            await body_task
        except asyncio.CancelledError:
            pass
        await bridge.disconnect()


@pytest.mark.asyncio
async def test_shm_full_handling(unique_shm_name):
    """Test dat ReflexExecutor gracefully omgaat met volle SHM."""
    bridge = ZeroCopyBridge(
        shm_name=unique_shm_name,
        shm_size=1024,  # Klein voor test
        max_chunk_size=512,
    )

    await bridge.connect()

    try:
        mock_exchange = AsyncMock()
        body = ReflexExecutor(
            exchange_interface=mock_exchange,
            shm_name=unique_shm_name,
            poll_interval_ms=10,
        )

        body_task = asyncio.create_task(body.run())

        # Schrijf te grote data
        huge_data = b"X" * 2048  # Groter dan SHM

        with pytest.raises((ValueError, BufferError)):  # Zou moeten falen of truncated
            await bridge.write_chunk(huge_data, is_final=True)

        # Executor moet nog steeds draaien (niet gecrasht)
        assert body._running is True

    finally:
        body.stop()
        body_task.cancel()
        try:
            await body_task
        except asyncio.CancelledError:
            pass
        await bridge.disconnect()


@pytest.mark.asyncio
async def test_body_timeout_recovery(unique_shm_name):
    """Test dat ReflexExecutor recovert na timeout."""
    bridge = ZeroCopyBridge(
        shm_name=unique_shm_name,
        shm_size=4096,
    )

    await bridge.connect()

    try:
        mock_exchange = AsyncMock()
        mock_exchange.submit_order = AsyncMock(
            side_effect=[
                TimeoutError("Exchange timeout"),
                {"order_id": "retry-123"},  # Retry succeeds
            ]
        )

        body = ReflexExecutor(
            exchange_interface=mock_exchange,
            shm_name=unique_shm_name,
            poll_interval_ms=10,
        )

        body_task = asyncio.create_task(body.run())

        # Eerste poging faalt (timeout)
        decision = {"action": "SELL", "symbol": "ETH-EUR", "quantity": 0.5}
        await bridge.write_chunk(json.dumps(decision).encode(), is_final=True)

        await asyncio.sleep(0.2)

        # Moet 2x geroepen zijn (retry)
        assert mock_exchange.submit_order.call_count == 2

        # ACK van retry
        ack_chunk = await bridge.read_chunk()
        ack = json.loads(ack_chunk.decode())
        assert ack["order_id"] == "retry-123"

    finally:
        body.stop()
        body_task.cancel()
        try:
            await body_task
        except asyncio.CancelledError:
            pass
        await bridge.disconnect()


# Import needed for test
from datetime import datetime
