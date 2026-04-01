"""
ML Training for Triad System

Trains models on episodic memory data to:
1. Predict decision outcomes
2. Optimize council weights
3. Improve coherence scoring
"""

import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset

from backend.core.memory.episodic_memory import get_episodic_memory

logger = logging.getLogger(__name__)


class TriadDataset(Dataset):
    """Dataset for Triad ML training."""

    def __init__(self, features: np.ndarray, labels: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.labels = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class OutcomePredictor(nn.Module):
    """
    Neural network to predict trade outcomes.

    Input: Market context + council inputs
    Output: Probability of success
    """

    def __init__(self, input_dim: int = 12):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(x)


class TriadMLTrainer:
    """
    ML Trainer for Triad system.

    Trains on episodic memory to:
    - Predict which decisions will succeed
    - Learn optimal council weights
    - Identify patterns in successful trades
    """

    def __init__(self, model_path: str = "models/triad"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)

        self.memory = get_episodic_memory()
        self.model = None

        logger.info("TriadMLTrainer initialized")

    def prepare_training_data(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from episodic memory.

        Returns:
            (features, labels) where labels are 1=success, 0=failure
        """
        # Get completed episodes with outcomes
        episodes = [ep for ep in self.memory.episodes if ep.outcome is not None]

        if len(episodes) < 10:
            logger.warning(f"Insufficient data: {len(episodes)} episodes (need 10+)")
            return None, None

        features = []
        labels = []

        for ep in episodes:
            # Feature vector
            feat = [
                ep.volatility,
                ep.fear_greed_index / 100,  # Normalize
                ep.confidence,
                ep.coherence,
                ep.karma_score,
                ep.guna_vector.get("sattva", 0.33),
                ep.guna_vector.get("rajas", 0.33),
                ep.guna_vector.get("tamas", 0.33),
                1.0 if ep.action == "buy" else 0.0,
                1.0 if ep.trend == "up" else 0.0 if ep.trend == "down" else 0.5,
                (
                    1.0
                    if ep.volume_profile == "high"
                    else 0.5 if ep.volume_profile == "normal" else 0.0
                ),
                1.0 if ep.execution_quality == "excellent" else 0.5,
            ]

            # Label: 1 = success, 0 = failure
            label = 1.0 if ep.outcome == "success" else 0.0

            features.append(feat)
            labels.append(label)

        return np.array(features), np.array(labels)

    def train(self, epochs: int = 50, batch_size: int = 8) -> dict:
        """
        Train outcome prediction model.

        Returns:
            Training metrics
        """
        # Prepare data
        X, y = self.prepare_training_data()
        if X is None:
            return {
                "status": "insufficient_data",
                "episodes": len(self.memory.episodes),
            }

        logger.info(f"Training on {len(X)} episodes")

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y if len(set(y)) > 1 else None,
        )

        # Datasets
        train_dataset = TriadDataset(X_train, y_train)
        test_dataset = TriadDataset(X_test, y_test)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size)

        # Model
        self.model = OutcomePredictor(input_dim=X.shape[1])
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

        # Training
        best_acc = 0
        history = []

        for epoch in range(epochs):
            # Train
            self.model.train()
            train_loss = 0
            for Xb, yb in train_loader:
                optimizer.zero_grad()
                pred = self.model(Xb).squeeze()
                loss = criterion(pred, yb)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            # Evaluate
            self.model.eval()
            correct = 0
            total = 0
            with torch.no_grad():
                for Xb, yb in test_loader:
                    pred = self.model(Xb).squeeze()
                    pred_labels = (pred > 0.5).float()
                    correct += (pred_labels == yb).sum().item()
                    total += len(yb)

            acc = correct / total if total > 0 else 0
            avg_loss = train_loss / len(train_loader)

            if acc > best_acc:
                best_acc = acc
                # Save best model
                torch.save(
                    self.model.state_dict(),
                    self.model_path / "outcome_predictor_best.pt",
                )

            history.append({"epoch": epoch + 1, "loss": avg_loss, "acc": acc})

            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1}: Loss={avg_loss:.4f}, Acc={acc:.2%}, Best={best_acc:.2%}"
                )

        # Save final
        torch.save(self.model.state_dict(), self.model_path / "outcome_predictor_final.pt")

        return {
            "status": "success",
            "best_accuracy": best_acc,
            "final_accuracy": acc,
            "training_episodes": len(X),
            "history": history,
        }

    def predict_outcome(
        self,
        market_context: dict,
        council_views: list[dict],
        confidence: float,
        coherence: float,
    ) -> float:
        """
        Predict probability of success for a decision.

        Returns:
            Probability 0-1
        """
        if self.model is None:
            # Try to load
            model_file = self.model_path / "outcome_predictor_best.pt"
            if model_file.exists():
                self.model = OutcomePredictor()
                self.model.load_state_dict(torch.load(model_file))
                self.model.eval()
            else:
                logger.warning("No trained model found")
                return 0.5  # Neutral

        # Build feature vector
        guna = council_views[0].get("guna_vector", {}) if council_views else {}

        feat = [
            market_context.get("volatility_1m", 0.02),
            (council_views[1].get("fear_greed_index", 50) / 100 if len(council_views) > 1 else 0.5),
            confidence,
            coherence,
            0.5,  # karma score (unknown for new trade)
            guna.get("sattva", 0.33),
            guna.get("rajas", 0.33),
            guna.get("tamas", 0.33),
            0.5,  # action (neutral)
            0.5,  # trend
            0.5,  # volume
            0.5,  # execution
        ]

        x = torch.FloatTensor([feat])

        with torch.no_grad():
            prob = self.model(x).item()

        return prob

    def analyze_patterns(self) -> dict:
        """
        Analyze patterns in successful vs failed trades.

        Returns:
            Insights dict
        """
        episodes = [ep for ep in self.memory.episodes if ep.outcome is not None]

        if len(episodes) < 5:
            return {"status": "insufficient_data"}

        successful = [ep for ep in episodes if ep.outcome == "success"]
        failed = [ep for ep in episodes if ep.outcome == "failure"]

        insights = {
            "status": "success",
            "total_analyzed": len(episodes),
            "success_count": len(successful),
            "failure_count": len(failed),
            "win_rate": len(successful) / len(episodes) if episodes else 0,
        }

        # Compare successful vs failed
        if successful and failed:
            insights["avg_confidence_success"] = sum(ep.confidence for ep in successful) / len(
                successful
            )
            insights["avg_confidence_failure"] = sum(ep.confidence for ep in failed) / len(failed)

            insights["avg_coherence_success"] = sum(ep.coherence for ep in successful) / len(
                successful
            )
            insights["avg_coherence_failure"] = sum(ep.coherence for ep in failed) / len(failed)

            # Best action
            action_success = {}
            for ep in episodes:
                if ep.outcome == "success":
                    action_success[ep.action] = action_success.get(ep.action, 0) + 1

            if action_success:
                insights["best_action"] = max(action_success, key=action_success.get)

        return insights


# Singleton
_ml_trainer = None


def get_ml_trainer():
    """Get singleton instance."""
    global _ml_trainer
    if _ml_trainer is None:
        _ml_trainer = TriadMLTrainer()
    return _ml_trainer


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("TRIAD ML TRAINER - TEST")
    print("=" * 60)

    trainer = get_ml_trainer()

    # Check data
    X, y = trainer.prepare_training_data()
    if X is not None:
        print(f"\nTraining data: {len(X)} episodes")
        print(f"Success rate: {y.mean():.1%}")

        # Train
        print("\nTraining model...")
        results = trainer.train(epochs=20)

        print("\nResults:")
        print(f"  Best accuracy: {results['best_accuracy']:.2%}")
        print(f"  Final accuracy: {results['final_accuracy']:.2%}")

        # Analyze
        patterns = trainer.analyze_patterns()
        print("\nPatterns:")
        print(f"  Win rate: {patterns.get('win_rate', 0):.1%}")
        if "avg_confidence_success" in patterns:
            print(f"  Avg confidence (success): {patterns['avg_confidence_success']:.2f}")
            print(f"  Avg confidence (failure): {patterns['avg_confidence_failure']:.2f}")
    else:
        print("\nInsufficient training data")
        print("Run some trades first to generate episodes with outcomes")
