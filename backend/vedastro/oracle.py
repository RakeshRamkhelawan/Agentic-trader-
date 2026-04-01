"""
XGBoost Oracle - The "Buddhi" (Intellect)

Lightweight ML model for fast astrological predictions.
Pre-trained on historical OHLCV + VedAstro features.
Supports online learning for continuous adaptation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
import xgboost as xgb

logger = logging.getLogger(__name__)


class XGBoostOracle:
    """
    XGBoost-based prediction model for astrological trading signals.

    Features:
    - Fast inference (< 1ms)
    - Confidence-based thresholding
    - Online learning support
    - Model persistence
    """

    DEFAULT_PARAMS = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "random_state": 42,
        "n_jobs": -1,
    }

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float = 0.6,
        min_samples: int = 100,
        model_params: dict | None = None,
    ):
        """
        Initialize XGBoost Oracle.

        Args:
            model_path: Path to pre-trained model
            confidence_threshold: Minimum confidence for trading
            min_samples: Minimum samples for training
            model_params: XGBoost hyperparameters
        """
        self.confidence_threshold = confidence_threshold
        self.min_samples = min_samples
        self.model_params = model_params or self.DEFAULT_PARAMS.copy()
        self.model = None
        self.feature_importance: dict[str, float] = {}
        self.training_history: list[dict] = []

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._init_default_model()

    def _init_default_model(self):
        """Initialize with default model architecture."""
        self.model = xgb.XGBClassifier(**self.model_params)
        logger.info("Initialized default XGBoost model")

    def predict(self, features: np.ndarray) -> dict[str, Any]:
        """
        Generate prediction from feature vector.

        Args:
            features: Feature vector (24 dimensions)

        Returns:
            Prediction with probability and confidence
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")

        # Ensure correct shape
        if len(features.shape) == 1:
            features = features.reshape(1, -1)

        # Predict probabilities
        proba = self.model.predict_proba(features)[0]
        prediction = int(np.argmax(proba))
        confidence = float(np.max(proba))

        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(proba)

        return {
            "direction": "UP" if prediction == 1 else "DOWN",
            "prediction": prediction,
            "up_probability": float(proba[1]),
            "down_probability": float(proba[0]),
            "confidence": confidence,
            "signal_strength": signal_strength,
            "should_trade": confidence >= self.confidence_threshold,
            "confidence_gap": abs(proba[1] - proba[0]),
        }

    def predict_batch(self, features: np.ndarray) -> list[dict[str, Any]]:
        """
        Batch prediction for multiple samples.

        Args:
            features: Feature matrix (n_samples x 24)

        Returns:
            List of predictions
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")

        probabilities = self.model.predict_proba(features)
        predictions = np.argmax(probabilities, axis=1)

        results = []
        for pred, proba in zip(predictions, probabilities, strict=False):
            confidence = float(np.max(proba))
            results.append(
                {
                    "direction": "UP" if pred == 1 else "DOWN",
                    "prediction": int(pred),
                    "up_probability": float(proba[1]),
                    "down_probability": float(proba[0]),
                    "confidence": confidence,
                    "should_trade": confidence >= self.confidence_threshold,
                }
            )

        return results

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_split: float = 0.2,
        early_stopping_rounds: int = 10,
    ) -> dict[str, float]:
        """
        Train model on historical data.

        Args:
            X: Feature matrix
            y: Labels (0=DOWN, 1=UP)
            validation_split: Fraction for validation
            early_stopping_rounds: Early stopping patience

        Returns:
            Training metrics
        """
        if len(X) < self.min_samples:
            raise ValueError(f"Insufficient samples: {len(X)} < {self.min_samples}")

        # Split validation set
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Train (new XGBoost API)
        self.model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        # Calculate metrics
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)

        train_acc = float(np.mean(train_pred == y_train))
        val_acc = float(np.mean(val_pred == y_val))

        # Get feature importance
        self._update_feature_importance()

        metrics = {
            "train_accuracy": train_acc,
            "val_accuracy": val_acc,
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "best_iteration": (
                self.model.best_iteration
                if hasattr(self.model, "best_iteration")
                else self.model_params["n_estimators"]
            ),
        }

        self.training_history.append(metrics)
        logger.info(f"Training complete: {metrics}")

        return metrics

    def update_online(
        self, X: np.ndarray, y: np.ndarray, learning_rate: float | None = None
    ) -> None:
        """
        Online learning update with new data.

        Args:
            X: New feature samples
            y: New labels
            learning_rate: Optional learning rate override
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")

        # Store current trees
        booster = self.model.get_booster()

        # Update with new data
        learning_rate or self.model_params.get("learning_rate", 0.1) * 0.5

        self.model.fit(X, y, xgb_model=booster, verbose=False)

        logger.info(f"Online update complete with {len(X)} samples")

    def _calculate_signal_strength(self, probabilities: np.ndarray) -> str:
        """
        Categorize signal strength.

        Args:
            probabilities: Prediction probabilities

        Returns:
            Signal strength category
        """
        confidence = float(np.max(probabilities))

        if confidence >= 0.8:
            return "STRONG"
        elif confidence >= 0.65:
            return "MODERATE"
        elif confidence >= 0.55:
            return "WEAK"
        else:
            return "UNCERTAIN"

    def _update_feature_importance(self):
        """Update feature importance dictionary."""
        if self.model is None:
            return

        importance = self.model.feature_importances_
        from .features import FeatureEngine

        feature_names = FeatureEngine().get_feature_names()
        self.feature_importance = {
            name: float(imp) for name, imp in zip(feature_names, importance, strict=False)
        }

    def get_top_features(self, n: int = 5) -> list[tuple[str, float]]:
        """
        Get top N most important features.

        Args:
            n: Number of features

        Returns:
            List of (feature_name, importance) tuples
        """
        if not self.feature_importance:
            self._update_feature_importance()

        sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
        return sorted_features[:n]

    def save_model(self, path: str) -> None:
        """
        Save model to disk.

        Args:
            path: Save path
        """
        if self.model is None:
            raise RuntimeError("No model to save")

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(path)

        # Save metadata
        metadata = {
            "confidence_threshold": self.confidence_threshold,
            "feature_importance": self.feature_importance,
            "training_history": self.training_history[-10:],  # Last 10
            "model_params": self.model_params,
        }

        meta_path = path.replace(".json", "_metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to {path}")

    def load_model(self, path: str) -> None:
        """
        Load model from disk.

        Args:
            path: Model path
        """
        self.model = xgb.XGBClassifier(**self.model_params)
        self.model.load_model(path)

        # Load metadata if available
        meta_path = path.replace(".json", "_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                metadata = json.load(f)
                self.confidence_threshold = metadata.get("confidence_threshold", 0.6)
                self.feature_importance = metadata.get("feature_importance", {})
                self.training_history = metadata.get("training_history", [])

        logger.info(f"Model loaded from {path}")

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {
            "initialized": self.model is not None,
            "confidence_threshold": self.confidence_threshold,
            "min_samples": self.min_samples,
            "feature_count": (len(self.feature_importance) if self.feature_importance else 0),
            "training_runs": len(self.training_history),
            "best_val_accuracy": max(
                (h.get("val_accuracy", 0) for h in self.training_history), default=0
            ),
        }
