"""
Execution Gateway Service.

Responsibility:
- Translate internal OrderRequests to Broker API calls (FIX/REST).
- Manage connection state with Brokers (Revolut, IBKR).
- Publish OrderFill events to Kafka.
"""

import asyncio
import logging

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Execution Gateway Service...")
    # TODO: Initialize Broker Adapters
    # TODO: Connect to Kafka
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
