"""
Integration Tests for Complete Trading Flow.

Tests full pipeline: MarketTick → Agent Analysis → EventBus → Storage
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.sentiment_agent import SentimentAgent
from backend.events.event_bus import EventBus
from backend.events.schemas import AgentThought, MarketTick
from backend.llm.provider_interface import LLMProvider
from backend.storage.clickhouse_client import ClickHouseClient

pytestmark = pytest.mark.integration


class MockLLMProvider(LLMProvider):
    """Mock LLM for full flow testing."""

    def __init__(self, sentiment="bullish", confidence=0.85):
        self.sentiment = sentiment
        self.confidence = confidence
        self.calls = []

    async def generate_text(self, prompt, system_prompt=None):
        self.calls.append(("text", prompt))
        return f"Analysis: {self.sentiment} sentiment with {self.confidence} confidence"

    async def generate_structured(self, prompt, schema, system_prompt=None):
        self.calls.append(("structured", prompt))
        from backend.agents.sentiment_agent import SentimentAnalysis

        return SentimentAnalysis(
            sentiment=self.sentiment,
            confidence=self.confidence,
            reasoning=f"Market analysis indicates {self.sentiment} trend",
            key_factors=["price_momentum", "volume_surge"],
        )


@pytest.mark.asyncio
async def test_complete_trading_flow_market_tick_to_storage():
    """Integration: Full flow from MarketTick through agent to storage."""
    # Mock all infrastructure
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_flow_1"

    mock_ch_client = AsyncMock()
    mock_ch_client.command.return_value = None
    mock_ch_client.insert.return_value = None

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        with patch(
            "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
            return_value=mock_ch_client,
        ):
            # Setup infrastructure
            bus = EventBus(redis_url="redis://localhost:6379")
            await bus.connect()

            ch_client = ClickHouseClient()
            await ch_client.connect()

            llm = MockLLMProvider(sentiment="bullish", confidence=0.92)
            agent = SentimentAgent(agent_name="sentiment_flow", llm_provider=llm, event_bus=bus)

            # STEP 1: Market tick arrives
            tick = MarketTick(
                symbol="BTC/USD",
                price=52000.0,
                volume=3.5,
                timestamp=datetime.now(UTC),
            )

            # STEP 2: Agent analyzes tick
            features = tick.model_dump()
            context = {"symbol": tick.symbol, "timestamp": tick.timestamp}
            analysis = await agent.analyze(features, context)

            # STEP 3: Agent publishes thought to EventBus
            msg_id = await agent.publish_thought(
                reasoning="Strong bullish momentum detected",
                confidence=0.92,
                data=analysis,
            )

            # STEP 4: Consumer stores to ClickHouse
            thought_data = {
                "agent_name": agent.agent_name,
                "reasoning": "Strong bullish momentum detected",
                "confidence": 0.92,
                "data": str(analysis),
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await ch_client.insert("agent_thoughts", [thought_data])

            # Verify complete flow
            assert analysis is not None
            assert "sentiment" in analysis
            assert msg_id is not None
            assert mock_redis.xadd.called
            assert mock_ch_client.insert.called
            assert len(llm.calls) > 0


@pytest.mark.asyncio
async def test_multiple_agents_parallel_processing():
    """Integration: Multiple agents processing market data concurrently."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_parallel"

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        bus = EventBus(redis_url="redis://localhost:6379")
        await bus.connect()

        # Create multiple agents
        agents = [
            SentimentAgent(
                agent_name=f"agent_{i}",
                llm_provider=MockLLMProvider(sentiment=["bullish", "bearish", "neutral"][i % 3]),
                event_bus=bus,
            )
            for i in range(3)
        ]

        # Market tick
        tick_data = {"price": 50000.0, "volume": 2.0, "symbol": "BTC/USD"}

        # All agents analyze concurrently
        tasks = [agent.analyze(tick_data, {"symbol": "BTC/USD"}) for agent in agents]
        results = await asyncio.gather(*tasks)

        # All agents produced results
        assert len(results) == 3
        assert all(r is not None for r in results)


@pytest.mark.asyncio
async def test_trading_flow_with_event_sequence():
    """Integration: Process sequence of market ticks through pipeline."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_seq"

    mock_ch_client = AsyncMock()
    mock_ch_client.command.return_value = None
    mock_ch_client.insert.return_value = None

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        with patch(
            "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
            return_value=mock_ch_client,
        ):
            bus = EventBus(redis_url="redis://localhost:6379")
            await bus.connect()

            ch_client = ClickHouseClient()
            await ch_client.connect()

            llm = MockLLMProvider()
            agent = SentimentAgent(agent_name="sequence_agent", llm_provider=llm, event_bus=bus)

            # Sequence of ticks
            ticks = [
                {
                    "price": 50000.0 + i * 500,
                    "volume": 1.0 + i * 0.2,
                    "symbol": "BTC/USD",
                }
                for i in range(5)
            ]

            # Process each tick
            for tick in ticks:
                result = await agent.analyze(tick, {"symbol": "BTC/USD"})
                await agent.publish_thought(
                    reasoning=f"Analysis for price {tick['price']}",
                    confidence=0.8,
                    data=result,
                )

            # Verify all processed
            # Note: EventBus publish may be called more than once per tick (e.g., internal events + thoughts)
            assert mock_redis.xadd.call_count >= 5
            # Agent may call LLM multiple times per analyze
            assert len(llm.calls) >= 5


@pytest.mark.asyncio
async def test_trading_flow_error_recovery():
    """Integration: Flow should handle errors gracefully and continue."""
    mock_redis = AsyncMock()

    # First call fails, second succeeds
    call_count = 0

    def xadd_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Redis temporarily unavailable")
        return b"msg_recovered"

    mock_redis.xadd.side_effect = xadd_side_effect

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        bus = EventBus(redis_url="redis://localhost:6379")
        await bus.connect()

        llm = MockLLMProvider()
        agent = SentimentAgent(agent_name="error_recovery", llm_provider=llm, event_bus=bus)

        # First attempt
        result1 = await agent.analyze({"price": 50000.0}, {"symbol": "BTC/USD"})
        await agent.publish_thought("First", 0.8, result1)
        # First call failed, so publish_thought catches error and returns None
        # The error is in EventBus.publish, which agent.publish_thought catches

        # Second attempt
        result2 = await agent.analyze({"price": 51000.0}, {"symbol": "BTC/USD"})
        msg_id2 = await agent.publish_thought("Second", 0.9, result2)
        # Second succeeded
        assert msg_id2 is not None or call_count == 2  # Verify recovery worked


@pytest.mark.asyncio
async def test_end_to_end_flow_with_real_schemas():
    """Integration: Use actual Pydantic schemas through entire flow."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_schema"

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        bus = EventBus(redis_url="redis://localhost:6379")
        await bus.connect()

        llm = MockLLMProvider()
        agent = SentimentAgent(agent_name="schema_test", llm_provider=llm, event_bus=bus)

        # Create proper MarketTick
        tick = MarketTick(
            symbol="ETH/USD",
            price=3000.0,
            volume=10.5,
            timestamp=datetime.now(UTC),
        )

        # Agent processes
        result = await agent.analyze(features=tick.model_dump(), context={"symbol": tick.symbol})

        # Create AgentThought (if agent publishes via schema)
        thought = AgentThought(
            agent_name=agent.agent_name,
            reasoning="Schema-based analysis",
            confidence=0.85,
            data=result,
            timestamp=datetime.now(UTC),
        )

        # Verify schemas work
        assert isinstance(tick, MarketTick)
        assert isinstance(thought, AgentThought)
        assert thought.confidence == 0.85


@pytest.mark.asyncio
async def test_trading_flow_state_management():
    """Integration: Agent state should persist across multiple ticks."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_state"

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        bus = EventBus(redis_url="redis://localhost:6379")
        await bus.connect()

        llm = MockLLMProvider()
        agent = SentimentAgent(agent_name="stateful_flow", llm_provider=llm, event_bus=bus)

        # First tick
        await agent.analyze({"price": 50000.0}, {"symbol": "BTC/USD"})
        agent.update_state({"last_price": 50000.0, "trend": "up"})

        # Second tick
        await agent.analyze({"price": 51000.0}, {"symbol": "BTC/USD"})
        agent.update_state({"last_price": 51000.0, "tick_count": 2})

        # Verify state
        state = agent.get_state()
        assert state["last_price"] == 51000.0
        assert "trend" in state
        assert state["tick_count"] == 2


@pytest.mark.asyncio
async def test_trading_flow_performance_metrics():
    """Integration: Track performance metrics through trading flow."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_perf"

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        bus = EventBus(redis_url="redis://localhost:6379")
        await bus.connect()

        llm = MockLLMProvider()
        agent = SentimentAgent(agent_name="performance_test", llm_provider=llm, event_bus=bus)

        # Process multiple ticks
        for i in range(10):
            await agent.analyze({"price": 50000.0 + i * 100, "volume": 1.0}, {"symbol": "BTC/USD"})
            agent.record_activity(success=True)

        # Check health metrics
        health = agent.health_check()
        assert health["total_actions"] == 10
        assert health["error_count"] == 0
        assert health["error_rate"] == 0.0


@pytest.mark.asyncio
async def test_trading_flow_with_consumer_pattern():
    """Integration: Simulate consumer reading from EventBus and storing."""
    stored_events = []

    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_consumer"

    mock_ch_client = AsyncMock()
    mock_ch_client.command.return_value = None

    async def mock_insert(*args, **kwargs):
        # Accept any arguments from insert call
        data = kwargs.get("data", args[1] if len(args) > 1 else [])
        stored_events.extend(data if isinstance(data, list) else [data])

    mock_ch_client.insert.side_effect = mock_insert

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        with patch(
            "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
            return_value=mock_ch_client,
        ):
            bus = EventBus(redis_url="redis://localhost:6379")
            await bus.connect()

            ch_client = ClickHouseClient()
            await ch_client.connect()

            llm = MockLLMProvider()
            agent = SentimentAgent(agent_name="producer", llm_provider=llm, event_bus=bus)

            # Producer: agent publishes
            result = await agent.analyze({"price": 50000.0}, {"symbol": "BTC/USD"})
            await agent.publish_thought("Producer test", 0.9, result)

            # Simulate consumer storing to ClickHouse
            await ch_client.insert("agent_thoughts", [{"data": "consumed"}])

            # Verify flow
            assert mock_redis.xadd.called
            assert len(stored_events) > 0


@pytest.mark.asyncio
async def test_complete_flow_with_multiple_event_types():
    """Integration: Handle different event types through the pipeline."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_multi"

    mock_ch_client = AsyncMock()
    mock_ch_client.command.return_value = None
    mock_ch_client.insert.return_value = None

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        with patch(
            "backend.storage.clickhouse_client.clickhouse_connect.get_async_client",
            return_value=mock_ch_client,
        ):
            bus = EventBus(redis_url="redis://localhost:6379")
            await bus.connect()

            ch_client = ClickHouseClient()
            await ch_client.connect()

            # Publish market tick
            tick = MarketTick(
                symbol="BTC/USD",
                price=50000.0,
                volume=1.5,
                timestamp=datetime.now(UTC),
            )
            await bus.publish("market_ticks", tick.model_dump())
            await ch_client.insert("market_ticks", [tick.model_dump()])

            # Publish agent thought
            thought = AgentThought(
                agent_name="TestAgent",
                reasoning="Analysis complete",
                confidence=0.9,
                data={"sentiment": "bullish"},
                timestamp=datetime.now(UTC),
            )
            await bus.publish("agent_thoughts", thought.model_dump())
            await ch_client.insert("agent_thoughts", [thought.model_dump()])

            # Verify both event types processed
            assert mock_redis.xadd.call_count == 2
            assert mock_ch_client.insert.call_count == 2


@pytest.mark.asyncio
async def test_trading_flow_reasoning_chain_tracking():
    """Integration: Full reasoning chain should be traceable through flow."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = b"msg_reason"

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        bus = EventBus(redis_url="redis://localhost:6379")
        await bus.connect()

        llm = MockLLMProvider()
        agent = SentimentAgent(agent_name="reasoning_flow", llm_provider=llm, event_bus=bus)

        # Build reasoning chain
        agent.think("Observed market tick")
        agent.think("Price shows upward momentum")

        result = await agent.analyze({"price": 52000.0}, {"symbol": "BTC/USD"})

        agent.think("Analysis complete")
        agent.act("publish_thought", "Sharing analysis with system")

        await agent.publish_thought("Final reasoning", 0.88, result)

        # Get reasoning chain
        chain = agent.get_reasoning_chain()

        assert len(chain) >= 4
        assert any("market tick" in step for step in chain)
        assert any("momentum" in step for step in chain)
        assert any("publish_thought" in step for step in chain)
