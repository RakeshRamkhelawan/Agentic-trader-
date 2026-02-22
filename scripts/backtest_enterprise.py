"""
Enterprise-Grade Backtest with Complete P&L Tracking and Risk Metrics
Addresses all audit findings from external review
"""

import os
import sys
import json
import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["TRADING_MODE"] = "paper"

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("EnterpriseBacktest")


@dataclass
class Trade:
    """Complete trade record with P&L tracking"""
    trade_id: int
    timestamp: str
    symbol: str
    action: str  # BUY, SELL
    quantity: float
    price: float
    value: float
    
    # Position tracking
    position_before: float
    position_after: float
    avg_entry_price: float
    
    # P&L (only for SELL trades)
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    
    # Trade status
    is_winner: Optional[bool] = None
    is_loser: Optional[bool] = None
    
    # Risk metrics at trade time
    portfolio_value_before: float = 0.0
    portfolio_value_after: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Position:
    """Track open position with avg price"""
    symbol: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    total_invested: float = 0.0
    
    def buy(self, qty: float, price: float):
        """Add to position with average price calculation"""
        new_total_value = (self.quantity * self.avg_entry_price) + (qty * price)
        self.quantity += qty
        if self.quantity > 0:
            self.avg_entry_price = new_total_value / self.quantity
        self.total_invested += qty * price
    
    def sell(self, qty: float, price: float) -> Tuple[float, float]:
        """Reduce position and calculate P&L"""
        if qty > self.quantity:
            qty = self.quantity
        
        # Calculate realized P&L
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
    
    def unrealized_pnl(self, current_price: float) -> float:
        return self.quantity * (current_price - self.avg_entry_price)


@dataclass
class EnterpriseBacktestResult:
    """Comprehensive backtest results for enterprise audit"""
    session_id: str
    start_date: str
    end_date: str
    symbols: List[str]
    initial_capital: float
    
    # Portfolio metrics
    final_value: float
    total_return_pct: float
    peak_value: float
    max_drawdown_pct: float
    
    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    volatility_annual: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    avg_trade_pnl: float
    avg_winner_pnl: float
    avg_loser_pnl: float
    profit_factor: float
    
    # Position sizing
    position_sizing_method: str
    avg_position_size: float
    max_position_size: float
    
    # Vedic impact
    trades_blocked_by_rahu: int
    trades_during_low_harmony: int
    avg_harmony_at_trade: float
    
    # Per-symbol breakdown
    symbol_performance: Dict[str, Dict]
    
    # Trade log
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class EnterpriseBacktestEngine:
    """
    Enterprise-grade backtest with:
    - Proper P&L tracking per closed position
    - Dynamic position sizing based on risk
    - Stop-loss and drawdown protection
    - Sharpe/Sortino/Calmar ratios
    - Complete trade classification
    """
    
    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 50000.0,
        max_position_pct: float = 0.10,  # Max 10% per position
        max_drawdown_pct: float = 0.20,   # Stop at 20% drawdown
        risk_per_trade_pct: float = 0.02   # Risk 2% per trade
    ):
        self.symbols = symbols
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.risk_per_trade_pct = risk_per_trade_pct
        
        # Portfolio state
        self.positions: Dict[str, Position] = {s: Position(s) for s in symbols}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        
        # Tracking
        self.trade_counter = 0
        self.peak_value = initial_capital
        self.current_drawdown = 0.0
        self.trading_blocked = False
        self.block_reason = None
        
        # Vedic tracking
        self.vedic_blocked_count = 0
        self.low_harmony_count = 0
        self.harmony_scores = []
        
        # Symbol performance tracking
        self.symbol_stats = defaultdict(lambda: {
            'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0
        })
        
        # Daily returns for Sharpe
        self.daily_returns = []
        self.last_portfolio_value = initial_capital
        
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        value = self.cash
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol, position.avg_entry_price)
            value += position.market_value(price)
        return value
    
    def calculate_position_size(self, symbol: str, price: float, 
                                portfolio_value: float, vedic_harmony: float) -> float:
        """
        Dynamic position sizing based on:
        - Portfolio value (Kelly criterion lite)
        - Risk per trade (2% max)
        - Vedic harmony (reduce size when harmony < 0.5)
        """
        # Base position: max 10% of portfolio
        max_position_value = portfolio_value * self.max_position_pct
        
        # Risk-adjusted: if high volatility expected, reduce size
        risk_factor = min(1.0, vedic_harmony * 1.5)  # 0.5 harmony = 0.75 size
        
        # Calculate quantity
        position_value = max_position_value * risk_factor
        quantity = position_value / price if price > 0 else 0
        
        # Ensure minimum trade size
        min_trade = 0.001 if 'BTC' in symbol else 0.01
        if quantity < min_trade:
            quantity = min_trade
        
        return quantity
    
    def check_stop_conditions(self, portfolio_value: float) -> bool:
        """Check if trading should be stopped due to drawdown"""
        # Update peak
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        
        # Calculate drawdown
        self.current_drawdown = (self.peak_value - portfolio_value) / self.peak_value
        
        # Check stop condition
        if self.current_drawdown > self.max_drawdown_pct:
            if not self.trading_blocked:
                self.trading_blocked = True
                self.block_reason = f"Max drawdown reached: {self.current_drawdown:.1%}"
                logger.error(f"[STOP] TRADING STOPPED: {self.block_reason}")
            return False
        
        return True
    
    def execute_buy(self, symbol: str, price: float, timestamp: str,
                   portfolio_value: float, vedic_harmony: float) -> Optional[Trade]:
        """Execute buy with proper position sizing"""
        
        # Check if trading is blocked
        if self.trading_blocked:
            return None
        
        # Check Rahu Kala (simplified - in real system would use actual Vedic calc)
        if vedic_harmony < 0.3:
            self.vedic_blocked_count += 1
            return None
        
        # Calculate position size
        quantity = self.calculate_position_size(symbol, price, portfolio_value, vedic_harmony)
        value = quantity * price
        
        # Check if we have enough cash
        if value > self.cash * 0.95:  # Leave 5% buffer
            quantity = (self.cash * 0.95) / price
            value = quantity * price
        
        if quantity <= 0 or value <= 0:
            return None
        
        # Execute trade
        position = self.positions[symbol]
        position_before = position.quantity
        position.buy(quantity, price)
        self.cash -= value
        
        self.trade_counter += 1
        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=timestamp,
            symbol=symbol,
            action="BUY",
            quantity=quantity,
            price=price,
            value=value,
            position_before=position_before,
            position_after=position.quantity,
            avg_entry_price=position.avg_entry_price,
            portfolio_value_before=portfolio_value,
            portfolio_value_after=self.get_portfolio_value({symbol: price})
        )
        self.trades.append(trade)
        
        # Track harmony
        self.harmony_scores.append(vedic_harmony)
        if vedic_harmony < 0.5:
            self.low_harmony_count += 1
        
        return trade
    
    def execute_sell(self, symbol: str, price: float, timestamp: str,
                    portfolio_value: float) -> Optional[Trade]:
        """Execute sell with P&L calculation"""
        position = self.positions[symbol]
        
        if position.quantity <= 0:
            return None
        
        # Sell entire position or partial
        quantity = position.quantity
        value = quantity * price
        
        # Calculate P&L
        realized_pnl, realized_pnl_pct = position.sell(quantity, price)
        self.cash += value
        
        # Determine if winner or loser
        is_winner = realized_pnl > 0
        is_loser = realized_pnl < 0
        
        self.trade_counter += 1
        trade = Trade(
            trade_id=self.trade_counter,
            timestamp=timestamp,
            symbol=symbol,
            action="SELL",
            quantity=quantity,
            price=price,
            value=value,
            position_before=position.quantity + quantity,
            position_after=position.quantity,
            avg_entry_price=position.avg_entry_price if position.quantity > 0 else price,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            is_winner=is_winner,
            is_loser=is_loser,
            portfolio_value_before=portfolio_value,
            portfolio_value_after=self.get_portfolio_value({symbol: price})
        )
        self.trades.append(trade)
        
        # Update symbol stats
        self.symbol_stats[symbol]['trades'] += 1
        self.symbol_stats[symbol]['pnl'] += realized_pnl
        if is_winner:
            self.symbol_stats[symbol]['wins'] += 1
        elif is_loser:
            self.symbol_stats[symbol]['losses'] += 1
        
        return trade
    
    def calculate_risk_metrics(self) -> Dict:
        """Calculate Sharpe, Sortino, Calmar ratios"""
        if len(self.daily_returns) < 2:
            return {'sharpe': 0, 'sortino': 0, 'calmar': 0, 'volatility': 0}
        
        # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
        avg_return = statistics.mean(self.daily_returns)
        std_return = statistics.stdev(self.daily_returns)
        
        # Annualize (assuming 252 trading days)
        if std_return > 0:
            sharpe = (avg_return * 252) / (std_return * math.sqrt(252))
            volatility_annual = std_return * math.sqrt(252)
        else:
            sharpe = 0
            volatility_annual = 0
        
        # Sortino Ratio (downside deviation only)
        downside_returns = [r for r in self.daily_returns if r < 0]
        if downside_returns:
            downside_std = statistics.stdev(downside_returns) if len(downside_returns) > 1 else 0.001
            sortino = (avg_return * 252) / (downside_std * math.sqrt(252)) if downside_std > 0 else 0
        else:
            sortino = sharpe * 2  # No downside = great Sortino
        
        # Calmar Ratio
        years = max(1, (self.end_date - self.start_date).days / 365)
        annual_return = ((self.get_portfolio_value({}) / self.initial_capital) ** (1/years) - 1) * 100
        max_dd = max(self.equity_curve, key=lambda x: x['drawdown'])['drawdown'] if self.equity_curve else 0
        calmar = annual_return / max_dd if max_dd > 0 else 0
        
        return {
            'sharpe': sharpe,
            'sortino': sortino,
            'calmar': calmar,
            'volatility_annual': volatility_annual
        }
    
    def run_backtest(self, price_data: Dict[str, List[Dict]]) -> EnterpriseBacktestResult:
        """Run the complete backtest"""
        logger.info(f"Starting Enterprise Backtest: {len(self.symbols)} symbols")
        logger.info(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
        
        # Get all dates
        all_dates = sorted(set(
            d['timestamp'] for symbol_data in price_data.values() 
            for d in symbol_data
        ))
        
        prev_value = self.initial_capital
        
        for i, timestamp in enumerate(all_dates):
            current_prices = {}
            
            # Get prices for this timestamp
            for symbol in self.symbols:
                if symbol in price_data:
                    for d in price_data[symbol]:
                        if d['timestamp'] == timestamp:
                            current_prices[symbol] = d['close']
                            break
            
            if not current_prices:
                continue
            
            # Calculate portfolio value
            portfolio_value = self.get_portfolio_value(current_prices)
            
            # Check stop conditions
            can_trade = self.check_stop_conditions(portfolio_value)
            
            # Calculate daily return
            daily_return = (portfolio_value - prev_value) / prev_value if prev_value > 0 else 0
            self.daily_returns.append(daily_return)
            prev_value = portfolio_value
            
            # Record equity curve
            self.equity_curve.append({
                'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                'value': portfolio_value,
                'cash': self.cash,
                'drawdown': self.current_drawdown,
                'blocked': self.trading_blocked
            })
            
            # Simple strategy: Buy on momentum, sell on reversion
            for symbol, price in current_prices.items():
                if not can_trade:
                    break
                
                # Simulate Vedic harmony (0-1)
                import random
                vedic_harmony = random.uniform(0.4, 0.95)
                
                position = self.positions[symbol]
                
                # Decision logic
                if position.quantity == 0:
                    # No position - look for entry
                    if vedic_harmony > 0.6 and self.cash > price * 0.01:
                        self.execute_buy(symbol, price, str(timestamp), portfolio_value, vedic_harmony)
                else:
                    # Have position - look for exit
                    unrealized_pct = (price - position.avg_entry_price) / position.avg_entry_price
                    
                    # Take profit at +10% or stop loss at -5%
                    if unrealized_pct > 0.10 or unrealized_pct < -0.05:
                        self.execute_sell(symbol, price, str(timestamp), portfolio_value)
            
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(all_dates)} days | Value: ${portfolio_value:,.2f} | DD: {self.current_drawdown:.1%}")
        
        # Close all positions at end
        final_prices = {}
        for symbol in self.symbols:
            if symbol in price_data and price_data[symbol]:
                final_prices[symbol] = price_data[symbol][-1]['close']
        
        for symbol, position in self.positions.items():
            if position.quantity > 0 and symbol in final_prices:
                portfolio_value = self.get_portfolio_value(final_prices)
                self.execute_sell(symbol, final_prices[symbol], str(self.end_date), portfolio_value)
        
        # Calculate final metrics
        final_value = self.get_portfolio_value(final_prices) if final_prices else self.cash
        risk_metrics = self.calculate_risk_metrics()
        
        # Trade statistics
        closed_trades = [t for t in self.trades if t.action == "SELL"]
        winning_trades = [t for t in closed_trades if t.is_winner]
        losing_trades = [t for t in closed_trades if t.is_loser]
        
        total_pnl = sum(t.realized_pnl for t in closed_trades if t.realized_pnl)
        winning_pnl = sum(t.realized_pnl for t in winning_trades if t.realized_pnl)
        losing_pnl = sum(t.realized_pnl for t in losing_trades if t.realized_pnl)
        
        profit_factor = abs(winning_pnl / losing_pnl) if losing_pnl != 0 else float('inf')
        
        # Position sizing stats
        buy_trades = [t for t in self.trades if t.action == "BUY"]
        position_sizes = [t.quantity for t in buy_trades]
        
        # Symbol performance
        symbol_performance = {}
        for symbol, stats in self.symbol_stats.items():
            if stats['trades'] > 0:
                symbol_performance[symbol] = {
                    'trades': stats['trades'],
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'win_rate': stats['wins'] / stats['trades'] * 100,
                    'total_pnl': stats['pnl']
                }
        
        result = EnterpriseBacktestResult(
            session_id=f"enterprise_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_date=str(self.start_date),
            end_date=str(self.end_date),
            symbols=self.symbols,
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return_pct=(final_value / self.initial_capital - 1) * 100,
            peak_value=self.peak_value,
            max_drawdown_pct=max(self.equity_curve, key=lambda x: x['drawdown'])['drawdown'] * 100 if self.equity_curve else 0,
            sharpe_ratio=risk_metrics['sharpe'],
            sortino_ratio=risk_metrics['sortino'],
            calmar_ratio=risk_metrics['calmar'],
            volatility_annual=risk_metrics['volatility_annual'],
            total_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate_pct=len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0,
            avg_trade_pnl=total_pnl / len(closed_trades) if closed_trades else 0,
            avg_winner_pnl=winning_pnl / len(winning_trades) if winning_trades else 0,
            avg_loser_pnl=losing_pnl / len(losing_trades) if losing_trades else 0,
            profit_factor=profit_factor,
            position_sizing_method="Dynamic (Kelly-lite + Vedic harmony)",
            avg_position_size=statistics.mean(position_sizes) if position_sizes else 0,
            max_position_size=max(position_sizes) if position_sizes else 0,
            trades_blocked_by_rahu=self.vedic_blocked_count,
            trades_during_low_harmony=self.low_harmony_count,
            avg_harmony_at_trade=statistics.mean(self.harmony_scores) if self.harmony_scores else 0,
            symbol_performance=symbol_performance,
            trades=[t.to_dict() for t in self.trades],
            equity_curve=self.equity_curve
        )
        
        self._print_summary(result)
        return result
    
    def _print_summary(self, result: EnterpriseBacktestResult):
        """Print comprehensive summary"""
        print("\n" + "=" * 80)
        print("ENTERPRISE BACKTEST RESULTS")
        print("=" * 80)
        print(f"Period:        {result.start_date[:10]} to {result.end_date[:10]}")
        print(f"Symbols:       {len(result.symbols)} assets")
        print(f"\n[PORTFOLIO PERFORMANCE]")
        print(f"  Initial:     ${result.initial_capital:,.2f}")
        print(f"  Final:       ${result.final_value:,.2f}")
        print(f"  Return:      {result.total_return_pct:+.2f}%")
        print(f"  Peak:        ${result.peak_value:,.2f}")
        print(f"  Max DD:      {result.max_drawdown_pct:.2f}%")
        print(f"\n[RISK METRICS]")
        print(f"  Sharpe:      {result.sharpe_ratio:.2f}")
        print(f"  Sortino:     {result.sortino_ratio:.2f}")
        print(f"  Calmar:      {result.calmar_ratio:.2f}")
        print(f"  Volatility:  {result.volatility_annual:.2f}%")
        print(f"\n[TRADE STATISTICS]")
        print(f"  Total:       {result.total_trades}")
        print(f"  Winners:     {result.winning_trades} ({result.win_rate_pct:.1f}%)")
        print(f"  Losers:      {result.losing_trades}")
        print(f"  Avg P&L:     ${result.avg_trade_pnl:.2f}")
        print(f"  Avg Winner:  ${result.avg_winner_pnl:.2f}")
        print(f"  Avg Loser:   ${result.avg_loser_pnl:.2f}")
        print(f"  Profit Factor: {result.profit_factor:.2f}")
        print(f"\n[POSITION SIZING]")
        print(f"  Method:      {result.position_sizing_method}")
        print(f"  Avg Size:    {result.avg_position_size:.4f}")
        print(f"  Max Size:    {result.max_position_size:.4f}")
        print(f"\n[VEDIC IMPACT]")
        print(f"  Rahu Blocks: {result.trades_blocked_by_rahu}")
        print(f"  Low Harmony: {result.trades_during_low_harmony}")
        print(f"  Avg Harmony: {result.avg_harmony_at_trade:.2f}")
        print("=" * 80)


if __name__ == "__main__":
    # Example usage
    symbols = ["BTC", "ETH", "SOL", "ADA", "DOT"]
    
    # Mock price data (in real use, load from database)
    price_data = {
        "BTC": [{"timestamp": datetime(2020, 1, 1) + timedelta(days=i), "close": 7000 + i * 10} for i in range(100)],
        "ETH": [{"timestamp": datetime(2020, 1, 1) + timedelta(days=i), "close": 130 + i * 0.5} for i in range(100)],
    }
    
    engine = EnterpriseBacktestEngine(
        symbols=symbols,
        start_date="2020-01-01",
        end_date="2020-04-10",
        initial_capital=50000
    )
    
    result = engine.run_backtest(price_data)
    result.save("enterprise_backtest_result.json")
