"""Database module for Prediction Market Intelligence."""

from src.db.duckdb_manager import DuckDBManager
from src.db.parquet_handler import ParquetHandler

__all__ = ["DuckDBManager", "ParquetHandler"]
