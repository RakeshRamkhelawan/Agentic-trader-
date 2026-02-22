"""
Historical Market Data Downloader
Downloads 50+ assets from Yahoo Finance (2020-2026) for backtesting
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataDownloader")

# Top 50+ assets (Crypto + Stocks + ETFs)
ASSETS = {
    # Major Cryptos (EUR pairs via USD conversion)
    "BTC": "BTC-USD",
    "ETH": "ETH-USD", 
    "SOL": "SOL-USD",
    "ADA": "ADA-USD",
    "DOT": "DOT-USD",
    "XRP": "XRP-USD",
    "LINK": "LINK-USD",
    "DOGE": "DOGE-USD",
    "LTC": "LTC-USD",
    "XLM": "XLM-USD",
    "AVAX": "AVAX-USD",
    "MATIC": "MATIC-USD",
    "UNI": "UNI-USD",
    "AAVE": "AAVE-USD",
    "ATOM": "ATOM-USD",
    "ALGO": "ALGO-USD",
    "ETC": "ETC-USD",
    "VET": "VET-USD",
    "FIL": "FIL-USD",
    "TRX": "TRX-USD",
    
    # Major Stocks
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "TSLA": "TSLA",
    "META": "META",
    "NVDA": "NVDA",
    "NFLX": "NFLX",
    "AMD": "AMD",
    "INTC": "INTC",
    "IBM": "IBM",
    "ORCL": "ORCL",
    "CRM": "CRM",
    "ADBE": "ADBE",
    "PYPL": "PYPL",
    "UBER": "UBER",
    "COIN": "COIN",
    "SNOW": "SNOW",
    "ZM": "ZM",
    "ROKU": "ROKU",
    
    # ETFs & Indices
    "SPY": "SPY",
    "QQQ": "QQQ",
    "IWM": "IWM",
    "VTI": "VTI",
    "EFA": "EFA",
    "EEM": "EEM",
    "TLT": "TLT",
    "GLD": "GLD",
    "USO": "USO",
    "VIX": "^VIX",
    
    # Inverse ETFs for Hedging (V12+)
    "SH": "SH",      # S&P 500 Inverse
    "PSQ": "PSQ",    # Nasdaq Inverse
    "RWM": "RWM",    # Russell 2000 Inverse
    "TBF": "TBF",    # Treasury 20+ Year Inverse
    
    # European Stocks
    "ASML": "ASML",
    "SAP": "SAP",
    "NESN": "NESN.SW",
    "ROG": "ROG.SW",
    "SHEL": "SHEL",
    "TTE": "TTE",
    "AIR": "AIR.PA",
}

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://trader:trading_secure@localhost:5456/trading_db"
)

# Convert asyncpg to psycopg2 for pandas
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")


class HistoricalDataDownloader:
    """Downloads and stores historical market data"""
    
    def __init__(self, start_date: str = "2020-01-01", end_date: str = "2026-12-31"):
        self.start_date = start_date
        self.end_date = end_date
        self.engine = create_engine(SYNC_DATABASE_URL)
        
    def ensure_tables(self):
        """Ensure database tables exist"""
        logger.info("Creating tables if not exist...")
        
        with self.engine.connect() as conn:
            # MarketCandles table - create it first
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_candles (
                    symbol VARCHAR NOT NULL,
                    timeframe VARCHAR NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    open DOUBLE PRECISION NOT NULL,
                    high DOUBLE PRECISION NOT NULL,
                    low DOUBLE PRECISION NOT NULL,
                    close DOUBLE PRECISION NOT NULL,
                    volume DOUBLE PRECISION NOT NULL,
                    provider VARCHAR,
                    PRIMARY KEY (symbol, timeframe, timestamp)
                );
            """))
            conn.commit()
            
            # Create hypertable for TimescaleDB (optional)
            try:
                conn.execute(text("""
                    SELECT create_hypertable('market_candles', 'timestamp', 
                        if_not_exists => TRUE, 
                        migrate_data => TRUE
                    );
                """))
                conn.commit()
                logger.info("TimescaleDB hypertable created/verified")
            except Exception as e:
                conn.rollback()
                logger.warning(f"TimescaleDB hypertable creation skipped: {e}")
            
            # Create indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_market_candles_symbol 
                ON market_candles (symbol, timestamp DESC);
            """))
            conn.commit()
        
        logger.info("Tables ready")
    
    def download_asset(self, symbol: str, yf_symbol: str) -> Optional[pd.DataFrame]:
        """Download historical data for a single asset"""
        try:
            logger.info(f"Downloading {symbol} ({yf_symbol})...")
            
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(
                start=self.start_date,
                end=self.end_date,
                interval="1d"  # Daily data
            )
            
            if df.empty:
                logger.warning(f"No data for {symbol}")
                return None
            
            # Rename columns to match our schema
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            
            # Add metadata columns
            df["symbol"] = symbol
            df["timeframe"] = "1d"
            df["provider"] = "yahoo_finance"
            df = df.reset_index()
            df = df.rename(columns={"Date": "timestamp"})
            
            # Ensure timestamp is timezone-aware
            if df["timestamp"].dt.tz is None:
                df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
            
            logger.info(f"Downloaded {len(df)} candles for {symbol}")
            return df[["symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume", "provider"]]
            
        except Exception as e:
            logger.error(f"Failed to download {symbol}: {e}")
            return None
    
    def store_data(self, df: pd.DataFrame) -> int:
        """Store DataFrame to database"""
        if df is None or df.empty:
            return 0
        
        try:
            # Use COPY for bulk insert
            rows_inserted = df.to_sql(
                "market_candles",
                self.engine,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000
            )
            
            logger.info(f"Stored {rows_inserted} rows")
            return rows_inserted
            
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            return 0
    
    def download_all(self, max_assets: Optional[int] = None):
        """Download all assets"""
        self.ensure_tables()
        
        assets = list(ASSETS.items())[:max_assets] if max_assets else list(ASSETS.items())
        
        total_candles = 0
        successful = 0
        failed = 0
        
        for symbol, yf_symbol in assets:
            df = self.download_asset(symbol, yf_symbol)
            
            if df is not None:
                rows = self.store_data(df)
                total_candles += rows
                successful += 1
            else:
                failed += 1
            
            # Rate limiting - be nice to Yahoo Finance
            import time
            time.sleep(0.5)
        
        logger.info("=" * 60)
        logger.info(f"Download Complete!")
        logger.info(f"Successful: {successful}/{len(assets)}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total candles: {total_candles:,}")
        logger.info("=" * 60)
        
        return {
            "successful": successful,
            "failed": failed,
            "total_candles": total_candles
        }
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_candles,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM market_candles
            """))
            row = result.fetchone()
            
            symbols_result = conn.execute(text("""
                SELECT symbol, COUNT(*) as count 
                FROM market_candles 
                GROUP BY symbol 
                ORDER BY count DESC
            """))
            symbols = {r[0]: r[1] for r in symbols_result.fetchall()}
            
            return {
                "total_candles": row[0],
                "unique_symbols": row[1],
                "earliest": row[2],
                "latest": row[3],
                "symbols": symbols
            }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download historical market data")
    parser.add_argument("--start", default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-12-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--max", type=int, help="Max number of assets to download")
    parser.add_argument("--stats", action="store_true", help="Show database stats only")
    
    args = parser.parse_args()
    
    downloader = HistoricalDataDownloader(
        start_date=args.start,
        end_date=args.end
    )
    
    if args.stats:
        stats = downloader.get_stats()
        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)
        print(f"Total candles: {stats['total_candles']:,}")
        print(f"Unique symbols: {stats['unique_symbols']}")
        print(f"Date range: {stats['earliest']} to {stats['latest']}")
        print("\nTop 10 assets by data points:")
        for sym, count in list(stats['symbols'].items())[:10]:
            print(f"  {sym}: {count:,} candles")
        return
    
    # Download all data
    result = downloader.download_all(max_assets=args.max)
    
    if result["successful"] > 0:
        stats = downloader.get_stats()
        print("\n" + "=" * 60)
        print("FINAL STATISTICS")
        print("=" * 60)
        print(f"Total candles in DB: {stats['total_candles']:,}")
        print(f"Unique symbols: {stats['unique_symbols']}")
        print(f"Date range: {stats['earliest']} to {stats['latest']}")


if __name__ == "__main__":
    main()
