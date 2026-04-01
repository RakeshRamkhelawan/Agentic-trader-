"""
Backtest Dataset Builder

Converteert bestaande backtest JSON/CSV data naar ML training datasets
voor LSTM/Transformer modellen.

Geen maanden wachten - gebruik je 200MB+ aan historische data!
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


class BacktestDatasetBuilder:
    """
    Bouwt ML datasets uit bestaande backtest data.

    Usage:
        builder = BacktestDatasetBuilder()

        # Train LSTM op historische patronen
        dataset = builder.build_lstm_dataset(
            backtest_dir="backtest_results",
            sequence_length=50,  # 50 tijdstappen input
            prediction_horizon=10  # 10 stappen ahead voorspellen
        )
    """

    def __init__(self):
        self.features = []
        self.labels = []

    def load_backtest_json(self, filepath: Path) -> dict:
        """Laad een backtest JSON file."""
        with open(filepath) as f:
            return json.load(f)

    def extract_equity_curve(self, backtest_data: dict) -> pd.DataFrame:
        """
        Extract equity curve als time series.

        Returns DataFrame met:
        - timestamp
        - equity_value
        - returns (gecalculeerd)
        - drawdown
        """
        equity = backtest_data.get("equity_curve", [])

        if not equity:
            return pd.DataFrame()

        df = pd.DataFrame(equity)

        # Bereken returns
        if "value" in df.columns:
            df["returns"] = df["value"].pct_change()
            df["cumulative_return"] = (df["value"] / df["value"].iloc[0]) - 1

            # Bereken drawdown
            df["peak"] = df["value"].cummax()
            df["drawdown"] = (df["value"] - df["peak"]) / df["peak"]

        return df

    def extract_harmony_features(self, backtest_data: dict) -> pd.DataFrame:
        """
        Extract harmony scores en elemental states.

        Features:
        - harmony_score (0-1)
        - elemental_balance (fire, water, earth, air, ether levels)
        - guna_balance (sattva, rajas, tamas)
        """
        harmony = backtest_data.get("harmony_curve", [])
        elemental = backtest_data.get("elemental_cycles", [])

        df = pd.DataFrame(harmony) if harmony else pd.DataFrame()

        # Voeg elemental features toe als beschikbaar
        if elemental and len(elemental) == len(harmony):
            df["fire"] = [e.get("fire", 0.2) for e in elemental]
            df["water"] = [e.get("water", 0.2) for e in elemental]
            df["earth"] = [e.get("earth", 0.2) for e in elemental]
            df["air"] = [e.get("air", 0.2) for e in elemental]
            df["ether"] = [e.get("ether", 0.2) for e in elemental]

        return df

    def load_harmony_csv(self, filepath: Path) -> pd.DataFrame:
        """
        Laad harmony CSV met granularere data per asset.
        """
        df = pd.read_csv(filepath)

        # Parse timestamps
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

        # Encode decisions
        if "decision" in df.columns:
            df["decision_encoded"] = (
                df["decision"].map({"BUY": 1, "SELL": -1, "HOLD": 0, "BLOCK": 0}).fillna(0)
            )

        # Encode planets (vedic feature)
        if "planet" in df.columns:
            # One-hot encode of ordinal encoding
            planet_mapping = {
                "SATURN": 0,
                "JUPITER": 1,
                "MARS": 2,
                "SUN": 3,
                "VENUS": 4,
                "MERCURY": 5,
                "MOON": 6,
            }
            df["planet_encoded"] = (
                df["planet"].str.extract(r"(\w+)")[0].map(planet_mapping).fillna(-1)
            )

        return df

    def build_lstm_dataset(
        self,
        backtest_dir: str = "backtest_results",
        sequence_length: int = 50,
        prediction_horizon: int = 10,
        min_samples: int = 1000,
    ) -> "LSTMDataset":
        """
        Bouw LSTM dataset uit alle backtest files.

        Input: [batch, sequence_length, num_features]
        Output: [batch, prediction_horizon] (future returns)
        """
        all_sequences = []
        all_labels = []

        backtest_path = Path(backtest_dir)
        json_files = list(backtest_path.glob("elemental_backtest_*.json"))

        logger.info(f"Processing {len(json_files)} backtest files...")

        for json_file in json_files[:20]:  # Limiteer tot 20 files voor nu
            try:
                data = self.load_backtest_json(json_file)

                # Extract features
                equity_df = self.extract_equity_curve(data)
                harmony_df = self.extract_harmony_features(data)

                if equity_df.empty or len(equity_df) < sequence_length + prediction_horizon:
                    continue

                # Combineer features
                features_df = pd.concat([equity_df, harmony_df], axis=1)
                features_df = features_df.fillna(method="ffill").fillna(0)

                # Selecteer numerieke kolommen
                numeric_cols = features_df.select_dtypes(include=[np.number]).columns
                features = features_df[numeric_cols].values

                # Genereer sequences
                for i in range(len(features) - sequence_length - prediction_horizon):
                    seq = features[i : i + sequence_length]

                    # Label: cumulative return over prediction_horizon
                    future_returns = (
                        equity_df["returns"]
                        .iloc[i + sequence_length : i + sequence_length + prediction_horizon]
                        .values
                        if "returns" in equity_df.columns
                        else [0]
                    )

                    label = np.sum(future_returns) if len(future_returns) > 0 else 0

                    all_sequences.append(seq)
                    all_labels.append(label)

            except Exception as e:
                logger.warning(f"Failed to process {json_file}: {e}")
                continue

        if len(all_sequences) < min_samples:
            logger.warning(f"Only {len(all_sequences)} sequences generated, need {min_samples}")

        logger.info(f"Dataset built: {len(all_sequences)} sequences")

        return LSTMDataset(all_sequences, all_labels)

    def build_classification_dataset(
        self, backtest_dir: str = "backtest_results", sequence_length: int = 20
    ) -> "ClassificationDataset":
        """
        Classificatie dataset: voorspel of de volgende actie BUY, SELL, of HOLD moet zijn.
        """
        all_sequences = []
        all_labels = []

        # Zoek harmony CSVs (die hebben de decisions)
        csv_files = list(Path("data/backtest_archive").glob("*_harmony.csv"))

        for csv_file in csv_files[:10]:
            try:
                df = self.load_harmony_csv(csv_file)

                if len(df) < sequence_length:
                    continue

                # Features: harmony scores over tijd
                for i in range(len(df) - sequence_length):
                    seq = df["harmony"].iloc[i : i + sequence_length].values

                    # Label: volgende decision
                    next_decision = df["decision_encoded"].iloc[i + sequence_length]

                    all_sequences.append(seq.reshape(-1, 1))
                    all_labels.append(int(next_decision) + 1)  # -1,0,1 -> 0,1,2

            except Exception as e:
                logger.warning(f"Failed to process {csv_file}: {e}")
                continue

        logger.info(f"Classification dataset: {len(all_sequences)} samples")

        return ClassificationDataset(all_sequences, all_labels)

    def get_dataset_statistics(self) -> dict:
        """Statistieken over de gegenereerde dataset."""
        return {
            "total_sequences": len(self.features) if self.features else 0,
            "sequence_length": len(self.features[0]) if self.features else 0,
            "num_features": (
                len(self.features[0][0]) if self.features and len(self.features[0]) > 0 else 0
            ),
            "positive_labels": (sum(1 for l in self.labels if l > 0) if self.labels else 0),
            "negative_labels": (sum(1 for l in self.labels if l < 0) if self.labels else 0),
        }


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
    """PyTorch Dataset voor classificatie (BUY/SELL/HOLD)."""

    def __init__(self, sequences: list[np.ndarray], labels: list[int]):
        self.sequences = [torch.FloatTensor(seq) for seq in sequences]
        self.labels = torch.LongTensor(labels)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]
