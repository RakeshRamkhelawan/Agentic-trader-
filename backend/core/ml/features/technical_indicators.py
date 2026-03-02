"""
Technical Indicators for Chitta Features

Voegt professionele trading indicators toe als features.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0):
    """Calculate Bollinger Bands."""
    middle = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower


def add_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """Voeg alle technical indicators toe aan DataFrame."""
    df = df.copy()

    price_col = "value" if "value" in df.columns else "close"
    if price_col not in df.columns:
        return df

    prices = df[price_col]

    if "returns" not in df.columns:
        df["returns"] = prices.pct_change()

    # RSI
    df["rsi_14"] = calculate_rsi(prices, window=14)
    df["rsi_7"] = calculate_rsi(prices, window=7)

    # MACD
    macd, signal, hist = calculate_macd(prices)
    df["macd"] = macd
    df["macd_signal"] = signal
    df["macd_hist"] = hist

    # Bollinger Bands
    upper, middle, lower = calculate_bollinger_bands(prices)
    df["bb_position"] = (prices - lower) / (upper - lower)
    df["bb_width"] = (upper - lower) / middle

    # Moving averages
    df["sma_10"] = prices.rolling(window=10).mean()
    df["sma_30"] = prices.rolling(window=30).mean()
    df["dist_sma10"] = (prices - df["sma_10"]) / df["sma_10"]
    df["dist_sma30"] = (prices - df["sma_30"]) / df["sma_30"]

    # Volatility
    df["volatility_7d"] = df["returns"].rolling(window=7).std()
    df["volatility_30d"] = df["returns"].rolling(window=30).std()

    # Trend
    df["trend_7d"] = np.where(df["returns"].rolling(7).sum() > 0, 1, -1)
    df["trend_30d"] = np.where(df["returns"].rolling(30).sum() > 0, 1, -1)

    # Momentum
    df["momentum_5d"] = prices.pct_change(periods=5)
    df["momentum_10d"] = prices.pct_change(periods=10)

    # Fill NaN
    df = df.ffill().fillna(0)

    return df


def get_feature_columns() -> list:
    """Lijst van alle feature columns."""
    return [
        "returns", "drawdown", "prana", "rsi_14", "rsi_7",
        "macd", "macd_signal", "macd_hist", "bb_position", "bb_width",
        "dist_sma10", "dist_sma30", "volatility_7d", "volatility_30d",
        "trend_7d", "trend_30d", "momentum_5d", "momentum_10d"
    ]
