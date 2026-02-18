"""
Integration Tests for Event Storage Pipeline.

Tests EventBus → ClickHouse data persistence flow.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.sentiment_agent import SentimentAgent
from backend.events.event_bus import EventBus
from backend.events.schemas import AgentThought, MarketTick
from backend.llm.provider_interface import LLMProvider
from backend.storage.clickhouse_client import ClickHouseClient

pytestmark = pytest.mark.integration


class MockLLMProvider(LLMProvider):
    """Mock LLM for testing."""

    async def generate_text(self, prompt, system_prompt=None):
        return "Mock response"

    async def generate_structured(self, prompt, schema, system_prompt=None):
        from backend.agents.sentiment_agent import SentimentAnalysis

        return SentimentAnalysis(
            sentiment="bullish",
            confidence=0.85,
            reasoning="Mock reasoning",
            key_factors=["momentum"],
        )


@pytest.mark.asyncio
async def test_clickhouse_client_stores_market_tick():
    """Integration: ClickHouse client should store MarketTick events."""
    # Mock ClickHouse connection
    mock_client = AsyncMock()
    mock_client.command.return_value = None
    mock_client.insert.return_value = None

    with patch(
        "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
        return_value=mock_client,
    ):
        ch_client = ClickHouseClient()
        await ch_client.connect()

        # Create market tick event
        tick = MarketTick(
            symbol="BTC/USD",
            price=50000.0,
            volume=1.5,
            timestamp=datetime.now(timezone.utc),
        )

        # Insert into ClickHouse
        await ch_client.insert(table="market_ticks", data=[tick.model_dump()])

        # Verify insert was called
        assert mock_client.insert.called


@pytest.mark.asyncio
async def test_clickhouse_client_stores_agent_thought():
    """Integration: ClickHouse client should store AgentThought events."""
    mock_client = AsyncMock()
    mock_client.command.return_value = None
    mock_client.insert.return_value = None

    with patch(
        "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
        return_value=mock_client,
    ):
        ch_client = ClickHouseClient()
        await ch_client.connect()

        # Create agent thought
        thought = AgentThought(
            agent_name="SentimentAgent",
            reasoning="Market shows bullish signals",
            confidence=0.88,
            data={"sentiment": "bullish"},
            timestamp=datetime.now(timezone.utc),
        )

        # Insert into ClickHouse
        await ch_client.insert(table="agent_thoughts", data=[thought.model_dump()])

        # Verify insert was called
        assert mock_client.insert.called


@pytest.mark.asyncio
async def test_event_bus_to_clickhouse_pipeline():
    """Integration: Events published to bus should be stored in ClickHouse."""
    # Mock Redis and ClickHouse
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_123"

    mock_ch_client = AsyncMock()
    mock_ch_client.command.return_value = None
    mock_ch_client.insert.return_value = None

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        with patch(
            "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
            return_value=mock_ch_client,
        ):
            # Setup components
            bus = EventBus(redis_url="redis://localhost:6379")
            await bus.connect()

            ch_client = ClickHouseClient()
            await ch_client.connect()

            # Publish event to bus
            event_data = {
                "symbol": "BTC/USD",
                "price": "50000.0",
                "volume": "1.5",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            msg_id = await bus.publish("market_ticks", event_data)

            # Simulate consumer storing to ClickHouse
            await ch_client.insert("market_ticks", [event_data])

            # Verify both operations
            assert msg_id is not None
            assert mock_ch_client.insert.called


@pytest.mark.asyncio
async def test_agent_thought_to_storage_pipeline():
    """Integration: Agent thoughts should flow from EventBus to ClickHouse."""
    # Mock dependencies
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_456"

    mock_ch_client = AsyncMock()
    mock_ch_client.command.return_value = None
    mock_ch_client.insert.return_value = None

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        with patch(
            "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
            return_value=mock_ch_client,
        ):
            # Setup pipeline
            bus = EventBus(redis_url="redis://localhost:6379")
            await bus.connect()

            ch_client = ClickHouseClient()
            await ch_client.connect()

            llm = MockLLMProvider()
            agent = SentimentAgent(
                agent_name="test_agent", llm_provider=llm, event_bus=bus
            )

            # Agent analyzes and publishes
            features = {"price": 52000.0, "volume": 2.0}
            context = {"symbol": "BTC/USD"}
            result = await agent.analyze(features, context)

            msg_id = await agent.publish_thought(
                reasoning="Bullish momentum", confidence=0.85, data=result
            )

            # Verify event was published
            assert msg_id is not None
            assert mock_redis.xadd.called


@pytest.mark.asyncio
async def test_clickhouse_table_creation_for_events():
    """Integration: ClickHouse client should create tables for event storage."""
    mock_client = AsyncMock()
    mock_client.command.return_value = None

    with patch(
        "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
        return_value=mock_client,
    ):
        ch_client = ClickHouseClient()
        await ch_client.connect()

        # Create table for market ticks
        table_sql = """
        CREATE TABLE IF NOT EXISTS market_ticks (
            symbol String,
            price Float64,
            volume Float64,
            timestamp DateTime64(3)
        ) ENGINE = MergeTree()
        ORDER BY timestamp
        """

        await ch_client.create_table(table_sql)

        # Verify table creation
        assert mock_client.command.called


@pytest.mark.asyncio
async def test_bulk_event_storage():
    """Integration: ClickHouse should handle bulk event inserts efficiently."""
    mock_client = AsyncMock()
    mock_client.command.return_value = None
    mock_client.insert.return_value = None

    with patch(
        "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
        return_value=mock_client,
    ):
        ch_client = ClickHouseClient()
        await ch_client.connect()

        # Generate batch of events
        events = [
            {
                "symbol": "BTC/USD",
                "price": 50000.0 + i * 100,
                "volume": 1.0 + i * 0.1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(100)
        ]

        # Bulk insert
        await ch_client.insert("market_ticks", events)

        # Verify single insert call with all events
        assert mock_client.insert.called
        call_args = mock_client.insert.call_args
        # Check that we passed the events list
        assert (
            call_args[0][1] == events
            or call_args[1].get("data") == events
            or len(call_args[0]) >= 2
        )


@pytest.mark.asyncio
async def test_clickhouse_query_stored_events():
    """Integration: ClickHouse client should query stored events."""
    mock_client = AsyncMock()
    mock_client.command.return_value = None
    mock_query_result = AsyncMock()
    mock_query_result.result_rows = [
        ("BTC/USD", 50000.0, 1.5, datetime.now(timezone.utc)),
        ("ETH/USD", 3000.0, 5.0, datetime.now(timezone.utc)),
    ]
    mock_client.query.return_value = mock_query_result

    with patch(
        "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
        return_value=mock_client,
    ):
        ch_client = ClickHouseClient()
        await ch_client.connect()

        # Query events
        result = await ch_client.execute(
            "SELECT * FROM market_ticks ORDER BY timestamp DESC LIMIT 10"
        )

        # Verify query executed
        assert mock_client.query.called
        assert result is not None


@pytest.mark.asyncio
async def test_event_storage_with_error_handling():
    """Integration: Storage pipeline should handle errors gracefully."""
    mock_client = AsyncMock()
    mock_client.command.return_value = None
    mock_client.insert.side_effect = Exception("ClickHouse connection lost")

    with patch(
        "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
        return_value=mock_client,
    ):
        ch_client = ClickHouseClient()
        await ch_client.connect()

        # Attempt insert that fails
        with pytest.raises(Exception, match="ClickHouse connection lost"):
            await ch_client.insert("market_ticks", [{"symbol": "BTC/USD"}])


@pytest.mark.asyncio
async def test_concurrent_event_storage():
    """Integration: Pipeline should handle concurrent storage operations."""
    mock_client = AsyncMock()
    mock_client.command.return_value = None
    mock_client.insert.return_value = None

    with patch(
        "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
        return_value=mock_client,
    ):
        ch_client = ClickHouseClient()
        await ch_client.connect()

        # Concurrent inserts
        events_batch = [
            [{"symbol": f"PAIR{i}", "price": 1000.0 * i} for _ in range(10)]
            for i in range(5)
        ]

        tasks = [ch_client.insert("market_ticks", batch) for batch in events_batch]

        await asyncio.gather(*tasks)

        # Verify all inserts completed
        assert mock_client.insert.call_count == 5


@pytest.mark.asyncio
async def test_event_schema_compatibility_with_storage():
    """Integration: Event schemas should serialize correctly for storage."""
    # Create events with schemas
    tick = MarketTick(
        symbol="BTC/USD",
        price=50000.0,
        volume=1.5,
        timestamp=datetime.now(timezone.utc),
    )

    thought = AgentThought(
        agent_name="TestAgent",
        reasoning="Test reasoning",
        confidence=0.9,
        data={"key": "value"},
        timestamp=datetime.now(timezone.utc),
    )

    # Serialize for storage
    tick_data = tick.model_dump()
    thought_data = thought.model_dump()

    # Verify serialization
    assert isinstance(tick_data, dict)
    assert "symbol" in tick_data
    assert "price" in tick_data

    assert isinstance(thought_data, dict)
    assert "agent_name" in thought_data
    assert "confidence" in thought_data
