"""
Backtest specifiek ontworpen om ML training data te genereren.

Strategy:
- Gebruik alleen HIGH-CONFIDENCE setups
- Strict filters (alleen traden als meerdere indicators align)
- Focus op QUALITY over quantity
- Genereer duidelijke features met echte predictive waarde
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLBacktestStrategy:
    """
    Strategie geoptimaliseerd voor ML training data.

    Vereisten voor trade:
    1. Trend alignment (meerdere timeframes)
    2. Volume confirmation
    3. Risk/reward > 1:2
    4. Geen tegenliggende signals
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)
        self.trades = []
        self.equity_curve = []
        self.features_log = []  # Detailed feature logging voor ML

    def calculate_features(self, prices: pd.Series, volumes: pd.Series) -> dict:
        """
        Bereken features die DAADWERKELIJK predictive zijn.
        """
        features = {}

        # Returns
        returns = prices.pct_change()

        # Trend (multiple timeframes)
        features['trend_5d'] = (prices.iloc[-1] / prices.iloc[-5] - 1) if len(prices) >= 5 else 0
        features['trend_10d'] = (prices.iloc[-1] / prices.iloc[-10] - 1) if len(prices) >= 10 else 0
        features['trend_20d'] = (prices.iloc[-1] / prices.iloc[-20] - 1) if len(prices) >= 20 else 0

        # Volatility regime
        features['volatility'] = returns.rolling(10).std().iloc[-1] if len(returns) >= 10 else 0
        features['volatility_pct'] = features['volatility'] / abs(returns.mean()) if returns.mean() != 0 else 0

        # Momentum
        features['momentum'] = returns.rolling(5).sum().iloc[-1] if len(returns) >= 5 else 0

        # RSI (manually calculated for speed)
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = (100 - (100 / (1 + rs))).iloc[-1] if not rs.empty else 50

        # Volume features
        if len(volumes) >= 10:
            features['volume_ratio'] = volumes.iloc[-1] / volumes.rolling(10).mean().iloc[-1]
        else:
            features['volume_ratio'] = 1.0

        # Bollinger position
        if len(prices) >= 20:
            sma = prices.rolling(20).mean().iloc[-1]
            std = prices.rolling(20).std().iloc[-1]
            features['bb_position'] = (prices.iloc[-1] - (sma - 2*std)) / (4*std) if std > 0 else 0.5
        else:
            features['bb_position'] = 0.5

        return features

    def should_trade(self, features: dict, symbol: str, current_price: float) -> tuple:
        """
        STRICT criteria voor ML-worthy trades.

        Returns: (should_trade: bool, direction: str, confidence: float)
        """
        score = 0
        reasons = []

        # 1. Trend alignment (meerdere timeframes moeten eensgezind zijn)
        if features['trend_5d'] > 0.02 and features['trend_10d'] > 0.01:
            score += 2
            reasons.append("uptrend_aligned")
        elif features['trend_5d'] < -0.02 and features['trend_10d'] < -0.01:
            score -= 2
            reasons.append("downtrend_aligned")

        # 2. RSI niet extreem (niet kopen als overbought)
        if features['rsi'] < 70:  # Not overbought
            score += 1
        if features['rsi'] > 30:  # Not oversold
            score -= 1

        # 3. Volume confirmation
        if features['volume_ratio'] > 1.5:  # High volume
            score += 1
            reasons.append("high_volume")

        # 4. Volatility niet te hoog (avoid chop)
        if features['volatility_pct'] < 2.0:  # Reasonable vol
            score += 1
            reasons.append("normal_volatility")

        # 5. Bollinger bands (mean reversion of trend following)
        if features['bb_position'] < 0.3:  # Near lower band = buy opportunity
            score += 1
            reasons.append("near_lower_band")
        elif features['bb_position'] > 0.7:  # Near upper band = sell opportunity
            score -= 1
            reasons.append("near_upper_band")

        # Decision
        if score >= 3:
            return True, "BUY", min(score / 5, 1.0)
        elif score <= -3:
            return True, "SELL", min(abs(score) / 5, 1.0)
        else:
            return False, "HOLD", 0.0

    async def run_backtest(
        self,
        price_data: dict,  # {symbol: DataFrame with price, volume}
        start_date: str,
        end_date: str
    ):
        """Run backtest met ML logging."""

        logger.info(f"Starting ML backtest from {start_date} to {end_date}")

        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        for date in dates:
            # Log daily equity
            portfolio_value = await self._calculate_portfolio_value(price_data, date)
            self.equity_curve.append({
                'timestamp': date.isoformat(),
                'value': portfolio_value
            })

            # Analyze each symbol
            for symbol, df in price_data.items():
                # Get data up to current date
                mask = df.index <= date
                hist = df[mask]

                if len(hist) < 30:  # Need enough history
                    continue

                current_price = hist['close'].iloc[-1]

                # Calculate features
                features = self.calculate_features(hist['close'], hist['volume'])

                # Check if we should trade
                should_trade, direction, confidence = self.should_trade(
                    features, symbol, current_price
                )

                # Log ALL features (voor ML training)
                feature_record = {
                    'timestamp': date.isoformat(),
                    'symbol': symbol,
                    'price': current_price,
                    **features,
                    'signal': direction,
                    'confidence': confidence
                }
                self.features_log.append(feature_record)

                # Execute trade if high confidence
                if should_trade and confidence > 0.6:
                    await self._execute_trade(
                        symbol, direction, current_price, features, confidence, date
                    )

        logger.info(f"Backtest complete. Trades: {len(self.trades)}")
        logger.info(f"Feature records: {len(self.features_log)}")

        return self._generate_report()

    async def _execute_trade(self, symbol, direction, price, features, confidence, date):
        """Execute and log trade."""
        side = OrderSide.BUY if direction == "BUY" else OrderSide.SELL

        # Position sizing based on confidence
        size = 0.1 * confidence  # Max 10% per trade, scaled by confidence

        order = OrderRequest(
            symbol=symbol,
            side=side,
            qty=size,
            order_type=OrderType.MARKET,
            client_order_id=f"ml_{date.strftime('%Y%m%d')}_{symbol}"
        )

        result = await self.portfolio.submit_order(order)

        if result.status.value == 'FILLED':
            self.trades.append({
                'timestamp': date.isoformat(),
                'symbol': symbol,
                'action': direction,
                'price': price,
                'size': size,
                'confidence': confidence,
                **features
            })

    async def _calculate_portfolio_value(self, price_data, date):
        """Calculate total portfolio value."""
        cash = (await self.portfolio.get_balance()).get('cash', 0)

        positions = await self.portfolio.get_positions()
        position_value = 0

        for symbol, pos in positions.items():
            if symbol in price_data:
                current_price = price_data[symbol].loc[
                    price_data[symbol].index <= date, 'close'
                ].iloc[-1]
                position_value += pos.get('quantity', 0) * current_price

        return cash + position_value

    def _generate_report(self):
        """Generate backtest report."""
        if not self.trades:
            return {"error": "No trades executed"}

        df = pd.DataFrame(self.trades)

        # Calculate P&L (simplified - assumes we can close at last known price)
        # In reality you'd need exit prices

        return {
            "total_trades": len(df),
            "buy_trades": len(df[df['action'] == 'BUY']),
            "sell_trades": len(df[df['action'] == 'SELL']),
            "avg_confidence": df['confidence'].mean(),
            "feature_records": len(self.features_log),
            "trades": self.trades,
            "features": self.features_log,
            "equity_curve": self.equity_curve
        }


async def main():
    """Generate ML training data."""

    # Load historical price data (from your existing backtests or fetch new)
    # For now, we'll use synthetic data structure

    logger.info("Generating ML-optimized backtest...")

    strategy = MLBacktestStrategy(initial_capital=100000.0)

    # TODO: Load actual price data
    # This would connect to your existing data sources

    logger.info("Saving results...")

    output = {
        "backtest_type": "ml_optimized",
        "timestamp": datetime.now().isoformat(),
        # Results would go here
    }

    output_file = f"backtest_results/ml_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
