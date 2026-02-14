from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional, List, Any
import pandas as pd
import numpy as np


class DataFeed(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    def load_data(
        self, symbols: List[str], start_date: datetime, end_date: datetime
    ) -> None:
        """Load data into memory."""
        pass

    @abstractmethod
    def get_latest_bar(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the latest bar for the current timestamp in the event loop."""
        pass

    @abstractmethod
    def next(self) -> bool:
        """Advance time one step. Return False if end of data."""
        pass

    @abstractmethod
    def current_time(self) -> datetime:
        """Return current simulation time."""
        pass


class MockDataFeed(DataFeed):
    """Generates random walk data for testing."""

    def __init__(self):
        self._data: Dict[str, pd.DataFrame] = {}
        self._current_index = 0
        self._timestamps: List[datetime] = []

    def load_data(
        self, symbols: List[str], start_date: datetime, end_date: datetime
    ) -> None:
        # Generate generic time range (daily)
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        self._timestamps = dates.to_pydatetime().tolist()

        for symbol in symbols:
            # Random walk
            prices = 100 + np.cumsum(np.random.randn(len(dates)))
            df = pd.DataFrame(
                {
                    "timestamp": dates,
                    "open": prices,
                    "high": prices + 1,
                    "low": prices - 1,
                    "close": prices,
                    "volume": np.random.randint(100, 1000, len(dates)),
                }
            )
            self._data[symbol] = df

    def next(self) -> bool:
        if self._current_index < len(self._timestamps) - 1:
            self._current_index += 1
            return True
        return False

    def current_time(self) -> datetime:
        if not self._timestamps:
            return datetime.now()
        return self._timestamps[self._current_index]

    def get_latest_bar(self, symbol: str) -> Optional[Dict[str, Any]]:
        if symbol not in self._data:
            return None

        df = self._data[symbol]
        # Inefficient for large data, but fine for mock
        try:
            row = df.iloc[self._current_index]
            return row.to_dict()
        except IndexError:
            return None
