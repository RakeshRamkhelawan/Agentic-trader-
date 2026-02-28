"""
Chitta Forecaster - Met veilige fallback voor als er geen model is.

Geen LSTM/Transformer die maanden training nodig heeft, maar een
progressief systeem dat start met heuristieken en geleidelijk naar ML gaat.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Forecast:
    """Voorspelling van toekomstige marktstaat."""
    predicted_volatility: float
    predicted_trend: str  # up, down, sideways
    confidence: float

    # Welke councils zouden van mening veranderen?
    expected_shifts: list[dict]

    # Model info
    model_type: str  # "heuristic", "linear", "lstm"
    training_samples: int


class BaseForecaster(ABC):
    """Abstract base voor alle forecasters."""

    @abstractmethod
    def predict(self, chitta_state: dict, horizon_minutes: int = 30) -> Forecast:
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Is deze forecaster klaar voor gebruik?"""
        pass


class HeuristicForecaster(BaseForecaster):
    """
    Rule-based fallback die altijd werkt.
    Gebruikt simpele heuristieken:
    - Recent hoge vol -> verwacht mean reversion
    - Trend persistence (momentum)
    - Support/resistance levels uit Chitta
    """

    def predict(self, chitta_state: dict, horizon_minutes: int = 30) -> Forecast:
        """
        Simpele heuristische voorspelling.
        """
        # Extract recent nodes
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

        # Analyseer recente emotions
        emotions = [n.get("emotion", "neutral") for n in nodes[-20:]]
        volatilities = [n.get("metadata", {}).get("volatility_1m", 0.02) for n in nodes[-20:]]

        # Trend persistence: als we euphoria hadden, verwacht pullback
        recent_emotion = emotions[-1] if emotions else "neutral"

        if recent_emotion in ["Euphoria", "Greed"]:
            trend = "down"  # Mean reversion
            confidence = 0.55
        elif recent_emotion in ["Capitulation", "Fear"]:
            trend = "up"    # Bounce expected
            confidence = 0.6
        else:
            trend = "sideways"
            confidence = 0.4

        # Volatiliteit: recente vol is best predictor voor korte termijn vol
        avg_vol = np.mean(volatilities) if volatilities else 0.02
        predicted_vol = avg_vol * 0.9  # slight mean reversion

        # Expected council shifts
        shifts = []
        if recent_emotion == "Euphoria":
            shifts.append({
                "council": "guna",
                "shift": "rajas → sattva",
                "reason": "volatility_compression_expected"
            })

        return Forecast(
            predicted_volatility=predicted_vol,
            predicted_trend=trend,
            confidence=confidence,
            expected_shifts=shifts,
            model_type="heuristic",
            training_samples=len(nodes)
        )

    def is_ready(self) -> bool:
        return True  # Altijd ready


class LinearRegressionForecaster(BaseForecaster):
    """
    Eenvoudige lineaire regressie op features uit Chitta.
    Training: ~100-500 samples nodig (weken, geen maanden).
    """

    def __init__(self):
        self.weights = None
        self.bias = None
        self.feature_means = None
        self.feature_stds = None
        self.training_samples = 0

    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Train op historische data.
        X: features [n_samples, n_features]
        y: target returns [n_samples]
        """
        # Normalize
        self.feature_means = np.mean(X, axis=0)
        self.feature_stds = np.std(X, axis=0) + 1e-8
        X_norm = (X - self.feature_means) / self.feature_stds

        # Analytic solution for linear regression
        # w = (X^T X)^-1 X^T y
        try:
            self.weights = np.linalg.pinv(X_norm.T @ X_norm) @ X_norm.T @ y
            self.bias = np.mean(y)
            self.training_samples = len(X)
            logger.info(f"Linear model trained on {len(X)} samples")
        except Exception as e:
            logger.error(f"Failed to train linear model: {e}")
            self.weights = None

    def predict(self, chitta_state: dict, horizon_minutes: int = 30) -> Forecast:
        if not self.is_ready():
            raise RuntimeError("Model not trained")

        # Extract features uit chitta
        features = self._extract_features(chitta_state)
        features_norm = (features - self.feature_means) / self.feature_stds

        # Predict
        pred_return = features_norm @ self.weights + self.bias

        # Convert naar forecast
        if pred_return > 0.005:
            trend = "up"
        elif pred_return < -0.005:
            trend = "down"
        else:
            trend = "sideways"

        return Forecast(
            predicted_volatility=abs(pred_return) * 2,  # rough estimate
            predicted_trend=trend,
            confidence=min(0.8, 0.5 + self.training_samples / 1000),
            expected_shifts=[],
            model_type="linear",
            training_samples=self.training_samples
        )

    def _extract_features(self, chitta_state: dict) -> np.ndarray:
        """Extract numerieke features uit Chitta state."""
        nodes = chitta_state.get("nodes", [])

        if not nodes:
            return np.zeros(5)

        # Simple features
        recent_vols = [n.get("metadata", {}).get("volatility_1m", 0.02) for n in nodes[-10:]]

        features = [
            np.mean(recent_vols) if recent_vols else 0.02,
            np.std(recent_vols) if len(recent_vols) > 1 else 0.0,
            len([n for n in nodes if n.get("emotion") == "Euphoria"]),
            len([n for n in nodes if n.get("emotion") == "Fear"]),
            len(nodes)  # Activity level
        ]

        return np.array(features)

    def is_ready(self) -> bool:
        return self.weights is not None and self.training_samples >= 100


class ChittaForecaster:
    """
    Progressive forecasting systeem.

    Start met heuristieken, schakelt over naar ML als er genoeg data is.
    """

    def __init__(self):
        self.heuristic = HeuristicForecaster()
        self.linear = LinearRegressionForecaster()
        self.lstm = None  # Alleen laden als pickle bestaat

        self._training_data = []  # Buffer voor online learning

    def predict(self, chitta_state: dict, horizon_minutes: int = 30) -> Forecast:
        """
        Maak voorspelling met best beschikbare model.
        """
        # Priority: LSTM > Linear > Heuristic
        if self.lstm and self.lstm.is_ready():
            return self.lstm.predict(chitta_state, horizon_minutes)
        elif self.linear.is_ready():
            return self.linear.predict(chitta_state, horizon_minutes)
        else:
            return self.heuristic.predict(chitta_state, horizon_minutes)

    def record_outcome(self, chitta_state: dict, actual_return: float):
        """
        Sla op voor online learning. Train periodiek nieuw model.
        """
        self._training_data.append({
            "state": chitta_state,
            "return": actual_return
        })

        # Train linear model als we genoeg data hebben (maar niet te vaak)
        if len(self._training_data) >= 100 and len(self._training_data) % 50 == 0:
            self._retrain_linear()

    def _retrain_linear(self):
        """Hertrain lineair model met nieuwe data."""
        if len(self._training_data) < 100:
            return

        # Prepare data
        X = []
        y = []

        for item in self._training_data[-500:]:  # Laatste 500
            features = self.linear._extract_features(item["state"])
            X.append(features)
            y.append(item["return"])

        X = np.array(X)
        y = np.array(y)

        self.linear.fit(X, y)
        logger.info(f"Retrained linear model on {len(X)} samples")

    def load_lstm(self, path: str):
        """
        Laad LSTM model als het bestaat (optioneel, voor later).
        """
        try:
            import pickle
            with open(path, 'rb') as f:
                self.lstm = pickle.load(f)
            logger.info(f"Loaded LSTM model from {path}")
        except FileNotFoundError:
            logger.warning(f"No LSTM model found at {path}, using progressive fallback")
            self.lstm = None
        except Exception as e:
            logger.error(f"Failed to load LSTM: {e}")
            self.lstm = None


# Singleton
forecaster = ChittaForecaster()
