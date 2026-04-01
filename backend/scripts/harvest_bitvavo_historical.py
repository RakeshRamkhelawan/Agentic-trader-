"""
Intelligence Synthesizer - Harvesting Bitvavo History into RAG.

This script processes historical Bitvavo CSV data, detects regimes,
enriches with Vedic context, and populates the ChromaDB knowledge base.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, List

import numpy as np
import pandas as pd
from chromadb.utils import embedding_functions

from backend.core.config.settings import settings
from backend.core.regime_detector import MarketRegime, RegimeDetector
from backend.storage.tenant_aware_chroma import TenantAwareChromaClient
from backend.vedastro.cloud_connector import VedAstroCloudConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class IntelligenceSynthesizer:
    def __init__(self, tenant_id: str = "default_tenant"):
        self.detector = RegimeDetector()
        self.vedastro = VedAstroCloudConnector()
        self.chroma = TenantAwareChromaClient(tenant_id=tenant_id)
        self.tenant_id = tenant_id

    async def initialize(self):
        """Initialize connections."""
        # Ensure collection exists
        self.collection = self.chroma.get_collection("trading_knowledge")
        logger.info(
            f"Connected to ChromaDB collection: trading_knowledge (Tenant: {self.tenant_id})"
        )

    async def process_csv(self, file_path: str, symbol: str):
        """Process a single historical CSV file."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        logger.info(f"Processing {symbol} from {file_path}...")
        df = pd.read_csv(file_path)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime")

        # Group by month for "Episodes"
        df["month"] = df["datetime"].dt.to_period("M")
        months = df["month"].unique()

        episodes_count = 0

        for month in months:
            month_df = df[df["month"] == month]
            if len(month_df) < 5:
                continue

            # Get data for regime detection (need previous data for SMAs)
            # Find index in full DF
            idx = month_df.index[-1]
            if idx < 200:
                # Need 200 candles for proper regime detection
                prices = df.iloc[: idx + 1]["close"].tolist()
            else:
                prices = df.iloc[idx - 200 : idx + 1]["close"].tolist()

            # Detect regime
            sma_50, sma_200, vol = self.detector.calculate_indicators(prices)
            current_price = month_df["close"].iloc[-1]
            regime = self.detector.detect(current_price, sma_50, sma_200, vol)

            # Calculate performance (outcome)
            start_price = month_df["close"].iloc[0]
            end_price = month_df["close"].iloc[-1]
            return_pct = ((end_price / start_price) - 1) * 100
            outcome = "success" if return_pct > 0 else "failure"

            # Get Vedic Context for the middle of the month
            mid_date = month_df["datetime"].iloc[len(month_df) // 2]
            dasha = await self.vedastro.get_dasha(
                mid_date, {"lat": settings.LATITUDE, "lon": settings.LONGITUDE}
            )

            mahadasha = dasha.get("Mahadasha", "Unknown")
            antardasha = dasha.get("Antardasha", "Unknown")

            # Synthesize "Strategic Snapshot"
            timestamp_str = mid_date.strftime("%B %Y")
            content = (
                f"{timestamp_str} {symbol} Market Episode: "
                f"The market was in a {regime} regime with a {return_pct:.1f}% monthly return. "
                f"VEDIC CONTEXT: Major planetary cycle was {mahadasha}-{antardasha}. "
                f"STRATEGIC LESSON: During this period, the {regime} trend was driven by "
                f"{'expansion' if mahadasha == 'Jupiter' else 'innovation' if mahadasha == 'Rahu' else 'structural shifts'}. "
                f"Performance outcome: {outcome}."
            )

            # Ingest into RAG
            doc_id = f"hist_{symbol.replace('/', '_')}_{month}"
            self.collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[
                    {
                        "source": "bitvavo_history",
                        "symbol": symbol,
                        "regime": str(regime),
                        "outcome": outcome,
                        "return_pct": float(return_pct),
                        "mahadasha": mahadasha,
                        "antardasha": antardasha,
                        "period": str(month),
                    }
                ],
            )

            episodes_count += 1
            if episodes_count % 10 == 0:
                logger.info(f"  Ingested {episodes_count} episodes for {symbol}...")

        logger.info(f"✓ Completed {symbol}: Ingested {episodes_count} episodes.")


async def main():
    synthesizer = IntelligenceSynthesizer()
    await synthesizer.initialize()

    # Process BTC and ETH
    await synthesizer.process_csv("data/historical/bitvavo/bitvavo/BTC_EUR_1d.csv", "BTC/EUR")
    await synthesizer.process_csv("data/historical/bitvavo/bitvavo/ETH_EUR_1d.csv", "ETH/EUR")

    logger.info("Intelligence Harvesting Complete.")
    await synthesizer.vedastro.close()


if __name__ == "__main__":
    asyncio.run(main())
