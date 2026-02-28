#!/usr/bin/env python3
"""
Train Chitta Model v2 - Getraind op backtest data met juiste structuur.

Usage:
    python scripts/train_chitta_model_v2.py --epochs 30
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train Chitta forecasting model v2")
    parser.add_argument(
        "--epochs",
        type=int,
        default=30,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size"
    )
    parser.add_argument(
        "--sequence-length",
        type=int,
        default=50,
        help="Sequence length (timesteps)"
    )
    parser.add_argument(
        "--prediction-horizon",
        type=int,
        default=5,
        help="How many steps ahead to predict"
    )
    parser.add_argument(
        "--backtest-dir",
        type=str,
        default="backtest_results",
        help="Directory met backtest JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Directory om getrainde modellen op te slaan"
    )
    parser.add_argument(
        "--model-type",
        type=str,
        choices=["lstm", "transformer"],
        default="lstm",
        help="Model architectuur"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("CHITTA MODEL TRAINING v2")
    logger.info("=" * 70)
    logger.info(f"Model type: {args.model_type}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Sequence length: {args.sequence_length}")
    logger.info(f"Prediction horizon: {args.prediction_horizon}")
    logger.info(f"Backtest dir: {args.backtest_dir}")
    logger.info("")

    # Check backtest dir
    backtest_path = Path(args.backtest_dir)
    if not backtest_path.exists():
        logger.error(f"Backtest directory {args.backtest_dir} bestaat niet!")
        sys.exit(1)

    # Import modules
    try:
        from backend.core.ml.backtest_dataset_builder_v2 import BacktestDatasetBuilderV2
        from backend.core.ml.lstm_model import ChittaLSTM, ChittaTransformer, ModelTrainer
        import torch
        from torch.utils.data import DataLoader, random_split
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Zorg dat je in de project root bent met activated venv")
        sys.exit(1)

    # Bouw dataset
    logger.info("Building dataset from backtest files...")
    builder = BacktestDatasetBuilderV2()

    try:
        dataset = builder.build_lstm_dataset(
            backtest_dir=args.backtest_dir,
            sequence_length=args.sequence_length,
            prediction_horizon=args.prediction_horizon,
            min_samples=100
        )
    except Exception as e:
        logger.error(f"Dataset building failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if len(dataset) == 0:
        logger.error("Geen training data gegenereerd!")
        sys.exit(1)

    logger.info(f"Dataset size: {len(dataset)} sequences")

    # Bepaal input size van eerste sample
    sample_seq, _ = dataset[0]
    input_size = sample_seq.shape[1]
    logger.info(f"Input features: {input_size}")

    # Split train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size

    logger.info(f"Train size: {train_size}, Val size: {val_size}")

    train_dataset, val_dataset = random_split(
        dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42)  # Reproducible
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0  # Windows compatibility
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        num_workers=0
    )

    # Initialiseer model
    logger.info(f"Initializing {args.model_type} model...")

    if args.model_type == "lstm":
        model = ChittaLSTM(
            input_size=input_size,
            hidden_size=128,
            num_layers=2,
            output_size=1,
            dropout=0.2
        )
    else:
        model = ChittaTransformer(
            input_size=input_size,
            d_model=128,
            nhead=8,
            num_layers=4,
            output_size=1,
            dropout=0.1
        )

    # Train
    trainer = ModelTrainer(model, learning_rate=0.001)

    logger.info("")
    logger.info("Starting training...")
    logger.info("")

    best_val_loss = float('inf')
    best_val_acc = 0.0

    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    for epoch in range(args.epochs):
        train_loss = trainer.train_epoch(train_loader)
        val_loss, val_acc = trainer.validate(val_loader)

        logger.info(
            f"Epoch {epoch+1:3d}/{args.epochs}: "
            f"Train Loss={train_loss:.6f}, "
            f"Val Loss={val_loss:.6f}, "
            f"Val Dir Acc={val_acc:.2%}"
        )

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            model_path = output_path / f"chitta_{args.model_type}_best.pt"
            trainer.save_model(str(model_path))
            logger.info(f"  -> Saved best model (val_loss: {val_loss:.6f})")

    logger.info("")
    logger.info("=" * 70)
    logger.info("TRAINING COMPLETED!")
    logger.info("=" * 70)
    logger.info(f"Best validation loss: {best_val_loss:.6f}")
    logger.info(f"Best validation accuracy: {best_val_acc:.2%}")
    logger.info(f"Model saved to: {args.output_dir}/chitta_{args.model_type}_best.pt")
    logger.info("")
    logger.info("Usage in production:")
    logger.info(f"  from backend.core.prediction.chitta_forecaster_v2 import ChittaForecasterV2")
    logger.info(f"  forecaster = ChittaForecasterV2()")
    logger.info(f"  forecaster.load_model('{args.output_dir}/chitta_{args.model_type}_best.pt')")


if __name__ == "__main__":
    main()
