"""
Market Data Processor Service.

Responsibility:
- Ingest raw Websocket/REST data from Providers.
- Normalize to internal 'MarketTick' format.
- Publish to Kafka topic 'market_data'.
- Calculate real-time Technical Indicators (Stream Processing).
"""

import asyncio
import logging


async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Market Data Processor...")
    # TODO: Connect to Polygon/Alpaca
    # TODO: Connect to Kafka
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
