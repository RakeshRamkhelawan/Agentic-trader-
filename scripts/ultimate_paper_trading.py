#!/usr/bin/env python3
"""
Ultimate Multi-Exchange Paper Trading System

Features:
- All symbols from Bitvavo AND Revolut X
- €10,000 starting capital
- 8-hour continuous trading
- Multiple trading agents
- Real market data from both exchanges

Usage:
    python scripts/ultimate_paper_trading.py --duration 8
"""

import asyncio
import argparse
import json
import os
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from backend.core.config.settings import settings


@dataclass
class TradingAgent:
    """Simple trading agent with strategy."""
    name: str
    strategy: str  # 'momentum', 'mean_reversion', 'random'
    risk_level: float = 0.1  # 10% of portfolio per trade
    min_confidence: float = 0.6
    
    def decide_trade(self, symbol: str, price: float, price_history: List[float]) -> Optional[Dict]:
        """Decide whether to trade based on strategy."""
        if len(price_history) < 3:
            return None
        
        if self.strategy == 'momentum':
            # Buy if price going up, sell if going down
            if price > price_history[-2] > price_history[-3]:
                return {'side': OrderSide.BUY, 'qty': 0.001, 'confidence': 0.7}
            elif price < price_history[-2] < price_history[-3]:
                return {'side': OrderSide.SELL, 'qty': 0.001, 'confidence': 0.7}
                
        elif self.strategy == 'mean_reversion':
            # Buy if price below average, sell if above
            avg = sum(price_history[-10:]) / len(price_history[-10:])
            if price < avg * 0.99:
                return {'side': OrderSide.BUY, 'qty': 0.001, 'confidence': 0.65}
            elif price > avg * 1.01:
                return {'side': OrderSide.SELL, 'qty': 0.001, 'confidence': 0.65}
                
        elif self.strategy == 'random':
            if random.random() > 0.7:
                side = OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
                return {'side': side, 'qty': 0.001, 'confidence': 0.6}
        
        return None


class MultiExchangePaperTrading:
    """Ultimate paper trading across multiple exchanges."""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)
        
        # Exchange connections
        self.bitvavo = None
        self.revolut = None
        
        # Symbol management
        self.symbols = {}  # exchange -> list of symbols
        self.price_history = {}  # symbol -> list of prices
        self.current_prices = {}  # symbol -> current price
        
        # Trading agents
        self.agents = [
            TradingAgent("MomentumAgent", "momentum", risk_level=0.1),
            TradingAgent("MeanRevAgent", "mean_reversion", risk_level=0.08),
            TradingAgent("RandomAgent", "random", risk_level=0.05),
            TradingAgent("AggressiveMomentum", "momentum", risk_level=0.15),
        ]
        
        # Tracking
        self.trades_executed = []
        self.start_time = None
        self.running = False
        
        # Statistics
        self.stats = {
            'total_trades': 0,
            'buy_trades': 0,
            'sell_trades': 0,
            'symbols_traded': set(),
            'agents_trades': {},
        }
        
        print("="*80)
        print("     ULTIMATE MULTI-EXCHANGE PAPER TRADING SYSTEM")
        print("="*80)
        print()
        print(f"Initial Capital: EUR {initial_capital:,.2f}")
        print(f"Trading Agents: {len(self.agents)}")
        for agent in self.agents:
            print(f"  - {agent.name} ({agent.strategy})")
        print()
        
    async def initialize_exchanges(self):
        """Initialize both exchange connections."""
        print("[INIT] Connecting to exchanges...")
        
        # Bitvavo
        try:
            from backend.execution.bitvavo_adapter import BitvavoAdapter
            self.bitvavo = BitvavoAdapter()
            success = await self.bitvavo.initialize()
            if success:
                # Get all EUR pairs
                eur_pairs = self.bitvavo.get_eur_pairs()
                # Select top pairs by volume (simulate with random selection for now)
                selected = random.sample(eur_pairs, min(50, len(eur_pairs)))
                self.symbols['bitvavo'] = selected
                print(f"[OK] Bitvavo: {len(selected)} pairs")
            else:
                print("[WARN] Bitvavo connection failed")
                self.symbols['bitvavo'] = []
        except Exception as e:
            print(f"[ERROR] Bitvavo: {e}")
            self.symbols['bitvavo'] = []
        
        # Revolut X
        try:
            from backend.integrations.revolut_x_client import RevolutXClient
            self.revolut = RevolutXClient()
            connected = await self.revolut.connect()
            if connected:
                # Get available symbols
                symbols = await self.revolut.get_symbols()
                # Filter for major pairs
                major_pairs = [s for s in symbols if any(x in s for x in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA'])]
                self.symbols['revolut'] = major_pairs[:30]  # Top 30
                print(f"[OK] Revolut X: {len(major_pairs[:30])} pairs")
            else:
                print("[WARN] Revolut X connection failed")
                self.symbols['revolut'] = []
        except Exception as e:
            print(f"[ERROR] Revolut X: {e}")
            self.symbols['revolut'] = []
        
        total_symbols = len(self.symbols['bitvavo']) + len(self.symbols['revolut'])
        print(f"[INFO] Total symbols to trade: {total_symbols}")
        print()
        
        if total_symbols == 0:
            raise RuntimeError("No symbols available from any exchange")
    
    async def fetch_all_prices(self):
        """Fetch prices for all symbols from both exchanges."""
        tasks = []
        
        # Bitvavo prices
        if self.bitvavo and self.symbols['bitvavo']:
            for symbol in self.symbols['bitvavo'][:20]:  # Limit to 20 for performance
                tasks.append(self._fetch_bitvavo_price(symbol))
        
        # Revolut X prices
        if self.revolut and self.symbols['revolut']:
            for symbol in self.symbols['revolut'][:20]:  # Limit to 20 for performance
                tasks.append(self._fetch_revolut_price(symbol))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_bitvavo_price(self, symbol: str):
        """Fetch price from Bitvavo."""
        try:
            ticker = await self.bitvavo.fetch_ticker(symbol)
            if ticker:
                price = ticker.get('last', 0)
                self.current_prices[f"bitvavo:{symbol}"] = price
                self.portfolio.update_price(symbol, price)
                
                # Update price history
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                self.price_history[symbol].append(price)
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol].pop(0)
        except Exception as e:
            pass  # Silently ignore failures
    
    async def _fetch_revolut_price(self, symbol: str):
        """Fetch price from Revolut X."""
        try:
            ticker = await self.revolut.get_ticker(symbol)
            if ticker:
                price = ticker.get('last', 0)
                self.current_prices[f"revolut:{symbol}"] = price
                self.portfolio.update_price(symbol, price)
                
                # Update price history
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                self.price_history[symbol].append(price)
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol].pop(0)
        except Exception as e:
            pass  # Silently ignore failures
    
    async def run_trading_cycle(self):
        """Run one trading cycle."""
        # Get all available symbols with prices
        available_symbols = []
        for exchange, symbols in self.symbols.items():
            for symbol in symbols:
                key = f"{exchange}:{symbol}"
                if key in self.current_prices and self.current_prices[key] > 0:
                    available_symbols.append((exchange, symbol))
        
        if not available_symbols:
            return
        
        # Randomly select symbols to trade this cycle
        symbols_to_trade = random.sample(available_symbols, min(5, len(available_symbols)))
        
        for exchange, symbol in symbols_to_trade:
            key = f"{exchange}:{symbol}"
            price = self.current_prices.get(key, 0)
            
            if price <= 0:
                continue
            
            # Get price history
            history = self.price_history.get(symbol, [])
            
            # Randomly assign an agent
            agent = random.choice(self.agents)
            
            # Agent decides
            decision = agent.decide_trade(symbol, price, history)
            
            if decision and decision['confidence'] >= agent.min_confidence:
                await self._execute_trade(
                    exchange=exchange,
                    symbol=symbol,
                    agent=agent,
                    decision=decision,
                    price=price
                )
    
    async def _execute_trade(self, exchange: str, symbol: str, agent: TradingAgent, decision: dict, price: float):
        """Execute a paper trade."""
        side = decision['side']
        qty = decision['qty']
        
        # Check balance constraints
        balance = await self.portfolio.get_balance()
        
        if side == OrderSide.BUY:
            cost = qty * price
            if balance.get('EUR', 0) < cost:
                return  # Insufficient funds
        else:
            if balance.get(symbol, 0) < qty:
                return  # Insufficient position
        
        # Execute trade
        order = OrderRequest(
            symbol=symbol,
            side=side,
            qty=qty,
            order_type=OrderType.MARKET,
            client_order_id=uuid.uuid4()
        )
        
        result = await self.portfolio.submit_order(order)
        
        if result.status.value == 'FILLED':
            trade = {
                'timestamp': datetime.now(UTC).isoformat(),
                'exchange': exchange,
                'symbol': symbol,
                'agent': agent.name,
                'strategy': agent.strategy,
                'side': side.value,
                'qty': qty,
                'price': price,
                'value': qty * price,
                'order_id': str(result.order_id),
            }
            self.trades_executed.append(trade)
            
            # Update stats
            self.stats['total_trades'] += 1
            self.stats['symbols_traded'].add(symbol)
            if agent.name not in self.stats['agents_trades']:
                self.stats['agents_trades'][agent.name] = 0
            self.stats['agents_trades'][agent.name] += 1
            
            if side == OrderSide.BUY:
                self.stats['buy_trades'] += 1
            else:
                self.stats['sell_trades'] += 1
            
            # Print trade
            timestamp = datetime.now(UTC).strftime("%H:%M:%S")
            print(f"[{timestamp}] [{agent.name:20}] {side.value:4} {qty:.6f} {symbol:12} @ EUR {price:,.2f}")
    
    async def status_reporter(self, interval: int = 60):
        """Periodic status report."""
        while self.running:
            await asyncio.sleep(interval)
            
            if not self.running:
                break
            
            elapsed = datetime.now(UTC) - self.start_time
            balance = await self.portfolio.get_balance()
            
            # Calculate portfolio value
            total_value = balance.get('EUR', 0)
            for symbol, qty in balance.items():
                if symbol != 'EUR' and symbol in self.current_prices:
                    total_value += qty * self.current_prices[symbol]
            
            pnl = total_value - self.initial_capital
            pnl_pct = (pnl / self.initial_capital) * 100
            
            print()
            print("-"*80)
            print(f"STATUS REPORT | Elapsed: {elapsed} | Trades: {self.stats['total_trades']}")
            print("-"*80)
            print(f"  Cash: EUR {balance.get('EUR', 0):,.2f}")
            print(f"  Portfolio Value: EUR {total_value:,.2f}")
            print(f"  P&L: EUR {pnl:+,.2f} ({pnl_pct:+.2f}%)")
            print(f"  Symbols Traded: {len(self.stats['symbols_traded'])}")
            print(f"  Buy/Sell: {self.stats['buy_trades']}/{self.stats['sell_trades']}")
            print()
    
    async def run(self, duration_hours: int = 8):
        """Run the trading system for specified duration."""
        self.start_time = datetime.now(UTC)
        end_time = self.start_time + timedelta(hours=duration_hours)
        
        self.running = True
        
        print(f"[START] Trading session started at {self.start_time}")
        print(f"[INFO] Will run until {end_time} ({duration_hours} hours)")
        print()
        
        # Start status reporter
        reporter_task = asyncio.create_task(self.status_reporter(interval=60))
        
        try:
            while datetime.now(UTC) < end_time and self.running:
                # Fetch all prices
                await self.fetch_all_prices()
                
                # Run trading cycle
                await self.run_trading_cycle()
                
                # Wait before next cycle
                await asyncio.sleep(10)  # 10 second intervals
                
        except asyncio.CancelledError:
            print("[INFO] Trading cancelled")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self.running = False
            reporter_task.cancel()
            try:
                await reporter_task
            except asyncio.CancelledError:
                pass
        
        print()
        print("="*80)
        print("     TRADING SESSION COMPLETE")
        print("="*80)
    
    async def close(self):
        """Cleanup connections."""
        if self.bitvavo:
            await self.bitvavo.close()
        if self.revolut:
            await self.revolut.disconnect()
    
    def save_session(self):
        """Save trading session to file."""
        session_data = {
            'session_info': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': datetime.now(UTC).isoformat(),
                'initial_capital': self.initial_capital,
                'final_balance': asyncio.run(self.portfolio.get_balance()),
                'exchanges': list(self.symbols.keys()),
                'total_symbols': sum(len(s) for s in self.symbols.values()),
            },
            'statistics': {
                'total_trades': self.stats['total_trades'],
                'buy_trades': self.stats['buy_trades'],
                'sell_trades': self.stats['sell_trades'],
                'unique_symbols': len(self.stats['symbols_traded']),
                'agents_performance': self.stats['agents_trades'],
            },
            'trades': self.trades_executed,
        }
        
        filename = f"ultimate_paper_session_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        print(f"[SAVE] Session saved to: {filename}")
        return filename


async def main():
    parser = argparse.ArgumentParser(description="Ultimate Multi-Exchange Paper Trading")
    parser.add_argument("--duration", type=int, default=8, help="Trading duration in hours")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital")
    
    args = parser.parse_args()
    
    # Check trading mode
    if settings.TRADING_MODE != "paper":
        print("[WARNING] TRADING_MODE is not 'paper'!")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            return
    
    trader = MultiExchangePaperTrading(initial_capital=args.capital)
    
    try:
        await trader.initialize_exchanges()
        await trader.run(duration_hours=args.duration)
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Stopping trading...")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        await trader.close()
        
        # Save and import
        filename = trader.save_session()
        
        # Import to database
        print("[IMPORT] Importing to database...")
        import subprocess
        result = subprocess.run(
            ["python", "scripts/import_ultimate_trades.py", filename],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[OK] Trades imported")
        else:
            print(f"[WARN] Import issue: {result.stderr}")
        
        # Final summary
        print()
        print("="*80)
        print("     FINAL SUMMARY")
        print("="*80)
        print(f"Total Trades: {trader.stats['total_trades']}")
        print(f"Symbols Traded: {len(trader.stats['symbols_traded'])}")
        print(f"Buy/Sell Ratio: {trader.stats['buy_trades']}/{trader.stats['sell_trades']}")
        print()
        print("Agent Performance:")
        for agent, count in trader.stats['agents_trades'].items():
            print(f"  {agent}: {count} trades")


if __name__ == "__main__":
    asyncio.run(main())
