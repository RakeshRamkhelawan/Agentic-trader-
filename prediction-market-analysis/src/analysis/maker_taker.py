"""
Maker/Taker Spread Analysis
Analyzes bid-ask spreads for prediction markets.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SpreadMetrics:
    """Spread analysis metrics."""

    mean_spread: float
    median_spread: float
    std_spread: float
    min_spread: float
    max_spread: float
    spread_percentage_mean: float
    liquidity_score: float  # 0-100, higher is better

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "mean_spread": self.mean_spread,
            "median_spread": self.median_spread,
            "std_spread": self.std_spread,
            "min_spread": self.min_spread,
            "max_spread": self.max_spread,
            "spread_percentage_mean": self.spread_percentage_mean,
            "liquidity_score": self.liquidity_score,
        }


class MakerTakerAnalyzer:
    """
    Analyzes maker/taker spreads in prediction markets.

    For binary prediction markets (YES/NO outcomes), analyzes the bid-ask
    spread between YES and NO prices.

    Usage:
        analyzer = MakerTakerAnalyzer()
        metrics = analyzer.analyze_market(df)
        print(metrics.liquidity_score)
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
        yes_price_col: str = "yes_price",
        no_price_col: str = "no_price",
        volume_col: str = "volume",
    ) -> Optional[SpreadMetrics]:
        """
        Analyze spreads in a market.

        Args:
            df: DataFrame with trade data
            yes_price_col: Column name for YES price
            no_price_col: Column name for NO price
            volume_col: Column name for volume/amount

        Returns:
            SpreadMetrics or None if insufficient data
        """
        if len(df) < self.min_trades:
            logger.warning(f"Insufficient trades: {len(df)} < {self.min_trades}")
            return None

        # Calculate spreads
        spreads = self._calculate_spreads(df, yes_price_col, no_price_col)

        # Calculate metrics
        mean_spread = spreads.mean()
        median_spread = spreads.median()
        std_spread = spreads.std()
        min_spread = spreads.min()
        max_spread = spreads.max()

        # Spread as percentage of mid-price
        mid_prices = (df[yes_price_col] + df[no_price_col]) / 2
        spread_percentage = (spreads / mid_prices * 100).mean()

        # Liquidity score (0-100)
        # Lower spreads = higher liquidity
        # Score = max 100 when spread_percentage is < 1%, decreases linearly
        liquidity_score = min(100, max(0, 100 * (1 - spread_percentage / 5)))

        return SpreadMetrics(
            mean_spread=float(mean_spread),
            median_spread=float(median_spread),
            std_spread=float(std_spread),
            min_spread=float(min_spread),
            max_spread=float(max_spread),
            spread_percentage_mean=float(spread_percentage),
            liquidity_score=float(liquidity_score),
        )

    def _calculate_spreads(
        self, df: pd.DataFrame, yes_col: str, no_col: str
    ) -> pd.Series:
        """
        Calculate spreads between YES and NO prices.

        Spread = ABS(YES_price - NO_price)
        In a binary market, YES + NO ≈ 1.0, so spread shows liquidity
        """
        return (df[yes_col] - df[no_col]).abs()

    def analyze_time_series(
        self,
        df: pd.DataFrame,
        time_col: str = "trade_time",
        yes_price_col: str = "yes_price",
        no_price_col: str = "no_price",
        window_hours: int = 1,
    ) -> pd.DataFrame:
        """
        Analyze spreads over time using rolling windows.

        Args:
            df: DataFrame with trade data and timestamp
            time_col: Column name for timestamp
            yes_price_col: Column name for YES price
            no_price_col: Column name for NO price
            window_hours: Hour window for rolling analysis

        Returns:
            DataFrame with time-indexed spread metrics
        """
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values(time_col)
        df = df.set_index(time_col)

        # Calculate spreads
        spreads = (df[yes_price_col] - df[no_price_col]).abs()

        # Rolling window statistics
        window = f"{window_hours}h"
        rolling = spreads.rolling(window)

        result = pd.DataFrame(
            {
                "mean_spread": rolling.mean(),
                "median_spread": rolling.median(),
                "std_spread": rolling.std(),
                "count": rolling.count(),
            }
        )

        return result.dropna()

    def compare_markets(
        self,
        markets_data: Dict[str, pd.DataFrame],
        yes_price_col: str = "yes_price",
        no_price_col: str = "no_price",
    ) -> pd.DataFrame:
        """
        Compare spreads across multiple markets.

        Args:
            markets_data: Dict of market_name -> DataFrame
            yes_price_col: Column name for YES price
            no_price_col: Column name for NO price

        Returns:
            DataFrame with comparison metrics
        """
        results = []

        for market_name, df in markets_data.items():
            metrics = self.analyze_market(df, yes_price_col, no_price_col)
            if metrics:
                row = metrics.to_dict()
                row["market"] = market_name
                results.append(row)

        return pd.DataFrame(results)

    def find_arbitrage_opportunities(
        self,
        df: pd.DataFrame,
        yes_price_col: str = "yes_price",
        no_price_col: str = "no_price",
        min_spread_pct: float = 0.5,
    ) -> pd.DataFrame:
        """
        Find potential arbitrage opportunities.

        In a fair binary market, YES_price + NO_price should equal 1.0
        When it deviates, there's an arbitrage opportunity.

        Args:
            df: Trade dataframe
            yes_price_col: Column name for YES price
            no_price_col: Column name for NO price
            min_spread_pct: Minimum deviation % to flag as opportunity

        Returns:
            DataFrame with arbitrage opportunities
        """
        df = df.copy()
        df["total_price"] = df[yes_price_col] + df[no_price_col]
        df["deviation_pct"] = (df["total_price"] - 1.0).abs() * 100

        # Filter for opportunities
        opportunities = df[df["deviation_pct"] > min_spread_pct].copy()

        if len(opportunities) > 0:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities")

        return opportunities[
            [yes_price_col, no_price_col, "total_price", "deviation_pct"]
        ]

    def calculate_market_efficiency(
        self,
        df: pd.DataFrame,
        yes_price_col: str = "yes_price",
        no_price_col: str = "no_price",
    ) -> float:
        """
        Calculate market efficiency score (0-100).

        Based on:
        - Spread tightness: YES + NO ≈ 1.0
        - Consistent pricing: Low volatility

        Args:
            df: Trade dataframe
            yes_price_col: Column name for YES price
            no_price_col: Column name for NO price

        Returns:
            Efficiency score 0-100 (higher is more efficient)
        """
        if len(df) < self.min_trades:
            return 0.0

        # Check if prices sum to ~1.0 (binary market invariant)
        total_prices = df[yes_price_col] + df[no_price_col]
        deviation = (total_prices - 1.0).abs().mean()

        # Efficiency score based on deviation
        # Perfect efficiency: deviation = 0, score = 100
        # Poor efficiency: deviation > 0.2, score = 0
        efficiency = max(0, min(100, 100 * (1 - deviation / 0.2)))

        return float(efficiency)
