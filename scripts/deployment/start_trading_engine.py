#!/usr/bin/env python3
"""Start the trading engine directly without bash script"""
import asyncio
import logging
import sys

# Add backend to path
sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TradingEngine")

async def main():
    from backend.main import start_services
    await start_services()

if __name__ == "__main__":
    asyncio.run(main())
