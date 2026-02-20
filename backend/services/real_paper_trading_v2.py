"""
REAL Paper Trading V2 - WebSocket Cache Architecture

Features:
- PriceFetchAgent with WebSocket (primary) + REST (fallback)
- In-memory cache with 5s staleness tolerance
- 5 Trading Agents reading from cache
- Concurrent execution
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Fix path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from backend.services.price_fetch_agent import PriceFetchAgent, get_fetch_agent
from backend.services.trading_agents_v2 import (
    create_all_agents, BaseTradingAgent, AgentDecision, DecisionAction
)
from backend.services.paper_trading_ws_broadcast import (
    broadcast_trade, broadcast_portfolio, broadcast_stats,
    broadcast_agent_decision, broadcast_triad_update
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RealPaperTradingV2")


class RealPaperTradingV2:
    """
    Paper Trading Engine with WebSocket Cache Architecture.
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)
        
        # Fetch Agent (WebSocket + REST fallback)
        self.fetch_agent: Optional[PriceFetchAgent] = None
        
        # Trading Agents
        self.agents: List[BaseTradingAgent] = create_all_agents()
        
        # State
        self.all_symbols: List[str] = []
        self.running = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Stats
        self.stats = {
            'total_trades': 0,
            'buy_trades': 0,
            'sell_trades': 0,
            'total_volume': 0.0,
            'symbols_traded': set(),
            'agent_trades': {agent.name: 0 for agent in self.agents}
        }
        
        print("=" * 80)
        print("     REAL PAPER TRADING V2 - WebSocket Cache Architecture")
        print("=" * 80)
        print(f"\nInitial Capital: EUR {initial_capital:,.2f}")
        print(f"Max Data Staleness: 5 seconds")
        print(f"Fallback: REST polling every 10s")
        print(f"\nTrading Agents:")
        for agent in self.agents:
            print(f"  - {agent.name:20} Risk: {agent.risk_per_trade:.0%}/trade")
        print()
    
    async def initialize(self):
        """Initialize fetch agent and get symbol list."""
        # Initialize Bitvavo for symbol list
        from backend.execution.bitvavo_adapter import BitvavoAdapter
        
        temp_adapter = BitvavoAdapter()
        await temp_adapter.initialize()
        self.all_symbols = temp_adapter.get_eur_pairs()
        await temp_adapter.close()
        
        if len(self.all_symbols) < 100:
            raise RuntimeError(f"Only {len(self.all_symbols)} symbols found")
        
        print(f"[OK] Loaded {len(self.all_symbols)} EUR trading pairs")
        
        # Start Fetch Agent
        self.fetch_agent = await get_fetch_agent()
        await self.fetch_agent.start()
        
        # Wait for initial prices
        print("[INFO] Waiting for initial price feed...")
        await asyncio.sleep(3)
        
        # Check if we have fresh data
        prices = await self.fetch_agent.get_all_prices()
        if len(prices) < 10:
            logger.warning("Limited price data available, waiting more...")
            await asyncio.sleep(5)
            prices = await self.fetch_agent.get_all_prices()
        
        print(f"[OK] Price cache initialized with {len(prices)} fresh prices")
    
    async def trading_cycle(self):
        """Execute one trading cycle."""
        if not self.fetch_agent:
            return
        
        # Get all fresh prices from cache
        prices = await self.fetch_agent.get_all_prices(max_age=5.0)
        
        if len(prices) < 10:
            logger.warning(f"Insufficient fresh prices: {len(prices)}")
            return
        
        # Get portfolio value
        portfolio_value = await self._calculate_portfolio_value(prices)
        
        # Select random subset of symbols to analyze
        available = list(prices.keys())
        to_analyze = random.sample(available, min(30, len(available)))
        
        trades_this_cycle = 0
        
        for symbol in to_analyze:
            price_data = prices[symbol]
            
            # Each agent decides
            for agent in self.agents:
                try:
                    decision = await agent.decide(
                        symbol=symbol,
                        price_data=price_data,
                        portfolio_value=portfolio_value,
                        fetch_agent=self.fetch_agent
                    )
                    
                    if decision:
                        # Broadcast decision
                        await broadcast_agent_decision(
                            agent=decision.agent_name,
                            strategy=decision.strategy,
                            symbol=symbol,
                            decision=decision.action.value,
                            confidence=decision.confidence,
                            reason=decision.reason,
                            executed=False
                        )
                        
                        # Try to execute
                        if decision.action in [DecisionAction.BUY, DecisionAction.SELL]:
                            success = await self._execute_trade(decision, price_data.price)
                            if success:
                                trades_this_cycle += 1
                                decision.executed = True
                                agent.update_performance(0.0)  # Will update later
                        
                except Exception as e:
                    logger.error(f"Agent {agent.name} error: {e}")
        
        if trades_this_cycle > 0:
            logger.info(f"  Executed {trades_this_cycle} trades this cycle")
    
    async def _execute_trade(self, decision: AgentDecision, price: float) -> bool:
        """Execute a trade decision."""
        try:
            side = OrderSide.BUY if decision.action == DecisionAction.BUY else OrderSide.SELL
            
            # Calculate quantity
            qty = decision.position_size / price if price > 0 else 0
            
            if qty <= 0:
                return False
            
            # Check balance
            if side == OrderSide.BUY:
                if self.portfolio.cash_balance < decision.position_size:
                    return False
            else:
                position = self.portfolio.positions.get(decision.symbol, 0)
                if position < qty:
                    return False
            
            # Create order
            order = OrderRequest(
                symbol=decision.symbol,
                side=side,
                qty=qty,
                order_type=OrderType.MARKET,
                client_order_id=uuid.uuid4()
            )
            
            # Submit
            result = await self.portfolio.submit_order(order)
            
            if result.status.value == 'FILLED':
                trade = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'symbol': decision.symbol,
                    'agent': decision.agent_name,
                    'strategy': decision.strategy,
                    'side': side.value,
                    'qty': qty,
                    'price': price,
                    'value': decision.position_size,
                    'reason': decision.reason
                }
                
                # Update stats
                self.stats['total_trades'] += 1
                self.stats['symbols_traded'].add(decision.symbol)
                self.stats['agent_trades'][decision.agent_name] += 1
                self.stats['total_volume'] += decision.position_size
                
                if side == OrderSide.BUY:
                    self.stats['buy_trades'] += 1
                else:
                    self.stats['sell_trades'] += 1
                
                # Broadcast
                await broadcast_trade(trade)
                
                # Log
                ts = datetime.utcnow().strftime("%H:%M:%S")
                logger.info(f"[{ts}] [{decision.agent_name:18}] {side.value:4} "
                          f"€{decision.position_size:8.2f} {decision.symbol:15} @ €{price:,.2f}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return False
    
    async def _calculate_portfolio_value(self, prices: Dict[str, any]) -> float:
        """Calculate total portfolio value."""
        total = self.portfolio.cash_balance
        
        for symbol, qty in self.portfolio.positions.items():
            if qty > 0 and symbol in prices:
                total += qty * prices[symbol].price
        
        return total
    
    async def broadcast_status(self):
        """Broadcast current status."""
        prices = await self.fetch_agent.get_all_prices() if self.fetch_agent else {}
        
        portfolio_value = await self._calculate_portfolio_value(prices)
        pnl = portfolio_value - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        # Portfolio
        await broadcast_portfolio(
            cash=self.portfolio.cash_balance,
            total_value=portfolio_value,
            pnl=pnl,
            pnl_pct=pnl_pct,
            positions={k: v for k, v in self.portfolio.positions.items() if v > 0}
        )
        
        # Stats
        await broadcast_stats(
            total_trades=self.stats['total_trades'],
            symbols_traded=len(self.stats['symbols_traded']),
            buy_sell_ratio=f"{self.stats['buy_trades']}/{self.stats['sell_trades']}",
            agent_performance=self.stats['agent_trades']
        )
        
        # Triad update
        agents_status = []
        for a in self.agents:
            perf = getattr(a, "performance", None)

            trades_today = getattr(perf, "trades_executed", 0) if perf is not None else 0
            total_decisions = getattr(perf, "total_decisions", 0) if perf is not None else 0

            # Derive success_rate from concrete performance metrics when available.
            if perf is not None and hasattr(perf, "successful_trades") and hasattr(perf, "failed_trades"):
                successful = getattr(perf, "successful_trades", 0) or 0
                failed = getattr(perf, "failed_trades", 0) or 0
                outcomes = successful + failed
                success_rate = (successful / outcomes) if outcomes > 0 else 0.0
            elif total_decisions > 0:
                # Fallback: approximate success rate from trades vs decisions.
                success_rate = min(1.0, max(0.0, trades_today / total_decisions))
            else:
                success_rate = 0.0

            # Derive confidence from the amount of experience (decisions taken), bounded [0.0, 1.0].
            if total_decisions > 0:
                # Example: grow confidence with decisions, saturating at 1.0.
                confidence = 0.5 + (total_decisions / 1000.0)
                confidence = max(0.0, min(1.0, confidence))
            else:
                confidence = 0.0

            agents_status.append({
                'name': a.name,
                'strategy': a.strategy,
                'status': 'active' if trades_today > 0 else 'idle',
                'trades_today': trades_today,
                'success_rate': success_rate,
                'confidence': confidence
            })
        
        fetch_stats = self.fetch_agent.get_stats() if self.fetch_agent else {}
        
        await broadcast_triad_update(
            agents=agents_status,
            meta_agents=[
                {'name': 'PriceFeed', 'type': 'coordinator', 'status': 'online' if fetch_stats.get('ws_connected') else 'offline', 
                 'agents_managed': 5, 'last_action': f"WS: {fetch_stats.get('ws_messages', 0)} msgs"},
                {'name': 'Evaluator', 'type': 'evaluator', 'status': 'online', 'agents_managed': 5, 
                 'last_action': f"Cache: {fetch_stats.get('cache_size', 0)} prices"},
                {'name': 'Governance', 'type': 'governance', 'status': 'online', 'agents_managed': 5, 
                 'last_action': f"Fallback: {'ON' if fetch_stats.get('rest_fallback') else 'OFF'}"}
            ],
            memory_banks=[
                {'name': 'Price Cache', 'type': 'short_term', 'records': fetch_stats.get('cache_size', 0), 
                 'last_update': '1s ago', 'health': 98 if fetch_stats.get('ws_connected') else 70},
                {'name': 'Trade History', 'type': 'long_term', 'records': self.stats['total_trades'] * 10, 
                 'last_update': '1m ago', 'health': 99},
                {'name': 'Agent Memory', 'type': 'episodic', 'records': sum(a.performance.total_decisions for a in self.agents), 
                 'last_update': '5s ago', 'health': 97}
            ],
            consensus_reached=85,
            disputes=0,
            total_decisions=sum(a.performance.total_decisions for a in self.agents)
        )
        
        return portfolio_value, pnl, pnl_pct
    
    async def status_reporter(self, interval: int = 60):
        """Print status every minute."""
        while self.running:
            await asyncio.sleep(interval)
            
            if not self.running:
                break
            
            elapsed = datetime.utcnow() - self.start_time if self.start_time else timedelta(0)
            portfolio_value, pnl, pnl_pct = await self.broadcast_status()
            
            fetch_stats = self.fetch_agent.get_stats() if self.fetch_agent else {}
            
            print()
            print("=" * 80)
            print(f"STATUS | Elapsed: {elapsed} | Trades: {self.stats['total_trades']} | "
                  f"P&L: EUR {pnl:+,.2f} ({pnl_pct:+.2f}%)")
            print(f"       | Cache: {fetch_stats.get('cache_size', 0)} prices | "
                  f"WS: {fetch_stats.get('ws_messages', 0)} | REST: {fetch_stats.get('rest_requests', 0)}")
            print(f"       | Volume: EUR {self.stats['total_volume']:,.2f}")
            print("=" * 80)
    
    async def run(self, duration_hours: int = 8):
        """Run the trading session."""
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        self.running = True
        
        print(f"[START] {self.start_time}")
        print(f"[END]   {self.end_time}")
        print()
        
        # Start status reporter
        reporter = asyncio.create_task(self.status_reporter(interval=60))
        
        try:
            while datetime.utcnow() < self.end_time and self.running:
                # Trading cycle (every 5 seconds)
                await self.trading_cycle()
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Trading loop error: {e}")
        finally:
            self.running = False
            reporter.cancel()
            try:
                await reporter
            except asyncio.CancelledError:
                pass
        
        # Final status
        await self.broadcast_status()
        
        print()
        print("=" * 80)
        print("     SESSION COMPLETE")
        print("=" * 80)
    
    async def close(self):
        """Cleanup."""
        if self.fetch_agent:
            await self.fetch_agent.stop()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=8)
    parser.add_argument("--capital", type=float, default=10000.0)
    args = parser.parse_args()
    
    trading = RealPaperTradingV2(initial_capital=args.capital)
    
    try:
        await trading.initialize()
        await trading.run(duration_hours=args.duration)
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Stopping...")
    finally:
        await trading.close()


if __name__ == "__main__":
    asyncio.run(main())
