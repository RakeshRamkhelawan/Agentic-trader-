#!/usr/bin/env python3
"""
Asset Discovery Manager - Beheer de AssetDiscoveryAgent.

Dit script vervangt de handmatige scripts:
- fetch_bitvavo_assets.py
- fetch_revolut_assets.py
- import_assets.py

Usage:
    # Start agent als autonome service
    python scripts/asset_discovery_manager.py --start
    
    # Eenmalige discovery cycle
    python scripts/asset_discovery_manager.py --discover
    
    # Metadata sync voor actieve assets
    python scripts/asset_discovery_manager.py --sync-metadata
    
    # Toon statistics
    python scripts/asset_discovery_manager.py --stats
    
    # Stop de agent (als die draait)
    python scripts/asset_discovery_manager.py --stop
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.agents.asset_discovery_agent import AssetDiscoveryAgent

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AssetDiscoveryManager")


async def start_agent_service():
    """Start de AssetDiscoveryAgent als autonome service."""
    logger.info("=" * 60)
    logger.info("Starting AssetDiscoveryAgent Service")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Configuration:")
    logger.info("  - Discovery interval: 24 hours")
    logger.info("  - Metadata sync interval: 1 hour")
    logger.info("  - Exchanges: Bitvavo, Revolut")
    logger.info("")

    agent = AssetDiscoveryAgent(
        discovery_interval=86400,  # 24 hours
        metadata_sync_interval=3600,  # 1 hour
    )

    await agent.start()

    logger.info("")
    logger.info("Agent is running. Press Ctrl+C to stop.")
    logger.info("")

    try:
        while True:
            await asyncio.sleep(10)
            stats = agent.get_statistics()
            if stats.get("assets_discovered", 0) > 0:
                logger.info(
                    f"Stats: {stats['assets_discovered']} discovered, "
                    f"{stats['assets_updated']} updated"
                )
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Shutting down...")
    finally:
        await agent.stop()
        logger.info("Agent stopped.")


async def run_discovery_once():
    """Voer één discovery cycle uit."""
    logger.info("=" * 60)
    logger.info("Running Asset Discovery (One-time)")
    logger.info("=" * 60)

    agent = AssetDiscoveryAgent()
    await agent._init_db()

    start_time = time.time()
    await agent.run_discovery_cycle()
    duration = time.time() - start_time

    stats = agent.get_statistics()
    logger.info("")
    logger.info("Results:")
    logger.info(f"  - Assets discovered: {stats['assets_discovered']}")
    logger.info(f"  - Duration: {duration:.2f}s")
    logger.info("")

    await agent.stop()


async def run_metadata_sync():
    """Sync metadata voor actieve assets."""
    logger.info("=" * 60)
    logger.info("Running Metadata Sync")
    logger.info("=" * 60)

    agent = AssetDiscoveryAgent()
    await agent._init_db()

    start_time = time.time()
    await agent.run_metadata_sync()
    duration = time.time() - start_time

    stats = agent.get_statistics()
    logger.info("")
    logger.info("Results:")
    logger.info(f"  - Assets updated: {stats['assets_updated']}")
    logger.info(f"  - Duration: {duration:.2f}s")
    logger.info("")

    await agent.stop()


async def show_stats():
    """Toon huidige statistics."""
    logger.info("=" * 60)
    logger.info("AssetDiscoveryAgent Statistics")
    logger.info("=" * 60)
    logger.info("")

    # TODO: Fetch from database
    logger.info("Run with --discover or --start to see live stats.")


def main():
    parser = argparse.ArgumentParser(
        description="Asset Discovery Manager - Beheer asset discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start autonome service
  python %(prog)s --start
  
  # Eenmalige discovery
  python %(prog)s --discover
  
  # Sync metadata
  python %(prog)s --sync-metadata
  
  # Toon statistics
  python %(prog)s --stats
        """,
    )

    parser.add_argument(
        "--start", action="store_true", help="Start de agent als autonome service"
    )
    parser.add_argument(
        "--discover", action="store_true", help="Voer één discovery cycle uit"
    )
    parser.add_argument(
        "--sync-metadata", action="store_true", help="Sync metadata voor actieve assets"
    )
    parser.add_argument("--stats", action="store_true", help="Toon statistics")

    args = parser.parse_args()

    if args.start:
        asyncio.run(start_agent_service())
    elif args.discover:
        asyncio.run(run_discovery_once())
    elif args.sync_metadata:
        asyncio.run(run_metadata_sync())
    elif args.stats:
        asyncio.run(show_stats())
    else:
        parser.print_help()
        print(
            "\nGeen actie gespecificeerd. Gebruik --start, --discover, --sync-metadata, of --stats"
        )


if __name__ == "__main__":
    main()
