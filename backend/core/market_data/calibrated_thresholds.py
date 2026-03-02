"""
Calibrated Thresholds for Market Emotion Detection

Uses historical backtest data to calculate proper percentiles
instead of hardcoded values (0.05, 0.3, etc.)
"""

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class CalibratedThresholds:
    """
    Kalibreerde drempels gebaseerd op historische backtest data.

    In plaats van willekeurige waarden (0.05, 0.3), gebruiken we:
    - 90th percentile voor extreme conditions
    - 75th percentile voor high conditions
    - 50th percentile voor normal conditions
    """

    def __init__(self, data_dir: str = "backtest_results"):
        self.data_dir = Path(data_dir)
        self.thresholds: dict | None = None
        self.stats: dict | None = None

        # Try to load from cache first
        cache_file = self.data_dir / ".calibration_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cached = json.load(f)
                    self.thresholds = cached.get("thresholds")
                    self.stats = cached.get("stats")
                    logger.info(f"Loaded cached calibration from {cache_file}")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

        if self.thresholds is None:
            self.thresholds = self._calibrate_from_data()
            self._save_cache(cache_file)

    def _calibrate_from_data(self) -> dict:
        """
        Analyseer alle ml_batch_*.json files om percentiles te berekenen.
        """
        logger.info("Calibrating thresholds from backtest data...")

        all_volatilities = []
        all_imbalances = []
        all_volume_ratios = []
        all_rsi_values = []

        # Load ml_batch files
        batch_files = list(self.data_dir.glob("ml_batch_*.json"))

        if not batch_files:
            logger.warning("No ml_batch files found! Using defaults.")
            return self._default_thresholds()

        logger.info(f"Found {len(batch_files)} batch files")

        for file in batch_files:
            try:
                with open(file) as f:
                    data = json.load(f)

                features = data.get("ml_features", [])

                for feature in features:
                    # ATR% as volatility proxy
                    if "atr_pct" in feature:
                        all_volatilities.append(feature["atr_pct"])

                    # Volume ratio - 1.0 = neutral
                    if "volume_ratio" in feature:
                        all_volume_ratios.append(feature["volume_ratio"])

                    # RSI for extremes
                    if "rsi" in feature:
                        all_rsi_values.append(feature["rsi"])

                    # Use bb_position as imbalance proxy
                    if "bb_position" in feature:
                        # Convert 0-1 to -1 to 1 range
                        imbalance = (feature["bb_position"] - 0.5) * 2
                        all_imbalances.append(imbalance)

            except Exception as e:
                logger.warning(f"Error loading {file}: {e}")

        if not all_volatilities:
            logger.warning("No data extracted! Using defaults.")
            return self._default_thresholds()

        # Calculate percentiles
        vol_series = pd.Series(all_volatilities)
        imb_series = pd.Series(all_imbalances) if all_imbalances else pd.Series([0])
        vol_ratio_series = pd.Series(all_volume_ratios) if all_volume_ratios else pd.Series([1.0])
        rsi_series = pd.Series(all_rsi_values) if all_rsi_values else pd.Series([50])

        self.stats = {
            "volatility": {
                "count": len(vol_series),
                "mean": float(vol_series.mean()),
                "std": float(vol_series.std()),
                "min": float(vol_series.min()),
                "max": float(vol_series.max()),
                "median": float(vol_series.median()),
            },
            "imbalance": {
                "count": len(imb_series),
                "mean": float(imb_series.mean()),
                "std": float(imb_series.std()),
            },
            "volume_ratio": {
                "count": len(vol_ratio_series),
                "mean": float(vol_ratio_series.mean()),
                "median": float(vol_ratio_series.median()),
            },
            "rsi": {
                "count": len(rsi_series),
                "mean": float(rsi_series.mean()),
                "std": float(rsi_series.std()),
            },
        }

        thresholds = {
            # Volatility percentiles
            "capitulation_vol": float(vol_series.quantile(0.90)),  # Extreme fear
            "euphoria_vol": float(vol_series.quantile(0.85)),  # Extreme greed
            "uncertainty_vol": float(vol_series.quantile(0.70)),  # High vol
            "normal_vol": float(vol_series.quantile(0.50)),  # Median
            # Imbalance (using bb_position as proxy)
            "extreme_imbalance": float(imb_series.quantile(0.90)),
            "high_imbalance": float(imb_series.quantile(0.75)),
            # Volume
            "high_volume": float(vol_ratio_series.quantile(0.80)),
            "extreme_volume": float(vol_ratio_series.quantile(0.95)),
            # RSI
            "oversold_rsi": float(rsi_series.quantile(0.10)),  # 10th percentile
            "overbought_rsi": float(rsi_series.quantile(0.90)),  # 90th percentile
            # Metadata
            "sample_size": len(vol_series),
            "calibration_date": pd.Timestamp.now().isoformat(),
        }

        logger.info(f"Calibration complete! Sample size: {thresholds['sample_size']}")
        logger.info(f"Volatility 90th percentile: {thresholds['capitulation_vol']:.4f}")
        logger.info(
            f"RSI extremes: {thresholds['oversold_rsi']:.1f} - {thresholds['overbought_rsi']:.1f}"
        )

        return thresholds

    def _default_thresholds(self) -> dict:
        """Fallback als er geen data is."""
        return {
            "capitulation_vol": 0.05,
            "euphoria_vol": 0.03,
            "uncertainty_vol": 0.025,
            "normal_vol": 0.02,
            "extreme_imbalance": 0.3,
            "high_imbalance": 0.2,
            "high_volume": 1.5,
            "extreme_volume": 2.5,
            "oversold_rsi": 30,
            "overbought_rsi": 70,
            "sample_size": 0,
            "calibration_date": "default",
            "note": "Using hardcoded defaults - no backtest data found",
        }

    def _save_cache(self, cache_file: Path):
        """Save calibration to cache."""
        try:
            cache_data = {
                "thresholds": self.thresholds,
                "stats": self.stats,
                "cached_at": pd.Timestamp.now().isoformat(),
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Cached calibration to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def detect_emotion(
        self, volatility_1m: float, imbalance: float, volume_ratio: float = 1.0
    ) -> str:
        """
        Detecteer markt emotie gebaseerd op kalibreerde drempels.

        Args:
            volatility_1m: 1-minuut realized volatility (bijv. 0.02 = 2%)
            imbalance: Order flow imbalance -1 tot 1
            volume_ratio: Huidig volume / gemiddeld volume

        Returns:
            str: "Capitulation", "Euphoria", "Uncertainty", of "Neutral"
        """
        # Capitulation = extreme vol + selling pressure
        if volatility_1m > self.thresholds["capitulation_vol"] and imbalance < -0.2:
            return "Capitulation"

        # Euphoria = high vol + buying pressure
        elif volatility_1m > self.thresholds["euphoria_vol"] and imbalance > 0.2:
            return "Euphoria"

        # Extreme volume can indicate both
        elif volume_ratio > self.thresholds["extreme_volume"]:
            if imbalance > 0.3:
                return "Euphoria"
            elif imbalance < -0.3:
                return "Capitulation"

        # Uncertainty = elevated vol maar geen duidelijke richting
        elif volatility_1m > self.thresholds["uncertainty_vol"] and abs(imbalance) < 0.1:
            return "Uncertainty"

        return "Neutral"

    def get_thresholds(self) -> dict:
        """Return alle kalibreerde drempels."""
        return self.thresholds.copy()

    def get_stats(self) -> dict | None:
        """Return statistieken van de kalibratie data."""
        return self.stats.copy() if self.stats else None

    def is_extreme_condition(self, volatility: float, rsi: float) -> bool:
        """Check of we in een extreme marktconditie zijn."""
        return (
            volatility > self.thresholds["capitulation_vol"]
            or rsi < self.thresholds["oversold_rsi"]
            or rsi > self.thresholds["overbought_rsi"]
        )


# Singleton instance voor gebruik in de applicatie
_calibrated_thresholds: CalibratedThresholds | None = None


def get_thresholds() -> CalibratedThresholds:
    """Get singleton instance of calibrated thresholds."""
    global _calibrated_thresholds
    if _calibrated_thresholds is None:
        _calibrated_thresholds = CalibratedThresholds()
    return _calibrated_thresholds


def detect_market_emotion(volatility_1m: float, imbalance: float, volume_ratio: float = 1.0) -> str:
    """Convenience functie voor emotion detection."""
    return get_thresholds().detect_emotion(volatility_1m, imbalance, volume_ratio)


if __name__ == "__main__":
    # Test kalibratie
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("CALIBRATED THRESHOLDS - TEST")
    print("=" * 60)

    cal = CalibratedThresholds()

    print("\nKalibreerde drempels:")
    for key, value in cal.get_thresholds().items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    print("\nStatistieken:")
    stats = cal.get_stats()
    if stats:
        for category, values in stats.items():
            print(f"\n  {category}:")
            for metric, val in values.items():
                if isinstance(val, float):
                    print(f"    {metric}: {val:.4f}")
                else:
                    print(f"    {metric}: {val}")

    # Test scenarios
    print("\n" + "=" * 60)
    print("TEST SCENARIOS:")
    print("=" * 60)

    scenarios = [
        (0.02, 0.0, 1.0, "Normale markt"),
        (0.08, -0.5, 2.5, "Crash (hoge vol, selling)"),
        (0.06, 0.4, 2.0, "Rally (hoge vol, buying)"),
        (0.04, 0.0, 1.2, "Onzeker (medium vol, neutraal)"),
    ]

    for vol, imb, vol_ratio, desc in scenarios:
        emotion = cal.detect_emotion(vol, imb, vol_ratio)
        print(f"\n{desc}:")
        print(f"  Vol: {vol:.2%}, Imb: {imb:+.2f}, VolRatio: {vol_ratio:.1f}")
        print(f"  -> Emotion: {emotion}")
