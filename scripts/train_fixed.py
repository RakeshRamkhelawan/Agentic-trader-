#!/usr/bin/env python3
"""
Fixed Training Script

Verbeteringen:
- Laadt ALLE backtest files (sequentiëel, geen parallel issues)
- Kleiner model (512K params ipv 2.1M)
- Betere regularization (dropout 0.3)
- Lagere learning rate (0.0005)
- Early stopping
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
import logging
import time
from typing import List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleTransformer(nn.Module):
    """Kleinere transformer (512K params ipv 2.1M)."""

    def __init__(self, input_size: int, d_model: int = 64, num_layers: int = 2):
        super().__init__()

        self.input_proj = nn.Linear(input_size, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=4,
            dim_feedforward=128,
            dropout=0.3,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.fc = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        x = self.input_proj(x)
        x = self.encoder(x)
        x = x.mean(dim=1)
        return self.fc(x)


class ChittaDataset(Dataset):
    """Simple dataset."""

    def __init__(self, sequences: List, labels: List):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


def load_backtest_data(backtest_dir: str = "backtest_results"):
    """Laadt ALLE backtest files sequentieel."""
    import json
    import pandas as pd
    import numpy as np
    from pathlib import Path

    json_files = list(Path(backtest_dir).glob("elemental_backtest_*.json"))
    logger.info(f"Loading {len(json_files)} files...")

    all_sequences = []
    all_labels = []

    for i, json_file in enumerate(json_files, 1):
        logger.info(f"  [{i}/{len(json_files)}] {json_file.name}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load equity curve
            equity = data.get("equity_curve", [])
            if not equity or len(equity) < 60:
                continue

            df = pd.DataFrame(equity)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            df["returns"] = df["value"].pct_change().fillna(0)

            # Features
            features = []
            for col in ["returns", "drawdown", "prana"]:
                if col in df.columns:
                    features.append(df[col].values)
                else:
                    features.append(np.zeros(len(df)))

            features = np.column_stack(features)

            # Generate sequences
            seq_len = 50
            pred_horizon = 5

            for j in range(len(features) - seq_len - pred_horizon):
                seq = features[j:j + seq_len]
                label = df["returns"].iloc[j + seq_len:j + seq_len + pred_horizon].sum()

                all_sequences.append(seq)
                all_labels.append(label)

        except Exception as e:
            logger.warning(f"    Error: {e}")
            continue

    logger.info(f"Total sequences: {len(all_sequences)}")
    return all_sequences, all_labels


def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0

    for seqs, labels in loader:
        seqs, labels = seqs.to(device), labels.to(device)

        optimizer.zero_grad()
        preds = model(seqs).squeeze()
        loss = criterion(preds, labels)
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()
        total_loss += loss.item()

    return total_loss / len(loader)


def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for seqs, labels in loader:
            seqs, labels = seqs.to(device), labels.to(device)
            preds = model(seqs).squeeze()
            loss = criterion(preds, labels)
            total_loss += loss.item()

            # Direction accuracy
            pred_sign = torch.sign(preds)
            true_sign = torch.sign(labels)
            correct += (pred_sign == true_sign).sum().item()
            total += len(labels)

    return total_loss / len(loader), correct / total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.0005)
    parser.add_argument("--patience", type=int, default=10)
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("FIXED CHITTA TRAINING")
    logger.info("=" * 60)
    logger.info(f"Config: epochs={args.epochs}, batch={args.batch_size}, lr={args.lr}")

    # Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")

    # Load data
    logger.info("\nLoading data...")
    sequences, labels = load_backtest_data()

    if len(sequences) == 0:
        logger.error("No data loaded!")
        return

    # Create dataset
    dataset = ChittaDataset(sequences, labels)
    input_size = sequences[0].shape[1]

    logger.info(f"Dataset: {len(dataset)} samples, {input_size} features")

    # Split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    logger.info(f"Train: {train_size}, Val: {val_size}")

    # Model
    logger.info("\nCreating model...")
    model = SimpleTransformer(input_size=input_size, d_model=64, num_layers=2)
    model = model.to(device)

    n_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Parameters: {n_params:,} (~512K)")

    # Training
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    # Training loop
    logger.info("\nStarting training...")
    best_val_loss = float('inf')
    patience_counter = 0
    history = []

    for epoch in range(args.epochs):
        start = time.time()

        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step(val_loss)

        epoch_time = time.time() - start

        logger.info(
            f"Epoch {epoch+1:3d}/{args.epochs}: "
            f"Train={train_loss:.6f}, Val={val_loss:.6f}, Acc={val_acc:.2%}, "
            f"LR={optimizer.param_groups[0]['lr']:.6f}, Time={epoch_time:.1f}s"
        )

        history.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'val_acc': val_acc
        })

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best
            torch.save(model.state_dict(), "models/production/chitta_fixed_best.pt")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

    # Save
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Best val loss: {best_val_loss:.6f}")

    # Save history
    with open("models/production/history_fixed.json", 'w') as f:
        json.dump(history, f, indent=2)

    logger.info("Model saved: models/production/chitta_fixed_best.pt")


if __name__ == "__main__":
    main()
