#!/usr/bin/env python3
"""
Robust Training - Werkt zelfs met errors
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
import time
import traceback
from typing import List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TinyTransformer(nn.Module):
    """Extra klein model - 25K params."""

    def __init__(self, input_size: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size * 50, 64),  # Flatten sequence
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        # x: [batch, seq, features] -> [batch, seq*features]
        x = x.view(x.size(0), -1)
        return self.net(x)


def load_data_simple():
    """Simplistic data loading - geen multiprocessing."""
    logger.info("Loading backtest data...")

    json_files = list(Path("backtest_results").glob("elemental_backtest_*.json"))[:5]  # Alleen 5 files

    sequences = []
    labels = []

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)

            equity = data.get("equity_curve", [])
            if len(equity) < 60:
                continue

            df = pd.DataFrame(equity)
            df["returns"] = df["value"].pct_change().fillna(0)

            features = df[["returns", "drawdown", "prana"]].fillna(0).values

            for i in range(len(features) - 55):
                seq = features[i:i+50]
                label = df["returns"].iloc[i+50:i+55].sum()
                sequences.append(seq)
                labels.append(label)

        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")
            continue

    logger.info(f"Loaded {len(sequences)} sequences")
    return sequences, labels


def main():
    logger.info("=" * 60)
    logger.info("ROBUST CHITTA TRAINING")
    logger.info("=" * 60)

    try:
        # Load data
        sequences, labels = load_data_simple()

        if len(sequences) == 0:
            logger.error("No data loaded!")
            return

        # Create dataset
        X = torch.FloatTensor(np.array(sequences))
        y = torch.FloatTensor(labels)

        dataset = torch.utils.data.TensorDataset(X, y)

        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_ds, val_ds = random_split(dataset, [train_size, val_size])

        # Kleine batch size voor stabiliteit
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=32)

        logger.info(f"Dataset: {len(dataset)} samples")
        logger.info(f"Train: {train_size}, Val: {val_size}")

        # Model
        device = "cpu"
        model = TinyTransformer(input_size=3)
        model = model.to(device)

        n_params = sum(p.numel() for p in model.parameters())
        logger.info(f"Model: {n_params:,} parameters")

        # Training
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        best_val_loss = float('inf')
        history = []

        logger.info("Starting training...")

        for epoch in range(30):
            try:
                # Train
                model.train()
                train_loss = 0
                for seqs, labs in train_loader:
                    seqs, labs = seqs.to(device), labs.to(device)

                    optimizer.zero_grad()
                    preds = model(seqs).squeeze()
                    loss = criterion(preds, labs)
                    loss.backward()
                    optimizer.step()

                    train_loss += loss.item()

                train_loss /= len(train_loader)

                # Validate
                model.eval()
                val_loss = 0
                correct = 0
                total = 0

                with torch.no_grad():
                    for seqs, labs in val_loader:
                        seqs, labs = seqs.to(device), labs.to(device)
                        preds = model(seqs).squeeze()
                        loss = criterion(preds, labs)
                        val_loss += loss.item()

                        pred_sign = torch.sign(preds)
                        true_sign = torch.sign(labs)
                        correct += (pred_sign == true_sign).sum().item()
                        total += len(labs)

                val_loss /= len(val_loader)
                val_acc = correct / total

                logger.info(f"Epoch {epoch+1:2d}: Train={train_loss:.6f}, Val={val_loss:.6f}, Acc={val_acc:.2%}")

                history.append({
                    'epoch': epoch + 1,
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                    'val_acc': val_acc
                })

                # Save best
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    torch.save(model.state_dict(), "models/production/chitta_robust.pt")

                    # Save history na elke verbetering
                    with open("models/production/history_robust.json", 'w') as f:
                        json.dump(history, f)

            except Exception as e:
                logger.error(f"Error in epoch {epoch+1}: {e}")
                traceback.print_exc()
                continue

        logger.info(f"\nTraining completed! Best val loss: {best_val_loss:.6f}")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
