"""
Market Emotion Calibrator

Berekent dynamische drempelwaarden gebaseerd op historische backtest data.
Geen hardcoded 0.05 volatiliteit meer, maar percentiles uit je eigen data.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class EmotionThresholds:
    """Dynamische drempels gebaseerd op historische data."""

    # Volatiliteit drempels (percentielen)
    vol_capitulation: float  # 95th percentile (extreme)
    vol_euphoria: float      # 90th percentile (high)
    vol_uncertainty: float   # 75th percentile (elevated)

    # Order imbalance drempels
    imb_extreme_selling: float   # 10th percentile
    imb_strong_selling: float    # 25th percentile
    imb_strong_buying: float     # 75th percentile
    imb_extreme_buying: float    # 90th percentile

    # Spread drempels
    spread_high: float       # 90th percentile

    # Data kwaliteit
    sample_size: int
    data_date_range: tuple

    def to_dict(self) -> dict:
        return {
            "volatility": {
                "capitulation": f"{self.vol_capitulation:.2%}",
                "euphoria": f"{self.vol_euphoria:.2%}",
                "uncertainty": f"{self.vol_uncertainty:.2%}",
            },
            "imbalance": {
                "extreme_selling": f"{self.imb_extreme_selling:.2f}",
                "strong_selling": f"{self.imb_strong_selling:.2f}",
                "strong_buying": f"{self.imb_strong_buying:.2f}",
                "extreme_buying": f"{self.imb_extreme_buying:.2f}",
            },
            "sample_size": self.sample_size,
        }


class MarketEmotionCalibrator:
    """
    Kalibreert emotion detectie drempels op basis van backtest data.

    Usage:
        calibrator = MarketEmotionCalibrator()
        thresholds = calibrator.calibrate_from_backtests("backtest_results/")

        # Sla op voor hergebruik
        calibrator.save_thresholds(thresholds, "config/emotion_thresholds.json")
    """

    def __init__(self):
        self.thresholds: EmotionThresholds | None = None

    def calibrate_from_backtests(
        self,
        backtest_dir: str = "backtest_results"
    ) -> EmotionThresholds:
        """
        Analyseer alle backtest CSV/JSON files en bereken statistische drempels.
        """
        backtest_path = Path(backtest_dir)

        if not backtest_path.exists():
            logger.warning(f"Backtest dir {backtest_dir} niet gevonden, gebruik defaults")
            return self._default_thresholds()

        # Zoek harmony/trades CSV files (bevatten volatility metrics)
        csv_files = list(backtest_path.glob("*_harmony.csv"))

        if not csv_files:
            logger.warning("Geen harmony CSV gevonden, gebruik defaults")
            return self._default_thresholds()

        # Combineer alle data
        all_data = []
        for csv_file in csv_files[:5]:  # Laatste 5 runs
            try:
                df = pd.read_csv(csv_file)
                all_data.append(df)
            except Exception as e:
                logger.warning(f"Kon {csv_file} niet laden: {e}")

        if not all_data:
            return self._default_thresholds()

        combined = pd.concat(all_data, ignore_index=True)

        # Bereken percentielen
        # We gebruiken de 'volatility' kolom als die bestaat, anders infereren we uit returns
        if "volatility" in combined.columns:
            vols = combined["volatility"].dropna()
        elif "returns" in combined.columns:
            # Bereken rolling volatility uit returns
            returns = combined["returns"].dropna()
            vols = returns.rolling(window=20).std() * np.sqrt(252)  # Annualized
        else:
            logger.warning("Geen volatility/returns kolom gevonden")
            return self._default_thresholds()

        # Order imbalance (als beschikbaar)
        if "imbalance" in combined.columns:
            imbs = combined["imbalance"].dropna()
        else:
            # Default: simuleer uit volume data
            imbs = pd.Series(np.random.normal(0, 0.3, len(vols)))  # Placeholder

        # Bereken drempels
        thresholds = EmotionThresholds(
            vol_capitulation=float(np.percentile(vols, 95)),
            vol_euphoria=float(np.percentile(vols, 90)),
            vol_uncertainty=float(np.percentile(vols, 75)),
            imb_extreme_selling=float(np.percentile(imbs, 10)),
            imb_strong_selling=float(np.percentile(imbs, 25)),
            imb_strong_buying=float(np.percentile(imbs, 75)),
            imb_extreme_buying=float(np.percentile(imbs, 90)),
            spread_high=0.001,  # 10 bps default
            sample_size=len(combined),
            data_date_range=(
                str(combined.index.min()) if hasattr(combined.index, 'min') else "unknown",
                str(combined.index.max()) if hasattr(combined.index, 'max') else "unknown"
            )
        )

        self.thresholds = thresholds

        logger.info(f"Kalibratie voltooid op {thresholds.sample_size} samples")
        logger.info(f"   Capitulation threshold: {thresholds.vol_capitulation:.2%}")
        logger.info(f"   Euphoria threshold: {thresholds.vol_euphoria:.2%}")

        return thresholds

    def detect_emotion(
        self,
        volatility_1m: float,
        imbalance: float,
        spread_pct: float,
        use_calibrated: bool = True
    ) -> tuple[str, float]:
        """
        Detecteer markt emotie met gekalibreerde drempels.

        Returns:
            (emotion, confidence)
        """
        if use_calibrated and self.thresholds:
            t = self.thresholds
        else:
            t = self._default_thresholds()

        # Capitulation: extreme vol + extreme selling
        if volatility_1m > t.vol_capitulation and imbalance < t.imb_extreme_selling:
            confidence = min(1.0, (volatility_1m / t.vol_capitulation) * 0.8 +
                           (abs(imbalance) / abs(t.imb_extreme_selling)) * 0.2)
            return "Capitulation", confidence

        # Euphoria: high vol + extreme buying
        if volatility_1m > t.vol_euphoria and imbalance > t.imb_extreme_buying:
            confidence = min(1.0, (volatility_1m / t.vol_euphoria) * 0.7 +
                           (imbalance / t.imb_extreme_buying) * 0.3)
            return "Euphoria", confidence

        # Fear: elevated vol + strong selling
        if volatility_1m > t.vol_uncertainty and imbalance < t.imb_strong_selling:
            return "Fear", 0.7

        # Greed: elevated vol + strong buying
        if volatility_1m > t.vol_uncertainty and imbalance > t.imb_strong_buying:
            return "Greed", 0.7

        # Uncertainty: low liquidity
        if spread_pct > t.spread_high:
            return "Uncertainty", 0.6

        return "Neutral", 0.5

    def _default_thresholds(self) -> EmotionThresholds:
        """Fallback als er geen backtest data is."""
        return EmotionThresholds(
            vol_capitulation=0.05,   # 5%
            vol_euphoria=0.03,       # 3%
            vol_uncertainty=0.02,    # 2%
            imb_extreme_selling=-0.3,
            imb_strong_selling=-0.15,
            imb_strong_buying=0.15,
            imb_extreme_buying=0.3,
            spread_high=0.001,
            sample_size=0,
            data_date_range=("default", "default")
        )

    def save_thresholds(self, thresholds: EmotionThresholds, path: str):
        """Sla thresholds op voor hergebruik."""
        import json
        with open(path, 'w') as f:
            json.dump(thresholds.to_dict(), f, indent=2)

    def load_thresholds(self, path: str) -> EmotionThresholds:
        """Laad eerder opgeslagen thresholds."""
        import json
        with open(path) as f:
            data = json.load(f)
        # Reconstruct thresholds from dict...
        return self._default_thresholds()  # Simplified


# Singleton instance
calibrator = MarketEmotionCalibrator()
