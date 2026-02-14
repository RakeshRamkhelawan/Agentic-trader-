"""
Volume Trends Analysis
Analyzes trading volume patterns and trends.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


@dataclass
class VolumeMetrics:
    """Volume analysis metrics."""

    total_volume: float
    mean_volume_per_trade: float
    median_volume: float
    std_volume: float
    max_volume: float
    trades_count: int
    volume_trend: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    peak_volume_time: Optional[str]  # ISO formatted datetime
    volume_concentration: float  # % of volume in top 10% trades

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_volume": self.total_volume,
            "mean_volume_per_trade": self.mean_volume_per_trade,
            "median_volume": self.median_volume,
            "std_volume": self.std_volume,
            "max_volume": self.max_volume,
            "trades_count": self.trades_count,
            "volume_trend": self.volume_trend,
            "trend_strength": self.trend_strength,
            "peak_volume_time": self.peak_volume_time,
            "volume_concentration": self.volume_concentration,
        }


class VolumeTrendsAnalyzer:
    """
    Analyzes trading volume trends and patterns.

    Detects volume spikes, trends, and concentration patterns.

    Usage:
        analyzer = VolumeTrendsAnalyzer()
        metrics = analyzer.analyze_market(df, volume_col="volume")
        print(f"Trend: {metrics.volume_trend}")
    """

    def __init__(self, min_trades: int = 10):
        """
        Initialize analyzer.

        Args:
            min_trades: Minimum trades required for analysis
        """
        self.min_trades = min_trades

    def analyze_market(
        self,
        df: pd.DataFrame,
        volume_col: str = "volume",
        time_col: Optional[str] = None,
    ) -> Optional[VolumeMetrics]:
        """
        Analyze volume metrics for a market.

        Args:
            df: DataFrame with trade data
            volume_col: Column name for volume/amount
            time_col: Column name for timestamp (if available)

        Returns:
            VolumeMetrics or None if insufficient data
        """
        if len(df) < self.min_trades:
            logger.warning(f"Insufficient trades: {len(df)} < {self.min_trades}")
            return None

        volumes = df[volume_col]

        # Basic metrics
        total_volume = float(volumes.sum())
        mean_volume = float(volumes.mean())
        median_volume = float(volumes.median())
        std_volume = float(volumes.std())
        max_volume = float(volumes.max())
        trades_count = len(df)

        # Trend analysis
        trend, strength = self._analyze_trend(volumes)

        # Peak volume time
        peak_time = None
        if time_col and time_col in df.columns:
            peak_idx = df[volume_col].idxmax()
            peak_time = str(df.loc[peak_idx, time_col])

        # Volume concentration (Herfindahl-like index)
        concentration = self._calculate_volume_concentration(volumes)

        return VolumeMetrics(
            total_volume=total_volume,
            mean_volume_per_trade=mean_volume,
            median_volume=median_volume,
            std_volume=std_volume,
            max_volume=max_volume,
            trades_count=trades_count,
            volume_trend=trend,
            trend_strength=strength,
            peak_volume_time=peak_time,
            volume_concentration=concentration,
        )

    def _analyze_trend(self, volumes: pd.Series) -> tuple:
        """
        Detect volume trend direction and strength.

        Uses linear regression to determine trend.

        Returns:
            (trend_direction, trend_strength)
            trend_direction: "increasing", "decreasing", or "stable"
            trend_strength: 0.0 to 1.0
        """
        if len(volumes) < 3:
            return "stable", 0.0

        # Linear regression on volume series
        x = pd.Series(range(len(volumes)))
        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, volumes)

        # Determine trend
        if p_value > 0.05:  # Not statistically significant
            trend = "stable"
            strength = 0.0
        elif slope > 0:
            trend = "increasing"
            strength = min(1.0, abs(r_value))
        else:
            trend = "decreasing"
            strength = min(1.0, abs(r_value))

        return trend, float(strength)

    def _calculate_volume_concentration(self, volumes: pd.Series) -> float:
        """
        Calculate volume concentration ratio.

        Returns % of total volume in top 10% of trades.
        High concentration > 70% indicates few large trades.
        """
        total_vol = volumes.sum()
        if total_vol == 0:
            return 0.0

        sorted_vols = volumes.sort_values(ascending=False)
        top_10_pct_count = max(1, len(sorted_vols) // 10)
        top_10_pct_volume = sorted_vols.head(top_10_pct_count).sum()

        return float((top_10_pct_volume / total_vol) * 100)

    def analyze_time_series(
        self,
        df: pd.DataFrame,
        time_col: str = "trade_time",
        volume_col: str = "volume",
        window_hours: int = 1,
    ) -> pd.DataFrame:
        """
        Analyze volume trends over time.

        Args:
            df: DataFrame with trade data
            time_col: Column name for timestamp
            volume_col: Column name for volume
            window_hours: Hour window for rolling analysis

        Returns:
            DataFrame with time-indexed volume metrics
        """
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values(time_col)
        df = df.set_index(time_col)

        window = f"{window_hours}h"
        rolling = df[volume_col].rolling(window)

        result = pd.DataFrame(
            {
                "total_volume": rolling.sum(),
                "mean_volume": rolling.mean(),
                "std_volume": rolling.std(),
                "count": rolling.count(),
                "max_volume": rolling.max(),
            }
        )

        return result.dropna()

    def detect_volume_spikes(
        self,
        df: pd.DataFrame,
        volume_col: str = "volume",
        time_col: str = "trade_time",
        detection_method: str = "zscore",
        threshold: float = 2.0,
    ) -> pd.DataFrame:
        """
        Detect anomalous volume spikes.

        Args:
            df: DataFrame with trade data
            volume_col: Column name for volume
            time_col: Column name for timestamp
            detection_method: "zscore" or "iqr"
            threshold: Detection threshold (zscore: 2-3, iqr: 1.5-3)

        Returns:
            DataFrame with spike events
        """
        df = df.copy()
        volumes = df[volume_col]

        if detection_method == "zscore":
            z_scores = scipy_stats.zscore(volumes)
            spikes = df[abs(z_scores) > threshold].copy()
            spikes["spike_magnitude"] = abs(z_scores[abs(z_scores) > threshold])

        elif detection_method == "iqr":
            Q1 = volumes.quantile(0.25)
            Q3 = volumes.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            spikes = df[(volumes < lower_bound) | (volumes > upper_bound)].copy()

        else:
            raise ValueError(f"Unknown detection_method: {detection_method}")

        logger.info(f"Detected {len(spikes)} volume spikes")
        return spikes.sort_values(time_col)

    def compare_markets(
        self, markets_data: Dict[str, pd.DataFrame], volume_col: str = "volume"
    ) -> pd.DataFrame:
        """
        Compare volume metrics across multiple markets.

        Args:
            markets_data: Dict of market_name -> DataFrame
            volume_col: Column name for volume

        Returns:
            DataFrame with comparison metrics
        """
        results = []

        for market_name, df in markets_data.items():
            metrics = self.analyze_market(df, volume_col)
            if metrics:
                row = metrics.to_dict()
                row["market"] = market_name
                results.append(row)

        return pd.DataFrame(results)

    def calculate_market_activity(
        self, df: pd.DataFrame, volume_col: str = "volume", time_col: str = "trade_time"
    ) -> float:
        """
        Calculate overall market activity score (0-100).

        Based on:
        - Total volume activity
        - Trade frequency
        - Consistency of trading

        Args:
            df: DataFrame with trade data
            volume_col: Column name for volume
            time_col: Column name for timestamp

        Returns:
            Activity score 0-100
        """
        if len(df) < self.min_trades:
            return 0.0

        # Normalize trade count (assume 100+ trades = max activity)
        trade_activity = min(100, len(df))

        # Normalize total volume (assume 10000 = max activity)
        volume_activity = min(100, df[volume_col].sum() / 100)

        # Time spread (trades distributed over time vs concentrated)
        if time_col in df.columns:
            time_range = (
                pd.to_datetime(df[time_col]).max() - pd.to_datetime(df[time_col]).min()
            )
            time_hours = time_range.total_seconds() / 3600

            # Score based on time spread (assume 24 hours = good spread)
            time_activity = min(100, time_hours * 4.17)  # 24 hours = 100
        else:
            time_activity = 50  # Neutral if no time data

        # Weighted average
        activity_score = (
            trade_activity * 0.4 + volume_activity * 0.4 + time_activity * 0.2
        )

        return float(activity_score)
