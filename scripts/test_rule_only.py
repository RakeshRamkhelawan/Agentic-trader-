#!/usr/bin/env python3
"""60-day rule-only backtest (no LLM) for comparison"""

import asyncio
import sys
sys.path.insert(0, '/app')

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from scripts.smart_consciousness_agents import RuleBasedSignals


class RuleOnlyBacktest:
    """Pure rule-based backtest without any LLM calls"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.equity_curve: List[Dict] = []
        self.trades: List[Dict] = []
        self.signals_generated = 0
        
    async def run(self, data: Dict[str, pd.DataFrame], days: int = 60) -> Dict:
        """Run rule-only backtest"""
        logger.info("=" * 70)
        logger.info("📊 RULE-ONLY BACKTEST (No LLM)")
        logger.info("=" * 70)
        logger.info(f"Symbols: {', '.join(data.keys())}")
        logger.info(f"Period: {days} days")
        logger.info(f"Capital: €{self.initial_capital:,.2f}")
        logger.info("-" * 70)
        
        # Align data
        aligned = self._align_data(data, days)
        if not aligned:
            return {"error": "No data"}
        
        dates = aligned[list(aligned.keys())[0]].index
        
        # Run simulation
        for i, date in enumerate(dates):
            progress = (i / len(dates)) * 100
            
            if i % 10 == 0:
                equity = self._calculate_equity(aligned, date)
                logger.info(f"  {progress:5.1f}% | {date.strftime('%Y-%m-%d')} | "
                           f"Equity: €{equity:>12,.2f} | Signals: {self.signals_generated}")
            
            for symbol in aligned.keys():
                df = aligned[symbol]
                df_slice = df.loc[:date]
                
                if len(df_slice) < 20:
                    continue
                
                # Generate rule-based signals (no API call!)
                signals = RuleBasedSignals.generate(df_slice)
                self.signals_generated += 1
                
                composite = signals.get('composite_signal', {})
                action = composite.get('signal', 'HOLD')
                confidence = composite.get('strength', 0.5)
                
                current = df_slice.iloc[-1]
                price = float(current['close'])
                
                # Execute
                await self._execute(action, symbol, price, date, confidence, signals)
            
            equity = self._calculate_equity(aligned, date)
            self.equity_curve.append({
                "date": date,
                "equity": equity,
                "cash": self.cash,
                "positions": len(self.positions)
            })
        
        return self._generate_results(aligned)
    
    def _align_data(self, data: Dict, days: int) -> Dict:
        aligned = {}
        for symbol, df in data.items():
            if df is None or df.empty:
                continue
            df = df.copy()
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            if len(df) > days:
                df = df.iloc[-days:].copy()
            aligned[symbol] = df
        return aligned
    
    async def _execute(self, action: str, symbol: str, price: float, 
                      date: datetime, confidence: float, signals: Dict):
        """Execute trading decision"""
        
        if confidence < 0.3:
            return
        
        # BUY
        if action == "BUY" and symbol not in self.positions:
            position_value = self.cash * 0.15 * confidence  # Fixed 15% size
            
            if position_value > 100:
                quantity = position_value / price
                self.positions[symbol] = {
                    "entry_date": date,
                    "entry_price": price,
                    "quantity": quantity,
                    "value": position_value
                }
                self.cash -= position_value
                logger.info(f"    📥 BUY {symbol} @ €{price:,.2f} (conf: {confidence:.2f})")
                
                self.trades.append({
                    "date": date,
                    "symbol": symbol,
                    "action": "BUY",
                    "price": price,
                    "quantity": quantity,
                    "value": position_value
                })
        
        # SELL with stop loss logic
        elif symbol in self.positions:
            position = self.positions[symbol]
            entry_price = position["entry_price"]
            pnl_pct = (price - entry_price) / entry_price
            
            # Stop loss at -8% or take profit at +15%
            should_sell = action == "SELL" or pnl_pct <= -0.08 or pnl_pct >= 0.15
            
            if should_sell:
                quantity = position["quantity"]
                sale_value = quantity * price
                pnl = sale_value - position["value"]
                
                self.cash += sale_value
                logger.info(f"    📤 SELL {symbol} @ €{price:,.2f} "
                           f"(P&L: €{pnl:,.2f}, {pnl_pct*100:+.2f}%)")
                
                self.trades.append({
                    "date": date,
                    "symbol": symbol,
                    "action": "SELL",
                    "price": price,
                    "quantity": quantity,
                    "value": sale_value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct * 100
                })
                
                del self.positions[symbol]
    
    def _calculate_equity(self, data: Dict, date: datetime) -> float:
        equity = self.cash
        for symbol, pos in self.positions.items():
            if symbol in data and date in data[symbol].index:
                price = data[symbol].loc[date, 'close']
                equity += pos["quantity"] * price
        return equity
    
    def _generate_results(self, data: Dict) -> Dict:
        if not self.equity_curve:
            return {"error": "No data"}
        
        equity_df = pd.DataFrame(self.equity_curve)
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        equity_df['daily_return'] = equity_df['equity'].pct_change()
        volatility = equity_df['daily_return'].std() * np.sqrt(365) * 100
        sharpe = (equity_df['daily_return'].mean() / equity_df['daily_return'].std()) * np.sqrt(365) if equity_df['daily_return'].std() > 0 else 0
        
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_dd = equity_df['drawdown'].min() * 100
        
        closed = [t for t in self.trades if t['action'] == 'SELL']
        winners = [t for t in closed if t.get('pnl', 0) > 0]
        win_rate = len(winners) / len(closed) * 100 if closed else 0
        
        return {
            "backtest_type": "RULE_ONLY",
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_return_pct": total_return,
            "cagr_pct": ((final_equity / self.initial_capital) ** (365 / len(equity_df)) - 1) * 100 if len(equity_df) > 0 else 0,
            "volatility_pct": volatility,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd,
            "total_trades": len(closed),
            "win_rate": win_rate,
            "signals_generated": self.signals_generated,
            "equity_curve": self.equity_curve,
            "trades": self.trades
        }


async def main():
    data_dir = Path("/app/data/historical_6year")
    data = {}
    
    for sym in ['BTC-EUR', 'ETH-EUR']:
        df = pd.read_pickle(data_dir / f'{sym}_1d_2020-2026_binance.pkl')
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        data[sym] = df
        print(f'Loaded {sym}: {len(df)} rows')
    
    engine = RuleOnlyBacktest(100000)
    print('\nRunning 60-day RULE-ONLY test...')
    results = await engine.run(data, days=60)
    
    print('\n' + '='*50)
    print('📊 RULE-ONLY RESULTS')
    print('='*50)
    print(f"Return: {results['total_return_pct']:+.2f}%")
    print(f"Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Sharpe: {results['sharpe_ratio']:.2f}")
    print(f"Max DD: {results['max_drawdown_pct']:.2f}%")
    print(f"Signals Generated: {results['signals_generated']}")

if __name__ == "__main__":
    asyncio.run(main())
