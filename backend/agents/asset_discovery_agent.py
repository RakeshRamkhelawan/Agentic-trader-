"""
AssetDiscoveryAgent - Autonome Asset Data Updates voor Research.

Deze agent vervangt de handmatige scripts:
- scripts/fetch_bitvavo_assets.py
- scripts/fetch_revolut_assets.py
- import_assets.py

Rol in OODA: **OBSERVE** (Asset Discovery Layer)
- Autonome discovery van nieuwe assets op exchanges
- Periodieke sync van asset metadata
- Database import met conflict handling
- Event-driven updates naar Research Agents
"""

import asyncio
import csv
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import backoff
import ccxt.async_support as ccxt
import httpx
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.agents.base_agent import BaseAgent
from backend.assets.models import Asset, AssetStatus, Base
from backend.core.config.settings import settings
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class AssetDiscoveryAgent(BaseAgent):
    """
    AssetDiscovery Agent - Autonome asset discovery en synchronisatie.

    Verantwoordelijkheden:
    1. Discovery: Zoek nieuwe assets op exchanges (Bitvavo, Revolut, etc.)
    2. Metadata Sync: Update prijs, volume, status van bestaande assets
    3. Database Import: Upsert assets naar PostgreSQL met conflict handling
    4. Event Publishing: Notificeer Research Agents van wijzigingen

    Configuratie:
    - discovery_interval: Hoe vaak nieuwe assets zoeken (default: 1x per dag)
    - metadata_sync_interval: Hoe vaak metadata updaten (default: elk uur)
    - batch_size: Database insert batch grootte (default: 50)
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        discovery_interval: int = 86400,  # 24 uur
        metadata_sync_interval: int = 3600,  # 1 uur
        batch_size: int = 50,
    ):
        super().__init__(
            agent_name="AssetDiscovery",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.OBSERVER,
        )

        # Intervals
        self.discovery_interval = discovery_interval
        self.metadata_sync_interval = metadata_sync_interval
        self.batch_size = batch_size

        # Stats
        self.assets_discovered = 0
        self.assets_updated = 0
        self.last_discovery_run: datetime | None = None
        self.last_metadata_sync: datetime | None = None

        # Task refs
        self._discovery_task: asyncio.Task | None = None
        self._metadata_sync_task: asyncio.Task | None = None
        self._running = False

        # Database
        self._db_engine = None
        self._async_session = None

        # Output dir
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    async def _init_db(self):
        """Initialize database connection."""
        if self._db_engine is None:
            db_url = settings.DATABASE_URL
            if "postgresql://" in db_url and "asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

            self._db_engine = create_async_engine(db_url, echo=False)
            self._async_session = sessionmaker(
                self._db_engine, class_=AsyncSession, expire_on_commit=False
            )

            # Ensure tables exist
            async with self._db_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    async def start(self):
        """Start de agent en begin met periodieke taken."""
        if self._running:
            logger.warning("AssetDiscoveryAgent already running")
            return

        self._running = True
        logger.info("AssetDiscoveryAgent starting...")

        # Initialize database
        await self._init_db()

        # Start background tasks
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        self._metadata_sync_task = asyncio.create_task(self._metadata_sync_loop())

        self.act("agent_started", "AssetDiscoveryAgent started with background loops")
        logger.info("AssetDiscoveryAgent started successfully")

    async def stop(self):
        """Stop de agent en cancel achtergrond taken."""
        self._running = False

        if self._discovery_task:
            self._discovery_task.cancel()
        if self._metadata_sync_task:
            self._metadata_sync_task.cancel()

        if self._db_engine:
            await self._db_engine.dispose()

        self.act("agent_stopped", "AssetDiscoveryAgent stopped")
        logger.info("AssetDiscoveryAgent stopped")

    async def _discovery_loop(self):
        """Hoofd loop voor asset discovery - draait periodiek."""
        while self._running:
            try:
                logger.info("[Discovery] Starting asset discovery cycle...")
                await self.run_discovery_cycle()
                self.last_discovery_run = datetime.now(UTC)
                logger.info(f"[Discovery] Completed. Next run in {self.discovery_interval}s")
            except Exception as e:
                logger.error(f"[Discovery] Error in discovery cycle: {e}")
                self.record_activity(success=False)

            await asyncio.sleep(self.discovery_interval)

    async def _metadata_sync_loop(self):
        """Hoofd loop voor metadata sync - draait vaker."""
        while self._running:
            try:
                logger.info("[Metadata] Starting metadata sync cycle...")
                await self.run_metadata_sync()
                self.last_metadata_sync = datetime.now(UTC)
                logger.info(f"[Metadata] Completed. Next run in {self.metadata_sync_interval}s")
            except Exception as e:
                logger.error(f"[Metadata] Error in metadata sync: {e}")
                self.record_activity(success=False)

            await asyncio.sleep(self.metadata_sync_interval)

    async def run_discovery_cycle(self):
        """
        Voer één discovery cycle uit voor alle geconfigureerde exchanges.
        """
        self.think("Starting asset discovery cycle for all exchanges")

        exchanges = ["bitvavo", "revolut"]
        all_assets: dict[str, dict[str, Any]] = {}

        for exchange_id in exchanges:
            try:
                assets = await self._discover_from_exchange(exchange_id)
                for asset in assets:
                    symbol = asset.get("symbol", "")
                    if symbol:
                        all_assets[symbol] = asset

                logger.info(f"[Discovery] Found {len(assets)} assets from {exchange_id}")

            except Exception as e:
                logger.error(f"[Discovery] Failed to fetch from {exchange_id}: {e}")

        # Save to files for debugging/backup
        await self._save_to_files(all_assets)

        # Import naar database
        if all_assets:
            imported = await self._import_to_database(list(all_assets.values()))
            self.assets_discovered += imported

            # Publish event
            await self._publish_discovery_event(imported, len(all_assets))

        self.act(
            "discovery_completed",
            f"Discovered {len(all_assets)} unique assets, imported {imported}",
        )

    async def run_metadata_sync(self):
        """
        Sync metadata (prijzen, volumes, status) voor actieve assets.
        Dit is lichter dan full discovery.
        """
        self.think("Starting metadata sync for active assets")

        try:
            # Haal actieve assets op uit DB
            async with self._async_session() as session:
                result = await session.execute(
                    text(
                        "SELECT symbol FROM assets WHERE status IN ('ACTIVE', 'WATCHED') LIMIT 100"
                    )
                )
                symbols = [row[0] for row in result.fetchall()]

            if not symbols:
                logger.info("[Metadata] No active assets to sync")
                return

            # Fetch tickers voor deze symbols
            updated = await self._sync_asset_metadata(symbols)
            self.assets_updated += updated

            self.act("metadata_synced", f"Updated metadata for {updated} assets")

        except Exception as e:
            logger.error(f"[Metadata] Sync failed: {e}")
            raise

    async def _discover_from_exchange(self, exchange_id: str) -> list[dict[str, Any]]:
        """
        Discover assets van een specifieke exchange.
        """
        if exchange_id == "bitvavo":
            return await self._fetch_bitvavo_assets()
        elif exchange_id == "revolut":
            return await self._fetch_revolut_assets()
        else:
            logger.warning(f"Unknown exchange: {exchange_id}")
            return []

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def _fetch_bitvavo_assets(self) -> list[dict[str, Any]]:
        """
        Fetch alle assets van Bitvavo via CCXT.
        """
        exchange = ccxt.bitvavo()
        assets = []

        try:
            await exchange.load_markets()

            for symbol, market in exchange.markets.items():
                assets.append(
                    {
                        "symbol": symbol,
                        "baseAsset": market.get("base", ""),
                        "quoteAsset": market.get("quote", ""),
                        "name": market.get(
                            "base", ""
                        ),  # Bitvavo doesn't provide full names in markets
                        "status": "active" if market.get("active", True) else "inactive",
                        "type": market.get("type", "spot"),
                        "exchange": "bitvavo",
                        "precision_price": market.get("precision", {}).get("price", 8),
                        "precision_amount": market.get("precision", {}).get("amount", 8),
                        "limits_min": market.get("limits", {}).get("amount", {}).get("min", 0),
                        "limits_max": market.get("limits", {}).get("amount", {}).get("max", None),
                    }
                )

            logger.info(f"[Bitvavo] Fetched {len(assets)} markets")
            return assets

        finally:
            await exchange.close()

    async def _fetch_revolut_assets(self) -> list[dict[str, Any]]:
        """
        Fetch assets van Revolut X via hun API.
        """
        assets = []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://app.revolut.com/api/crypto/trading/token-list",
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )

                if response.status_code == 200:
                    data = response.json()

                    if isinstance(data, list):
                        for item in data:
                            symbol = item.get("symbol", "")
                            if symbol:
                                assets.append(
                                    {
                                        "symbol": symbol,
                                        "baseAsset": item.get(
                                            "baseAsset",
                                            symbol.split("-")[0] if "-" in symbol else "",
                                        ),
                                        "quoteAsset": item.get("quoteAsset", ""),
                                        "name": item.get("name", ""),
                                        "status": item.get("status", "active"),
                                        "type": "crypto",
                                        "exchange": "revolut",
                                    }
                                )
                    elif isinstance(data, dict) and "tokens" in data:
                        for item in data["tokens"]:
                            symbol = item.get("symbol", "")
                            if symbol:
                                assets.append(
                                    {
                                        "symbol": symbol,
                                        "baseAsset": item.get("baseAsset", ""),
                                        "quoteAsset": item.get("quoteAsset", ""),
                                        "name": item.get("name", ""),
                                        "status": item.get("status", "active"),
                                        "type": "crypto",
                                        "exchange": "revolut",
                                    }
                                )
                else:
                    logger.warning(f"[Revolut] API returned {response.status_code}")

        except Exception as e:
            logger.warning(f"[Revolut] API fetch failed: {e}")

        # Fallback naar hardcoded lijst als API faalt
        if not assets:
            assets = self._get_revolut_fallback_assets()

        return assets

    def _get_revolut_fallback_assets(self) -> list[dict[str, Any]]:
        """Fallback assets voor Revolut als API niet beschikbaar is."""
        fallback = [
            {
                "symbol": "BTC-EUR",
                "baseAsset": "BTC",
                "quoteAsset": "EUR",
                "name": "Bitcoin",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "ETH-EUR",
                "baseAsset": "ETH",
                "quoteAsset": "EUR",
                "name": "Ethereum",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "SOL-EUR",
                "baseAsset": "SOL",
                "quoteAsset": "EUR",
                "name": "Solana",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "ADA-EUR",
                "baseAsset": "ADA",
                "quoteAsset": "EUR",
                "name": "Cardano",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "DOT-EUR",
                "baseAsset": "DOT",
                "quoteAsset": "EUR",
                "name": "Polkadot",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "XRP-EUR",
                "baseAsset": "XRP",
                "quoteAsset": "EUR",
                "name": "XRP",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "LINK-EUR",
                "baseAsset": "LINK",
                "quoteAsset": "EUR",
                "name": "Chainlink",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "DOGE-EUR",
                "baseAsset": "DOGE",
                "quoteAsset": "EUR",
                "name": "Dogecoin",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "LTC-EUR",
                "baseAsset": "LTC",
                "quoteAsset": "EUR",
                "name": "Litecoin",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
            {
                "symbol": "XLM-EUR",
                "baseAsset": "XLM",
                "quoteAsset": "EUR",
                "name": "Stellar",
                "status": "active",
                "type": "crypto",
                "exchange": "revolut",
            },
        ]
        logger.info("[Revolut] Using fallback asset list")
        return fallback

    async def _sync_asset_metadata(self, symbols: list[str]) -> int:
        """
        Sync metadata (prijzen, volumes) voor een lijst van symbols.
        """
        updated = 0

        try:
            exchange = ccxt.bitvavo()
            await exchange.load_markets()

            # Fetch tickers in batches
            for i in range(0, len(symbols), 100):
                batch = symbols[i : i + 100]

                try:
                    tickers = await exchange.fetch_tickers(batch)

                    async with self._async_session() as session:
                        for symbol, ticker in tickers.items():
                            await session.execute(
                                text(
                                    """
                                    UPDATE assets
                                    SET metadata_info = metadata_info || :metadata,
                                        last_updated = NOW()
                                    WHERE symbol = :symbol
                                """
                                ),
                                {
                                    "symbol": symbol,
                                    "metadata": json.dumps(
                                        {
                                            "last_price": ticker.get("last"),
                                            "volume_24h": ticker.get("volume"),
                                            "high_24h": ticker.get("high"),
                                            "low_24h": ticker.get("low"),
                                            "change_24h": ticker.get("change"),
                                            "change_percent_24h": ticker.get("percentage"),
                                        }
                                    ),
                                },
                            )
                        await session.commit()
                        updated += len(tickers)

                except Exception as e:
                    logger.warning(f"[Metadata] Failed to fetch tickers batch: {e}")

            await exchange.close()

        except Exception as e:
            logger.error(f"[Metadata] Sync error: {e}")

        return updated

    async def _import_to_database(self, assets: list[dict[str, Any]]) -> int:
        """
        Import assets naar database met UPSERT (insert or update).
        """
        if not assets:
            return 0

        imported = 0

        async with self._async_session() as session:
            try:
                for i in range(0, len(assets), self.batch_size):
                    batch = assets[i : i + self.batch_size]

                    values = []
                    for asset in batch:
                        values.append(
                            {
                                "symbol": asset.get("symbol", ""),
                                "name": asset.get("name", asset.get("baseAsset", "")),
                                "status": AssetStatus.DISCOVERED,
                                "metadata_info": {
                                    "source": asset.get("exchange", "unknown"),
                                    "baseAsset": asset.get("baseAsset", ""),
                                    "quoteAsset": asset.get("quoteAsset", ""),
                                    "type": asset.get("type", "crypto"),
                                    "precision": {
                                        "price": asset.get("precision_price", 8),
                                        "amount": asset.get("precision_amount", 8),
                                    },
                                    "limits": {
                                        "min": asset.get("limits_min", 0),
                                        "max": asset.get("limits_max"),
                                    },
                                    "discovered_at": datetime.now(UTC).isoformat(),
                                },
                            }
                        )

                    if values:
                        stmt = (
                            insert(Asset)
                            .values(values)
                            .on_conflict_do_update(
                                index_elements=["symbol"],
                                set_={
                                    "metadata_info": Asset.metadata_info.concat(
                                        values[0]["metadata_info"]
                                    ),
                                    "last_updated": datetime.now(UTC),
                                },
                            )
                        )
                        await session.execute(stmt)
                        imported += len(values)

                await session.commit()
                logger.info(f"[Database] Imported {imported} assets")

            except Exception as e:
                await session.rollback()
                logger.error(f"[Database] Import failed: {e}")
                raise

        return imported

    async def _save_to_files(self, assets: dict[str, dict[str, Any]]):
        """
        Sla assets op naar CSV/JSON voor debugging/backup.
        """
        if not assets:
            return

        assets_list = list(assets.values())
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        # JSON
        json_path = self.data_dir / f"discovered_assets_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(assets_list, f, indent=2, ensure_ascii=False)

        # CSV
        csv_path = self.data_dir / f"discovered_assets_{timestamp}.csv"
        if assets_list:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=assets_list[0].keys())
                writer.writeheader()
                writer.writerows(assets_list)

        logger.info(f"[Files] Saved {len(assets_list)} assets to {json_path}")

    async def _publish_discovery_event(self, imported: int, total: int):
        """
        Publish discovery event naar event bus.
        """
        if not self.event_bus:
            return

        event_data = {
            "agent": "AssetDiscoveryAgent",
            "event_type": "assets_discovered",
            "imported": imported,
            "total_discovered": total,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        try:
            await self.event_bus.publish("asset_discovery", event_data)
            logger.debug(f"[Event] Published discovery event: {imported} assets")
        except Exception as e:
            logger.warning(f"[Event] Failed to publish: {e}")

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        BaseAgent abstract method - niet gebruikt voor deze agent.
        """
        return {
            "recommendation": "Use run_discovery_cycle() or start() for AssetDiscoveryAgent",
            "confidence": 0.0,
        }

    def get_statistics(self) -> dict[str, Any]:
        """
        Krijg agent statistieken.
        """
        health = self.health_check()
        return {
            **health,
            "assets_discovered": self.assets_discovered,
            "assets_updated": self.assets_updated,
            "last_discovery_run": (
                self.last_discovery_run.isoformat() if self.last_discovery_run else None
            ),
            "last_metadata_sync": (
                self.last_metadata_sync.isoformat() if self.last_metadata_sync else None
            ),
            "discovery_interval": self.discovery_interval,
            "metadata_sync_interval": self.metadata_sync_interval,
        }
