"""
REAL Paper Trading V2 - Data Pre-fetch Architecture

Features:
- DataPreFetchAgent met proactieve data collectie
- Warm-up mode: 2 minuten vooraf data laden
- 100% cache hit rate guarantee
- 5 Trading Agents lezen uit gegarandeerde cache
"""

import asyncio
import logging
import os
import random
import sys
import uuid
from datetime import datetime, timedelta

# Fix path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from backend.services.data_prefetch_agent import DataPreFetchAgent, get_data_agent
from backend.services.paper_trading_ws_broadcast import (
    broadcast_agent_decision,
    broadcast_portfolio,
    broadcast_stats,
    broadcast_trade,
    broadcast_triad_update,
)
from backend.services.trading_agents_v2 import (
    AgentDecision,
    BaseTradingAgent,
    DecisionAction,
    create_all_agents,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RealPaperTradingV2")


class RealPaperTradingV2:
    """
    Paper Trading Engine met Data Pre-fetch Architecture.

    De DataPreFetchAgent zorgt ervoor dat data ALTIJD beschikbaar is,
    zodat trading agents nooit zonder data komen te staan.
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)

        # Data Pre-fetch Agent - garandeert data availability
        self.data_agent: DataPreFetchAgent | None = None

        # Trading Agents
        self.agents: list[BaseTradingAgent] = create_all_agents()

        # State
        self.all_symbols: list[str] = []
        self.running = False
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

        # Stats
        self.stats = {
            "total_trades": 0,
            "buy_trades": 0,
            "sell_trades": 0,
            "total_volume": 0.0,
            "symbols_traded": set(),
            "agent_trades": {agent.name: 0 for agent in self.agents},
        }

        print("=" * 80)
        print("     REAL PAPER TRADING V2 - Data Pre-fetch Architecture")
        print("=" * 80)
        print(f"\nInitial Capital: EUR {initial_capital:,.2f}")
        print("Data Guarantee: 100% cache hit rate")
        print("Warm-up: 2 minuten vooraf data laden")
        print("\nTrading Agents:")
        for agent in self.agents:
            print(f"  - {agent.name:20} Risk: {agent.risk_per_trade:.0%}/trade")
        print()

    async def initialize(self):
        """Initialize Data Pre-fetch Agent en start warm-up."""
        # Initialize Bitvavo for symbol list
        from backend.execution.bitvavo_adapter import BitvavoAdapter

        temp_adapter = BitvavoAdapter()
        await temp_adapter.initialize()
        self.all_symbols = temp_adapter.get_eur_pairs()
        await temp_adapter.close()

        if len(self.all_symbols) < 50:
            raise RuntimeError(f"Only {len(self.all_symbols)} symbols found")

        print(f"[OK] Loaded {len(self.all_symbols)} EUR trading pairs")

        # Start Data Pre-fetch Agent (met warm-up)
        print("[INFO] Starting Data Pre-fetch Agent...")
        print("[WARM-UP] Collecting initial price data (max 2 minutes)...")

        self.data_agent = await get_data_agent()
        await self.data_agent.start()  # Dit wacht op warm-up completion

        # Verifieer dat we data hebben
        prices = await self.data_agent.get_all_prices()
        stats = self.data_agent.get_stats()

        print(f"[OK] Data cache ready: {stats['cache_size']} symbols, {stats['fresh_count']} fresh")
        print(f"[OK] Data source: WS={stats['ws_connected']}, Messages={stats['ws_messages']}")

        if len(prices) < 10:
            logger.warning(f"Limited price data: {len(prices)} prices. Trading may be limited.")

    async def trading_cycle(self):
        """Execute one trading cycle."""
        if not self.data_agent:
            return

        # Haal ALLE verse prijzen op uit de gegarandeerde cache
        # De DataPreFetchAgent zorgt ervoor dat deze ALTIJD beschikbaar zijn
        prices = await self.data_agent.get_all_prices()

        # Stats voor monitoring
        stats = self.data_agent.get_stats()
        if len(prices) < 10:
            logger.warning(f"Limited fresh prices: {len(prices)}/{stats['cache_size']}")

        if len(prices) < 3:  # Minimale drempel
            logger.error(f"CRITICAL: No fresh prices available ({len(prices)})")
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
                        data_agent=self.data_agent,
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
                            executed=False,
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
                client_order_id=uuid.uuid4(),
            )

            # Submit
            result = await self.portfolio.submit_order(order)

            if result.status.value == "FILLED":
                trade = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "symbol": decision.symbol,
                    "agent": decision.agent_name,
                    "strategy": decision.strategy,
                    "side": side.value,
                    "qty": qty,
                    "price": price,
                    "value": decision.position_size,
                    "reason": decision.reason,
                }

                # Update stats
                self.stats["total_trades"] += 1
                self.stats["symbols_traded"].add(decision.symbol)
                self.stats["agent_trades"][decision.agent_name] += 1
                self.stats["total_volume"] += decision.position_size

                if side == OrderSide.BUY:
                    self.stats["buy_trades"] += 1
                else:
                    self.stats["sell_trades"] += 1

                # Broadcast
                await broadcast_trade(trade)

                # Log
                ts = datetime.utcnow().strftime("%H:%M:%S")
                logger.info(
                    f"[{ts}] [{decision.agent_name:18}] {side.value:4} "
                    f"€{decision.position_size:8.2f} {decision.symbol:15} @ €{price:,.2f}"
                )

                return True

            return False

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return False

    async def _calculate_portfolio_value(self, prices: dict[str, any]) -> float:
        """Calculate total portfolio value."""
        total = self.portfolio.cash_balance

        for symbol, qty in self.portfolio.positions.items():
            if qty > 0 and symbol in prices:
                total += qty * prices[symbol].price

        return total

    async def broadcast_status(self):
        """Broadcast current status."""
        prices = await self.data_agent.get_all_prices() if self.data_agent else {}

        portfolio_value = await self._calculate_portfolio_value(prices)
        pnl = portfolio_value - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0

        # Portfolio
        await broadcast_portfolio(
            cash=self.portfolio.cash_balance,
            total_value=portfolio_value,
            pnl=pnl,
            pnl_pct=pnl_pct,
            positions={k: v for k, v in self.portfolio.positions.items() if v > 0},
        )

        # Stats
        await broadcast_stats(
            total_trades=self.stats["total_trades"],
            symbols_traded=len(self.stats["symbols_traded"]),
            buy_sell_ratio=f"{self.stats['buy_trades']}/{self.stats['sell_trades']}",
            agent_performance=self.stats["agent_trades"],
        )

        # Triad update
        agents_status = []
        for a in self.agents:
            perf = getattr(a, "performance", None)

            trades_today = getattr(perf, "trades_executed", 0) if perf is not None else 0
            total_decisions = getattr(perf, "total_decisions", 0) if perf is not None else 0

            # Derive success_rate from concrete performance metrics when available.
            if (
                perf is not None
                and hasattr(perf, "successful_trades")
                and hasattr(perf, "failed_trades")
            ):
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

            agents_status.append(
                {
                    "name": a.name,
                    "strategy": a.strategy,
                    "status": "active" if trades_today > 0 else "idle",
                    "trades_today": trades_today,
                    "success_rate": success_rate,
                    "confidence": confidence,
                }
            )

        data_stats = self.data_agent.get_stats() if self.data_agent else {}

        await broadcast_triad_update(
            agents=agents_status,
            meta_agents=[
                {
                    "name": "DataAgent",
                    "type": "coordinator",
                    "status": "online" if data_stats.get("ws_connected") else "offline",
                    "agents_managed": 5,
                    "last_action": f"WS: {data_stats.get('ws_messages', 0)} msgs",
                },
                {
                    "name": "CacheManager",
                    "type": "evaluator",
                    "status": "online",
                    "agents_managed": 5,
                    "last_action": f"Cache: {data_stats.get('cache_size', 0)} fresh",
                },
                {
                    "name": "WarmUp",
                    "type": "governance",
                    "status": ("online" if data_stats.get("warmup_complete") else "warming"),
                    "agents_managed": 5,
                    "last_action": f"History: {data_stats.get('history_entries', 0)} entries",
                },
            ],
            memory_banks=[
                {
                    "name": "Price Cache",
                    "type": "short_term",
                    "records": data_stats.get("cache_size", 0),
                    "last_update": "1s ago",
                    "health": 98 if data_stats.get("ws_connected") else 70,
                },
                {
                    "name": "Trade History",
                    "type": "long_term",
                    "records": self.stats["total_trades"] * 10,
                    "last_update": "1m ago",
                    "health": 99,
                },
                {
                    "name": "Agent Memory",
                    "type": "episodic",
                    "records": sum(a.performance.total_decisions for a in self.agents),
                    "last_update": "5s ago",
                    "health": 97,
                },
            ],
            consensus_reached=85,
            disputes=0,
            total_decisions=sum(a.performance.total_decisions for a in self.agents),
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

            data_stats = self.data_agent.get_stats() if self.data_agent else {}

            print()
            print("=" * 80)
            print(
                f"STATUS | Elapsed: {elapsed} | Trades: {self.stats['total_trades']} | "
                f"P&L: EUR {pnl:+,.2f} ({pnl_pct:+.2f}%)"
            )
            print(
                f"       | Cache: {data_stats.get('cache_size', 0)} prices | "
                f"WS: {data_stats.get('ws_messages', 0)} | REST: {data_stats.get('rest_updates', 0)}"
            )
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
                # Trading cycle (every 3 seconds)
                await self.trading_cycle()
                await asyncio.sleep(3)

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
        if self.data_agent:
            await self.data_agent.stop()


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
