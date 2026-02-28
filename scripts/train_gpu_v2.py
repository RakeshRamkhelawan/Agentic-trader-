#!/usr/bin/env python3
"""
GPU Training v2 - Groter model + Meer features

Fixes:
- Groter model (2M parameters)
- Meer features (RSI, MACD, etc)
- Hogere learning rate
- Meer hidden layers
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_rsi(prices, window=14):
    delta = np.diff(prices, prepend=prices[0])
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=window).mean().values
    avg_loss = pd.Series(loss).rolling(window=window).mean().values
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))


def add_features(df):
    """Add technical indicators."""
    df = df.copy()

    # Returns
    df['returns'] = df['value'].pct_change().fillna(0)

    # RSI
    df['rsi'] = calculate_rsi(df['value'].values)

    # Moving averages
    df['sma10'] = df['value'].rolling(10).mean()
    df['sma30'] = df['value'].rolling(30).mean()
    df['dist_sma10'] = (df['value'] - df['sma10']) / df['sma10']
    df['dist_sma30'] = (df['value'] - df['sma30']) / df['sma30']

    # Volatility
    df['volatility'] = df['returns'].rolling(10).std()

    # Price momentum
    df['momentum'] = df['value'].pct_change(5)

    return df.fillna(0)


class LargeTransformer(nn.Module):
    """Groter transformer model."""

    def __init__(self, input_size: int):
        super().__init__()

        d_model = 256

        self.input_proj = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, d_model)
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=8,
            dim_feedforward=1024,
            dropout=0.2,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=4)

        self.fc = nn.Sequential(
            nn.Linear(d_model, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        x = self.input_proj(x)
        x = self.encoder(x)
        x = x.mean(dim=1)
        return self.fc(x)


def load_data():
    """Load data with features."""
    logger.info("Loading backtest files...")

    json_files = list(Path("backtest_results").glob("elemental_backtest_*.json"))
    logger.info(f"Found {len(json_files)} files")

    all_seqs = []
    all_labels = []

    for i, json_file in enumerate(json_files, 1):
        if i % 2 == 0:
            logger.info(f"  [{i}/{len(json_files)}] {json_file.name}")

        with open(json_file) as f:
            data = json.load(f)

        equity = data.get("equity_curve", [])
        if len(equity) < 60:
            continue

        df = pd.DataFrame(equity)
        df = add_features(df)

        # Feature columns
        feature_cols = ['returns', 'drawdown', 'prana', 'rsi', 'dist_sma10', 'dist_sma30', 'volatility', 'momentum']
        features = df[feature_cols].values

        for j in range(len(features) - 55):
            seq = features[j:j+50]
            label = df["returns"].iloc[j+50:j+55].sum()
            all_seqs.append(seq)
            all_labels.append(label)

    logger.info(f"Total: {len(all_seqs)} sequences")
    return np.array(all_seqs), np.array(all_labels)


def main():
    logger.info("=" * 60)
    logger.info("CHITTA GPU TRAINING v2")
    logger.info("=" * 60)

    if not torch.cuda.is_available():
        logger.error("CUDA not available!")
        return

    device = "cuda"
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")

    # Load data
    sequences, labels = load_data()

    if len(sequences) == 0:
        logger.error("No data loaded!")
        return

    X = torch.FloatTensor(sequences).to(device)
    y = torch.FloatTensor(labels).to(device)
    dataset = torch.utils.data.TensorDataset(X, y)

    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=256)

    logger.info(f"Dataset: {len(dataset)} samples")
    logger.info(f"Train: {train_size}, Val: {val_size}")
    logger.info(f"Features: {sequences.shape[2]}")

    # Model
    input_size = sequences.shape[2]
    model = LargeTransformer(input_size).to(device)

    n_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model: {n_params:,} parameters (~2M)")

    # Training
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=0.01, epochs=30, steps_per_epoch=len(train_loader)
    )

    best_val_loss = float('inf')
    patience = 0
    history = []

    logger.info("\nStarting training...")

    for epoch in range(30):
        start = time.time()

        # Train
        model.train()
        train_loss = 0
        for seqs, labs in train_loader:
            optimizer.zero_grad()
            preds = model(seqs).squeeze()
            loss = criterion(preds, labs)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validate
        model.eval()
        val_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for seqs, labs in val_loader:
                preds = model(seqs).squeeze()
                loss = criterion(preds, labs)
                val_loss += loss.item()

                pred_sign = torch.sign(preds)
                true_sign = torch.sign(labs)
                correct += (pred_sign == true_sign).sum().item()
                total += len(labs)

        val_loss /= len(val_loader)
        val_acc = correct / total

        epoch_time = time.time() - start

        logger.info(
            f"Epoch {epoch+1:2d}/30: "
            f"Train={train_loss:.6f}, Val={val_loss:.6f}, Acc={val_acc:.2%}, "
            f"LR={scheduler.get_last_lr()[0]:.6f}, Time={epoch_time:.1f}s"
        )

        history.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'val_acc': val_acc
        })

        # Save best
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience = 0
            torch.save(model.state_dict(), "models/production/chitta_gpu_v2.pt")
            with open("models/production/history_gpu_v2.json", 'w') as f:
                json.dump(history, f)
        else:
            patience += 1
            if patience > 10:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

    logger.info(f"\nDone! Best val loss: {best_val_loss:.6f}")


if __name__ == "__main__":
    main()
