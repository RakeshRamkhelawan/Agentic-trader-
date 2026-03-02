"""
Train ML model on ALL 15 batches combined.

This creates a robust model that learns from diverse market conditions.
"""

import json
import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset, DataLoader
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    def __len__(self):
        return len(self.X)
    def __getitem__(self, i):
        return self.X[i], self.y[i]


class DirectionPredictor(nn.Module):
    """Neural network for price direction prediction."""
    def __init__(self, input_dim=8):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)


def load_all_batches():
    """Load and combine all batch datasets."""
    files = sorted(Path('backtest_results').glob('ml_batch_*.json'))

    all_features = []

    for file in files:
        logger.info(f"Loading {file.name}...")
        with open(file) as f:
            data = json.load(f)

        # Extract features and create target
        features = data['ml_features']

        for i in range(len(features) - 1):
            f = features[i]
            next_f = features[i + 1]

            # Current features
            x = [
                f['rsi'] / 100.0,  # Normalize RSI to 0-1
                np.tanh(f['macd'] / 10),  # Normalize MACD
                f['bb_position'],  # Already 0-1
                np.tanh(f['mom_1d'] * 10),  # Normalize momentum
                f['volume_ratio'] / 3,  # Normalize volume
                np.tanh(f['atr_pct'] * 10),  # Normalize ATR
                f['trend'] / 2.0 + 0.5,  # Convert -1/1 to 0/1
                f['confidence']  # Already 0-1
            ]

            # Target: 1 if price goes up, 0 if down
            price_change = (next_f['price'] - f['price']) / f['price']
            y = 1.0 if price_change > 0 else 0.0

            all_features.append((x, y))

    logger.info(f"Total samples loaded: {len(all_features)}")
    return all_features


def train_model():
    """Train model on all batches."""

    logger.info("=" * 60)
    logger.info("TRAINING ON ALL 15 BATCHES")
    logger.info("=" * 60)

    # Load data
    data = load_all_batches()

    X = np.array([d[0] for d in data])
    y = np.array([d[1] for d in data])

    logger.info(f"Dataset shape: X={X.shape}, y={y.shape}")
    logger.info(f"Class distribution: {np.mean(y)*100:.1f}% positive")

    # Check feature variance
    logger.info("\nFeature variance:")
    feature_names = ['RSI', 'MACD', 'BB_POS', 'MOM', 'VOL_RATIO', 'ATR', 'TREND', 'CONFIDENCE']
    for i, name in enumerate(feature_names):
        logger.info(f"  {name}: var={np.var(X[:, i]):.4f}, std={np.std(X[:, i]):.4f}")

    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Save scaler
    joblib.dump(scaler, 'backtest_results/unified_scaler.joblib')

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")

    # Datasets
    train_dataset = TradingDataset(X_train, y_train)
    test_dataset = TradingDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=128)

    # Model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DirectionPredictor(input_dim=8).to(device)

    criterion = nn.BCELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=5, verbose=True
    )

    logger.info(f"\nTraining on {device}")
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")

    # Baseline
    baseline_acc = max(np.mean(y_test), 1 - np.mean(y_test))
    logger.info(f"Baseline accuracy: {baseline_acc*100:.1f}%")

    # Training loop
    best_acc = 0
    best_epoch = 0
    patience = 15
    patience_counter = 0

    for epoch in range(200):
        # Train
        model.train()
        train_loss = 0
        for Xb, yb in train_loader:
            Xb, yb = Xb.to(device), yb.to(device)

            optimizer.zero_grad()
            pred = model(Xb).squeeze()
            loss = criterion(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()

        # Evaluate
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for Xb, yb in test_loader:
                Xb, yb = Xb.to(device), yb.to(device)
                pred = model(Xb).squeeze()
                pred_labels = (pred > 0.5).float()
                correct += (pred_labels == yb).sum().item()
                total += len(yb)

        acc = correct / total
        avg_loss = train_loss / len(train_loader)

        # Update scheduler
        scheduler.step(acc)

        # Save best
        if acc > best_acc:
            best_acc = acc
            best_epoch = epoch
            torch.save(model.state_dict(), 'backtest_results/unified_direction_model.pt')
            patience_counter = 0
        else:
            patience_counter += 1

        # Logging
        if epoch % 20 == 0 or epoch == 199:
            logger.info(f"Epoch {epoch+1:3d}: Loss={avg_loss:.4f}, Acc={acc*100:.1f}%, Best={best_acc*100:.1f}% @ {best_epoch+1}")

        # Early stopping
        if patience_counter >= patience:
            logger.info(f"Early stopping at epoch {epoch+1}")
            break

    # Final results
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Best accuracy: {best_acc*100:.2f}%")
    logger.info(f"Baseline: {baseline_acc*100:.2f}%")
    logger.info(f"Improvement: +{(best_acc - baseline_acc)*100:.2f} percentage points")
    logger.info(f"Best epoch: {best_epoch+1}")

    if best_acc > baseline_acc + 0.02:
        logger.info("✅ MODEL LEARNED PATTERNS!")
    else:
        logger.info("⚠️ Model at baseline level")

    logger.info(f"\nModel saved: backtest_results/unified_direction_model.pt")
    logger.info(f"Scaler saved: backtest_results/unified_scaler.joblib")

    return best_acc


if __name__ == "__main__":
    train_model()
