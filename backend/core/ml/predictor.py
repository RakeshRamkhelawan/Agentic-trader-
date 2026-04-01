"""ML-based trade prediction engine."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np


class SignalDirection(Enum):
    """Trade signal directions."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class ConfidenceLevel(Enum):
    """Prediction confidence levels."""

    LOW = "low"  # 50-65%
    MEDIUM = "medium"  # 65-80%
    HIGH = "high"  # 80-95%
    VERY_HIGH = "very_high"  # >95%


@dataclass
class PredictionResult:
    """Result of a trade prediction."""

    symbol: str
    direction: SignalDirection
    confidence: float  # 0-1
    confidence_level: ConfidenceLevel
    predicted_return: float  # Expected return %
    risk_score: float  # 0-1, higher = riskier
    time_horizon: str  # e.g., "1h", "1d", "1w"
    features_used: list[str]
    timestamp: datetime
    model_version: str
    explanation: dict[str, Any]  # Feature importance, reasoning

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction.value,
            "confidence": round(self.confidence, 4),
            "confidence_level": self.confidence_level.value,
            "predicted_return": round(self.predicted_return, 4),
            "risk_score": round(self.risk_score, 4),
            "time_horizon": self.time_horizon,
            "features_used": self.features_used,
            "timestamp": self.timestamp.isoformat(),
            "model_version": self.model_version,
            "explanation": self.explanation,
        }


class TradePredictor:
    """
    ML-based trade prediction system.

    Uses ensemble of models:
    - Trend prediction (LSTM/GRU)
    - Pattern recognition (CNN)
    - Feature-based classifier (XGBoost/Random Forest)
    """

    def __init__(self):
        self.model_version = "v1.0.0"
        self.prediction_history: list[PredictionResult] = []
        self.accuracy_tracking: dict[str, float] = {}

    def predict(
        self,
        symbol: str,
        price_history: list[float],
        volume_history: list[float],
        time_horizon: str = "1d",
        market_context: dict | None = None,
    ) -> PredictionResult:
        """
        Generate trade prediction for a symbol.

        Args:
            symbol: Trading pair symbol
            price_history: Historical price data
            volume_history: Historical volume data
            time_horizon: Prediction timeframe
            market_context: Additional market data

        Returns:
            Prediction result with confidence and explanation
        """
        # Feature extraction (simplified - in production use proper feature engineering)
        features = self._extract_features(price_history, volume_history)

        # Ensemble prediction (mock implementation)
        direction, confidence, predicted_return = self._ensemble_predict(features, market_context)

        # Calculate risk score
        risk_score = self._calculate_risk(features, predicted_return)

        # Feature importance (mock)
        feature_importance = {
            "trend_strength": 0.35,
            "volume_momentum": 0.25,
            "rsi_divergence": 0.20,
            "support_resistance": 0.15,
            "market_sentiment": 0.05,
        }

        # Determine confidence level
        confidence_level = self._get_confidence_level(confidence)

        result = PredictionResult(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            confidence_level=confidence_level,
            predicted_return=predicted_return,
            risk_score=risk_score,
            time_horizon=time_horizon,
            features_used=list(features.keys()),
            timestamp=datetime.utcnow(),
            model_version=self.model_version,
            explanation={
                "feature_importance": feature_importance,
                "top_signals": self._get_top_signals(features),
                "contradictory_signals": [],
                "market_regime": self._detect_market_regime(features),
            },
        )

        self.prediction_history.append(result)
        return result

    def _extract_features(
        self,
        prices: list[float],
        volumes: list[float],
    ) -> dict[str, float]:
        """Extract technical features from price/volume data."""
        if len(prices) < 20:
            return {}

        # Calculate returns
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]

        features = {
            # Trend features
            "sma_10": np.mean(prices[-10:]),
            "sma_20": np.mean(prices[-20:]),
            "trend_slope": self._calculate_slope(prices[-20:]),
            # Volatility
            "volatility_20": np.std(returns[-20:]) if len(returns) >= 20 else 0,
            "atr": self._calculate_atr(prices),
            # Momentum
            "rsi": self._calculate_rsi(prices),
            "momentum_10": ((prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0),
            # Volume
            "volume_sma_10": np.mean(volumes[-10:]) if len(volumes) >= 10 else 0,
            "volume_ratio": (volumes[-1] / np.mean(volumes[-10:]) if len(volumes) >= 10 else 1),
            # Price action
            "distance_from_high": (max(prices[-20:]) - prices[-1]) / prices[-1],
            "distance_from_low": (prices[-1] - min(prices[-20:])) / prices[-1],
        }

        return features

    def _calculate_slope(self, prices: list[float]) -> float:
        """Calculate linear trend slope."""
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        return slope

    def _calculate_atr(self, prices: list[float], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(prices) < period + 1:
            return 0

        tr_values = []
        for i in range(1, min(period + 1, len(prices))):
            tr = abs(prices[-i] - prices[-i - 1])
            tr_values.append(tr)

        return np.mean(tr_values) if tr_values else 0

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _ensemble_predict(
        self,
        features: dict[str, float],
        market_context: dict | None,
    ) -> tuple:
        """
        Run ensemble prediction.

        In production, this would call actual ML models.
        For now, returns rule-based predictions.
        """
        if not features:
            return SignalDirection.HOLD, 0.5, 0.0

        # Trend model score
        trend_score = 0
        if features.get("trend_slope", 0) > 0:
            trend_score += 0.3
        if features.get("momentum_10", 0) > 0:
            trend_score += 0.2
        if features.get("rsi", 50) < 70 and features.get("rsi", 50) > 30:
            trend_score += 0.1

        # Mean reversion model score
        mr_score = 0
        if features.get("rsi", 50) < 30:
            mr_score = 0.6  # Oversold = buy signal
        elif features.get("rsi", 50) > 70:
            mr_score = -0.6  # Overbought = sell signal

        # Combine scores
        combined_score = trend_score + mr_score

        # Determine direction
        if combined_score > 0.3:
            direction = SignalDirection.BUY
            confidence = min(0.5 + combined_score, 0.95)
            predicted_return = combined_score * 2  # Scale to %
        elif combined_score < -0.3:
            direction = SignalDirection.SELL
            confidence = min(0.5 - combined_score, 0.95)
            predicted_return = combined_score * 2
        else:
            direction = SignalDirection.HOLD
            confidence = 0.5
            predicted_return = 0.0

        return direction, confidence, predicted_return

    def _calculate_risk(self, features: dict[str, float], predicted_return: float) -> float:
        """Calculate risk score based on features."""
        risk = 0.5  # Base risk

        # Higher volatility = higher risk
        volatility = features.get("volatility_20", 0)
        risk += volatility * 10  # Scale appropriately

        # Distance from extremes affects risk
        rsi = features.get("rsi", 50)
        if rsi < 20 or rsi > 80:
            risk += 0.1  # Extreme RSI = potential reversal risk

        # Higher predicted return = higher risk (generally)
        risk += abs(predicted_return) * 0.1

        return min(risk, 1.0)

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Map confidence score to level."""
        if confidence >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.80:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.65:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _get_top_signals(self, features: dict[str, float]) -> list[dict]:
        """Get top trading signals from features."""
        signals = []

        rsi = features.get("rsi", 50)
        if rsi < 30:
            signals.append(
                {
                    "signal": "RSI_OVERSOLD",
                    "strength": (30 - rsi) / 30,
                    "direction": "buy",
                }
            )
        elif rsi > 70:
            signals.append(
                {
                    "signal": "RSI_OVERBOUGHT",
                    "strength": (rsi - 70) / 30,
                    "direction": "sell",
                }
            )

        if features.get("trend_slope", 0) > 0:
            signals.append(
                {
                    "signal": "UPTREND",
                    "strength": min(features["trend_slope"] * 100, 1),
                    "direction": "buy",
                }
            )
        elif features.get("trend_slope", 0) < 0:
            signals.append(
                {
                    "signal": "DOWNTREND",
                    "strength": min(abs(features["trend_slope"]) * 100, 1),
                    "direction": "sell",
                }
            )

        return signals[:3]  # Top 3 signals

    def _detect_market_regime(self, features: dict[str, float]) -> str:
        """Detect current market regime."""
        volatility = features.get("volatility_20", 0)
        trend = features.get("trend_slope", 0)

        if volatility > 0.05:
            return "high_volatility"
        elif abs(trend) > 0.01:
            return "trending" if trend > 0 else "downtrend"
        else:
            return "ranging"

    def get_prediction_accuracy(
        self,
        symbol: str | None = None,
        days: int = 30,
    ) -> dict[str, float]:
        """Calculate prediction accuracy metrics."""
        cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days)

        relevant = [
            p
            for p in self.prediction_history
            if p.timestamp > cutoff and (symbol is None or p.symbol == symbol)
        ]

        if not relevant:
            return {"accuracy": 0.0, "count": 0}

        # In production, compare with actual outcomes
        # For now, return mock metrics
        return {
            "accuracy": 0.72,
            "precision": 0.68,
            "recall": 0.75,
            "f1_score": 0.71,
            "count": len(relevant),
            "by_direction": {
                "buy": {
                    "accuracy": 0.70,
                    "count": len([p for p in relevant if p.direction == SignalDirection.BUY]),
                },
                "sell": {
                    "accuracy": 0.74,
                    "count": len([p for p in relevant if p.direction == SignalDirection.SELL]),
                },
            },
        }


# Global predictor instance
trade_predictor = TradePredictor()
