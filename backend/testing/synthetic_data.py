"""
Synthetic Data Generator - Genereer controleerbare market scenarios.

Creates trending, ranging, volatile, en crash scenarios.
"""

import math
import random
from datetime import datetime, timedelta, UTC
from typing import List

from backend.testing.market_datasets import OHLCV


def generate_trending_market(
    start_price: float = 50000.0,
    trend_strength: float = 0.02,  # 2% per day
    num_days: int = 30,
    volatility: float = 0.01,
    start_date: datetime = None,
) -> List[OHLCV]:
    """
    Genereer trending market (uptrend or downtrend).

    Args:
        start_price: Starting price
        trend_strength: Daily trend % (positive=up, negative=down)
        num_days: Number of days
        volatility: Daily volatility (% range)
        start_date: Start datetime (defaults to now)

    Returns:
        List of OHLCV candles (1 per day)
    """
    if start_date is None:
        start_date = datetime.now(UTC)

    candles = []
    current_price = start_price

    for day in range(num_days):
        timestamp = start_date + timedelta(days=day)

        # Daily trend
        daily_trend = current_price * trend_strength

        # Add noise
        noise = random.uniform(-volatility, volatility) * current_price

        # Calculate OHLC
        open_price = current_price
        close_price = current_price + daily_trend + noise

        # High/Low within volatility range
        high_price = max(open_price, close_price) * (1 + random.uniform(0, volatility))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, volatility))

        # Volume (randomized)
        volume = random.uniform(10000, 50000)

        candles.append(
            OHLCV(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )

        current_price = close_price

    return candles


def generate_ranging_market(
    center_price: float = 50000.0,
    range_pct: float = 0.05,  # +/- 5%
    num_days: int = 30,
    start_date: datetime = None,
) -> List[OHLCV]:
    """
    Genereer ranging (sideways) market.

    Args:
        center_price: Center price of range
        range_pct: Range percentage around center
        num_days: Number of days
        start_date: Start datetime

    Returns:
        List of OHLCV candles
    """
    if start_date is None:
        start_date = datetime.now(UTC)

    candles = []
    range_low = center_price * (1 - range_pct)
    range_high = center_price * (1 + range_pct)

    current_price = center_price

    for day in range(num_days):
        timestamp = start_date + timedelta(days=day)

        # Oscillate within range
        open_price = current_price
        close_price = random.uniform(range_low, range_high)

        high_price = max(open_price, close_price) * 1.01
        low_price = min(open_price, close_price) * 0.99

        # Clamp to range
        high_price = min(high_price, range_high)
        low_price = max(low_price, range_low)

        volume = random.uniform(8000, 30000)

        candles.append(
            OHLCV(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )

        current_price = close_price

    return candles


def generate_volatile_market(
    start_price: float = 50000.0,
    volatility: float = 0.05,  # 5% swings
    num_days: int = 30,
    start_date: datetime = None,
) -> List[OHLCV]:
    """
    Genereer high-volatility market met spikes.

    Args:
        start_price: Starting price
        volatility: Daily swing percentage
        num_days: Number of days
        start_date: Start datetime

    Returns:
        List of OHLCV candles
    """
    if start_date is None:
        start_date = datetime.now(UTC)

    candles = []
    current_price = start_price

    for day in range(num_days):
        timestamp = start_date + timedelta(days=day)

        # Large random moves
        move_pct = random.uniform(-volatility, volatility) * 2

        open_price = current_price
        close_price = current_price * (1 + move_pct)

        # Wide high/low range
        high_factor = 1 + random.uniform(0, volatility)
        low_factor = 1 - random.uniform(0, volatility)

        high_price = max(open_price, close_price) * high_factor
        low_price = min(open_price, close_price) * low_factor

        volume = random.uniform(20000, 100000)  # Higher volume

        candles.append(
            OHLCV(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )

        current_price = close_price

    return candles


def generate_flash_crash(
    start_price: float = 50000.0,
    crash_depth: float = 0.20,  # -20%
    recovery_hours: int = 6,
    start_date: datetime = None,
) -> List[OHLCV]:
    """
    Genereer flash crash scenario met recovery.

    Args:
        start_price: Pre-crash price
        crash_depth: Crash depth (0.20 = -20%)
        recovery_hours: Hours to full recovery
        start_date: Start datetime

    Returns:
        List of hourly OHLCV candles
    """
    if start_date is None:
        start_date = datetime.now(UTC)

    candles = []
    crash_price = start_price * (1 - crash_depth)

    # Pre-crash (normal)
    for hour in range(24):
        timestamp = start_date + timedelta(hours=hour)
        price = start_price + random.uniform(-100, 100)

        candles.append(
            OHLCV(
                timestamp=timestamp,
                open=price,
                high=price * 1.005,
                low=price * 0.995,
                close=price,
                volume=random.uniform(5000, 10000),
            )
        )

    # CRASH (1 hour)
    crash_timestamp = start_date + timedelta(hours=24)
    candles.append(
        OHLCV(
            timestamp=crash_timestamp,
            open=start_price,
            high=start_price,
            low=crash_price,  # Flash low
            close=crash_price * 1.05,  # Slight bounce
            volume=200000,  # Massive volume
        )
    )

    # Recovery
    for hour in range(recovery_hours):
        timestamp = crash_timestamp + timedelta(hours=hour + 1)
        recovery_pct = (hour + 1) / recovery_hours
        price = crash_price + (start_price - crash_price) * recovery_pct

        candles.append(
            OHLCV(
                timestamp=timestamp,
                open=price,
                high=price * 1.01,
                low=price * 0.99,
                close=price,
                volume=random.uniform(50000, 100000),
            )
        )

    return candles
