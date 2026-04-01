"""
Bulk Intelligence Synthesizer - Ingesting 431 symbols into RAG.

This script fetches Vedic context for 96 months ONCE, then processes
all historical Bitvavo CSVs to create 40k+ RAG episodes efficiently.
"""

import asyncio
import glob
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backend.core.config.settings import settings
from backend.core.regime_detector import MarketRegime, RegimeDetector
from backend.storage.tenant_aware_chroma import TenantAwareChromaClient
from backend.vedastro.cloud_connector import VedAstroCloudConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BulkIntelligenceSynthesizer:
    def __init__(self, tenant_id: str = "default_tenant"):
        self.detector = RegimeDetector()
        self.vedastro = VedAstroCloudConnector()
        self.chroma = TenantAwareChromaClient(tenant_id=tenant_id)
        self.tenant_id = tenant_id
        self.vedic_cache: Dict[str, Dict[str, str]] = {}

    async def initialize(self):
        """Initialize connections and collection."""
        self.collection = self.chroma.get_collection("trading_knowledge")
        logger.info(f"Connected to ChromaDB (Tenant: {self.tenant_id})")

    async def build_vedic_cache(self, start_year: int = 2018, end_year: int = 2026):
        """Pre-fetch Vedic context for all months to avoid redundant API calls."""
        logger.info(f"Building Vedic cache from {start_year} to {end_year}...")

        current_date = datetime(start_year, 1, 15)  # Mid-month
        end_date = datetime(end_year, 4, 1)

        while current_date < end_date:
            month_key = current_date.strftime("%Y-%m")
            try:
                dasha = await self.vedastro.get_dasha(
                    current_date, {"lat": settings.LATITUDE, "lon": settings.LONGITUDE}
                )
                self.vedic_cache[month_key] = {
                    "mahadasha": dasha.get("Mahadasha", "Unknown"),
                    "antardasha": dasha.get("Antardasha", "Unknown"),
                }
                if len(self.vedic_cache) % 12 == 0:
                    logger.info(f"  Cached {len(self.vedic_cache)} months...")
            except Exception as e:
                logger.error(f"  Failed caching {month_key}: {e}")

            # Move to next month
            # Add 30 days and set to 15th
            next_month = current_date + timedelta(days=32)
            current_date = datetime(next_month.year, next_month.month, 15)

        logger.info(f"✓ Vedic Cache Complete: {len(self.vedic_cache)} entries.")

    async def process_all_csvs(self, catalog_dir: str):
        """Process all CSV files in the catalog and ingest into RAG."""
        files = glob.glob(os.path.join(catalog_dir, "*.csv"))
        logger.info(f"Found {len(files)} CSV files in catalog.")

        batch_ids = []
        batch_docs = []
        batch_metas = []
        total_ingested = 0

        for file_path in files:
            symbol = os.path.basename(file_path).replace("_1d.csv", "").replace("_", "/")
            try:
                df = pd.read_csv(file_path)
                df["datetime"] = pd.to_datetime(df["datetime"])
                df["month_key"] = df["datetime"].dt.strftime("%Y-%m")

                # Iterate by month
                for month_key, month_df in df.groupby("month_key"):
                    if len(month_df) < 5:
                        continue

                    # Vedic context from cache
                    vedic = self.vedic_cache.get(
                        month_key, {"mahadasha": "Unknown", "antardasha": "Unknown"}
                    )

                    # Regime Detection
                    last_idx = month_df.index[-1]
                    # Need up to 200 previous rows for indicators
                    start_idx = max(0, last_idx - 200)
                    prices = df.iloc[start_idx : last_idx + 1]["close"].tolist()

                    sma_50, sma_200, vol = self.detector.calculate_indicators(prices)
                    current_price = month_df["close"].iloc[-1]
                    regime = self.detector.detect(current_price, sma_50, sma_200, vol)

                    # Outcome
                    start_price = month_df["close"].iloc[0]
                    end_price = month_df["close"].iloc[-1]
                    return_pct = float(((end_price / start_price) - 1) * 100)
                    outcome = "success" if return_pct > 0 else "failure"

                    # Document
                    content = (
                        f"{month_key} {symbol}: Market regime was {regime} with {return_pct:.1f}% return. "
                        f"Vedic Lord: {vedic['mahadasha']}-{vedic['antardasha']}."
                    )

                    doc_id = f"bulk_{symbol.replace('/', '_')}_{month_key}"

                    batch_ids.append(doc_id)
                    batch_docs.append(content)
                    batch_metas.append(
                        {
                            "source": "bitvavo_massive",
                            "symbol": symbol,
                            "regime": str(regime),
                            "outcome": outcome,
                            "return_pct": return_pct,
                            "mahadasha": vedic["mahadasha"],
                            "antardasha": vedic["antardasha"],
                            "period": month_key,
                        }
                    )

                    # Bulk insert every 500 episodes
                    if len(batch_ids) >= 500:
                        self.collection.upsert(
                            ids=batch_ids, documents=batch_docs, metadatas=batch_metas
                        )
                        total_ingested += len(batch_ids)
                        logger.info(f"  Ingested {total_ingested} episodes...")
                        batch_ids, batch_docs, batch_metas = [], [], []

            except Exception as e:
                logger.error(f"  Error processing {symbol}: {e}")

        # Final batch
        if batch_ids:
            self.collection.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_metas)
            total_ingested += len(batch_ids)

        logger.info(f"✓ Massive Intelligence Harvesting Complete: {total_ingested} episodes.")


async def main():
    synthesizer = BulkIntelligenceSynthesizer()
    await synthesizer.initialize()

    # 1. Build Cache
    await synthesizer.build_vedic_cache()

    # 2. Process Full Catalog
    catalog_path = "data/historical/bitvavo/full_catalog"
    await synthesizer.process_all_csvs(catalog_path)

    await synthesizer.vedastro.close()


if __name__ == "__main__":
    asyncio.run(main())
