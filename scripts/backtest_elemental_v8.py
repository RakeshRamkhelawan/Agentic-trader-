"""
Elemental System Backtest V8 - SELF-DIRECTING POSITION SIZING

V8 Key Changes:
- Fire Agent has 60-day rolling volatility memory
- Fire fully autonomous for position sizing (no external constraints)
- Ether uses p75 harmony thresholds (~0.6398)
- Fire.record_price() called EVERY cycle for EVERY symbol
- Navagraha planet multipliers: MARS +40%, SATURN -40%

Expected V8 Results:
- UNI: small positions (<50 EUR) due to high volatility
- SPY: larger positions (200-800 EUR) due to low volatility
- Execute rate: 18-26%
- Consensus: >95%
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["TRADING_MODE"] = "paper"

import json
import time
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field, asdict

from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("BacktestV8")

# Import V8 Manager
from backend.agents.elemental_agent_manager_v8 import (
    ElementalAgentManagerV8, NavagrahaState
)


@dataclass
class Trade:
    trade_id: int
    timestamp: str
    symbol: str
    action: str  # BUY, SELL
    quantity: float
    price: float
    value: float
    position_size: float  # V8: Fire's autonomous size
    position_before: float = 0
    position_after: float = 0
    avg_entry_price: float = 0
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    is_winner: Optional[bool] = None
    is_loser: Optional[bool] = None
    harmony_score: float = 0.0
    dominant_planet: str = ""
    fire_decision: str = ""
    ether_decision: str = ""
    portfolio_value_before: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    total_invested: float = 0.0
    entry_date: str = ""
    
    def buy(self, qty: float, price: float):
        new_total_value = (self.quantity * self.avg_entry_price) + (qty * price)
        self.quantity += qty
        if self.quantity > 0:
            self.avg_entry_price = new_total_value / self.quantity
        self.total_invested += qty * price
    
    def sell(self, qty: float, price: float) -> Tuple[float, float]:
        if qty > self.quantity:
            qty = self.quantity
        cost_basis = qty * self.avg_entry_price
        sale_value = qty * price
        realized_pnl = sale_value - cost_basis
        realized_pnl_pct = (realized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        self.quantity -= qty
        if self.quantity <= 0.0001:
            self.quantity = 0
            self.avg_entry_price = 0
            self.total_invested = 0
        return realized_pnl, realized_pnl_pct
    
    def market_value(self, current_price: float) -> float:
        return self.quantity * current_price


@dataclass 
class V8BacktestResult:
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
    elemental_cycles: int
    avg_harmony_score: float
    fire_blocks: int
    ether_blocks: int
    consensus_trades: int
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
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class V8BacktestEngine:
    """V8 Backtest Engine with Fire Agent autonomous sizing"""
    
    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0
    ):
        self.symbols = symbols
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        self.initial_capital = initial_capital
        self.cash = initial_capital
        
        self.positions: Dict[str, Position] = {s: Position(s) for s in symbols}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.harmony_curve: List[Dict] = []
        
        self.agent_manager = ElementalAgentManagerV8()
        self.peak_value = initial_capital
        self.current_drawdown = 0.0
        
        # Stats
        self.fire_blocks = 0
        self.ether_blocks = 0
        self.consensus_trades = 0
        self.position_sizes_taken: List[float] = []  # Track Fire's position sizes
        self.symbol_position_sizes: Dict[str, List[float]] = defaultdict(list)
        
        # Database connection
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db"
        ).replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")
        
        self.trade_counter = 0
        
        logger.info("=" * 60)
        logger.info("V8: FIRE AGENT AUTONOMOUS POSITION SIZING")
        logger.info("=" * 60)
    
    def _get_price_data(self) -> Dict[str, List[Dict]]:
        """Fetch price data from database"""
        logger.info(f"Fetching data for {len(self.symbols)} symbols...")
        
        engine = create_engine(self.db_url)
        price_data = {}
        
        with engine.connect() as conn:
            for i, symbol in enumerate(self.symbols, 1):
                result = conn.execute(text("""
                    SELECT timestamp, close
                    FROM market_candles
                    WHERE symbol = :symbol
                      AND timestamp >= :start
                      AND timestamp <= :end
                    ORDER BY timestamp ASC
                """), {
                    "symbol": symbol,
                    "start": self.start_date.isoformat(),
                    "end": self.end_date.isoformat()
                })
                
                rows = [{"timestamp": row[0], "close": row[1]} for row in result]
                
                if rows:
                    price_data[symbol] = rows
                    if i <= 10 or i % 10 == 0:
                        logger.info(f"  [{i}/{len(self.symbols)}] {symbol}: {len(rows)} days")
        
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
    
    def _pre_seed_fire_agent(self, price_data: Dict[str, List[Dict]], start_date: datetime):
        """Pre-seed Fire Agent with 60 days of price history"""
        logger.info("Pre-seeding Fire Agent with 60-day volatility memory...")
        
        # Make start_date naive for comparison
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
            
            # Take last 60 rows
            seed_rows = pre_seed_rows[-60:] if len(pre_seed_rows) >= 60 else pre_seed_rows
            
            for row in seed_rows:
                self.agent_manager.fire_agent.record_price(symbol, row["close"])
            
            if len(seed_rows) > 0:
                logger.debug(f"  {symbol}: seeded with {len(seed_rows)} days")
    
    def run_backtest(self) -> V8BacktestResult:
        """Run the complete V8 backtest"""
        
        # Get price data
        price_data = self._get_price_data()
        if not price_data:
            raise ValueError("No price data found!")
        
        # Get trading dates
        trading_dates = self._get_trading_dates(price_data)
        
        # Pre-seed Fire Agent
        self._pre_seed_fire_agent(price_data, self.start_date)
        
        logger.info("\n" + "=" * 60)
        logger.info("STARTING V8 BACKTEST")
        logger.info("=" * 60)
        
        cycle_count = 0
        
        for trading_date in trading_dates:
            date_str = trading_date.strftime("%Y-%m-%d")
            
            # Get prices for this date
            day_prices = {}
            for symbol in self.symbols:
                price = self._get_price_for_date(price_data, symbol, trading_date)
                if price:
                    day_prices[symbol] = price
            
            if not day_prices:
                continue
            
            # Process each symbol
            self._process_day(trading_date, day_prices)
            cycle_count += len(day_prices)
            
            # Progress update
            if cycle_count % 500 == 0:
                portfolio_val = self._calculate_portfolio_value(day_prices)
                logger.info(f"Processed {cycle_count} cycles | Portfolio: ${portfolio_val:,.2f}")
        
        return self._generate_result()
    
    def _get_price_for_date(self, price_data: Dict, symbol: str, target_date: datetime) -> Optional[float]:
        """Get price for specific symbol and date"""
        if symbol not in price_data:
            return None
        
        target_naive = target_date.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
        
        for row in price_data[symbol]:
            ts = row["timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts = ts.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            
            if ts == target_naive:
                return row["close"]
        
        return None
    
    def _process_day(self, trading_date: datetime, day_prices: Dict[str, float]):
        """Process one trading day"""
        prana_level = 85.0
        portfolio_value = self._calculate_portfolio_value(day_prices)
        
        for symbol, current_price in day_prices.items():
            # V8: Fire records price EVERY cycle, even on BLOCK
            self.agent_manager.fire_agent.record_price(symbol, current_price)
            
            # Run agent cycle
            synthesis = self.agent_manager.process_trading_cycle(
                symbol=symbol,
                current_price=current_price,
                portfolio_value=portfolio_value,
                current_positions=self.positions,
                prana_level=prana_level
            )
            
            # Track blocks
            if synthesis.blocking_agent == "fire":
                self.fire_blocks += 1
            elif synthesis.blocking_agent == "ether":
                self.ether_blocks += 1
            
            if synthesis.consensus_achieved:
                self.consensus_trades += 1
            
            # Record harmony
            self.harmony_curve.append({
                "timestamp": trading_date.isoformat(),
                "symbol": symbol,
                "harmony": synthesis.harmony_score,
                "consensus": synthesis.consensus_achieved,
                "planet": self._get_planet_for_date(trading_date)
            })
            
            # Execute trade
            if synthesis.final_decision == "EXECUTE" and synthesis.approved_action:
                self._execute_trade(
                    symbol=symbol,
                    action=synthesis.approved_action,
                    position_size=synthesis.approved_qty,  # V8: Fire's size
                    price=current_price,
                    date=trading_date,
                    harmony=synthesis.harmony_score,
                    planet=self._get_planet_for_date(trading_date)
                )
        
        # Update equity curve
        final_value = self._calculate_portfolio_value(day_prices)
        self.equity_curve.append({
            "timestamp": trading_date.isoformat(),
            "portfolio_value": final_value,
            "cash": self.cash,
            "positions_value": final_value - self.cash
        })
        
        # Update peak/drawdown
        if final_value > self.peak_value:
            self.peak_value = final_value
        self.current_drawdown = (self.peak_value - final_value) / self.peak_value
    
    def _get_planet_for_date(self, dt: datetime) -> str:
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        return planets[dt.day % 7]
    
    def _execute_trade(self, symbol: str, action: str, position_size: float,
                       price: float, date: datetime, harmony: float, planet: str):
        """Execute trade with V8 Fire-determined position size"""
        
        position = self.positions[symbol]
        portfolio_val = self.cash + sum(
            pos.market_value(price) for pos in self.positions.values()
        )
        
        if action == "BUY" and position.quantity == 0:
            # V8: Use Fire's autonomous position size
            qty = int(position_size / price)
            cost = qty * price
            
            if self.cash >= cost and qty > 0:
                position_before = position.quantity
                position.buy(qty, price)
                position.entry_date = date.isoformat()
                
                self.cash -= cost
                self.trade_counter += 1
                
                # Track position sizes
                self.position_sizes_taken.append(position_size)
                self.symbol_position_sizes[symbol].append(position_size)
                
                trade = Trade(
                    trade_id=self.trade_counter,
                    timestamp=date.isoformat(),
                    symbol=symbol,
                    action="BUY",
                    quantity=qty,
                    price=price,
                    value=cost,
                    position_size=position_size,  # V8: Store Fire's size
                    position_before=position_before,
                    position_after=position.quantity,
                    avg_entry_price=position.avg_entry_price,
                    harmony_score=harmony,
                    dominant_planet=planet,
                    portfolio_value_before=portfolio_val
                )
                self.trades.append(trade)
        
        elif action == "SELL" and position.quantity > 0:
            self._close_position(symbol, price, date, planet)
    
    def _close_position(self, symbol: str, exit_price: float, exit_date: datetime, planet: str):
        """Close position and record outcome"""
        position = self.positions[symbol]
        if position.quantity <= 0:
            return
        
        qty = position.quantity
        realized_pnl, realized_pnl_pct = position.sell(qty, exit_price)
        proceeds = qty * exit_price
        
        self.cash += proceeds
        self.trade_counter += 1
        
        # Feedback to agents
        self.agent_manager.record_trade_outcome(symbol, realized_pnl, realized_pnl_pct)
        
        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=exit_date.isoformat(),
            symbol=symbol,
            action="SELL",
            quantity=qty,
            price=exit_price,
            value=proceeds,
            position_size=0,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            is_winner=realized_pnl > 0,
            is_loser=realized_pnl < 0,
            dominant_planet=planet,
            portfolio_value_before=self.cash - proceeds
        )
        self.trades.append(trade)
    
    def _calculate_portfolio_value(self, day_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value"""
        value = self.cash
        for symbol, position in self.positions.items():
            price = day_prices.get(symbol, position.avg_entry_price)
            value += position.market_value(price)
        return value
    
    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate max drawdown from equity curve"""
        if not self.equity_curve:
            return 0.0, 0.0
        
        peak = self.equity_curve[0]["portfolio_value"]
        max_dd = 0.0
        peak_value = peak
        
        for point in self.equity_curve:
            val = point["portfolio_value"]
            if val > peak:
                peak = val
                peak_value = val
            dd = (peak - val) / peak
            max_dd = max(max_dd, dd)
        
        return max_dd, peak_value
    
    def _generate_result(self) -> V8BacktestResult:
        """Generate final backtest results"""
        final_value = self.cash + sum(
            pos.market_value(pos.avg_entry_price) for pos in self.positions.values()
        )
        
        total_return = ((final_value / self.initial_capital) - 1) * 100
        max_dd, peak = self._calculate_max_drawdown()
        
        # Calculate returns for Sharpe
        returns = []
        for i in range(1, len(self.equity_curve)):
            r = (self.equity_curve[i]["portfolio_value"] / 
                 self.equity_curve[i-1]["portfolio_value"]) - 1
            returns.append(r)
        
        volatility = statistics.stdev(returns) * (252 ** 0.5) * 100 if returns else 0
        avg_return = statistics.mean(returns) * 252 * 100 if returns else 0
        sharpe = (avg_return / volatility) if volatility > 0 else 0
        
        # Trade stats
        winning_trades = sum(1 for t in self.trades if t.is_winner)
        losing_trades = sum(1 for t in self.trades if t.is_loser)
        total_trades = len(self.trades)
        win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
        
        winner_pnl = sum(t.realized_pnl for t in self.trades if t.is_winner)
        loser_pnl = sum(t.realized_pnl for t in self.trades if t.is_loser)
        profit_factor = abs(winner_pnl / loser_pnl) if loser_pnl != 0 else float('inf')
        
        avg_trade_pnl = sum(t.realized_pnl or 0 for t in self.trades) / total_trades if total_trades > 0 else 0
        
        # Agent stats
        agent_stats = self.agent_manager.get_agent_stats()
        
        # Position size analysis
        avg_position_size = (sum(self.position_sizes_taken) / len(self.position_sizes_taken)) if self.position_sizes_taken else 0
        
        symbol_pos_summary = {}
        for symbol, sizes in self.symbol_position_sizes.items():
            if sizes:
                symbol_pos_summary[symbol] = {
                    "avg": sum(sizes) / len(sizes),
                    "min": min(sizes),
                    "max": max(sizes),
                    "count": len(sizes)
                }
        
        # Harmony stats
        harmony_scores = [h["harmony"] for h in self.harmony_curve]
        avg_harmony = statistics.mean(harmony_scores) if harmony_scores else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("V8 BACKTEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Final Value:          ${final_value:,.2f}")
        logger.info(f"Total Return:         {total_return:+.2f}%")
        logger.info(f"Max Drawdown:         {max_dd*100:.2f}%")
        logger.info(f"Sharpe Ratio:         {sharpe:.2f}")
        logger.info(f"Total Trades:         {total_trades}")
        logger.info(f"Win Rate:             {win_rate:.1f}%")
        logger.info(f"Execute Rate:         {agent_stats.get('execute_rate_pct', 0):.2f}%")
        logger.info(f"Consensus Rate:       {agent_stats.get('consensus_achieved_pct', 0):.2f}%")
        logger.info(f"Avg Position Size:    ${avg_position_size:,.2f}")
        logger.info(f"Avg Harmony:          {avg_harmony:.4f}")
        
        logger.info("\nSymbol Position Summary (V8 Fire Sizing):")
        for symbol, summary in sorted(symbol_pos_summary.items()):
            logger.info(f"  {symbol:6s}: avg=${summary['avg']:8,.2f}, range=[${summary['min']:8,.2f}, ${summary['max']:8,.2f}], n={summary['count']}")
        
        return V8BacktestResult(
            session_id=f"v8_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
            elemental_cycles=agent_stats.get("total_cycles", 0),
            avg_harmony_score=avg_harmony,
            fire_blocks=self.fire_blocks,
            ether_blocks=self.ether_blocks,
            consensus_trades=self.consensus_trades,
            execute_rate_pct=agent_stats.get("execute_rate_pct", 0),
            consensus_rate_pct=agent_stats.get("consensus_achieved_pct", 0),
            avg_position_size=avg_position_size,
            symbol_position_summary=symbol_pos_summary,
            agent_stats={k: v for k, v in agent_stats.items() if isinstance(v, dict)},
            trades=[t.to_dict() for t in self.trades],
            equity_curve=self.equity_curve,
            harmony_curve=self.harmony_curve
        )


def main():
    """Run V8 smoke test (2021)"""
    # Use a subset of symbols for faster testing
    symbols = ["BTC", "ETH", "SPY", "QQQ", "GLD", "AAPL", "MSFT", "UNI", "SOL"]
    
    engine = V8BacktestEngine(
        symbols=symbols,
        start_date="2021-01-01",
        end_date="2021-12-31",
        initial_capital=100000.0
    )
    
    result = engine.run_backtest()
    
    # Save results
    result.save(f"backtest_v8_2021_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    return result


if __name__ == "__main__":
    main()
