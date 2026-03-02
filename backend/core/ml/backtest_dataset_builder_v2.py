"""
Backtest Dataset Builder v2 - Aangepast aan de werkelijke data structuur.

De backtest JSON heeft:
- equity_curve: [{timestamp, value, cash, drawdown, blocked, prana}]
- harmony_curve: [{timestamp, symbol, harmony, decision, action, planet}] (per symbol!)
- trades: [{timestamp, symbol, action, harmony_score, ...}]
- elemental_cycles: integer (count)
- agent_stats: {fire, water, air, earth, ether: {avg_confidence, ...}}
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


class BacktestDatasetBuilderV2:
    """
    Bouwt ML datasets uit bestaande backtest data.
    """

    def __init__(self):
        self.features = []
        self.labels = []

    def load_backtest_json(self, filepath: Path) -> dict:
        """Laad een backtest JSON file."""
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)

    def process_equity_curve(self, backtest_data: dict) -> pd.DataFrame:
        """
        Process equity curve naar features.

        Returns DataFrame met:
        - timestamp
        - value (portfolio value)
        - returns (percentage change)
        - drawdown
        - prana
        """
        equity = backtest_data.get("equity_curve", [])

        if not equity:
            return pd.DataFrame()

        df = pd.DataFrame(equity)

        # Parse timestamps
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

        # Bereken returns als niet aanwezig
        if "returns" not in df.columns and "value" in df.columns:
            df["returns"] = df["value"].pct_change().fillna(0)

        return df

    def aggregate_harmony_by_timestamp(self, backtest_data: dict) -> pd.DataFrame:
        """
        De harmony_curve heeft entries per symbol.
        We aggregeren naar 1 waarde per timestamp.

        Returns: DataFrame met timestamp, avg_harmony, decision_counts
        """
        harmony = backtest_data.get("harmony_curve", [])

        if not harmony:
            return pd.DataFrame()

        df = pd.DataFrame(harmony)

        if "timestamp" not in df.columns:
            return pd.DataFrame()

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Aggregeer per timestamp
        aggregated = df.groupby("timestamp").agg({
            "harmony": ["mean", "std", "min", "max"],
            "decision": lambda x: x.mode()[0] if len(x.mode()) > 0 else "HOLD",
            "action": lambda x: x.mode()[0] if len(x.mode()) > 0 else "HOLD",
            "symbol": "count"  # Aantal assets met data
        }).reset_index()

        # Flatten column names
        aggregated.columns = [
            "timestamp", "harmony_mean", "harmony_std", "harmony_min", "harmony_max",
            "dominant_decision", "dominant_action", "num_assets"
        ]

        return aggregated

    def extract_elemental_features(self, backtest_data: dict) -> dict:
        """
        Extract elemental confidence scores uit agent_stats.
        """
        agent_stats = backtest_data.get("agent_stats", {})

        features = {}
        for element in ["fire", "water", "air", "earth", "ether"]:
            if element in agent_stats:
                stats = agent_stats[element]
                features[f"{element}_confidence"] = stats.get("avg_confidence", 0.5)
                features[f"{element}_min_conf"] = stats.get("min_confidence", 0.0)
                features[f"{element}_max_conf"] = stats.get("max_confidence", 1.0)
            else:
                features[f"{element}_confidence"] = 0.5
                features[f"{element}_min_conf"] = 0.0
                features[f"{element}_max_conf"] = 1.0

        return features

    def extract_trade_features(self, backtest_data: dict) -> pd.DataFrame:
        """
        Extract trade informatie als features.
        """
        trades = backtest_data.get("trades", [])

        if not trades:
            return pd.DataFrame()

        df = pd.DataFrame(trades)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        return df

    def build_lstm_dataset(
        self,
        backtest_dir: str = "backtest_results",
        sequence_length: int = 50,
        prediction_horizon: int = 5,
        min_samples: int = 100
    ) -> "LSTMDataset":
        """
        Bouw LSTM dataset uit alle backtest files.

        Features per timestep:
        - returns (equity change)
        - drawdown
        - prana
        - harmony_mean
        - harmony_std
        - fire/water/air/earth/ether confidence
        - num_assets

        Label: cumulative return over prediction_horizon
        """
        all_sequences = []
        all_labels = []

        backtest_path = Path(backtest_dir)
        json_files = list(backtest_path.glob("elemental_backtest_*.json"))

        logger.info(f"Processing {len(json_files)} backtest files...")

        for json_file in json_files:
            try:
                data = self.load_backtest_json(json_file)

                # Extract data
                equity_df = self.process_equity_curve(data)
                harmony_df = self.aggregate_harmony_by_timestamp(data)
                elemental_features = self.extract_elemental_features(data)

                if equity_df.empty or len(equity_df) < sequence_length + prediction_horizon:
                    continue

                # Merge equity en harmony data
                if not harmony_df.empty:
                    combined = pd.merge(
                        equity_df,
                        harmony_df,
                        on="timestamp",
                        how="left"
                    )
                else:
                    combined = equity_df.copy()

                # Fill missing values
                combined = combined.fillna(method="ffill").fillna(0)

                # Bouw feature matrix
                feature_cols = [
                    "returns", "drawdown", "prana",
                    "harmony_mean", "harmony_std", "num_assets"
                ]

                # Voeg elemental features toe (constant per backtest)
                for key, value in elemental_features.items():
                    combined[key] = value
                    feature_cols.append(key)

                # Zorg dat alle kolommen bestaan
                for col in feature_cols:
                    if col not in combined.columns:
                        combined[col] = 0.0

                features = combined[feature_cols].values

                # Genereer sequences
                n_sequences = 0
                for i in range(len(features) - sequence_length - prediction_horizon):
                    seq = features[i:i + sequence_length]

                    # Label: cumulative return over prediction_horizon
                    future_returns = combined["returns"].iloc[
                        i + sequence_length:i + sequence_length + prediction_horizon
                    ].values

                    label = np.sum(future_returns)

                    all_sequences.append(seq)
                    all_labels.append(label)
                    n_sequences += 1

                logger.info(f"  {json_file.name}: {n_sequences} sequences")

            except Exception as e:
                logger.warning(f"Failed to process {json_file}: {e}")
                import traceback
                traceback.print_exc()
                continue

        if len(all_sequences) < min_samples:
            logger.warning(f"Only {len(all_sequences)} sequences generated, need {min_samples}")
        else:
            logger.info(f"Dataset built: {len(all_sequences)} total sequences")

        return LSTMDataset(all_sequences, all_labels)

    def build_classification_dataset(
        self,
        backtest_dir: str = "backtest_results",
        sequence_length: int = 20
    ) -> "ClassificationDataset":
        """
        Classificatie dataset: voorspel of de volgende actie BUY, SELL, of HOLD moet zijn.

        Gebruikt trades data voor labels.
        """
        all_sequences = []
        all_labels = []

        backtest_path = Path(backtest_dir)
        json_files = list(backtest_path.glob("elemental_backtest_*.json"))

        for json_file in json_files:
            try:
                data = self.load_backtest_json(json_file)

                equity_df = self.process_equity_curve(data)
                trades_df = self.extract_trade_features(data)

                if equity_df.empty or trades_df.empty:
                    continue

                # Maak tijdseries van trades (BUY=1, SELL=-1, geen trade=0)
                trades_by_time = trades_df.groupby("timestamp").apply(
                    lambda x: 1 if "BUY" in x["action"].values else (-1 if "SELL" in x["action"].values else 0)
                ).to_dict()

                equity_df["trade_signal"] = equity_df["timestamp"].map(trades_by_time).fillna(0)

                # Features
                features = equity_df[["returns", "drawdown", "prana"]].values

                for i in range(len(features) - sequence_length):
                    seq = features[i:i + sequence_length]
                    # Label: is er een trade in het volgende tijdsinterval?
                    label = int(equity_df["trade_signal"].iloc[i + sequence_length]) + 1  # -1,0,1 -> 0,1,2

                    all_sequences.append(seq)
                    all_labels.append(label)

            except Exception as e:
                logger.warning(f"Failed to process {json_file}: {e}")
                continue

        logger.info(f"Classification dataset: {len(all_sequences)} samples")

        return ClassificationDataset(all_sequences, all_labels)


class LSTMDataset(Dataset):
    """PyTorch Dataset voor LSTM training."""

    def __init__(self, sequences: list[np.ndarray], labels: list[float]):
        self.sequences = [torch.FloatTensor(seq) for seq in sequences]
        self.labels = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


class ClassificationDataset(Dataset):
    """PyTorch Dataset voor classificatie."""

    def __init__(self, sequences: list[np.ndarray], labels: list[int]):
        self.sequences = [torch.FloatTensor(seq) for seq in sequences]
        self.labels = torch.LongTensor(labels)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]
