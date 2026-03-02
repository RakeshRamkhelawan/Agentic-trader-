#!/usr/bin/env python3
"""
Train LSTM/Transformer model op bestaande backtest data.

Geen live data nodig - gebruik je historische backtests!

Usage:
    python scripts/train_chitta_model.py --model lstm --epochs 50
    python scripts/train_chitta_model.py --model transformer --epochs 30
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train Chitta forecasting model")
    parser.add_argument(
        "--model",
        type=str,
        choices=["lstm", "transformer"],
        default="lstm",
        help="Model type to train"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size"
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

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("CHITTA MODEL TRAINING")
    logger.info("=" * 60)
    logger.info(f"Model type: {args.model}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Backtest dir: {args.backtest_dir}")
    logger.info("")

    # Check of backtest dir bestaat
    backtest_path = Path(args.backtest_dir)
    if not backtest_path.exists():
        logger.error(f"Backtest directory {args.backtest_dir} bestaat niet!")
        logger.error("Zorg dat je backtest JSON files in deze directory hebt:")
        logger.error("  - elemental_backtest_*.json")
        logger.error("  - backtest_v*.json")
        sys.exit(1)

    # Tel beschikbare files
    json_files = list(backtest_path.glob("elemental_backtest_*.json"))
    logger.info(f"Gevonden {len(json_files)} backtest files")

    if len(json_files) == 0:
        logger.error("Geen backtest JSON files gevonden!")
        sys.exit(1)

    # Maak output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    try:
        from backend.core.ml.lstm_model import train_on_backtest_data

        # Train model
        model = train_on_backtest_data(
            backtest_dir=args.backtest_dir,
            model_type=args.model,
            epochs=args.epochs,
            batch_size=args.batch_size
        )

        logger.info("")
        logger.info("=" * 60)
        logger.info("TRAINING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Model saved to: {args.output_dir}/chitta_{args.model}_best.pt")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Kopieer het model naar je productie omgeving")
        logger.info("2. Update de ChittaForecaster om dit model te gebruiken:")
        logger.info(f"   forecaster.load_lstm('{args.output_dir}/chitta_{args.model}_best.pt')")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
