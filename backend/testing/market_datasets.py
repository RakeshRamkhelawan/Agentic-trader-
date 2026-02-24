"""
Market Datasets - Core dataset structures voor backtesting.

Defines OHLCV data, market scenarios, en evaluation datasets.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.core.schemas.ooda_types import MarketRegime


@dataclass
class OHLCV:
    """
    Open-High-Low-Close-Volume candlestick data.

    Standard market data representation.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):
        """Validate OHLCV constraints."""
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) must be >= Low ({self.low})")
        if self.high < self.close:
            raise ValueError(f"High ({self.high}) must be >= Close ({self.close})")
        if self.low > self.close:
            raise ValueError(f"Low ({self.low}) must be <= Close ({self.close})")
        if self.high < self.open:
            raise ValueError(f"High ({self.high}) must be >= Open ({self.open})")
        if self.low > self.open:
            raise ValueError(f"Low ({self.low}) must be <= Open ({self.open})")
        if self.volume < 0:
            raise ValueError(f"Volume ({self.volume}) must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass
class MarketScenario:
    """
    Single market scenario voor testing.

    Contains OHLCV data + metadata about expected behavior.
    """

    name: str
    description: str
    symbol: str
    timeframe: str  # "1h", "1d"
    data_points: list[OHLCV]
    expected_regime: MarketRegime
    metadata: dict[str, Any]

    def __post_init__(self):
        """Validate scenario."""
        if not self.data_points:
            raise ValueError("Scenario must have at least 1 data point")
        if self.timeframe not in ["1m", "5m", "15m", "1h", "4h", "1d"]:
            raise ValueError(f"Invalid timeframe: {self.timeframe}")

    def get_price_range(self) -> tuple[float, float]:
        """Get min/max prices in scenario."""
        all_prices = []
        for candle in self.data_points:
            all_prices.extend([candle.low, candle.high])
        return (min(all_prices), max(all_prices))

    def get_duration_hours(self) -> float:
        """Get scenario duration in hours."""
        if len(self.data_points) < 2:
            return 0.0

        start = self.data_points[0].timestamp
        end = self.data_points[-1].timestamp
        delta = end - start
        return delta.total_seconds() / 3600

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            "name": self.name,
            "description": self.description,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "data": [candle.to_dict() for candle in self.data_points],
            "expected_regime": self.expected_regime.value,
            "metadata": self.metadata,
        }


class EvaluationDataset:
    """
    Collection van market scenarios.

    Provides filtering en scenario management.
    """

    def __init__(self):
        """Initialize empty dataset."""
        self.scenarios: dict[str, MarketScenario] = {}

    def add_scenario(self, scenario: MarketScenario):
        """
        Add scenario to dataset.

        Args:
            scenario: MarketScenario to add
        """
        self.scenarios[scenario.name] = scenario

    def get_scenario(self, name: str) -> MarketScenario | None:
        """
        Get scenario by name.

        Args:
            name: Scenario name

        Returns:
            MarketScenario or None
        """
        return self.scenarios.get(name)

    def list_scenarios(self) -> list[str]:
        """
        List all scenario names.

        Returns:
            List of scenario names
        """
        return list(self.scenarios.keys())

    def filter_by_regime(self, regime: MarketRegime) -> list[MarketScenario]:
        """
        Filter scenarios by expected regime.

        Args:
            regime: MarketRegime to filter by

        Returns:
            List of matching scenarios
        """
        return [
            scenario for scenario in self.scenarios.values() if scenario.expected_regime == regime
        ]

    def filter_by_symbol(self, symbol: str) -> list[MarketScenario]:
        """
        Filter scenarios by symbol.

        Args:
            symbol: Symbol to filter by (e.g., "BTC/USDT")

        Returns:
            List of matching scenarios
        """
        return [scenario for scenario in self.scenarios.values() if scenario.symbol == symbol]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get dataset statistics.

        Returns:
            Statistics dict
        """
        if not self.scenarios:
            return {"total_scenarios": 0, "regimes": {}, "symbols": []}

        regime_counts = {}
        symbols = set()

        for scenario in self.scenarios.values():
            regime = scenario.expected_regime.value
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            symbols.add(scenario.symbol)

        return {
            "total_scenarios": len(self.scenarios),
            "regimes": regime_counts,
            "symbols": sorted(list(symbols)),
        }
