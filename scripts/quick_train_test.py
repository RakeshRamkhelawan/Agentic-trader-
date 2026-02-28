#!/usr/bin/env python3
"""
Quick training test - gebruikt maar 2 backtest files voor snelle test.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.core.ml.backtest_dataset_builder_v2 import BacktestDatasetBuilderV2
from backend.core.ml.lstm_model import ChittaLSTM, ModelTrainer
from torch.utils.data import DataLoader, random_split
import torch

logger.info("Quick training test with subset of data...")

# Alleen 2 files gebruiken voor snelheid
builder = BacktestDatasetBuilderV2()

# Manually load only 2 files
import json
import pandas as pd
import numpy as np
from pathlib import Path

backtest_files = list(Path("backtest_results").glob("elemental_backtest_*.json"))[:2]
logger.info(f"Using {len(backtest_files)} files for quick test")

all_sequences = []
all_labels = []

for json_file in backtest_files:
    with open(json_file) as f:
        data = json.load(f)

    equity = data.get("equity_curve", [])
    if not equity:
        continue

    df = pd.DataFrame(equity)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    df["returns"] = df["value"].pct_change().fillna(0)

    # Simple features
    features = df[["returns", "drawdown", "prana"]].fillna(0).values

    seq_len = 20
    pred_horizon = 3

    for i in range(len(features) - seq_len - pred_horizon):
        seq = features[i:i + seq_len]
        label = df["returns"].iloc[i + seq_len:i + seq_len + pred_horizon].sum()
        all_sequences.append(seq)
        all_labels.append(label)

logger.info(f"Generated {len(all_sequences)} sequences")

if len(all_sequences) < 100:
    logger.error("Not enough data!")
    sys.exit(1)

# Create dataset
from backend.core.ml.backtest_dataset_builder_v2 import LSTMDataset
dataset = LSTMDataset(all_sequences, all_labels)

# Split
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_ds, val_ds = random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=16)

# Model
sample_seq, _ = dataset[0]
input_size = sample_seq.shape[1]
model = ChittaLSTM(input_size=input_size, hidden_size=64, num_layers=1, dropout=0.1)

# Train
trainer = ModelTrainer(model, learning_rate=0.01)

logger.info("Training for 5 epochs...")
for epoch in range(5):
    train_loss = trainer.train_epoch(train_loader)
    val_loss, val_acc = trainer.validate(val_loader)
    logger.info(f"Epoch {epoch+1}: Train Loss={train_loss:.6f}, Val Loss={val_loss:.6f}, Acc={val_acc:.2%}")

# Save model
Path("models").mkdir(exist_ok=True)
trainer.save_model("models/chitta_quick_test.pt")
logger.info("Model saved to models/chitta_quick_test.pt")
logger.info("Quick test completed successfully!")
