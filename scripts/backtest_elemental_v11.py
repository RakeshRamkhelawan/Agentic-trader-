"""
Elemental System Backtest V9 - POSITION REVIEW LOOP

V9 Key Changes:
- Position Review Loop: eerst open posities reviewen, dan entries
- Slippage 0.1% + commissie 0.05%
- Survivorship bias mitigatie (IPO dates)
- Earth/Fire/Water agents kunnen posities sluiten

Fire Agent sizing ONGEWIJZIGD van v8
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["TRADING_MODE"] = "paper"

import json
import logging
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("BacktestV11")

from backend.agents.elemental_agent_manager_v11 import (
    ElementalAgentManagerV11, MacroSignal)


@dataclass
class Trade:
    trade_id: int
    timestamp: str
    symbol: str
    action: str
    quantity: float
    price: float
    value: float
    position_size: float
    harmony: float = 0.0
    dominant_planet: str = ""
    exit_reason: str = ""  # V9: POSITION_REVIEW of NORMAL
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    is_winner: Optional[bool] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class V11BacktestResult:
    session_id: str
    start_date: str
    end_date: str
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
    position_review_exits: int  # V9
    normal_exits: int  # V9
    elemental_cycles: int
    avg_harmony_score: float
    execute_rate_pct: float
    consensus_rate_pct: float
    avg_position_size: float
    symbol_position_summary: Dict[str, Dict]
    agent_stats: Dict[str, Dict]
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    harmony_curve: List[Dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class V11BacktestEngine:
    """V9 Backtest Engine with Position Review Loop"""

    # V9: Trading costs
    SLIPPAGE_PCT = 0.001  # 0.1%
    COMMISSION_PCT = 0.0005  # 0.05%

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

        # V9: Open positions tracking
        self.open_positions: Dict[
            str, Dict
        ] = {}  # symbol -> {entry_price, entry_date, quantity}

        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.harmony_curve: List[Dict] = []

        self.agent_manager = ElementalAgentManagerV11()
        self.peak_value = initial_capital

        # Stats
        self.position_sizes_taken: List[float] = []
        self.symbol_position_sizes: Dict[str, List[float]] = defaultdict(list)
        self.position_review_exit_count = 0
        self.normal_exit_count = 0
        self.partial_exit_count = 0
        self.total_cycles_processed = 0

        # Database
        self.db_url = (
            os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db",
            )
            .replace("+asyncpg", "+psycopg2")
            .replace("postgresql+psycopg2", "postgresql")
        )

        self.trade_counter = 0

        logger.info("=" * 60)
        logger.info("V11: PARTIAL EXITS + CRYPTO DECAY + DAILY FREQ")
        logger.info("=" * 60)

    def _get_price_data(self) -> Dict[str, List[Dict]]:
        """Fetch price data from database"""
        logger.info(f"Fetching data for {len(self.symbols)} symbols...")

        engine = create_engine(self.db_url)
        price_data = {}

        with engine.connect() as conn:
            for i, symbol in enumerate(self.symbols, 1):
                result = conn.execute(
                    text(
                        """
                    SELECT timestamp, close
                    FROM market_candles
                    WHERE symbol = :symbol
                      AND timestamp >= :start
                      AND timestamp <= :end
                    ORDER BY timestamp ASC
                """
                    ),
                    {
                        "symbol": symbol,
                        "start": self.start_date.isoformat(),
                        "end": self.end_date.isoformat(),
                    },
                )

                rows = [{"timestamp": row[0], "close": row[1]} for row in result]

                if rows:
                    price_data[symbol] = rows
                    if i <= 10 or i % 10 == 0:
                        logger.info(
                            f"  [{i}/{len(self.symbols)}] {symbol}: {len(rows)} days"
                        )

        return price_data

    def _get_trading_dates(self, price_data: Dict[str, List[Dict]]) -> List[datetime]:
        """Get sorted list of all trading dates"""
        all_dates = set()
        for rows in price_data.values():
            for row in rows:
                ts = row["timestamp"]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts = ts.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
                all_dates.add(ts)

        dates = sorted(list(all_dates))
        logger.info(f"Total trading days: {len(dates)}")
        return dates

    def _pre_seed_fire_agent(
        self, price_data: Dict[str, List[Dict]], start_date: datetime
    ):
        """Pre-seed Fire Agent with 60 days of price history"""
        logger.info("Pre-seeding Fire Agent with 60-day volatility memory...")

        start_naive = start_date.replace(tzinfo=None)

        for symbol, rows in price_data.items():
            pre_seed_rows = []
            for r in rows:
                ts = r["timestamp"]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts = ts.replace(tzinfo=None)
                if ts < start_naive:
                    pre_seed_rows.append(r)

            seed_rows = (
                pre_seed_rows[-60:] if len(pre_seed_rows) >= 60 else pre_seed_rows
            )

            for row in seed_rows:
                self.agent_manager.fire_agent.record_price(symbol, row["close"])

    def run_backtest(self) -> V11BacktestResult:
        """Run V9 backtest with Position Review Loop"""

        price_data = self._get_price_data()
        if not price_data:
            raise ValueError("No price data found!")

        trading_dates = self._get_trading_dates(price_data)
        self._pre_seed_fire_agent(price_data, self.start_date)

        logger.info("\n" + "=" * 60)
        logger.info("STARTING V11 BACKTEST")
        logger.info("=" * 60)
        logger.info(
            f"Expected cycles: {len(trading_dates)} days × {len(self.symbols)} symbols = {len(trading_dates) * len(self.symbols):,}"
        )

        cycle_count = 0

        for trading_date in trading_dates:
            self._process_day(trading_date, price_data)
            cycle_count += 1
            self.total_cycles_processed += 1

            if cycle_count % 200 == 0:
                portfolio_val = self._calculate_portfolio_value(
                    price_data, trading_date
                )
                open_count = len(self.open_positions)
                logger.info(
                    f"Day {cycle_count}/{len(trading_dates)} | Portfolio: ${portfolio_val:,.2f} | Open: {open_count}"
                )

        logger.info(f"Total cycles processed: {self.total_cycles_processed:,}")
        logger.info(f"Agent cycles: {self.agent_manager.total_cycles:,}")

        return self._generate_result(price_data)

    def _process_day(self, trading_date: datetime, price_data: Dict[str, List[Dict]]):
        """V11: Process one day with Position Review Loop + Partial Exits"""

        # Get macro signal for Water Agent
        macro_signal = self._get_macro_signal(price_data, trading_date)

        # ═══════════════════════════════════════════════════════════
        # STAP 1: REVIEW ALL OPEN POSITIONS (always first)
        # ═══════════════════════════════════════════════════════════

        # V11: Time-based exits first
        self._check_time_based_exits(trading_date, price_data)

        # V11: Agent-based position review + partial exits
        for symbol in list(self.open_positions.keys()):
            current_price = self._get_price_for_date(price_data, symbol, trading_date)
            if current_price is None:
                continue

            # Fire records price for ATR calculation (even for open positions)
            self.agent_manager.fire_agent.record_price(symbol, current_price)

            # Get position details for PnL calculation
            pos = self.open_positions[symbol]
            entry_price = pos["entry_price"]
            quantity = pos["quantity"]

            # V11: Position Review (partial exits disabled for stability)
            action, exit_reason = self.agent_manager.evaluate_open_position(
                symbol, current_price, macro_signal, trading_date, entry_price, quantity
            )

            # Skip partial exits for now - use only full exits
            if action == "PARTIAL_EXIT":
                action = "HOLD"  # Disable partial exits temporarily

            if action == "EXIT":
                self._close_position(
                    symbol=symbol,
                    exit_price=current_price,
                    exit_date=trading_date,
                    exit_reason=exit_reason,
                    price_data=price_data,
                )

        # ═══════════════════════════════════════════════════════════
        # STAP 2: EVALUATE NEW ENTRIES
        # ═══════════════════════════════════════════════════════════
        for symbol in self.symbols:
            # Skip if already in open position
            if symbol in self.open_positions:
                continue

            # V10: Survivorship bias check
            if not self.agent_manager.is_symbol_available(symbol, trading_date):
                continue

            current_price = self._get_price_for_date(price_data, symbol, trading_date)
            if current_price is None:
                continue

            portfolio_value = self._calculate_portfolio_value(price_data, trading_date)

            # V10: Process entry cycle
            entry_result = self.agent_manager.process_entry_cycle(
                symbol=symbol,
                current_price=current_price,
                portfolio_value=portfolio_value,
                cycle_date=trading_date,
                prana_level=85.0,
            )

            if entry_result:
                self._execute_entry(entry_result, trading_date, price_data)

        # Record equity curve
        final_value = self._calculate_portfolio_value(price_data, trading_date)
        self.equity_curve.append(
            {
                "timestamp": trading_date.isoformat(),
                "portfolio_value": final_value,
                "cash": self.cash,
                "open_positions": len(self.open_positions),
            }
        )

        # Update peak/drawdown
        if final_value > self.peak_value:
            self.peak_value = final_value

    def _get_macro_signal(
        self, price_data: Dict, trading_date: datetime
    ) -> MacroSignal:
        """Get macro signal from SPY prices"""
        if "SPY" in price_data:
            spy_prices = []
            for row in price_data["SPY"]:
                ts = row["timestamp"]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts = ts.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
                if ts <= trading_date:
                    spy_prices.append(row["close"])

            return self.agent_manager.water_agent.get_macro_signal(spy_prices)

        return MacroSignal(risk_on_score=0.5, regime="neutral")

    def _get_price_for_date(
        self, price_data: Dict, symbol: str, target_date: datetime
    ) -> Optional[float]:
        """Get price for specific symbol and date"""
        if symbol not in price_data:
            return None

        target_naive = target_date.replace(
            tzinfo=None, hour=0, minute=0, second=0, microsecond=0
        )

        for row in price_data[symbol]:
            ts = row["timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts = ts.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)

            if ts == target_naive:
                return row["close"]

        return None

    def _execute_entry(self, entry: Dict, entry_date: datetime, price_data: Dict):
        """Execute buy entry"""
        symbol = entry["symbol"]
        entry_price = entry["entry_price"]
        quantity = entry["quantity"]
        position_size = entry["position_size"]

        cost = entry_price * quantity

        if self.cash >= cost and quantity > 0:
            self.cash -= cost

            self.open_positions[symbol] = {
                "entry_price": entry_price,
                "entry_date": entry_date,
                "quantity": quantity,
            }

            self.trade_counter += 1
            self.position_sizes_taken.append(position_size)
            self.symbol_position_sizes[symbol].append(position_size)

            trade = Trade(
                trade_id=self.trade_counter,
                timestamp=entry_date.isoformat(),
                symbol=symbol,
                action="BUY",
                quantity=quantity,
                price=entry_price,
                value=cost,
                position_size=position_size,
                harmony=entry["harmony"],
                dominant_planet=entry["planet"],
            )
            self.trades.append(trade)

    def _close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_date: datetime,
        exit_reason: str,
        price_data: Dict,
    ):
        """V9: Close position with feedback dispatch"""
        if symbol not in self.open_positions:
            return

        pos = self.open_positions[symbol]
        qty = pos["quantity"]
        entry_price = pos["entry_price"]
        entry_date = pos["entry_date"]

        # V9: Apply slippage on exit
        actual_exit_price = exit_price * (1 - self.SLIPPAGE_PCT)

        proceeds = actual_exit_price * qty
        cost_basis = entry_price * qty

        # V9: Apply commission
        commission_exit = proceeds * self.COMMISSION_PCT
        commission_entry = cost_basis * self.COMMISSION_PCT

        pnl = proceeds - cost_basis - commission_exit - commission_entry
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        win = pnl > 0

        self.cash += proceeds

        # V9: Record exit for agents
        self.agent_manager.record_trade_outcome(symbol, pnl, win)

        # Track exit type
        if exit_reason != "NORMAL":
            self.position_review_exit_count += 1
        else:
            self.normal_exit_count += 1

        self.trade_counter += 1

        # Calculate holding days
        holding_days = (
            (exit_date - entry_date).days if isinstance(entry_date, datetime) else 0
        )

        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=exit_date.isoformat(),
            symbol=symbol,
            action="SELL",
            quantity=qty,
            price=actual_exit_price,
            value=proceeds,
            position_size=0,
            exit_reason=exit_reason,
            realized_pnl=pnl,
            realized_pnl_pct=pnl_pct,
            is_winner=win,
        )
        self.trades.append(trade)

        del self.open_positions[symbol]

    def _partial_close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_date: datetime,
        exit_reason: str,
        price_data: Dict,
    ):
        """V11: Close 50% of position for profit taking"""
        if symbol not in self.open_positions:
            return

        pos = self.open_positions[symbol]
        total_qty = pos["quantity"]
        partial_qty = total_qty * 0.5  # Sell 50%
        entry_price = pos["entry_price"]
        entry_date = pos["entry_date"]

        # Apply slippage on exit
        actual_exit_price = exit_price * (1 - self.SLIPPAGE_PCT)

        proceeds = actual_exit_price * partial_qty
        cost_basis = entry_price * partial_qty

        # Apply commission
        commission_exit = proceeds * self.COMMISSION_PCT
        commission_entry = cost_basis * self.COMMISSION_PCT

        pnl = proceeds - cost_basis - commission_exit - commission_entry
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        win = pnl > 0

        self.cash += proceeds

        # Record exit for agents
        self.agent_manager.record_trade_outcome(symbol, pnl, win)

        # Track partial exit
        self.partial_exit_count += 1

        self.trade_counter += 1

        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=exit_date.isoformat(),
            symbol=symbol,
            action="SELL",
            quantity=partial_qty,
            price=actual_exit_price,
            value=proceeds,
            position_size=0,
            exit_reason=exit_reason,
            realized_pnl=pnl,
            realized_pnl_pct=pnl_pct,
            is_winner=win,
        )
        self.trades.append(trade)

        # Update remaining position
        remaining_qty = total_qty - partial_qty
        if remaining_qty > 0:
            self.open_positions[symbol]["quantity"] = remaining_qty
        else:
            del self.open_positions[symbol]

    def _check_time_based_exits(self, trading_date: datetime, price_data: Dict):
        """V9: Close positions held longer than max holding period"""
        MAX_HOLDING_DAYS = 90  # Verhoogd naar 90 dagen

        for symbol in list(self.open_positions.keys()):
            pos = self.open_positions[symbol]
            entry_date = pos["entry_date"]

            if isinstance(entry_date, datetime):
                holding_days = (trading_date - entry_date).days
            else:
                continue

            if holding_days >= MAX_HOLDING_DAYS:
                current_price = self._get_price_for_date(
                    price_data, symbol, trading_date
                )
                if current_price:
                    self._close_position(
                        symbol=symbol,
                        exit_price=current_price,
                        exit_date=trading_date,
                        exit_reason="time_based",
                        price_data=price_data,
                    )

    def _calculate_portfolio_value(
        self, price_data: Dict, target_date: datetime
    ) -> float:
        """Calculate current portfolio value"""
        value = self.cash
        for symbol, pos in self.open_positions.items():
            current_price = self._get_price_for_date(price_data, symbol, target_date)
            if current_price:
                value += pos["quantity"] * current_price
            else:
                value += pos["quantity"] * pos["entry_price"]
        return value

    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate max drawdown"""
        if not self.equity_curve:
            return 0.0, self.initial_capital

        peak = self.equity_curve[0]["portfolio_value"]
        max_dd = 0.0
        peak_val = peak

        for point in self.equity_curve:
            val = point["portfolio_value"]
            if val > peak:
                peak = val
                peak_val = val
            dd = (peak - val) / peak
            max_dd = max(max_dd, dd)

        return max_dd, peak_val

    def _generate_result(self, price_data: Dict) -> V11BacktestResult:
        """Generate final results"""
        final_value = self._calculate_portfolio_value(price_data, self.end_date)
        total_return = ((final_value / self.initial_capital) - 1) * 100
        max_dd, peak = self._calculate_max_drawdown()

        # Calculate Sharpe
        returns = []
        for i in range(1, len(self.equity_curve)):
            r = (
                self.equity_curve[i]["portfolio_value"]
                / self.equity_curve[i - 1]["portfolio_value"]
            ) - 1
            returns.append(r)

        volatility = statistics.stdev(returns) * (252**0.5) * 100 if returns else 0
        avg_return = statistics.mean(returns) * 252 * 100 if returns else 0
        sharpe = (avg_return / volatility) if volatility > 0 else 0

        # Trade stats
        sell_trades = [t for t in self.trades if t.action == "SELL"]
        winning_trades = sum(1 for t in sell_trades if t.is_winner)
        losing_trades = sum(1 for t in sell_trades if not t.is_winner)
        total_trades = len(sell_trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        winner_pnl = sum(t.realized_pnl for t in sell_trades if t.is_winner)
        loser_pnl = sum(t.realized_pnl for t in sell_trades if not t.is_winner)
        profit_factor = abs(winner_pnl / loser_pnl) if loser_pnl != 0 else float("inf")

        avg_trade_pnl = (
            sum(t.realized_pnl or 0 for t in sell_trades) / total_trades
            if total_trades > 0
            else 0
        )

        # Agent stats
        agent_stats = self.agent_manager.get_agent_stats()

        # Position size analysis
        avg_position_size = (
            (sum(self.position_sizes_taken) / len(self.position_sizes_taken))
            if self.position_sizes_taken
            else 0
        )

        symbol_pos_summary = {}
        for symbol, sizes in self.symbol_position_sizes.items():
            if sizes:
                symbol_pos_summary[symbol] = {
                    "avg": sum(sizes) / len(sizes),
                    "min": min(sizes),
                    "max": max(sizes),
                    "count": len(sizes),
                }

        # Harmony stats
        harmony_scores = [h["harmony"] for h in self.harmony_curve]
        avg_harmony = statistics.mean(harmony_scores) if harmony_scores else 0

        logger.info("\n" + "=" * 60)
        logger.info("V11 BACKTEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Final Value:          ${final_value:,.2f}")
        logger.info(f"Total Return:         {total_return:+.2f}%")
        logger.info(f"Max Drawdown:         {max_dd*100:.2f}%")
        logger.info(f"Sharpe Ratio:         {sharpe:.2f}")
        logger.info(f"Total Trades:         {total_trades}")
        logger.info(f"Win Rate:             {win_rate:.1f}%")
        logger.info(f"Position Review Exits: {self.position_review_exit_count}")
        logger.info(f"Normal Exits:         {self.normal_exit_count}")
        logger.info(
            f"Execute Rate:         {agent_stats.get('execute_rate_pct', 0):.2f}%"
        )
        logger.info(
            f"Consensus Rate:       {agent_stats.get('consensus_achieved_pct', 0):.2f}%"
        )
        logger.info(f"Avg Position Size:    ${avg_position_size:,.2f}")
        logger.info(f"Avg Harmony:          {avg_harmony:.4f}")

        logger.info("\nSymbol Position Summary (V9 Fire Sizing):")
        for symbol, summary in sorted(symbol_pos_summary.items())[:15]:
            logger.info(
                f"  {symbol:6s}: avg=${summary['avg']:8,.2f}, range=[${summary['min']:8,.2f}, ${summary['max']:8,.2f}], n={summary['count']}"
            )

        return V11BacktestResult(
            session_id=f"v9_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_date=self.start_date.isoformat(),
            end_date=self.end_date.isoformat(),
            symbols=self.symbols,
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return_pct=total_return,
            peak_value=peak,
            max_drawdown_pct=max_dd * 100,
            sharpe_ratio=sharpe,
            volatility_annual=volatility,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=win_rate,
            avg_trade_pnl=avg_trade_pnl,
            profit_factor=profit_factor,
            position_review_exits=self.position_review_exit_count,
            normal_exits=self.normal_exit_count,
            elemental_cycles=agent_stats.get("total_cycles", 0),
            avg_harmony_score=avg_harmony,
            execute_rate_pct=agent_stats.get("execute_rate_pct", 0),
            consensus_rate_pct=agent_stats.get("consensus_achieved_pct", 0),
            avg_position_size=avg_position_size,
            symbol_position_summary=symbol_pos_summary,
            agent_stats={k: v for k, v in agent_stats.items() if isinstance(v, dict)},
            trades=[t.to_dict() for t in self.trades],
            equity_curve=self.equity_curve,
            harmony_curve=self.harmony_curve,
        )


def main():
    """Run V11 smoke test (2021)"""
    symbols = ["BTC", "ETH", "SPY", "QQQ", "GLD", "AAPL", "MSFT", "UNI", "SOL"]

    engine = V11BacktestEngine(
        symbols=symbols,
        start_date="2021-01-01",
        end_date="2021-12-31",
        initial_capital=100000.0,
    )

    result = engine.run_backtest()

    output_file = f"backtest_v11_2021_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result.save(output_file)

    logger.info(f"\nResults saved to {output_file}")

    return result


if __name__ == "__main__":
    main()
