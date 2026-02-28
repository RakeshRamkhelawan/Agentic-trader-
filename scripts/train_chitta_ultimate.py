"""
Ultimate Chitta Training Script

Combineert ALLE verbeteringen:
- GPU support
- Technical indicators (RSI, MACD, Bollinger)
- Transformer + LSTM + Ensemble
- Hyperparameter tuning
- Fast parallel data loading

Usage:
    # Snelle test
    python scripts/train_chitta_ultimate.py --quick

    # Volledige training
    python scripts/train_chitta_ultimate.py --model-type transformer --epochs 50

    # Hyperparameter tuning
    python scripts/train_chitta_ultimate.py --tune --n-trials 20
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
import logging
import time
from typing import Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

# Import onze modules
from backend.core.ml.fast_dataset_builder import FastBacktestDatasetBuilder
from backend.core.ml.models.lstm_model import ChittaLSTM, ModelTrainer
from backend.core.ml.models.transformer_model import ChittaTransformer
from backend.core.ml.models.ensemble_model import ChittaEnsemble
from backend.core.ml.features.technical_indicators import add_all_features

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print mooie sectie header."""
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"  {title}")
    logger.info("=" * 70)


def get_device() -> str:
    """Bepaal beste device (GPU > CPU)."""
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        device = "cpu"
        logger.info("No GPU detected, using CPU")
    return device


def create_model(
    model_type: str,
    input_size: int,
    hidden_size: int,
    num_layers: int,
    dropout: float,
    device: str
) -> nn.Module:
    """Create model based on type."""

    if model_type == "lstm":
        model = ChittaLSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            output_size=1
        )
    elif model_type == "transformer":
        model = ChittaTransformer(
            input_size=input_size,
            d_model=hidden_size,
            nhead=8,
            num_layers=num_layers,
            dropout=dropout,
            output_size=1
        )
    elif model_type == "ensemble":
        model = ChittaEnsemble(
            input_size=input_size,
            lstm_hidden=hidden_size,
            lstm_layers=num_layers,
            transformer_d_model=hidden_size,
            transformer_layers=num_layers,
            dropout=dropout,
            ensemble_method="weighted"
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    return model.to(device)


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int,
    learning_rate: float,
    device: str
) -> dict:
    """Train model en return metrics."""

    trainer = ModelTrainer(model, learning_rate=learning_rate, device=device)

    best_val_loss = float('inf')
    history = {
        "train_loss": [],
        "val_loss": [],
        "val_acc": []
    }

    for epoch in range(epochs):
        start_time = time.time()

        # Train
        train_loss = trainer.train_epoch(train_loader)

        # Validate
        val_loss, val_acc = trainer.validate(val_loader)

        # Log
        epoch_time = time.time() - start_time
        logger.info(
            f"Epoch {epoch+1:3d}/{epochs}: "
            f"Train={train_loss:.6f}, Val={val_loss:.6f}, Acc={val_acc:.2%}, "
            f"Time={epoch_time:.1f}s"
        )

        # Save history
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()

    # Load best model
    model.load_state_dict(best_model_state)

    return {
        "model": model,
        "best_val_loss": best_val_loss,
        "history": history
    }


def main():
    parser = argparse.ArgumentParser(description="Ultimate Chitta Training")

    # Data args
    parser.add_argument("--backtest-dir", default="backtest_results")
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--sequence-length", type=int, default=50)
    parser.add_argument("--prediction-horizon", type=int, default=5)

    # Model args
    parser.add_argument("--model-type", choices=["lstm", "transformer", "ensemble"], default="transformer")
    parser.add_argument("--hidden-size", type=int, default=128)
    parser.add_argument("--num-layers", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.2)

    # Training args
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--train-split", type=float, default=0.8)

    # Mode
    parser.add_argument("--quick", action="store_true", help="Snelle test met minder data")
    parser.add_argument("--tune", action="store_true", help="Hyperparameter tuning")
    parser.add_argument("--n-trials", type=int, default=10)

    # Output
    parser.add_argument("--output-dir", default="models")
    parser.add_argument("--save-history", action="store_true")

    args = parser.parse_args()

    # Quick mode
    if args.quick:
        logger.info("QUICK MODE: Using subset of data")
        args.max_files = 2
        args.epochs = 5
        args.batch_size = 16

    # Print header
    print_section("CHITTA ULTIMATE TRAINING")
    logger.info(f"Model: {args.model_type}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Device: {get_device()}")

    # Device
    device = get_device()

    # Load data
    print_section("LOADING DATA")
    builder = FastBacktestDatasetBuilder(use_cache=True)
    dataset = builder.build_dataset(
        backtest_dir=args.backtest_dir,
        sequence_length=args.sequence_length,
        prediction_horizon=args.prediction_horizon,
        max_files=args.max_files,
        n_workers=4
    )

    if len(dataset) == 0:
        logger.error("Geen training data!")
        return

    sample_seq, _ = dataset[0]
    input_size = sample_seq.shape[1]

    logger.info(f"Dataset size: {len(dataset)}")
    logger.info(f"Input features: {input_size}")
    logger.info(f"Sequence length: {args.sequence_length}")

    # Split data
    train_size = int(args.train_split * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    logger.info(f"Train: {train_size}, Val: {val_size}")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    # Hyperparameter tuning of direct training
    if args.tune:
        print_section("HYPERPARAMETER TUNING")
        from scripts.tune_hyperparameters import HyperparameterTuner

        tuner = HyperparameterTuner(dataset, input_size)
        import numpy as np

        param_distributions = {
            "model_type": [args.model_type],
            "hidden_size": [64, 128, 256],
            "num_layers": [2, 3, 4],
            "dropout": lambda: np.random.uniform(0.1, 0.3),
            "learning_rate": lambda: 10 ** np.random.uniform(-4, -2.5),
            "batch_size": [16, 32]
        }

        best_params = tuner.random_search(param_distributions, n_trials=args.n_trials)

        # Update args met beste params
        args.hidden_size = best_params.hidden_size
        args.num_layers = best_params.num_layers
        args.dropout = best_params.dropout
        args.learning_rate = best_params.learning_rate
        args.batch_size = best_params.batch_size

        logger.info(f"Best params: {best_params.to_dict()}")

    # Create model
    print_section("CREATING MODEL")
    model = create_model(
        args.model_type,
        input_size,
        args.hidden_size,
        args.num_layers,
        args.dropout,
        device
    )

    # Count parameters
    n_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model parameters: {n_params:,}")

    # Train
    print_section("TRAINING")
    start_time = time.time()

    results = train_model(
        model,
        train_loader,
        val_loader,
        args.epochs,
        args.learning_rate,
        device
    )

    train_time = time.time() - start_time

    # Results
    print_section("RESULTS")
    logger.info(f"Training time: {train_time:.1f}s ({train_time/60:.1f} min)")
    logger.info(f"Best val loss: {results['best_val_loss']:.6f}")
    logger.info(f"Final val accuracy: {results['history']['val_acc'][-1]:.2%}")

    # Save model
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    model_path = output_dir / f"chitta_{args.model_type}_ultimate.pt"

    torch.save({
        'model_state_dict': results['model'].state_dict(),
        'config': {
            'model_type': args.model_type,
            'input_size': input_size,
            'hidden_size': args.hidden_size,
            'num_layers': args.num_layers,
            'dropout': args.dropout,
            'sequence_length': args.sequence_length
        },
        'metrics': {
            'best_val_loss': results['best_val_loss'],
            'final_val_acc': results['history']['val_acc'][-1]
        }
    }, model_path)

    logger.info(f"Model saved: {model_path}")

    # Save history
    if args.save_history:
        history_path = output_dir / f"chitta_{args.model_type}_history.json"
        with open(history_path, 'w') as f:
            json.dump(results['history'], f)
        logger.info(f"History saved: {history_path}")

    print_section("COMPLETE")
    logger.info("Training completed successfully!")
    logger.info(f"Model ready for inference: ChittaForecasterV2.load_model('{model_path}')")


if __name__ == "__main__":
    main()
