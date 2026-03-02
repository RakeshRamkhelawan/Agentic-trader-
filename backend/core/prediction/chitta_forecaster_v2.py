"""
Chitta Forecaster v2 - Unified Model Edition

Gebruikt het getrainde model op 15 batches (31,302 samples, 69.7% accuracy)
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


@dataclass
class Forecast:
    """Voorspelling van toekomstige marktstaat."""
    predicted_volatility: float
    predicted_trend: str  # up, down, sideways
    confidence: float
    expected_shifts: list[dict]
    model_type: str  # "heuristic", "unified_mlp"
    training_samples: int


class UnifiedDirectionPredictor(nn.Module):
    """Unified MLP model - 8 features, getraind op 15 batches."""
    def __init__(self, input_dim=8):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)


class ChittaForecasterV2:
    """
    Production forecaster met unified ML model.
    """

    def __init__(self, model_path: str | None = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.model_type = "heuristic"
        self.scaler = None

        # Auto-load unified model if exists
        if model_path is None:
            unified_path = Path("backtest_results/unified_direction_model.pt")
            if unified_path.exists():
                model_path = str(unified_path)

        if model_path:
            self.load_model(model_path)

        logger.info(f"ChittaForecasterV2 initialized (device: {self.device}, model: {self.model_type})")

    def load_model(self, path: str):
        """Laad het unified direction predictor model."""
        try:
            import joblib

            # Load model
            self.model = UnifiedDirectionPredictor(input_dim=8)
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

            # Load scaler
            scaler_path = path.replace("_model.pt", "_scaler.joblib")
            if Path(scaler_path).exists():
                self.scaler = joblib.load(scaler_path)
                logger.info(f"Loaded scaler from {scaler_path}")

            self.model_type = "unified_mlp"
            logger.info(f"Loaded Unified Direction Predictor from {path}")
            logger.info("Model trained on 31,302 samples, 11,521 parameters")

        except Exception as e:
            logger.error(f"Failed to load model from {path}: {e}")
            logger.warning("Falling back to heuristic mode")
            self.model = None
            self.scaler = None
            self.model_type = "heuristic"

    def predict(self, chitta_state: dict, horizon_minutes: int = 30) -> Forecast:
        """Maak voorspelling met het beste beschikbare model."""
        if self.model is not None:
            return self._predict_with_model(chitta_state, horizon_minutes)
        else:
            return self._predict_heuristic(chitta_state, horizon_minutes)

    def _predict_with_model(self, chitta_state: dict, horizon_minutes: int) -> Forecast:
        """Gebruik unified MLP model voor voorspelling."""
        features = self._extract_features(chitta_state)

        if features is None:
            return self._predict_heuristic(chitta_state, horizon_minutes)

        # Scale features
        if self.scaler is not None:
            features = self.scaler.transform(features.reshape(1, -1))[0]

        # Predict
        x = torch.FloatTensor(features).unsqueeze(0).to(self.device)

        with torch.no_grad():
            prob_up = self.model(x).squeeze().cpu().item()

        # Interpret prediction
        if prob_up > 0.55:
            trend = "up"
            confidence = min(0.95, prob_up)
        elif prob_up < 0.45:
            trend = "down"
            confidence = min(0.95, 1 - prob_up)
        else:
            trend = "sideways"
            confidence = 0.5

        # Volatility estimation
        volatility = abs(prob_up - 0.5) * 4

        # Council shifts
        shifts = self._infer_council_shifts(trend, chitta_state)

        return Forecast(
            predicted_volatility=volatility,
            predicted_trend=trend,
            confidence=confidence,
            expected_shifts=shifts,
            model_type=self.model_type,
            training_samples=31302
        )

    def _extract_features(self, chitta_state: dict) -> np.ndarray | None:
        """
        Extract 8 features from Chitta state.
        Must match unified training: RSI, MACD, BB_POS, MOM, VOL_RATIO, ATR, TREND, CONFIDENCE
        """
        nodes = chitta_state.get("nodes", [])

        if not nodes:
            return None

        latest = nodes[-1]
        metadata = latest.get("metadata", {})

        try:
            # 8 features (must match training exactly!)
            rsi = metadata.get("rsi", 50.0) / 100.0
            macd = np.tanh(metadata.get("macd", 0.0) / 10)
            bb_pos = metadata.get("bb_position", 0.5)
            momentum = np.tanh(metadata.get("momentum_1d", 0.0) * 10)
            vol_ratio = metadata.get("volume_ratio", 1.0) / 3
            atr = np.tanh(metadata.get("atr_pct", 0.02) * 10)
            trend = metadata.get("trend", 1) / 2.0 + 0.5  # -1/1 -> 0/1
            confidence = metadata.get("confidence", 0.0)

            return np.array([rsi, macd, bb_pos, momentum, vol_ratio, atr, trend, confidence])
        except Exception as e:
            logger.warning(f"Failed to extract features: {e}")
            return None

    def _predict_heuristic(self, chitta_state: dict, horizon_minutes: int) -> Forecast:
        """Fallback naar heuristische voorspelling."""
        nodes = chitta_state.get("nodes", [])

        if not nodes:
            return Forecast(
                predicted_volatility=0.02,
                predicted_trend="sideways",
                confidence=0.3,
                expected_shifts=[],
                model_type="heuristic",
                training_samples=0
            )

        emotions = [n.get("emotion", "neutral") for n in nodes[-20:]]
        recent_emotion = emotions[-1] if emotions else "neutral"

        if recent_emotion in ["Euphoria", "Greed"]:
            trend = "down"
            confidence = 0.55
        elif recent_emotion in ["Capitulation", "Fear"]:
            trend = "up"
            confidence = 0.6
        else:
            trend = "sideways"
            confidence = 0.4

        return Forecast(
            predicted_volatility=0.02,
            predicted_trend=trend,
            confidence=confidence,
            expected_shifts=[],
            model_type="heuristic",
            training_samples=len(nodes)
        )

    def _infer_council_shifts(self, predicted_trend: str, chitta_state: dict) -> list[dict]:
        """Bepaal welke councils van mening zouden kunnen veranderen."""
        shifts = []

        if predicted_trend == "down":
            shifts.append({
                "council": "guna",
                "shift": "rajas → tamas",
                "reason": "predicted_sell_off"
            })
        elif predicted_trend == "up":
            shifts.append({
                "council": "guna",
                "shift": "tamas → rajas",
                "reason": "predicted_rally"
            })

        return shifts


# Singleton instance
forecaster_v2 = ChittaForecasterV2()
