"""
Elemental System Backtest V14 - CYCLE RESTORATION

V14 Key Changes:
- Cycle counting: Incremented PER DAY (outside symbol loop)
- Earth threshold: Reverted to 3 consecutive losses
- Goal: Restore cycles to V10 level (~4,000+)

Retained from V12/V13:
- Water: TLT/Bond inverse logic
- Fire: ATR-based position sizing
- Hedge pairs infrastructure
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["TRADING_MODE"] = "paper"

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy import create_engine, text

from backend.agents.elemental_agent_manager_v14 import (
    INVERSE_ETFS, ElementalAgentManagerV14)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("BacktestV14")


@dataclass
class Trade:
    trade_id: int
    timestamp: datetime
    symbol: str
    action: str
    quantity: float
    price: float
    value: float
    position_size: float
    harmony: float
    dominant_planet: str
    exit_reason: str = ""
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    is_winner: Optional[bool] = None


class V14BacktestEngine:
    """
    V14: Cycle restoration - increment cycles per day, not per symbol
    """

    SLIPPAGE_PCT = 0.001
    COMMISSION_PCT = 0.0005

    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
    ):
        self.symbols = symbols
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        self.initial_capital = initial_capital
        self.cash = initial_capital

        self.open_positions: Dict[str, Dict] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.harmony_curve: List[Dict] = []

        self.agent_manager = ElementalAgentManagerV14()
        self.peak_value = initial_capital

        self.position_sizes_taken: List[float] = []
        self.symbol_position_sizes: Dict[str, List[float]] = defaultdict(list)

        self.trade_counter = 0
        self.hedge_entries_count = 0

        db_url = (
            os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db",
            )
            .replace("+asyncpg", "+psycopg2")
            .replace("postgresql+psycopg2", "postgresql")
        )

        self.engine = create_engine(db_url)

        self._price_data_cache: Dict[str, List[Dict]] = {}
        self._trading_dates: List[datetime] = []

    def fetch_price_data(self) -> Dict[str, List[Dict]]:
        """Fetch historical price data"""
        logger.info(f"Fetching data for {len(self.symbols)} symbols...")

        price_data = {}

        with self.engine.connect() as conn:
            for i, symbol in enumerate(self.symbols, 1):
                result = conn.execute(
                    text(
                        """
                    SELECT timestamp, open, high, low, close, volume
                    FROM market_candles
                    WHERE symbol = :symbol
                    AND timestamp >= :start
                    AND timestamp <= :end
                    AND timeframe = '1d'
                    ORDER BY timestamp
                """
                    ),
                    {"symbol": symbol, "start": self.start_date, "end": self.end_date},
                )

                rows = [dict(row._mapping) for row in result]
                if rows:
                    price_data[symbol] = rows
                    if i <= 20 or i % 10 == 0:
                        logger.info(
                            f"  [{i}/{len(self.symbols)}] {symbol}: {len(rows)} days"
                        )

        self._price_data_cache = price_data

        all_dates = set()
        for symbol_data in price_data.values():
            for row in symbol_data:
                all_dates.add(row["timestamp"])

        self._trading_dates = sorted(all_dates)
        logger.info(f"Total trading days: {len(self._trading_dates)}")

        return price_data

    def _get_price_for_date(
        self, price_data: Dict, symbol: str, date: datetime
    ) -> Optional[float]:
        """Get price for symbol on specific date"""
        if symbol not in price_data:
            return None

        for row in price_data[symbol]:
            if row["timestamp"] == date:
                return float(row["close"])

        return None

    def _calculate_portfolio_value(
        self, price_data: Dict, current_date: datetime
    ) -> float:
        """Calculate total portfolio value"""
        value = self.cash

        for symbol, position in self.open_positions.items():
            current_price = self._get_price_for_date(price_data, symbol, current_date)
            if current_price:
                position_value = position["quantity"] * current_price
                value += position_value

        return value

    def _execute_entry(
        self, entry_result: Dict, trading_date: datetime, price_data: Dict
    ):
        """Execute entry trade"""
        symbol = entry_result["symbol"]

        self.open_positions[symbol] = {
            "entry_price": entry_result["entry_price"],
            "entry_date": trading_date,
            "quantity": entry_result["quantity"],
            "position_size": entry_result["position_size"],
            "harmony": entry_result["harmony"],
            "planet": entry_result["planet"],
        }

        self.cash -= entry_result["position_size"]

        self.position_sizes_taken.append(entry_result["position_size"])
        self.symbol_position_sizes[symbol].append(entry_result["position_size"])

        self.trade_counter += 1
        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=trading_date,
            symbol=symbol,
            action="BUY",
            quantity=entry_result["quantity"],
            price=entry_result["entry_price"],
            value=entry_result["quantity"] * entry_result["entry_price"],
            position_size=entry_result["position_size"],
            harmony=entry_result["harmony"],
            dominant_planet=entry_result["planet"],
        )
        self.trades.append(trade)

    def _execute_exit(
        self,
        symbol: str,
        current_price: float,
        trading_date: datetime,
        reason: str,
        price_data: Dict,
    ):
        """Execute exit trade"""
        if symbol not in self.open_positions:
            return

        position = self.open_positions[symbol]

        exit_price = current_price * (1 - self.SLIPPAGE_PCT)
        exit_value = position["quantity"] * exit_price
        commission = exit_value * self.COMMISSION_PCT
        net_exit_value = exit_value - commission

        entry_value = position["quantity"] * position["entry_price"]
        realized_pnl = net_exit_value - entry_value
        realized_pnl_pct = realized_pnl / entry_value

        self.cash += net_exit_value

        del self.open_positions[symbol]

        is_winner = realized_pnl > 0
        self.agent_manager.record_trade_outcome(symbol, realized_pnl, is_winner)

        self.trade_counter += 1
        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=trading_date,
            symbol=symbol,
            action="SELL",
            quantity=position["quantity"],
            price=exit_price,
            value=exit_value,
            position_size=position["position_size"],
            harmony=position["harmony"],
            dominant_planet=position["planet"],
            exit_reason=reason,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            is_winner=is_winner,
        )
        self.trades.append(trade)

        if "review" in reason.lower():
            self.agent_manager.position_review_exits += 1

    def _process_day(self, trading_date: datetime, price_data: Dict):
        """
        V14: Process single trading day
        Key change: increment_cycle() called ONCE per day (outside symbol loop)
        """
        # ═══════════════════════════════════════════════════════════
        # V14: STEP 0 - INCREMENT CYCLE (once per day, outside symbol loop)
        # ═══════════════════════════════════════════════════════════
        self.agent_manager.increment_cycle()

        # ═══════════════════════════════════════════════════════════
        # STEP 1: POSITION REVIEW (evaluate open positions)
        # ═══════════════════════════════════════════════════════════
        positions_to_exit = []

        for symbol, position in list(self.open_positions.items()):
            current_price = self._get_price_for_date(price_data, symbol, trading_date)
            if not current_price:
                continue

            # Update Fire agent price history for position
            self.agent_manager.fire_agent.record_price(symbol, current_price)

            # Get macro signal for position review
            prices = list(self.agent_manager.fire_agent.price_history.get(symbol, []))
            macro_signal = self.agent_manager.water_agent.get_macro_signal(prices)

            should_exit, reason = self.agent_manager.evaluate_open_position(
                symbol, current_price, macro_signal, trading_date
            )

            if should_exit:
                positions_to_exit.append((symbol, reason))

        # Execute exits
        for symbol, reason in positions_to_exit:
            current_price = self._get_price_for_date(price_data, symbol, trading_date)
            if current_price:
                self._execute_exit(
                    symbol, current_price, trading_date, reason, price_data
                )

        # ═══════════════════════════════════════════════════════════
        # STEP 2: PRIMARY ENTRY EVALUATION
        # ═══════════════════════════════════════════════════════════
        primary_entries = []

        for symbol in self.symbols:
            # Skip inverse ETFs - handled separately
            if symbol in INVERSE_ETFS:
                continue

            # Skip if already in open position
            if symbol in self.open_positions:
                continue

            # V14: Earth should_enter check
            if not self.agent_manager.earth_agent.should_enter(symbol):
                continue

            # Survivorship bias check
            if not self.agent_manager.is_symbol_available(symbol, trading_date):
                continue

            current_price = self._get_price_for_date(price_data, symbol, trading_date)
            if current_price is None:
                continue

            portfolio_value = self._calculate_portfolio_value(price_data, trading_date)

            # V14: Process entry (NO cycle counting - done at day level)
            entry_result = self.agent_manager.process_entry_evaluation(
                symbol=symbol,
                current_price=current_price,
                portfolio_value=portfolio_value,
                cycle_date=trading_date,
                prana_level=85.0,
            )

            if entry_result:
                self._execute_entry(entry_result, trading_date, price_data)
                primary_entries.append(symbol)

        # ═══════════════════════════════════════════════════════════
        # STEP 3: EVALUATE HEDGE ENTRIES
        # ═══════════════════════════════════════════════════════════
        for primary_symbol in primary_entries:
            prices = list(
                self.agent_manager.fire_agent.price_history.get(primary_symbol, [])
            )
            macro_signal = self.agent_manager.water_agent.get_macro_signal(prices)

            hedge_sym, hedge_conf = self.agent_manager.water_agent.get_hedge_signal(
                primary_symbol, macro_signal
            )

            if hedge_sym and hedge_sym not in self.open_positions:
                current_price_hedge = self._get_price_for_date(
                    price_data, hedge_sym, trading_date
                )
                if not current_price_hedge:
                    continue

                portfolio_value = self._calculate_portfolio_value(
                    price_data, trading_date
                )

                entry_result = self.agent_manager.process_entry_evaluation(
                    symbol=hedge_sym,
                    current_price=current_price_hedge,
                    portfolio_value=portfolio_value * 0.3,  # 30% of normal size
                    cycle_date=trading_date,
                    prana_level=85.0,
                )

                if entry_result:
                    self._execute_entry(entry_result, trading_date, price_data)
                    self.hedge_entries_count += 1

        # Record equity curve
        portfolio_value = self._calculate_portfolio_value(price_data, trading_date)
        self.equity_curve.append(
            {
                "timestamp": trading_date.isoformat(),
                "value": portfolio_value,
                "cash": self.cash,
                "open_positions": len(self.open_positions),
            }
        )

        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value

    def run_backtest(self):
        """Run the full backtest"""
        logger.info("=" * 70)
        logger.info("V14: CYCLE RESTORATION")
        logger.info("Goal: Restore cycles to V10 level (~4,000+)")
        logger.info("=" * 70)

        price_data = self.fetch_price_data()

        if not price_data:
            logger.error("No price data available")
            return None

        # Pre-seed Fire agent with 60-day volatility memory
        logger.info("Pre-seeding Fire Agent with 60-day volatility memory...")
        prestart = self.start_date - timedelta(days=90)

        with self.engine.connect() as conn:
            for symbol in self.symbols:
                result = conn.execute(
                    text(
                        """
                    SELECT timestamp, close
                    FROM market_candles
                    WHERE symbol = :symbol
                    AND timestamp >= :prestart
                    AND timestamp < :start
                    AND timeframe = '1d'
                    ORDER BY timestamp
                """
                    ),
                    {"symbol": symbol, "prestart": prestart, "start": self.start_date},
                )

                for row in result:
                    self.agent_manager.fire_agent.record_price(symbol, float(row[1]))

        logger.info("\n" + "=" * 60)
        logger.info("STARTING V14 BACKTEST")
        logger.info("=" * 60)

        # Process each trading day
        total_days = len(self._trading_dates)
        for i, trading_date in enumerate(self._trading_dates):
            self._process_day(trading_date, price_data)

            if (i + 1) % 200 == 0 or i == total_days - 1:
                portfolio_value = self._calculate_portfolio_value(
                    price_data, trading_date
                )
                logger.info(
                    f"Day {i+1}/{total_days} | "
                    f"Portfolio: ${portfolio_value:,.2f} | "
                    f"Open: {len(self.open_positions)}"
                )

        # V14 FIX: Close all open positions at end of backtest
        final_date = self._trading_dates[-1]
        positions_to_close = list(self.open_positions.keys())
        if positions_to_close:
            logger.info(
                f"\nClosing {len(positions_to_close)} open positions at end of backtest..."
            )
            for symbol in positions_to_close:
                current_price = self._get_price_for_date(price_data, symbol, final_date)
                if current_price:
                    self._execute_exit(
                        symbol, current_price, final_date, "backtest_end", price_data
                    )

            # Update final equity curve entry after closing positions
            final_value = self._calculate_portfolio_value(price_data, final_date)
            self.equity_curve[-1] = {
                "timestamp": final_date.isoformat(),
                "value": final_value,
                "cash": self.cash,
                "open_positions": len(self.open_positions),
            }

        # Calculate final stats
        final_value = self._calculate_portfolio_value(
            price_data, self._trading_dates[-1]
        )
        total_return = (final_value - self.initial_capital) / self.initial_capital

        winning_trades = [t for t in self.trades if t.action == "SELL" and t.is_winner]
        losing_trades = [
            t for t in self.trades if t.action == "SELL" and not t.is_winner
        ]

        total_profit = sum(t.realized_pnl for t in winning_trades if t.realized_pnl)
        total_loss = abs(sum(t.realized_pnl for t in losing_trades if t.realized_pnl))
        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

        agent_stats = self.agent_manager.get_agent_stats()

        logger.info("\n" + "=" * 60)
        logger.info("V14 BACKTEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Final Value:          ${final_value:,.2f}")
        logger.info(f"Total Return:         {total_return*100:+.2f}%")
        logger.info(
            f"Max Drawdown:         {(1 - final_value/self.peak_value)*100:.2f}%"
        )

        # Calculate Sharpe
        daily_returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (
                self.equity_curve[i]["value"] - self.equity_curve[i - 1]["value"]
            ) / self.equity_curve[i - 1]["value"]
            daily_returns.append(ret)

        if daily_returns:
            sharpe = (np.mean(daily_returns) * 252) / (
                np.std(daily_returns) * np.sqrt(252)
            )
        else:
            sharpe = 0

        logger.info(f"Sharpe Ratio:         {sharpe:.2f}")
        logger.info(
            f"Total Trades:         {len([t for t in self.trades if t.action == 'SELL'])}"
        )
        logger.info(
            f"Win Rate:             {len(winning_trades)/len(winning_trades + losing_trades)*100:.1f}%"
        )
        logger.info(
            f"Position Review Exits: {self.agent_manager.position_review_exits}"
        )
        logger.info("Normal Exits:         0")
        logger.info(f"Hedge Entries:        {self.hedge_entries_count}")
        logger.info(f"Elemental Cycles:     {agent_stats['total_cycles']:,}")
        logger.info(f"Execute Rate:         {agent_stats['execute_rate_pct']:.2f}%")
        logger.info(
            f"Consensus Rate:       {agent_stats['consensus_achieved_pct']:.2f}%"
        )
        logger.info(
            f"Avg Position Size:    ${sum(self.position_sizes_taken)/len(self.position_sizes_taken) if self.position_sizes_taken else 0:.2f}"
        )

        # Position summary
        logger.info("\nSymbol Position Summary (V9 Fire Sizing):")
        for symbol, sizes in self.symbol_position_sizes.items():
            if sizes:
                avg_size = sum(sizes) / len(sizes)
                logger.info(f"  {symbol:8} avg=${avg_size:8.2f}, n={len(sizes)}")

        return V14BacktestResult(
            session_id=f"v14_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_date=self.start_date,
            end_date=self.end_date,
            symbols=self.symbols,
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return_pct=total_return * 100,
            peak_value=self.peak_value,
            max_drawdown_pct=(1 - final_value / self.peak_value) * 100,
            sharpe_ratio=sharpe,
            volatility_annual=np.std(daily_returns) * np.sqrt(252) * 100
            if daily_returns
            else 0,
            total_trades=len([t for t in self.trades if t.action == "SELL"]),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate_pct=len(winning_trades) / len(winning_trades + losing_trades) * 100
            if (winning_trades or losing_trades)
            else 0,
            avg_trade_pnl=sum(
                t.realized_pnl
                for t in self.trades
                if t.action == "SELL" and t.realized_pnl
            )
            / len([t for t in self.trades if t.action == "SELL"])
            if self.trades
            else 0,
            profit_factor=profit_factor,
            position_review_exits=self.agent_manager.position_review_exits,
            normal_exits=0,
            hedge_entries=self.hedge_entries_count,
            elemental_cycles=agent_stats["total_cycles"],
            avg_harmony_score=0,
            execute_rate_pct=agent_stats["execute_rate_pct"],
            consensus_rate_pct=agent_stats["consensus_achieved_pct"],
            avg_position_size=sum(self.position_sizes_taken)
            / len(self.position_sizes_taken)
            if self.position_sizes_taken
            else 0,
            symbol_position_summary={
                sym: {
                    "avg": sum(sizes) / len(sizes),
                    "min": min(sizes),
                    "max": max(sizes),
                    "count": len(sizes),
                }
                for sym, sizes in self.symbol_position_sizes.items()
            },
            agent_stats=agent_stats,
            trades=[asdict(t) for t in self.trades],
            equity_curve=self.equity_curve,
            harmony_curve=self.harmony_curve,
        )


@dataclass
class V14BacktestResult:
    """V14 backtest results container"""

    session_id: str
    start_date: datetime
    end_date: datetime
    symbols: List[str]
    initial_capital: float
    final_value: float
    total_return_pct: float
    peak_value: float
    max_drawdown_pct: float
    sharpe_ratio: float
    volatility_annual: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    avg_trade_pnl: float
    profit_factor: float
    position_review_exits: int
    normal_exits: int
    hedge_entries: int
    elemental_cycles: int
    avg_harmony_score: float
    execute_rate_pct: float
    consensus_rate_pct: float
    avg_position_size: float
    symbol_position_summary: Dict
    agent_stats: Dict
    trades: List[Dict]
    equity_curve: List[Dict]
    harmony_curve: List[Dict]

    def save(self, filepath: str):
        """Save results to JSON"""
        data = {
            "session_id": self.session_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "symbols": self.symbols,
            "initial_capital": self.initial_capital,
            "final_value": self.final_value,
            "total_return_pct": self.total_return_pct,
            "peak_value": self.peak_value,
            "max_drawdown_pct": self.max_drawdown_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "volatility_annual": self.volatility_annual,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate_pct": self.win_rate_pct,
            "avg_trade_pnl": self.avg_trade_pnl,
            "profit_factor": self.profit_factor,
            "position_review_exits": self.position_review_exits,
            "normal_exits": self.normal_exits,
            "hedge_entries": self.hedge_entries,
            "elemental_cycles": self.elemental_cycles,
            "avg_harmony_score": self.avg_harmony_score,
            "execute_rate_pct": self.execute_rate_pct,
            "consensus_rate_pct": self.consensus_rate_pct,
            "avg_position_size": self.avg_position_size,
            "symbol_position_summary": self.symbol_position_summary,
            "agent_stats": self.agent_stats,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "harmony_curve": self.harmony_curve,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"\nResults saved to: {filepath}")


if __name__ == "__main__":
    # Quick smoke test
    symbols = ["AAPL", "BTC", "ETH", "NVDA", "MSFT"]
    engine = V14BacktestEngine(
        symbols=symbols,
        start_date="2021-01-01",
        end_date="2021-12-31",
        initial_capital=100000.0,
    )
    result = engine.run_backtest()
    if result:
        result.save(
            f"backtest_v14_smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
