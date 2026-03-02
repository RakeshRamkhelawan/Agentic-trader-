import asyncio
import os

import pytest
from dotenv import load_dotenv

# Load env before imports
load_dotenv()

# Override DB URL for local host access if needed
# If running on host, we need localhost:5456
# If running in docker, we need postgres:5432
# FOr this script running on HOST:
if os.getenv("POSTGRES_PORT") == "5432":  # If mistakenly set to internal
    pass
    # Actually, let's just force the known localhost mapping for this test script
    # os.environ["DATABASE_URL"] = "postgresql+asyncpg://app:app_secure@localhost:5456/trading_db"

import redis.asyncio as redis
from sqlalchemy import text

from backend.core.config.settings import settings

# backend.core.database uses DATABASE_URL from env.
from backend.core.database import system_admin_session
from backend.storage.clickhouse_init import get_clickhouse_client


@pytest.mark.asyncio
async def test_redis_connection():
    """Verify Redis connection."""
    print(f"Connecting to Redis at {settings.REDIS_URL}")
    r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await r.ping()
    await r.set("integration_test_key", "valid")
    val = await r.get("integration_test_key")
    assert val == "valid"
    await r.close()
    print("✅ Redis Connection OK")


@pytest.mark.asyncio
async def test_postgres_connection():
    """Verify Postgres connection."""
    print("Connecting to Postgres...")
    async with system_admin_session() as session:
        result = await session.execute(text("SELECT 1"))
        val = result.scalar()
        assert val == 1
    print("✅ Postgres Connection OK")


def test_clickhouse_connection():
    """Verify ClickHouse connection."""
    print(f"Connecting to ClickHouse at {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}")
    client = get_clickhouse_client()
    assert client is not None
    result = client.command("SELECT 1")
    assert result == 1
    print("✅ ClickHouse Connection OK")


@pytest.mark.asyncio
async def test_clickhouse_writer_integration():
    """Verify ClickHouseWriter can write and read from REAL ClickHouse."""
    import time
    from datetime import datetime

    from backend.market_data.sinks.clickhouse_writer import ClickHouseWriter

    client = get_clickhouse_client()
    assert client is not None

    # Ensure table exists (MEMORY engine for speed/cleanup)
    client.command("CREATE TABLE IF NOT EXISTS market_events_test ENGINE = Memory AS market_events")

    writer = ClickHouseWriter(client, table="market_events_test", batch_size=1, flush_interval=0.1)

    ts = datetime.now().timestamp()
    item = {
        "symbol": "TEST/INT",
        "ts_exchange": ts,
        "ts_received": ts,
        "price": 123.45,
        "bids": [(123.40, 1.0)],
        "asks": [(123.50, 1.0)],
        "size": 0.5,
        "side": "buy",
        "checksum": 999,
    }

    await writer.enqueue(item)

    # Run writer briefly
    task = asyncio.create_task(writer.run())
    await asyncio.sleep(0.5)
    writer.stop()
    await task

    # Verify Data
    await asyncio.sleep(0.5)

    result = client.query("SELECT * FROM market_events_test WHERE symbol='TEST/INT'")
    assert result.row_count >= 1

    # Cleanup
    client.command("DROP TABLE market_events_test")
    print("✅ ClickHouse Writer OK")


if __name__ == "__main__":
    # Force Windows Scheduler for proper loop handling if needed, but default is usually fine in 3.13
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(test_redis_connection())
        loop.run_until_complete(test_postgres_connection())
        test_clickhouse_connection()  # Sync
        loop.run_until_complete(test_clickhouse_writer_integration())
        print("\n🎉 ALL ARCHITECTURE TESTS PASSED 🎉")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
    finally:
        loop.close()
