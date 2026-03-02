"""
Batch Backtest Generator - Genereert 15 aparte datasets

Splits de backtest in kleine delen die snel completeren.
Elk deel is onafhankelijk en kan gebruikt worden voor ML training.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastBacktest:
    """Geoptimaliseerde backtest voor snelle uitvoering."""

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.reset()

    def reset(self):
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.ml_features = []

    def calc_indicators(self, prices: np.ndarray, volumes: np.ndarray) -> Dict:
        """Snelle indicator berekening met NumPy."""
        n = len(prices)

        # Returns
        returns = np.diff(prices) / prices[:-1]

        # RSI (simplified)
        gains = np.where(returns > 0, returns, 0)
        losses = np.where(returns < 0, -returns, 0)

        # Simple moving averages for RSI
        if len(gains) >= 14:
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50.0

        # MACD
        ema12 = pd.Series(prices).ewm(span=12).mean().iloc[-1]
        ema26 = pd.Series(prices).ewm(span=26).mean().iloc[-1]
        macd = ema12 - ema26

        # Bollinger position
        sma20 = np.mean(prices[-20:])
        std20 = np.std(prices[-20:])
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20
        bb_position = (prices[-1] - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

        # Momentum
        mom_1d = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
        mom_3d = (prices[-1] - prices[-4]) / prices[-4] if len(prices) >= 4 else 0

        # Volume
        vol_sma = np.mean(volumes[-10:])
        volume_ratio = volumes[-1] / vol_sma if vol_sma > 0 else 1.0

        # ATR
        atr = np.mean(np.abs(returns[-14:])) * prices[-1] if len(returns) >= 14 else prices[-1] * 0.02
        atr_pct = atr / prices[-1]

        # Trend
        sma10 = np.mean(prices[-10:])
        sma30 = np.mean(prices[-30:]) if len(prices) >= 30 else sma10
        trend = 1 if sma10 > sma30 else -1

        return {
            'rsi': float(rsi),
            'macd': float(macd),
            'macd_hist': float(macd * 0.1),
            'bb_position': float(np.clip(bb_position, 0, 1)),
            'bb_width': float(std20 / sma20) if sma20 > 0 else 0.02,
            'mom_1d': float(mom_1d),
            'mom_3d': float(mom_3d),
            'volume_ratio': float(volume_ratio),
            'atr_pct': float(atr_pct),
            'trend': int(trend)
        }

    def generate_signal(self, ind: Dict) -> tuple:
        """Genereer trading signal."""
        score = 0

        # RSI extremes
        if ind['rsi'] < 30:
            score += 3
        elif ind['rsi'] > 70:
            score -= 3

        # Bollinger
        if ind['bb_position'] < 0.2:
            score += 2
        elif ind['bb_position'] > 0.8:
            score -= 2

        # MACD
        if ind['macd_hist'] < 0 and ind['macd'] < 0:
            score += 1
        elif ind['macd_hist'] > 0 and ind['macd'] > 0:
            score -= 1

        # Volume
        if ind['volume_ratio'] > 1.2:
            score += 1 if score > 0 else -1 if score < 0 else 0

        # Volatility filter
        if ind['atr_pct'] > 0.05:
            score = 0

        action = "HOLD"
        confidence = 0.0

        if score >= 4:
            action = "BUY"
            confidence = min(score / 6, 1.0)
        elif score <= -4:
            action = "SELL"
            confidence = min(abs(score) / 6, 1.0)

        return action, confidence, ind

    def run(self, symbols: List[str], prices_dict: Dict[str, np.ndarray],
            volumes_dict: Dict[str, np.ndarray], dates: pd.DatetimeIndex,
            batch_id: int) -> Dict:
        """Run backtest voor een batch van symbols."""

        logger.info(f"[Batch {batch_id}] Starting: {len(symbols)} symbols x {len(dates)} days")

        for i, date_idx in enumerate(range(len(dates))):
            date = dates[date_idx]

            # Log equity (elke 5e dag voor snelheid)
            if i % 5 == 0:
                total_value = self.cash
                for sym in self.positions:
                    if date_idx < len(prices_dict[sym]):
                        total_value += self.positions[sym]['quantity'] * prices_dict[sym][date_idx]

                self.equity_curve.append({
                    'timestamp': date.isoformat(),
                    'value': total_value,
                    'cash': self.cash
                })

            # Process each symbol
            for symbol in symbols:
                prices = prices_dict[symbol]
                volumes = volumes_dict[symbol]

                if date_idx < 35 or date_idx >= len(prices):
                    continue

                hist_prices = prices[:date_idx+1]
                hist_volumes = volumes[:date_idx+1]
                current_price = prices[date_idx]

                # Calculate indicators
                ind = self.calc_indicators(hist_prices, hist_volumes)

                # Generate signal
                action, confidence, features = self.generate_signal(ind)

                # Log features
                self.ml_features.append({
                    'timestamp': date.isoformat(),
                    'symbol': symbol,
                    'price': float(current_price),
                    'action': action,
                    'confidence': confidence,
                    **features
                })

                # Execute trade
                if action == "BUY" and confidence > 0.6 and symbol not in self.positions:
                    position_value = self.cash * 0.05 * confidence
                    quantity = position_value / current_price
                    cost = quantity * current_price

                    if cost <= self.cash:
                        self.cash -= cost
                        self.positions[symbol] = {
                            'quantity': quantity,
                            'entry_price': current_price,
                            'entry_idx': date_idx,
                            'stop_loss': current_price * 0.98,
                            'take_profit': current_price * 1.04
                        }

                # Check exits
                if symbol in self.positions:
                    pos = self.positions[symbol]

                    if current_price <= pos['stop_loss']:
                        pnl = (current_price - pos['entry_price']) * pos['quantity']
                        self._close_trade(symbol, current_price, date, pnl, "STOP_LOSS", date_idx)
                    elif current_price >= pos['take_profit']:
                        pnl = (current_price - pos['entry_price']) * pos['quantity']
                        self._close_trade(symbol, current_price, date, pnl, "TAKE_PROFIT", date_idx)
                    elif (date_idx - pos['entry_idx']) >= 10:
                        pnl = (current_price - pos['entry_price']) * pos['quantity']
                        self._close_trade(symbol, current_price, date, pnl, "TIME_EXIT", date_idx)

            if (i + 1) % 500 == 0:
                logger.info(f"[Batch {batch_id}] Progress: {i+1}/{len(dates)} days, {len(self.trades)} trades")

        return self._generate_report(batch_id)

    def _close_trade(self, symbol: str, price: float, date: datetime,
                     pnl: float, exit_reason: str, idx: int):
        """Close position."""
        pos = self.positions[symbol]
        self.cash += pos['quantity'] * price

        self.trades.append({
            'symbol': symbol,
            'entry_date': pos.get('entry_date', date.isoformat()),
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

    def _generate_report(self, batch_id: int) -> Dict:
        """Generate report."""
        if not self.trades:
            return {"error": "No trades", "batch_id": batch_id}

        wins = sum(1 for t in self.trades if t['win'] == 1)
        losses = len(self.trades) - wins
        win_rate = wins / len(self.trades) if self.trades else 0

        total_pnl = sum(t['pnl'] for t in self.trades)
        avg_win = sum(t['pnl'] for t in self.trades if t['win'] == 1) / wins if wins > 0 else 0
        avg_loss = sum(t['pnl'] for t in self.trades if t['win'] == 0) / losses if losses > 0 else 0

        return {
            "batch_id": batch_id,
            "backtest_type": "ml_optimized_batch",
            "strategy": "mean_reversion_rsi",
            "total_trades": len(self.trades),
            "winning_trades": wins,
            "losing_trades": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_return_pct": (total_pnl / self.initial_capital) * 100,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(avg_win * wins / (avg_loss * losses)) if losses > 0 and avg_loss != 0 else float('inf'),
            "feature_count": len(self.ml_features),
            "trades": self.trades,
            "ml_features": self.ml_features,
            "equity_curve": self.equity_curve
        }


def generate_market_data(symbol: str, n_days: int, seed: int) -> tuple:
    """Generate synthetic data voor een symbol."""
    np.random.seed(seed)

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
    elif symbol in ['SOL', 'AVAX', 'DOT', 'LINK', 'AAVE']:
        start_price = np.random.uniform(20, 200)
    else:
        start_price = np.random.uniform(1, 500)

    prices = start_price * np.exp(np.cumsum(returns))
    volumes = np.random.lognormal(10, 0.5, n_days)

    return prices, volumes


def run_batch(batch_id: int, symbols: List[str], start_date: str, end_date: str):
    """Run een enkele batch."""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)

    # Generate data voor alle symbols in deze batch
    prices_dict = {}
    volumes_dict = {}

    for symbol in symbols:
        prices, volumes = generate_market_data(symbol, n_days, seed=batch_id * 100 + hash(symbol) % 100)
        prices_dict[symbol] = prices
        volumes_dict[symbol] = volumes

    # Run backtest
    backtest = FastBacktest()
    results = backtest.run(symbols, prices_dict, volumes_dict, dates, batch_id)

    # Save
    output_file = f"backtest_results/ml_batch_{batch_id:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path("backtest_results").mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"[Batch {batch_id}] SAVED: {output_file}")
    logger.info(f"[Batch {batch_id}] Trades: {results['total_trades']}, Win Rate: {results['win_rate']:.1%}, Features: {results['feature_count']}")

    return results


def main():
    """Genereer 15 batches van ML training data."""

    logger.info("=" * 70)
    logger.info("BATCH BACKTEST GENERATOR - 15 Datasets")
    logger.info("=" * 70)

    # Config
    n_batches = 15
    symbols_per_batch = 3
    days_per_batch = 730  # ~2 years

    # All possible symbols
    all_symbols = [
        'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'AAVE',
        'ATOM', 'ALGO', 'VET', 'FIL', 'ETC', 'XLM', 'TRX', 'EOS', 'XTZ', 'NEAR',
        'MANA', 'SAND', 'GRT', 'SNX', 'COMP', 'MKR', 'YFI', 'CRV', '1INCH', 'LRC'
    ]

    # Date ranges voor variatie
    date_ranges = [
        ('2019-01-01', '2020-12-31'),  # Pre-COVID
        ('2020-06-01', '2022-05-31'),  # COVID boom
        ('2021-01-01', '2022-12-31'),  # Bull to bear
        ('2022-06-01', '2024-05-31'),  # Bear market
        ('2023-01-01', '2024-12-31'),  # Recovery
    ]

    logger.info(f"Configuration:")
    logger.info(f"  Batches: {n_batches}")
    logger.info(f"  Symbols per batch: {symbols_per_batch}")
    logger.info(f"  Days per batch: {days_per_batch}")
    logger.info(f"")

    all_results = []

    for batch_id in range(1, n_batches + 1):
        logger.info("")
        logger.info(f"{'='*70}")
        logger.info(f"BATCH {batch_id}/{n_batches}")
        logger.info(f"{'='*70}")

        # Select symbols voor deze batch
        start_idx = (batch_id - 1) * symbols_per_batch % len(all_symbols)
        batch_symbols = all_symbols[start_idx:start_idx + symbols_per_batch]

        # Select date range
        date_range = date_ranges[batch_id % len(date_ranges)]

        logger.info(f"Symbols: {batch_symbols}")
        logger.info(f"Period: {date_range[0]} to {date_range[1]}")

        # Run batch
        try:
            result = run_batch(batch_id, batch_symbols, date_range[0], date_range[1])
            all_results.append(result)
        except Exception as e:
            logger.error(f"[Batch {batch_id}] ERROR: {e}")

        logger.info(f"[Batch {batch_id}] COMPLETE")

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("ALL BATCHES COMPLETE!")
    logger.info("=" * 70)

    total_features = sum(r['feature_count'] for r in all_results if 'feature_count' in r)
    total_trades = sum(r['total_trades'] for r in all_results if 'total_trades' in r)
    avg_win_rate = np.mean([r['win_rate'] for r in all_results if 'win_rate' in r])

    logger.info(f"Total ML features: {total_features:,}")
    logger.info(f"Total trades: {total_trades}")
    logger.info(f"Average win rate: {avg_win_rate:.1%}")
    logger.info(f"")
    logger.info("Files generated:")
    for i in range(1, n_batches + 1):
        files = list(Path("backtest_results").glob(f"ml_batch_{i:02d}_*.json"))
        if files:
            size_mb = files[0].stat().st_size / (1024 * 1024)
            logger.info(f"  Batch {i:2d}: {files[0].name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
