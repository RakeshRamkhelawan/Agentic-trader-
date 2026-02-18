"""
Parquet File Handler
Utilities for reading and writing Parquet files.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ParquetHandler:
    """
    Handles Parquet file I/O operations.

    Supports reading/writing Parquet files with automatic
    directory creation and file discovery.

    Usage:
        handler = ParquetHandler(base_dir="/app/data")
        df = handler.read_parquet("kalshi", "2024-01-15")
        handler.write_parquet(df, "kalshi", "2024-01-15")
    """

    def __init__(self, base_dir: str = "/app/data"):
        """
        Initialize Parquet handler.

        Args:
            base_dir: Base directory for Parquet files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_directory(self, source: str) -> Path:
        """
        Get directory for a data source.

        Args:
            source: Source name (e.g., "kalshi", "polymarket")

        Returns:
            Path to source directory
        """
        directory = self.base_dir / source.lower()
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def read_parquet(self, source: str, filename: Optional[str] = None) -> pd.DataFrame:
        """
        Read Parquet file(s).

        If filename is None, reads all Parquet files in the source directory
        and returns concatenated DataFrame.

        Args:
            source: Data source (e.g., "kalshi", "polymarket")
            filename: Specific filename (without .parquet extension)

        Returns:
            pandas DataFrame

        Raises:
            FileNotFoundError: If file(s) not found
        """
        directory = self.get_directory(source)

        if filename:
            file_path = directory / f"{filename}.parquet"
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            logger.info(f"Reading Parquet: {file_path}")
            return pd.read_parquet(file_path)

        # Read all Parquet files
        parquet_files = list(directory.glob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(f"No Parquet files found in {directory}")

        logger.info(f"Reading {len(parquet_files)} Parquet files from {directory}")
        dfs = [pd.read_parquet(f) for f in sorted(parquet_files)]
        return pd.concat(dfs, ignore_index=True)

    def write_parquet(
        self, df: pd.DataFrame, source: str, filename: str, mode: str = "overwrite"
    ) -> Path:
        """
        Write DataFrame to Parquet file.

        Args:
            df: DataFrame to write
            source: Data source (e.g., "kalshi", "polymarket")
            filename: Target filename (without .parquet extension)
            mode: "overwrite" or "append"

        Returns:
            Path to written file
        """
        directory = self.get_directory(source)
        file_path = directory / f"{filename}.parquet"

        if mode == "append" and file_path.exists():
            existing_df = pd.read_parquet(file_path)
            df = pd.concat([existing_df, df], ignore_index=True)

        logger.info(f"Writing Parquet: {file_path} ({len(df)} rows)")
        df.to_parquet(file_path, engine="pyarrow", compression="snappy")
        return file_path

    def list_parquet_files(self, source: str) -> list[Path]:
        """
        List all Parquet files in a source directory.

        Args:
            source: Data source (e.g., "kalshi", "polymarket")

        Returns:
            List of file paths
        """
        directory = self.get_directory(source)
        return sorted(directory.glob("*.parquet"))

    def get_file_info(self, source: str, filename: str) -> dict:
        """
        Get information about a Parquet file.

        Args:
            source: Data source
            filename: Filename (without .parquet extension)

        Returns:
            Dictionary with row_count, columns, file_size
        """
        directory = self.get_directory(source)
        file_path = directory / f"{filename}.parquet"

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        df = pd.read_parquet(file_path)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)

        return {
            "filename": filename,
            "file_path": str(file_path),
            "row_count": len(df),
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "file_size_mb": round(file_size_mb, 2),
        }

    def delete_parquet(self, source: str, filename: str) -> None:
        """
        Delete a Parquet file.

        Args:
            source: Data source
            filename: Filename (without .parquet extension)
        """
        directory = self.get_directory(source)
        file_path = directory / f"{filename}.parquet"

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted Parquet: {file_path}")
        else:
            raise FileNotFoundError(f"File not found: {file_path}")

    def clear_source_directory(self, source: str) -> int:
        """
        Delete all Parquet files in a source directory.

        Args:
            source: Data source

        Returns:
            Number of files deleted
        """
        directory = self.get_directory(source)
        parquet_files = list(directory.glob("*.parquet"))

        for file_path in parquet_files:
            file_path.unlink()

        logger.info(f"Deleted {len(parquet_files)} Parquet files from {source}")
        return len(parquet_files)
