"""
XGBoost Training Pipeline for VedAstro-Tattvas Fusion

This script trains an XGBoost model on historical OHLCV data
combined with VedAstro planetary features.

Usage:
    python scripts/train_xgboost_model.py \
        --data data/historical/btc_ohlcv.csv \
        --symbol BTC \
        --output models/xgboost_btc.json

Requirements:
    - Historical OHLCV data (CSV with columns: timestamp, open, high, low, close, volume)
    - VedAstro libraries (or HTTP bridge running)
    - Python 3.10+
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.vedastro.connector import VedAstroConnector, VedAstroConfig
from backend.vedastro.features import FeatureEngine
from backend.vedastro.oracle import XGBoostOracle

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AstroFeatureGenerator:
    """Generates astrological features for historical data."""
    
    def __init__(self, use_http_fallback: bool = False):
        self.vedastro = VedAstroConnector(
            VedAstroConfig(use_http_fallback=use_http_fallback)
        )
        self.feature_engine = FeatureEngine()
        self.kundli_cache = {}
    
    async def initialize(self, symbol: str, birth_date: datetime):
        """Pre-calculate Kundli for asset."""
        self.kundli_cache[symbol] = await self.vedastro.calculate_kundli(
            symbol, birth_date
        )
        logger.info(f"Cached Kundli for {symbol}")
    
    async def generate_features(
        self, 
        symbol: str, 
        timestamp: datetime,
        price: float,
        technical_indicators: Optional[Dict] = None
    ) -> Optional[np.ndarray]:
        """Generate feature vector for a timestamp."""
        kundli = self.kundli_cache.get(symbol)
        if not kundli:
            return None
        
        # Get transits for this timestamp
        transits = await self.vedastro.calculate_transits(timestamp, kundli)
        
        # Mock Tattva state (would come from historical SystemIdentity state)
        tattva_state = {
            'coherence': 0.6,
            'gunas': {'sattva': 0.4, 'rajas': 0.4, 'tamas': 0.2}
        }
        
        # Extract features
        features = self.feature_engine.extract(
            kundli, transits, price, tattva_state, technical_indicators
        )
        
        return features


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators for dataset."""
    # Returns (price change %)
    df['returns'] = df['close'].pct_change()
    
    # Moving averages
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # Volatility (20-day)
    df['volatility'] = df['returns'].rolling(window=20).std()
    
    # Trend strength (price vs SMA distance)
    df['trend_strength'] = (df['close'] - df['sma_20']) / df['sma_20']
    
    # Volume indicators
    df['volume_sma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # RSI (14-day)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    return df


def create_labels(df: pd.DataFrame, lookahead: int = 1, threshold: float = 0.005) -> pd.DataFrame:
    """
    Create binary labels for training.
    
    Label = 1 (UP) if future return > threshold
    Label = 0 (DOWN) if future return < -threshold
    Otherwise NaN (neutral, excluded from training)
    """
    future_return = df['close'].shift(-lookahead) / df['close'] - 1
    
    df['label'] = np.nan
    df.loc[future_return > threshold, 'label'] = 1  # UP
    df.loc[future_return < -threshold, 'label'] = 0  # DOWN
    
    df['future_return'] = future_return
    
    return df


async def prepare_training_data(
    data_path: str,
    symbol: str,
    birth_date: datetime,
    use_http_fallback: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare training data from OHLCV CSV.
    
    Returns:
        X: Feature matrix (n_samples x n_features)
        y: Labels (n_samples,)
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path, parse_dates=['timestamp'])
    df = df.sort_values('timestamp')
    
    logger.info(f"Loaded {len(df)} rows")
    
    # Calculate technical indicators
    logger.info("Calculating technical indicators...")
    df = calculate_technical_indicators(df)
    
    # Create labels
    logger.info("Creating labels...")
    df = create_labels(df, lookahead=1, threshold=0.005)
    
    # Initialize VedAstro
    logger.info("Initializing VedAstro...")
    generator = AstroFeatureGenerator(use_http_fallback)
    await generator.initialize(symbol, birth_date)
    
    # Generate astro features for each row
    logger.info("Generating astrological features...")
    features_list = []
    labels_list = []
    
    for idx, row in df.iterrows():
        if idx < 50:  # Skip first 50 rows (need SMA data)
            continue
        
        if pd.isna(row['label']):
            continue
        
        technical = {
            'volatility': row.get('volatility', 0.02),
            'trend': row.get('trend_strength', 0),
            'rsi': row.get('rsi', 50),
            'volume_ratio': row.get('volume_ratio', 1)
        }
        
        features = await generator.generate_features(
            symbol, row['timestamp'], row['close'], technical
        )
        
        if features is not None:
            features_list.append(features)
            labels_list.append(int(row['label']))
        
        if len(features_list) % 100 == 0:
            logger.info(f"Processed {len(features_list)} samples...")
    
    X = np.array(features_list)
    y = np.array(labels_list)
    
    logger.info(f"Generated {len(X)} training samples")
    logger.info(f"Class distribution: UP={sum(y)}, DOWN={len(y)-sum(y)}")
    
    return X, y


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    output_path: str,
    validation_split: float = 0.2
) -> Dict:
    """
    Train XGBoost model with cross-validation.
    
    Returns:
        Training metrics
    """
    logger.info("Training XGBoost model...")
    
    # Time-series split for validation
    tscv = TimeSeriesSplit(n_splits=5)
    
    oracle = XGBoostOracle()
    
    # Split data
    split_idx = int(len(X) * (1 - validation_split))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Train
    metrics = oracle.train(
        X_train, y_train,
        validation_split=0.1,  # Internal validation
        early_stopping_rounds=20
    )
    
    # Validate on holdout set
    val_predictions = oracle.predict_batch(X_val)
    y_pred = [p['prediction'] for p in val_predictions]
    
    # Calculate metrics
    metrics['val_accuracy'] = accuracy_score(y_val, y_pred)
    metrics['val_precision'] = precision_score(y_val, y_pred, zero_division=0)
    metrics['val_recall'] = recall_score(y_val, y_pred, zero_division=0)
    metrics['val_f1'] = f1_score(y_val, y_pred, zero_division=0)
    
    logger.info(f"Validation metrics: {metrics}")
    
    # Save model
    oracle.save_model(output_path)
    logger.info(f"Model saved to {output_path}")
    
    # Feature importance
    top_features = oracle.get_top_features(10)
    logger.info("Top 10 features:")
    for name, importance in top_features:
        logger.info(f"  {name}: {importance:.4f}")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description='Train XGBoost model with VedAstro features'
    )
    parser.add_argument(
        '--data', '-d',
        required=True,
        help='Path to OHLCV CSV file'
    )
    parser.add_argument(
        '--symbol', '-s',
        required=True,
        help='Asset symbol (BTC, ETH, etc.)'
    )
    parser.add_argument(
        '--output', '-o',
        default='models/xgboost_model.json',
        help='Output path for trained model'
    )
    parser.add_argument(
        '--birth-date',
        help='Asset birth date (YYYY-MM-DD). Auto-detected for known assets.'
    )
    parser.add_argument(
        '--use-http',
        action='store_true',
        help='Use HTTP fallback instead of C# interop'
    )
    
    args = parser.parse_args()
    
    # Determine birth date
    from backend.vedastro.orchestrator import TattvaOrchestrator
    
    if args.birth_date:
        birth_date = datetime.strptime(args.birth_date, '%Y-%m-%d')
    else:
        birth_date = TattvaOrchestrator.ASSET_BIRTHDAYS.get(args.symbol)
        if not birth_date:
            raise ValueError(f"Unknown symbol {args.symbol}. Provide --birth-date.")
    
    logger.info(f"Training model for {args.symbol} (born {birth_date.date()})")
    
    # Run async preparation
    X, y = asyncio.run(prepare_training_data(
        args.data, args.symbol, birth_date, args.use_http
    ))
    
    if len(X) < 1000:
        logger.warning(f"Low sample count: {len(X)}. Model may not generalize well.")
    
    # Train model
    metrics = train_model(X, y, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Model saved to: {args.output}")
    print(f"Training samples: {len(X)}")
    print(f"Validation accuracy: {metrics.get('val_accuracy', 0):.4f}")
    print(f"Validation F1: {metrics.get('val_f1', 0):.4f}")
    print("="*60)


if __name__ == "__main__":
    main()
