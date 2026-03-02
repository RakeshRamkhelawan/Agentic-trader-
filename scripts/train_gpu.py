#!/usr/bin/env python3
"""
GPU Training voor Chitta

Gebruikt je RTX 4060 8GB voor ~20-30x snellere training
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


class GPUTransformer(nn.Module):
    """Transformer optimized for GPU."""

    def __init__(self, input_size: int, d_model: int = 128, num_layers: int = 3):
        super().__init__()

        self.input_proj = nn.Linear(input_size, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=8,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.fc = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )

    def forward(self, x):
        x = self.input_proj(x)
        x = self.encoder(x)
        x = x.mean(dim=1)  # Global average pooling
        return self.fc(x)


def load_data():
    """Load all backtest data."""
    logger.info("Loading backtest files...")

    json_files = list(Path("backtest_results").glob("elemental_backtest_*.json"))
    logger.info(f"Found {len(json_files)} files")

    all_seqs = []
    all_labels = []

    for i, json_file in enumerate(json_files, 1):
        logger.info(f"  [{i}/{len(json_files)}] {json_file.name}")

        with open(json_file) as f:
            data = json.load(f)

        equity = data.get("equity_curve", [])
        if len(equity) < 60:
            continue

        df = pd.DataFrame(equity)
        df["returns"] = df["value"].pct_change().fillna(0)

        features = df[["returns", "drawdown", "prana"]].fillna(0).values

        for j in range(len(features) - 55):
            seq = features[j:j+50]
            label = df["returns"].iloc[j+50:j+55].sum()
            all_seqs.append(seq)
            all_labels.append(label)

    logger.info(f"Total: {len(all_seqs)} sequences")
    return np.array(all_seqs), np.array(all_labels)


def main():
    logger.info("=" * 60)
    logger.info("CHITTA GPU TRAINING")
    logger.info("=" * 60)

    # Device
    if not torch.cuda.is_available():
        logger.error("CUDA NOT AVAILABLE! Install PyTorch with CUDA support.")
        logger.error("  pip install torch --index-url https://download.pytorch.org/whl/cu124")
        return

    device = "cuda"
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3

    logger.info(f"GPU: {gpu_name}")
    logger.info(f"VRAM: {gpu_memory:.1f} GB")

    # Load data
    sequences, labels = load_data()

    if len(sequences) == 0:
        logger.error("No data loaded!")
        return

    # Create dataset and move to GPU
    X = torch.FloatTensor(sequences).to(device)
    y = torch.FloatTensor(labels).to(device)

    dataset = torch.utils.data.TensorDataset(X, y)

    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    # Larger batch size for GPU
    train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=256)

    logger.info(f"Dataset: {len(dataset)} samples")
    logger.info(f"Train: {train_size}, Val: {val_size}")
    logger.info(f"Batch size: 256 (GPU optimized)")

    # Model
    input_size = sequences.shape[2]
    model = GPUTransformer(input_size).to(device)

    n_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model: {n_params:,} parameters")

    # Training
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3)

    best_val_loss = float('inf')
    history = []

    logger.info("\nStarting training...")
    torch.cuda.synchronize()  # Wait for GPU init

    for epoch in range(50):
        start = time.time()

        # Train
        model.train()
        train_loss = 0
        for seqs, labs in train_loader:
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
                preds = model(seqs).squeeze()
                loss = criterion(preds, labs)
                val_loss += loss.item()

                pred_sign = torch.sign(preds)
                true_sign = torch.sign(labs)
                correct += (pred_sign == true_sign).sum().item()
                total += len(labs)

        val_loss /= len(val_loader)
        val_acc = correct / total

        scheduler.step(val_loss)

        epoch_time = time.time() - start

        logger.info(
            f"Epoch {epoch+1:2d}/50: "
            f"Train={train_loss:.6f}, Val={val_loss:.6f}, Acc={val_acc:.2%}, "
            f"Time={epoch_time:.1f}s"
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
            torch.save(model.state_dict(), "models/production/chitta_gpu.pt")

            with open("models/production/history_gpu.json", 'w') as f:
                json.dump(history, f)

    logger.info(f"\nDone! Best val loss: {best_val_loss:.6f}")
    logger.info(f"Model saved: models/production/chitta_gpu.pt")


if __name__ == "__main__":
    main()
