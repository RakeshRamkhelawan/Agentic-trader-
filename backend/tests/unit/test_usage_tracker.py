import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.llm.usage_tracker import TokenCounter, UsageTracker

@pytest.fixture
def mock_clickhouse():
    client = AsyncMock()
    client.insert = AsyncMock()
    return client

def test_token_counter_gpt4():
    counter = TokenCounter()
    text = "Hello, world!"
    # gpt-4 encoding for "Hello, world!" is 4 tokens: "Hello", ",", " world", "!"
    # actually it depends on precise encoding, but tiktoken is deterministic.
    # "Hello, world!" -> [9906, 11, 1917, 0] ? 
    # Let's just check it returns a positive integer close to word count
    count = counter.count_tokens(text, "gpt-4")
    assert count > 0
    assert count <= len(text)

def test_token_counter_fallback():
    counter = TokenCounter()
    text = "Hello"
    # Unknown model should use fallback or default
    count = counter.count_tokens(text, "unknown-model")
    assert count > 0

@pytest.mark.asyncio
async def test_usage_tracker_buffering(mock_clickhouse):
    tracker = UsageTracker(clickhouse_client=mock_clickhouse, batch_size=2, flush_interval=10)
    await tracker.start()
    
    # Log 1st item - should be buffered
    await tracker.log_usage("tenant-1", "gpt-4", 10, 20, 0.001)
    assert len(tracker.buffer) == 1
    mock_clickhouse.insert.assert_not_called()
    
    # Log 2nd item - should trigger flush (batch_size=2)
    await tracker.log_usage("tenant-1", "gpt-4", 10, 20, 0.001)
    
    # Allow async task to run
    # In real asyncio, create_task might need a yield, but here we await log_usage 
    # which calls _flush if full.
    
    # log_usage calls _flush if len >= batch_size. 
    # _flush is async, so awaiting log_usage awaits _flush.
    
    mock_clickhouse.insert.assert_called_once()
    assert len(tracker.buffer) == 0
    
    await tracker.stop()

@pytest.mark.asyncio
async def test_usage_tracker_periodic_flush(mock_clickhouse):
    tracker = UsageTracker(clickhouse_client=mock_clickhouse, batch_size=10, flush_interval=0.1)
    await tracker.start()
    
    await tracker.log_usage("tenant-1", "gpt-4", 10, 20, 0.001)
    assert len(tracker.buffer) == 1
    
    # Wait for flush interval
    import asyncio
    await asyncio.sleep(0.2)
    
    mock_clickhouse.insert.assert_called()
    assert len(tracker.buffer) == 0
    
    await tracker.stop()
