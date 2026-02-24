"""
Historical CSV Data Feed for the custom BacktestEngine.

Implements the DataFeed ABC to load OHLCV data from CSV files
and iterate through bars sequentially during a backtest.
"""

from datetime import datetime
from typing import Any

import pandas as pd

from backend.backtesting.data_feed import DataFeed


class HistoricalCSVData(DataFeed):
    """
    Loads historical OHLCV data from a CSV file.

    Expected CSV columns: datetime (or date), open, high, low, close, volume.
    The feed supports date filtering via load_data(symbols, start, end).
    """

    def __init__(self, csv_path: str):
        """
        Args:
            csv_path: Absolute path to the CSV file.
        """
        self.csv_path = csv_path
        self._data: dict[str, pd.DataFrame] = {}
        self._current_index: int = 0
        self._timestamps: list[datetime] = []

    def load_data(self, symbols: list[str], start_date: datetime, end_date: datetime) -> None:
        """Load CSV and filter to [start_date, end_date] for each symbol."""
        df = pd.read_csv(self.csv_path)

        # Normalize datetime column
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
        elif "date" in df.columns:
            df.rename(columns={"date": "datetime"}, inplace=True)
            df["datetime"] = pd.to_datetime(df["datetime"])
        elif "timestamp" in df.columns:
            df.rename(columns={"timestamp": "datetime"}, inplace=True)
            df["datetime"] = pd.to_datetime(df["datetime"])
        else:
            raise ValueError("CSV must have a 'datetime', 'date', or 'timestamp' column.")

        # Filter date range
        mask = (df["datetime"] >= pd.Timestamp(start_date)) & (
            df["datetime"] <= pd.Timestamp(end_date)
        )
        df = df.loc[mask].copy()
        df.sort_values("datetime", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Store timestamps
        self._timestamps = df["datetime"].dt.to_pydatetime().tolist()

        # Assign the same dataframe to every requested symbol
        # (CSV typically holds one instrument; multi-symbol CSVs need a 'symbol' column)
        if "symbol" in df.columns:
            for sym in symbols:
                sym_df = df[df["symbol"] == sym].reset_index(drop=True)
                self._data[sym] = sym_df
        else:
            for sym in symbols:
                self._data[sym] = df.copy()

        self._current_index = 0

    def next(self) -> bool:
        """Advance to the next bar. Return False at end of data."""
        if self._current_index < len(self._timestamps) - 1:
            self._current_index += 1
            return True
        return False

    def current_time(self) -> datetime:
        """Return current simulation time."""
        if not self._timestamps:
            return datetime.now()
        return self._timestamps[self._current_index]

    def get_latest_bar(self, symbol: str) -> dict[str, Any] | None:
        """Return the OHLCV bar for the current index."""
        if symbol not in self._data:
            return None

        df = self._data[symbol]
        try:
            row = df.iloc[self._current_index]
            return row.to_dict()
        except IndexError:
            return None
