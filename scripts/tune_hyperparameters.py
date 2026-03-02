"""
Hyperparameter Tuning voor Chitta Models

Automatisch zoeken naar beste configuratie met:
- Grid search
- Random search
- Bayesian optimization (optuna)

Usage:
    python scripts/tune_hyperparameters.py --method random --n-trials 20
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
import logging
from dataclasses import dataclass
from typing import Dict, Any

import torch
from torch.utils.data import DataLoader, random_split

from backend.core.ml.fast_dataset_builder import FastBacktestDatasetBuilder
from backend.core.ml.models.lstm_model import ChittaLSTM, ModelTrainer
from backend.core.ml.models.transformer_model import ChittaTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HyperParams:
    """Hyperparameter configuratie."""
    model_type: str = "lstm"
    hidden_size: int = 128
    num_layers: int = 2
    dropout: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    sequence_length: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "sequence_length": self.sequence_length
        }


class HyperparameterTuner:
    """Hyperparameter tuning met verschillende strategieën."""

    def __init__(self, dataset, input_size: int):
        self.dataset = dataset
        self.input_size = input_size
        self.results = []

    def grid_search(self, param_grid: Dict[str, list]) -> HyperParams:
        """
        Grid search over alle combinaties.

        Usage:
            param_grid = {
                "hidden_size": [64, 128, 256],
                "num_layers": [1, 2, 3],
                "dropout": [0.1, 0.2, 0.3]
            }
        """
        best_score = float('inf')
        best_params = None

        # Genereer alle combinaties
        import itertools
        keys = list(param_grid.keys())
        values = [param_grid[k] for k in keys]

        total_combinations = 1
        for v in values:
            total_combinations *= len(v)

        logger.info(f"Grid search: {total_combinations} combinations")

        for i, combination in enumerate(itertools.product(*values)):
            params = dict(zip(keys, combination))
            logger.info(f"Trial {i+1}/{total_combinations}: {params}")

            score = self._evaluate_params(params)

            if score < best_score:
                best_score = score
                best_params = params
                logger.info(f"  -> New best! Score: {score:.6f}")

            self.results.append({
                "params": params,
                "score": score,
                "is_best": score == best_score
            })

        return HyperParams(**best_params)

    def random_search(self, param_distributions: Dict[str, Any], n_trials: int = 20) -> HyperParams:
        """
        Random search - efficiënter dan grid voor hoge dimensies.

        Usage:
            param_distributions = {
                "hidden_size": [64, 128, 256, 512],
                "num_layers": [1, 2, 3],
                "dropout": lambda: np.random.uniform(0.1, 0.5)
            }
        """
        import random
        import numpy as np

        best_score = float('inf')
        best_params = None

        logger.info(f"Random search: {n_trials} trials")

        for i in range(n_trials):
            # Sample parameters
            params = {}
            for key, dist in param_distributions.items():
                if callable(dist):
                    params[key] = dist()
                elif isinstance(dist, list):
                    params[key] = random.choice(dist)
                else:
                    params[key] = dist

            logger.info(f"Trial {i+1}/{n_trials}: {params}")

            score = self._evaluate_params(params)

            if score < best_score:
                best_score = score
                best_params = params
                logger.info(f"  -> New best! Score: {score:.6f}")

            self.results.append({
                "params": params,
                "score": score,
                "is_best": score == best_score
            })

        return HyperParams(**best_params)

    def _evaluate_params(self, params: Dict[str, Any]) -> float:
        """
        Evalueer één set hyperparameters.

        Returns:
            Validation loss (lager is beter)
        """
        try:
            # Create model
            if params.get("model_type", "lstm") == "lstm":
                model = ChittaLSTM(
                    input_size=self.input_size,
                    hidden_size=params.get("hidden_size", 128),
                    num_layers=params.get("num_layers", 2),
                    dropout=params.get("dropout", 0.2),
                    output_size=1
                )
            else:
                model = ChittaTransformer(
                    input_size=self.input_size,
                    d_model=params.get("hidden_size", 128),
                    num_layers=params.get("num_layers", 2),
                    dropout=params.get("dropout", 0.2),
                    output_size=1
                )

            # Create dataloaders
            batch_size = params.get("batch_size", 32)
            train_size = int(0.8 * len(self.dataset))
            val_size = len(self.dataset) - train_size
            train_ds, val_ds = random_split(self.dataset, [train_size, val_size])

            train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_ds, batch_size=batch_size)

            # Train
            trainer = ModelTrainer(model, learning_rate=params.get("learning_rate", 0.001))

            # Train voor 5 epochs (snelle evaluatie)
            for epoch in range(5):
                trainer.train_epoch(train_loader)

            # Evaluate
            val_loss, _ = trainer.validate(val_loader)

            return val_loss

        except Exception as e:
            logger.error(f"Error evaluating params: {e}")
            return float('inf')

    def save_results(self, path: str):
        """Sla tuning results op."""
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["grid", "random"], default="random")
    parser.add_argument("--n-trials", type=int, default=10)
    parser.add_argument("--max-files", type=int, default=3)
    parser.add_argument("--output", default="tuning_results.json")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("HYPERPARAMETER TUNING")
    logger.info("=" * 60)

    # Load dataset
    logger.info("Loading dataset...")
    builder = FastBacktestDatasetBuilder(use_cache=True)
    dataset = builder.build_dataset(
        backtest_dir="backtest_results",
        max_files=args.max_files,
        sequence_length=50,
        n_workers=4
    )

    sample_seq, _ = dataset[0]
    input_size = sample_seq.shape[1]
    logger.info(f"Dataset: {len(dataset)} sequences, {input_size} features")

    # Initialize tuner
    tuner = HyperparameterTuner(dataset, input_size)

    # Run tuning
    if args.method == "grid":
        param_grid = {
            "hidden_size": [64, 128],
            "num_layers": [1, 2],
            "dropout": [0.1, 0.2],
            "learning_rate": [0.001, 0.01]
        }
        best_params = tuner.grid_search(param_grid)

    else:  # random
        import numpy as np
        param_distributions = {
            "model_type": ["lstm"],
            "hidden_size": [64, 128, 256],
            "num_layers": [1, 2, 3],
            "dropout": lambda: np.random.uniform(0.1, 0.4),
            "learning_rate": lambda: 10 ** np.random.uniform(-4, -2),
            "batch_size": [16, 32, 64]
        }
        best_params = tuner.random_search(param_distributions, n_trials=args.n_trials)

    # Results
    logger.info("")
    logger.info("=" * 60)
    logger.info("BEST HYPERPARAMETERS:")
    logger.info("=" * 60)
    for key, value in best_params.to_dict().items():
        logger.info(f"  {key}: {value}")

    # Save
    tuner.save_results(args.output)

    # Save best config
    with open("best_config.json", 'w') as f:
        json.dump(best_params.to_dict(), f, indent=2)
    logger.info("Best config saved to best_config.json")


if __name__ == "__main__":
    main()
