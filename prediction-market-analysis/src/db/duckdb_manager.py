"""
DuckDB Database Manager
Manages DuckDB connections, schema creation, and query execution.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional, Union

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class DuckDBManager:
    """
    Manages DuckDB database connections and operations.

    Supports both persistent (file-based) and in-memory databases.
    Can directly query Parquet files.

    Usage:
        manager = DuckDBManager(db_path="/app/data/prediction_market.duckdb")
        manager.initialize()
        df = manager.query("SELECT * FROM kalshi_trades LIMIT 10")
        manager.close()
    """

    # Schema versie voor migrations
    SCHEMA_VERSION = 1

    def __init__(
        self,
        db_path: Optional[str] = None,
        data_dir: str = "/app/data",
        read_only: bool = False,
    ):
        """
        Initialize DuckDB manager.

        Args:
            db_path: Path to DuckDB database file. None for in-memory.
            data_dir: Base directory for Parquet data files.
            read_only: Open database in read-only mode.
        """
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.read_only = read_only
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        self._initialized = False

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Get active database connection."""
        if self._conn is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._conn

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized

    def initialize(self) -> None:
        """
        Initialize database connection and create schema.

        Creates tables if they don't exist.
        Registers Parquet file views.
        """
        logger.info(f"Initializing DuckDB (path: {self.db_path or ':memory:'})")

        if self.db_path:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            self._conn = duckdb.connect(self.db_path, read_only=self.read_only)
        else:
            self._conn = duckdb.connect(":memory:")

        # Create schema
        self._create_schema()

        # Register Parquet views if data directory exists
        if self.data_dir.exists():
            self._register_parquet_views()

        self._initialized = True
        logger.info("DuckDB initialized successfully")

    def _create_schema(self) -> None:
        """Create database schema (tables and indexes)."""

        # Kalshi trades table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kalshi_trades (
                id VARCHAR,
                ticker VARCHAR,
                category VARCHAR,
                market_title VARCHAR,
                side VARCHAR,
                yes_price DOUBLE,
                no_price DOUBLE,
                volume INTEGER,
                trade_time TIMESTAMP,
                taker_side VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Polymarket trades table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS polymarket_trades (
                id VARCHAR,
                market_slug VARCHAR,
                category VARCHAR,
                title VARCHAR,
                outcome VARCHAR,
                price DOUBLE,
                amount DOUBLE,
                side VARCHAR,
                trade_time TIMESTAMP,
                maker_address VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Signals table (generated signals)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_signals (
                signal_id VARCHAR PRIMARY KEY,
                market VARCHAR,
                category VARCHAR,
                signal_type VARCHAR,
                confidence DOUBLE,
                symbol VARCHAR,
                indicators JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Analysis results table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_results (
                analysis_id VARCHAR PRIMARY KEY,
                analysis_type VARCHAR,
                market VARCHAR,
                status VARCHAR,
                result JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """
        )

        logger.info("Schema created/verified")

    def _register_parquet_views(self) -> None:
        """
        Register Parquet files as views for direct querying.

        Creates views like:
        - kalshi_parquet → reads all parquet files in data/kalshi/
        - polymarket_parquet → reads all parquet files in data/polymarket/
        """
        kalshi_dir = self.data_dir / "kalshi"
        poly_dir = self.data_dir / "polymarket"

        if kalshi_dir.exists() and list(kalshi_dir.glob("*.parquet")):
            parquet_path = str(kalshi_dir / "*.parquet")
            self.conn.execute(
                f"""
                CREATE OR REPLACE VIEW kalshi_parquet AS
                SELECT * FROM read_parquet('{parquet_path}')
            """
            )
            logger.info(f"Registered Kalshi Parquet view: {parquet_path}")

        if poly_dir.exists() and list(poly_dir.glob("*.parquet")):
            parquet_path = str(poly_dir / "*.parquet")
            self.conn.execute(
                f"""
                CREATE OR REPLACE VIEW polymarket_parquet AS
                SELECT * FROM read_parquet('{parquet_path}')
            """
            )
            logger.info(f"Registered Polymarket Parquet view: {parquet_path}")

    def query(
        self, sql: str, params: Optional[list[Any]] = None, as_dataframe: bool = True
    ) -> Union[pd.DataFrame, list[tuple]]:
        """
        Execute a query and return results.

        Args:
            sql: SQL query string
            params: Query parameters for parameterized queries
            as_dataframe: Return as pandas DataFrame (True) or list of tuples

        Returns:
            Query results as DataFrame or list of tuples

        Raises:
            RuntimeError: If database not initialized
            duckdb.Error: If query fails
        """
        if params:
            result = self.conn.execute(sql, params)
        else:
            result = self.conn.execute(sql)

        if as_dataframe:
            return result.fetchdf()
        return result.fetchall()

    def execute(self, sql: str, params: Optional[list[Any]] = None) -> None:
        """
        Execute a statement (INSERT, UPDATE, DELETE, DDL).

        Args:
            sql: SQL statement
            params: Statement parameters
        """
        if params:
            self.conn.execute(sql, params)
        else:
            self.conn.execute(sql)

    def insert_dataframe(
        self, table: str, df: pd.DataFrame, if_exists: str = "append"
    ) -> int:
        """
        Insert a pandas DataFrame into a table.

        Args:
            table: Target table name
            df: DataFrame to insert
            if_exists: "append" or "replace"

        Returns:
            Number of rows inserted
        """
        if if_exists == "replace":
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.register("_temp_df", df)

        # Get available columns from dataframe
        columns = list(df.columns)
        columns_str = ", ".join(columns)

        # Insert only the columns that exist in the dataframe
        self.conn.execute(
            f"INSERT INTO {table} ({columns_str}) SELECT {columns_str} FROM _temp_df"
        )
        self.conn.unregister("_temp_df")

        return len(df)

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        result = self.conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name],
        ).fetchone()
        return result[0] > 0

    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._initialized = False
            logger.info("DuckDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
