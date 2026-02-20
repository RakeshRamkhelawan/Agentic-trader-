#!/usr/bin/env python3
"""
Live Paper Trading - Production Version with WebSocket Broadcasting

Real-time paper trading that broadcasts all events to the frontend.
This creates a "production-live" experience with paper money.

Usage:
    python scripts/live_paper_trading_production.py --duration 8
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

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from backend.core.config.settings import settings
from backend.services.paper_trading_ws_broadcast import broadcast_trade, broadcast_portfolio, broadcast_stats


@dataclass
class TradingAgent:
    """Trading agent with strategy."""
    name: str
    strategy: str
    risk_level: float = 0.1
    min_confidence: float = 0.6
    trade_count: int = 0
    pnl: float = 0.0
    
    def decide_trade(self, symbol: str, price: float, price_history: List[float]) -> Optional[Dict]:
        """Decide whether to trade."""
        if len(price_history) < 3:
            return None
        
        if self.strategy == 'momentum':
            if price > price_history[-2] > price_history[-3]:
                return {'side': OrderSide.BUY, 'qty': 0.001, 'confidence': 0.7, 'reason': 'uptrend'}
            elif price < price_history[-2] < price_history[-3]:
                return {'side': OrderSide.SELL, 'qty': 0.001, 'confidence': 0.7, 'reason': 'downtrend'}
                
        elif self.strategy == 'mean_reversion':
            avg = sum(price_history[-10:]) / len(price_history[-10:])
            if price < avg * 0.995:
                return {'side': OrderSide.BUY, 'qty': 0.001, 'confidence': 0.65, 'reason': 'below_avg'}
            elif price > avg * 1.005:
                return {'side': OrderSide.SELL, 'qty': 0.001, 'confidence': 0.65, 'reason': 'above_avg'}
                
        elif self.strategy == 'breakout':
            if len(price_history) >= 20:
                high_20 = max(price_history[-20:])
                low_20 = min(price_history[-20:])
                if price > high_20 * 0.998:
                    return {'side': OrderSide.BUY, 'qty': 0.001, 'confidence': 0.75, 'reason': 'breakout_high'}
                elif price < low_20 * 1.002:
                    return {'side': OrderSide.SELL, 'qty': 0.001, 'confidence': 0.75, 'reason': 'breakdown_low'}
        
        return None


class LivePaperTradingProduction:
    """Production-grade live paper trading with WebSocket broadcasting."""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)
        
        # Exchanges
        self.bitvavo = None
        self.revolut = None
        
        # Symbols
        self.symbols = {}
        self.price_history = {}
        self.current_prices = {}
        
        # Agents
        self.agents = [
            TradingAgent("MomentumTrader", "momentum", risk_level=0.12),
            TradingAgent("MeanReversion", "mean_reversion", risk_level=0.08),
            TradingAgent("BreakoutHunter", "breakout", risk_level=0.15),
            TradingAgent("ConservativeMR", "mean_reversion", risk_level=0.05),
            TradingAgent("AggressiveMom", "momentum", risk_level=0.20),
        ]
        
        # Tracking
        self.trades = []
        self.start_time = None
        self.running = False
        self.cycle_count = 0
        
        # Stats
        self.stats = {
            'total_trades': 0,
            'buy_trades': 0,
            'sell_trades': 0,
            'symbols_traded': set(),
            'agents_trades': {agent.name: 0 for agent in self.agents},
        }
        
        print("="*80)
        print("     LIVE PAPER TRADING - PRODUCTION MODE")
        print("="*80)
        print()
        print(f"Initial Capital: EUR {initial_capital:,.2f}")
        print(f"Trading Mode: PAPER (no real money)")
        print(f"Agents: {len(self.agents)}")
        for agent in self.agents:
            print(f"  - {agent.name:20} ({agent.strategy})")
        print()
        print("WebSocket channels:")
        print("  - paper_trading.live")
        print("  - paper_trading.stats")
        print("  - paper_trading.agents")
        print()
        
    async def initialize(self):
        """Initialize exchanges."""
        print("[INIT] Connecting to exchanges...")
        
        # Bitvavo
        try:
            from backend.execution.bitvavo_adapter import BitvavoAdapter
            self.bitvavo = BitvavoAdapter()
            success = await self.bitvavo.initialize()
            if success:
                eur_pairs = self.bitvavo.get_eur_pairs()
                # Select diverse pairs (majors + some alts)
                majors = [p for p in eur_pairs if any(x in p for x in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA'])]
                alts = [p for p in eur_pairs if p not in majors]
                selected = majors[:10] + random.sample(alts, min(20, len(alts)))
                self.symbols['bitvavo'] = selected
                print(f"[OK] Bitvavo: {len(selected)} pairs")
            else:
                self.symbols['bitvavo'] = []
        except Exception as e:
            print(f"[WARN] Bitvavo: {e}")
            self.symbols['bitvavo'] = []
        
        # Revolut X (optional)
        try:
            from backend.integrations.revolut_x_client import RevolutXClient
            self.revolut = RevolutXClient()
            connected = await self.revolut.connect()
            if connected:
                symbols = await self.revolut.get_symbols()
                major_pairs = [s for s in symbols if any(x in s for x in ['BTC', 'ETH', 'SOL'])]
                self.symbols['revolut'] = major_pairs[:10]
                print(f"[OK] Revolut X: {len(major_pairs[:10])} pairs")
            else:
                self.symbols['revolut'] = []
        except Exception as e:
            print(f"[WARN] Revolut X: {e}")
            self.symbols['revolut'] = []
        
        total = sum(len(s) for s in self.symbols.values())
        print(f"[INFO] Total symbols: {total}")
        print()
        
        if total == 0:
            raise RuntimeError("No symbols available")
        
        # Broadcast session start
        await broadcast_stats(0, 0, "0/0", {})  # Session starting
            'capital': self.initial_capital,
            'exchanges': list(self.symbols.keys()),
            'symbols_count': total,
            'agents': [a.name for a in self.agents],
        })
        
    async def fetch_prices(self):
        """Fetch all prices."""
        # Bitvavo
        if self.bitvavo and self.symbols['bitvavo']:
            for symbol in self.symbols['bitvavo']:
                try:
                    ticker = await self.bitvavo.fetch_ticker(symbol)
                    if ticker and ticker.get('last'):
                        price = float(ticker['last'])
                        key = f"bitvavo:{symbol}"
                        self.current_prices[key] = price
                        self.portfolio.update_price(symbol, price)
                        
                        if symbol not in self.price_history:
                            self.price_history[symbol] = []
                        self.price_history[symbol].append(price)
                        if len(self.price_history[symbol]) > 50:
                            self.price_history[symbol].pop(0)
                        
                        # Broadcast price
                        pass  # Price update broadcast
                except:
                    pass
                await asyncio.sleep(0.1)  # Rate limit
        
        # Revolut
        if self.revolut and self.symbols['revolut']:
            for symbol in self.symbols['revolut']:
                try:
                    ticker = await self.revolut.get_ticker(symbol)
                    if ticker and ticker.get('last'):
                        price = float(ticker['last'])
                        key = f"revolut:{symbol}"
                        self.current_prices[key] = price
                        self.portfolio.update_price(symbol, price)
                        
                        if symbol not in self.price_history:
                            self.price_history[symbol] = []
                        self.price_history[symbol].append(price)
                        
                        pass  # Price update broadcast
                except:
                    pass
                await asyncio.sleep(0.1)
    
    async def trading_cycle(self):
        """Execute one trading cycle."""
        self.cycle_count += 1
        
        # Get available symbols
        available = []
        for ex, symbols in self.symbols.items():
            for sym in symbols:
                key = f"{ex}:{sym}"
                if key in self.current_prices and self.current_prices[key] > 0:
                    available.append((ex, sym))
        
        if not available:
            return
        
        # Select symbols for this cycle
        to_trade = random.sample(available, min(3, len(available)))
        
        for exchange, symbol in to_trade:
            key = f"{exchange}:{symbol}"
            price = self.current_prices.get(key, 0)
            history = self.price_history.get(symbol, [])
            
            if price <= 0 or len(history) < 3:
                continue
            
            # Random agent
            agent = random.choice(self.agents)
            decision = agent.decide_trade(symbol, price, history)
            
            if decision and decision['confidence'] >= agent.min_confidence:
                # Broadcast agent decision
                pass  # Agent decision broadcast
                    agent.name,
                    {
                        'symbol': symbol,
                        'side': decision['side'].value,
                        'confidence': decision['confidence'],
                        'reason': decision['reason'],
                        'price': price,
                    }
                )
                
                await self._execute_trade(exchange, symbol, agent, decision, price)
    
    async def _execute_trade(self, exchange: str, symbol: str, agent: TradingAgent, decision: dict, price: float):
        """Execute trade."""
        side = decision['side']
        qty = decision['qty']
        
        # Check balance
        balance = await self.portfolio.get_balance()
        
        if side == OrderSide.BUY:
            cost = qty * price
            if balance.get('EUR', 0) < cost:
                return
        else:
            if balance.get(symbol, 0) < qty:
                return
        
        # Execute
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
            self.trades.append(trade)
            
            # Update stats
            self.stats['total_trades'] += 1
            self.stats['symbols_traded'].add(symbol)
            self.stats['agents_trades'][agent.name] += 1
            agent.trade_count += 1
            
            if side == OrderSide.BUY:
                self.stats['buy_trades'] += 1
            else:
                self.stats['sell_trades'] += 1
            
            # Broadcast trade
            await broadcast_trade(trade)
            
            # Console output
            ts = datetime.now(UTC).strftime("%H:%M:%S")
            print(f"[{ts}] [{agent.name:18}] {side.value:4} {qty:.4f} {symbol:12} @ EUR {price:,.2f}")
    
    async def broadcast_portfolio(self):
        """Broadcast portfolio update."""
        balance = await self.portfolio.get_balance()
        
        # Calculate total value
        total_value = balance.get('EUR', 0)
        for symbol, qty in balance.items():
            if symbol != 'EUR' and qty > 0:
                key = f"bitvavo:{symbol}"
                price = self.current_prices.get(key, 0)
                if price == 0:
                    key = f"revolut:{symbol}"
                    price = self.current_prices.get(key, 0)
                total_value += qty * price
        
        pnl = total_value - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        await broadcast_portfolio(
            cash=balance.get('EUR', 0),
            total_value=total_value,
            pnl=pnl,
            pnl_pct=pnl_pct,
            positions={k: v for k, v in balance.items() if k != 'EUR' and v > 0}
        )
        
        return total_value, pnl, pnl_pct
    
    async def stats_reporter(self, interval: int = 30):
        """Periodic stats report."""
        while self.running:
            await asyncio.sleep(interval)
            
            if not self.running:
                break
            
            elapsed = datetime.now(UTC) - self.start_time if self.start_time else timedelta(0)
            total_value, pnl, pnl_pct = await self.broadcast_portfolio()
            
            # Broadcast stats
            await broadcast_stats(
                total_trades=self.stats['total_trades'],
                symbols_traded=len(self.stats['symbols_traded']),
                buy_sell_ratio=f"{self.stats['buy_trades']}/{self.stats['sell_trades']}",
                agent_performance=self.stats['agents_trades']
            )
            
            # Console output
            print()
            print("-"*80)
            print(f"STATS | {elapsed} | Trades: {self.stats['total_trades']} | P&L: EUR {pnl:+,.2f} ({pnl_pct:+.2f}%)")
            print("-"*80)
    
    async def run(self, duration_hours: int = 8):
        """Run trading session."""
        self.start_time = datetime.now(UTC)
        end_time = self.start_time + timedelta(hours=duration_hours)
        
        self.running = True
        
        print(f"[START] {self.start_time}")
        print(f"[END]   {end_time}")
        print()
        
        # Start stats reporter
        reporter = asyncio.create_task(self.stats_reporter(interval=30))
        
        try:
            while datetime.now(UTC) < end_time and self.running:
                # Fetch prices
                await self.fetch_prices()
                
                # Trading cycle
                await self.trading_cycle()
                
                # Wait
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self.running = False
            reporter.cancel()
            try:
                await reporter
            except asyncio.CancelledError:
                pass
        
        # Final broadcast
        await self.broadcast_portfolio()
        await broadcast_stats(self.stats['total_trades'], len(self.stats['symbols_traded']), f"{self.stats['buy_trades']}/{self.stats['sell_trades']}", self.stats['agents_trades'])
            'total_trades': self.stats['total_trades'],
            'final_pnl': sum(t.get('value', 0) * (1 if t['side'] == 'SELL' else -1) for t in self.trades),
        })
        
        print()
        print("="*80)
        print("     SESSION COMPLETE")
        print("="*80)
    
    async def close(self):
        """Cleanup."""
        if self.bitvavo:
            await self.bitvavo.close()
        if self.revolut:
            await self.revolut.disconnect()
    
    def save(self):
        """Save session."""
        data = {
            'session': {
                'start': self.start_time.isoformat() if self.start_time else None,
                'capital': self.initial_capital,
                'exchanges': list(self.symbols.keys()),
            },
            'stats': self.stats,
            'trades': self.trades,
        }
        
        filename = f"live_paper_session_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"[SAVE] {filename}")
        return filename


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=8)
    parser.add_argument("--capital", type=float, default=10000.0)
    args = parser.parse_args()
    
    if settings.TRADING_MODE != "paper":
        print("[WARNING] TRADING_MODE != 'paper'")
        if input("Continue? (yes/no): ").lower() != "yes":
            return
    
    trader = LivePaperTradingProduction(initial_capital=args.capital)
    
    try:
        await trader.initialize()
        await trader.run(duration_hours=args.duration)
    except KeyboardInterrupt:
        print("\n[INTERRUPT]")
    finally:
        await trader.close()
        filename = trader.save()
        
        # Import to DB
        print("[IMPORT] To database...")
        import subprocess
        subprocess.run(["python", "scripts/import_ultimate_trades.py", filename], 
                      capture_output=True)
        
        # Summary
        print()
        print("FINAL SUMMARY")
        print(f"Total Trades: {trader.stats['total_trades']}")
        print(f"Symbols: {len(trader.stats['symbols_traded'])}")
        print("Agent Performance:")
        for name, count in trader.stats['agents_trades'].items():
            print(f"  {name}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
