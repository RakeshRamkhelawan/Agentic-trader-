"""
ML-Optimized Backtest - EFFICIENT VERSION

Genereert meer training data voor ML met betere performance.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLOptimizedBacktest:
    """Backtest voor ML training data."""

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.ml_features = []

    def calculate_indicators(self, prices: pd.Series, volumes: pd.Series) -> pd.DataFrame:
        """Bereken technische indicators."""
        df = pd.DataFrame({'price': prices, 'volume': volumes})

        # RSI
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df['price'].ewm(span=12).mean()
        ema26 = df['price'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        sma20 = df['price'].rolling(window=20).mean()
        std20 = df['price'].rolling(window=20).std()
        df['bb_upper'] = sma20 + (std20 * 2)
        df['bb_lower'] = sma20 - (std20 * 2)
        df['bb_position'] = (df['price'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma20

        # Momentum
        df['mom_1d'] = df['price'].pct_change(1)
        df['mom_3d'] = df['price'].pct_change(3)
        df['mom_5d'] = df['price'].pct_change(5)

        # Volume
        df['volume_sma'] = df['volume'].rolling(window=10).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        # ATR
        high = df['price'].rolling(window=2).max()
        low = df['price'].rolling(window=2).min()
        tr1 = high - low
        tr2 = abs(high - df['price'].shift())
        tr3 = abs(low - df['price'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        df['atr_pct'] = df['atr'] / df['price']

        # Trend
        df['sma_10'] = df['price'].rolling(window=10).mean()
        df['sma_30'] = df['price'].rolling(window=30).mean()
        df['trend'] = np.where(df['sma_10'] > df['sma_30'], 1, -1)

        return df

    def generate_signal(self, indicators: pd.Series) -> Tuple[str, float, Dict]:
        """Genereer trading signal."""
        features = {
            'rsi': indicators['rsi'],
            'macd': indicators['macd'],
            'macd_hist': indicators['macd_hist'],
            'bb_position': indicators['bb_position'],
            'bb_width': indicators['bb_width'],
            'mom_1d': indicators['mom_1d'],
            'mom_3d': indicators['mom_3d'],
            'volume_ratio': indicators['volume_ratio'],
            'atr_pct': indicators['atr_pct'],
            'trend': indicators['trend']
        }

        score = 0

        # RSI extremes
        if indicators['rsi'] < 30:
            score += 3
            features['rsi_extreme'] = -1
        elif indicators['rsi'] > 70:
            score -= 3
            features['rsi_extreme'] = 1
        else:
            features['rsi_extreme'] = 0

        # Bollinger Bands
        if indicators['bb_position'] < 0.2:
            score += 2
            features['bb_near_band'] = -1
        elif indicators['bb_position'] > 0.8:
            score -= 2
            features['bb_near_band'] = 1
        else:
            features['bb_near_band'] = 0

        # MACD
        if indicators['macd_hist'] < 0 and indicators['macd'] < 0:
            score += 1
        elif indicators['macd_hist'] > 0 and indicators['macd'] > 0:
            score -= 1

        # Volume
        if indicators['volume_ratio'] > 1.2:
            score += 1 if score > 0 else -1 if score < 0 else 0

        # Volatility filter
        if indicators['atr_pct'] > 0.05:
            score = 0

        if score >= 4:
            return "BUY", min(score / 6, 1.0), features
        elif score <= -4:
            return "SELL", min(abs(score) / 6, 1.0), features
        else:
            return "HOLD", 0.0, features

    def run_backtest(self, price_data: Dict[str, pd.DataFrame],
                     start_date: str, end_date: str) -> Dict:
        """Run backtest."""
        logger.info(f"Backtest: {start_date} to {end_date}, {len(price_data)} symbols")

        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        for i, date in enumerate(dates):
            # Log equity (daily)
            total_value = self.cash
            for sym in self.positions:
                hist = price_data[sym][price_data[sym].index <= date]
                if len(hist) > 0:
                    total_value += self.positions[sym]['quantity'] * hist['price'].iloc[-1]

            self.equity_curve.append({
                'timestamp': date.isoformat(),
                'value': total_value,
                'cash': self.cash
            })

            # Check each symbol
            for symbol, df in price_data.items():
                hist = df[df.index <= date]

                if len(hist) < 35:
                    continue

                indicators_df = self.calculate_indicators(hist['price'], hist['volume'])
                current = indicators_df.iloc[-1]
                current_price = current['price']

                action, confidence, features = self.generate_signal(current)

                # Log ML features
                self.ml_features.append({
                    'timestamp': date.isoformat(),
                    'symbol': symbol,
                    'price': current_price,
                    'action': action,
                    'confidence': confidence,
                    **features
                })

                # Execute trade
                if action == "BUY" and confidence > 0.6:
                    self._execute_trade(symbol, action, current_price, confidence, date)

                # Check exits
                self._check_exits(symbol, current_price, date)

            if (i + 1) % 500 == 0:
                logger.info(f"  {i+1}/{len(dates)} days, {len(self.trades)} trades")

        return self._generate_report()

    def _execute_trade(self, symbol: str, action: str, price: float,
                       confidence: float, date: datetime):
        """Execute trade."""
        if symbol in self.positions:
            return

        position_value = self.cash * 0.05 * confidence
        quantity = position_value / price
        cost = quantity * price

        if cost <= self.cash:
            self.cash -= cost
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'entry_date': date,
                'stop_loss': price * 0.98,
                'take_profit': price * 1.04
            }

    def _check_exits(self, symbol: str, current_price: float, date: datetime):
        """Check exits."""
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]

        if current_price <= pos['stop_loss']:
            pnl = (current_price - pos['entry_price']) * pos['quantity']
            self._close_trade(symbol, current_price, date, pnl, "STOP_LOSS")
        elif current_price >= pos['take_profit']:
            pnl = (current_price - pos['entry_price']) * pos['quantity']
            self._close_trade(symbol, current_price, date, pnl, "TAKE_PROFIT")
        elif (date - pos['entry_date']).days >= 10:
            pnl = (current_price - pos['entry_price']) * pos['quantity']
            self._close_trade(symbol, current_price, date, pnl, "TIME_EXIT")

    def _close_trade(self, symbol: str, price: float, date: datetime,
                     pnl: float, exit_reason: str):
        """Close position."""
        pos = self.positions[symbol]
        self.cash += pos['quantity'] * price

        self.trades.append({
            'symbol': symbol,
            'entry_date': pos['entry_date'].isoformat(),
            'exit_date': date.isoformat(),
            'entry_price': pos['entry_price'],
            'exit_price': price,
            'quantity': pos['quantity'],
            'pnl': pnl,
            'pnl_pct': (price - pos['entry_price']) / pos['entry_price'],
            'exit_reason': exit_reason,
            'win': 1 if pnl > 0 else 0
        })

        del self.positions[symbol]

    def _generate_report(self) -> Dict:
        """Generate report."""
        if not self.trades:
            return {"error": "No trades"}

        trades_df = pd.DataFrame(self.trades)
        wins = len(trades_df[trades_df['win'] == 1])
        losses = len(trades_df[trades_df['win'] == 0])
        win_rate = wins / len(trades_df) if len(trades_df) > 0 else 0

        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['win'] == 1]['pnl'].mean() if wins > 0 else 0
        avg_loss = trades_df[trades_df['win'] == 0]['pnl'].mean() if losses > 0 else 0

        return {
            "backtest_type": "ml_optimized",
            "strategy": "mean_reversion_rsi",
            "total_trades": len(trades_df),
            "winning_trades": wins,
            "losing_trades": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_return_pct": (total_pnl / self.initial_capital) * 100,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(avg_win * wins / (avg_loss * losses)) if losses > 0 else float('inf'),
            "feature_count": len(self.ml_features),
            "trades": self.trades,
            "ml_features": self.ml_features,
            "equity_curve": self.equity_curve
        }


def generate_data(symbols: List[str], start_date: str, end_date: str, seed: int = 42) -> Dict[str, pd.DataFrame]:
    """Generate synthetic market data."""
    np.random.seed(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)

    price_data = {}

    for symbol in symbols:
        # Random regime
        regime = np.random.choice(['bull', 'bear', 'sideways', 'volatile'])

        if regime == 'bull':
            drift, vol = 0.001, 0.025
        elif regime == 'bear':
            drift, vol = -0.0005, 0.03
        elif regime == 'volatile':
            drift, vol = 0.0, 0.05
        else:
            drift, vol = 0.0002, 0.02

        returns = np.random.normal(drift, vol, n_days)

        # Mean reversion
        for i in range(20, n_days):
            if returns[i-10:i].sum() > 0.15:
                returns[i] -= 0.015
            elif returns[i-10:i].sum() < -0.15:
                returns[i] += 0.015

        # Starting price
        if symbol in ['BTC', 'ETH']:
            start_price = np.random.uniform(20000, 60000)
        elif symbol in ['SOL', 'AVAX', 'DOT', 'LINK']:
            start_price = np.random.uniform(20, 200)
        else:
            start_price = np.random.uniform(1, 500)

        prices = start_price * np.exp(np.cumsum(returns))
        volumes = np.random.lognormal(10, 0.5, n_days)

        price_data[symbol] = pd.DataFrame({
            'price': prices,
            'volume': volumes
        }, index=dates)

    return price_data


def main():
    """Generate ML training data - MEDIUM SIZE (completes in ~5 min)."""

    logger.info("=" * 60)
    logger.info("GENERATING ML TRAINING DATA (Medium Scale)")
    logger.info("=" * 60)

    # 15 symbols x 4 years = ~22,000 features
    symbols = [
        'BTC', 'ETH', 'SOL', 'ADA', 'DOT',
        'AVAX', 'MATIC', 'LINK', 'UNI', 'AAVE',
        'ATOM', 'ALGO', 'VET', 'FIL', 'ETC'
    ]

    start_date = '2020-01-01'
    end_date = '2023-12-31'

    logger.info(f"Symbols: {len(symbols)}")
    logger.info(f"Date range: {start_date} to {end_date}")
    logger.info("")

    # Generate data
    logger.info("Generating market data...")
    price_data = generate_data(symbols, start_date, end_date)

    # Run backtest
    backtest = MLOptimizedBacktest()
    results = backtest.run_backtest(price_data, start_date, end_date)

    # Save
    output_file = f"backtest_results/ml_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path("backtest_results").mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info("")
    logger.info("=" * 60)
    logger.info("BACKTEST COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total trades: {results['total_trades']}")
    logger.info(f"Win rate: {results['win_rate']:.2%}")
    logger.info(f"Total return: {results['total_return_pct']:.2f}%")
    logger.info(f"ML features: {results['feature_count']:,}")
    logger.info(f"Saved to: {output_file}")

    if results['feature_count'] > 0:
        features_df = pd.DataFrame(results['ml_features'])
        logger.info("\nFeature variance:")
        for col in ['rsi', 'macd', 'bb_position']:
            if col in features_df.columns:
                logger.info(f"  {col}: std={features_df[col].std():.3f}")


if __name__ == "__main__":
    main()
