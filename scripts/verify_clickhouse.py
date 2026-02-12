
import asyncio
import logging
import requests
import time
from backend.storage.clickhouse_init import get_clickhouse_client, init_clickhouse
from backend.market_data.models import UnifiedMarketEvent, EventType
from backend.core.config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("--- Starting ClickHouse Verification ---")
    
    # 1. Connection (Requests)
    try:
        settings = Settings()
        url = f"http://{settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}/?query=SELECT%201"
        logger.info(f"Testing Raw Requests to {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}...")
        response = requests.get(url, auth=(settings.CLICKHOUSE_USER, settings.CLICKHOUSE_PASSWORD))
        if response.status_code == 200:
            logger.info("✅ Raw Requests: Success!")
        else:
            logger.error(f"❌ Raw Requests Failed: {response.text}")
            return
    except Exception as e:
        logger.error(f"❌ Raw Requests Connection Error: {e}")
        return

    # 2. Init Schema
    try:
        logger.info("Initializing Schema...")
        if not init_clickhouse():
             logger.error("❌ Schema Initialization Failed (init_clickhouse returned False).")
             return
        
        client = get_clickhouse_client()
        if not client:
             logger.error("❌ Failed to get ClickHouse client.")
             return

        logger.info("Verifying table 'market_events' exists...")
        # Check table exists via command
        exists = client.command("EXISTS TABLE market_events")
        if exists:
             logger.info("✅ Table 'market_events' exists.")
        else:
             logger.error("❌ Table 'market_events' does NOT exist.")
             return
    except Exception as e:
        logger.error(f"❌ Schema Initialization Failed: {e}")
        return

    # 3. Insert Test Data via ClickHouseWriter
    from backend.market_data.sinks.clickhouse_writer import ClickHouseWriter
    logger.info("Instantiating ClickHouseWriter...")
    writer = ClickHouseWriter(client, table="market_events", batch_size=1, flush_interval=0.1)
    
    logger.info("Enqueuing Test Event...")
    event = UnifiedMarketEvent(
        event_type=EventType.TICKER,
        venue="test_venue",
        symbol="TEST/USDT",
        ts_exchange=time.time(),
        ts_received=time.time(),
        price=100.5,
        size=1.0,
        side="buy",
        bids=[(100.0, 1.0), (99.0, 2.0)],
        asks=[(101.0, 1.0), (102.0, 0.5)]
    )
    
    batch = [event.to_dict()]
    try:
        logger.info("Flushing batch via Writer...")
        await writer._flush(batch)
        logger.info("✅ Insertion via Writer Successful.")
    except Exception as e:
        logger.error(f"❌ Insertion via Writer Failed: {e}")
        return

    # 4. Query Data
    logger.info("Sleeping 1s for consistency...")
    await asyncio.sleep(1)
    
    try:
        # Check Count
        count_res = client.query("SELECT count() FROM market_events")
        logger.info(f"Total Rows: {count_res.first_row[0]}")
        
        # Query Specific
        result = client.query("SELECT * FROM market_events WHERE symbol='TEST/USDT' ORDER BY ts_received DESC LIMIT 1")
        if result.row_count > 0:
            logger.info(f"✅ Data Retrieved: {result.first_row}")
        else:
            logger.error("❌ No data found for TEST/USDT.")
            # Show all data?
            all_res = client.query("SELECT symbol, ts_received FROM market_events LIMIT 5")
            logger.info(f"Sample Data: {all_res.result_rows}")
    except Exception as e:
        logger.error(f"❌ Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
