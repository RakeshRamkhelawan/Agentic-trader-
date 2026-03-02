"""
Tests for HistoricalCSVData (Step 4B - GREEN).

Validates CSV loading, date filtering, and bar iteration
using the custom DataFeed ABC.
"""

import os
import tempfile
from datetime import datetime

import pytest

from backend.backtesting.data_feed_historical import HistoricalCSVData


@pytest.fixture
def sample_csv(tmp_path):
    """Create a minimal CSV file with 5 days of data."""
    csv_file = tmp_path / "test_ohlcv.csv"
    csv_file.write_text(
        "datetime,open,high,low,close,volume\n"
        "2023-01-01,100,105,95,102,1000\n"
        "2023-01-02,102,110,101,108,1200\n"
        "2023-01-03,108,112,106,107,1100\n"
        "2023-01-04,107,109,103,104,900\n"
        "2023-01-05,104,106,100,105,950\n"
    )
    return str(csv_file)


def test_load_csv_data(sample_csv):
    """HistoricalCSVData should load all rows for the requested symbol."""
    feed = HistoricalCSVData(sample_csv)
    feed.load_data(
        symbols=["BTC/USD"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 5),
    )

    bar = feed.get_latest_bar("BTC/USD")
    assert bar is not None
    assert bar["close"] == 102  # First bar


def test_date_filtering(sample_csv):
    """Only bars within [start_date, end_date] should be loaded."""
    feed = HistoricalCSVData(sample_csv)
    feed.load_data(
        symbols=["BTC/USD"],
        start_date=datetime(2023, 1, 2),
        end_date=datetime(2023, 1, 3),
    )

    # Should only have 2 bars (Jan 2 and Jan 3)
    bar = feed.get_latest_bar("BTC/USD")
    assert bar is not None
    assert bar["close"] == 108  # Jan 2 close

    assert feed.next() is True  # Advance to Jan 3
    bar = feed.get_latest_bar("BTC/USD")
    assert bar["close"] == 107  # Jan 3 close

    assert feed.next() is False  # No more data


def test_next_iteration(sample_csv):
    """next() should advance through all bars and stop at the end."""
    feed = HistoricalCSVData(sample_csv)
    feed.load_data(
        symbols=["BTC/USD"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 5),
    )

    count = 1  # Already at first bar
    while feed.next():
        count += 1
    assert count == 5


def test_current_time(sample_csv):
    """current_time() should return the datetime of the current bar."""
    feed = HistoricalCSVData(sample_csv)
    feed.load_data(
        symbols=["BTC/USD"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 5),
    )

    assert feed.current_time() == datetime(2023, 1, 1)
    feed.next()
    assert feed.current_time() == datetime(2023, 1, 2)


def test_unknown_symbol(sample_csv):
    """get_latest_bar should return None for unknown symbols."""
    feed = HistoricalCSVData(sample_csv)
    feed.load_data(
        symbols=["BTC/USD"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 5),
    )

    assert feed.get_latest_bar("ETH/USD") is None
