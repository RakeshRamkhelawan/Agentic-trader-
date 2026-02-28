"""
Fast Dataset Builder - Geoptimaliseerd voor snelle training.

Features:
- GPU acceleration support
- Parallel data loading
- Memory-efficient processing
- Caching van verwerkte sequences
"""

import json
import logging
import pickle
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path(".cache/chitta_datasets")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def process_single_file(args):
    """
    Process één backtest file (voor parallel processing).
    """
    json_file, sequence_length, prediction_horizon = args

    try:
        with open(json_file, encoding='utf-8') as f:
            data = json.load(f)

        equity = data.get("equity_curve", [])
        if not equity or len(equity) < sequence_length + prediction_horizon + 10:
            return [], []

        df = pd.DataFrame(equity)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # Returns
        df["returns"] = df["value"].pct_change().fillna(0)

        # Features
        features_list = []
        for col in ["returns", "drawdown", "prana", "cash"]:
            if col in df.columns:
                features_list.append(df[col].values)
            else:
                features_list.append(np.zeros(len(df)))

        # Stack features
        features = np.column_stack(features_list)

        # Generate sequences
        sequences = []
        labels = []

        n = len(features)
        for i in range(n - sequence_length - prediction_horizon):
            if i % 10 == 0:  # Sample elke 10e sequence voor snelheid
                seq = features[i:i + sequence_length]
                label = df["returns"].iloc[i + sequence_length:i + sequence_length + prediction_horizon].sum()

                sequences.append(seq)
                labels.append(label)

        return sequences, labels

    except Exception as e:
        logger.error(f"Error processing {json_file}: {e}")
        return [], []


class FastBacktestDatasetBuilder:
    """
    Geoptimaliseerde dataset builder met caching en parallel processing.
    """

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache

    def build_dataset(
        self,
        backtest_dir: str = "backtest_results",
        sequence_length: int = 50,
        prediction_horizon: int = 5,
        max_files: int | None = None,
        n_workers: int = 4
    ) -> "FastLSTMDataset":
        """
        Bouw dataset met parallel processing.
        """
        backtest_path = Path(backtest_dir)
        json_files = list(backtest_path.glob("elemental_backtest_*.json"))

        if max_files:
            json_files = json_files[:max_files]

        logger.info(f"Processing {len(json_files)} files with {n_workers} workers...")

        # Check cache
        cache_key = f"dataset_{len(json_files)}_{sequence_length}_{prediction_horizon}.pkl"
        cache_path = CACHE_DIR / cache_key

        if self.use_cache and cache_path.exists():
            logger.info(f"Loading from cache: {cache_path}")
            with open(cache_path, 'rb') as f:
                sequences, labels = pickle.load(f)
            return FastLSTMDataset(sequences, labels)

        # Parallel processing
        args_list = [(f, sequence_length, prediction_horizon) for f in json_files]

        all_sequences = []
        all_labels = []

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            results = list(executor.map(process_single_file, args_list))

            for seqs, labs in results:
                all_sequences.extend(seqs)
                all_labels.extend(labs)

        logger.info(f"Dataset built: {len(all_sequences)} sequences")

        # Cache result
        if self.use_cache:
            with open(cache_path, 'wb') as f:
                pickle.dump((all_sequences, all_labels), f)
            logger.info(f"Cached to: {cache_path}")

        return FastLSTMDataset(all_sequences, all_labels)


class FastLSTMDataset(Dataset):
    """Memory-efficient dataset dat op GPU kan worden geladen."""

    def __init__(self, sequences: list[np.ndarray], labels: list[float], device: str = "cpu"):
        # Convert naar tensors één keer
        self.sequences = torch.FloatTensor(np.array(sequences))
        self.labels = torch.FloatTensor(labels)

        # Move to GPU indien beschikbaar
        if device == "cuda" and torch.cuda.is_available():
            self.sequences = self.sequences.cuda()
            self.labels = self.labels.cuda()
            logger.info(f"Dataset moved to GPU ({self.sequences.device})")

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

    def to_device(self, device: str):
        """Verplaats dataset naar ander device."""
        self.sequences = self.sequences.to(device)
        self.labels = self.labels.to(device)
