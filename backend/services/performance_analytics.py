"""
Performance Analytics Service.

Calculates trading performance metrics including Sharpe Ratio,
Sortino Ratio, Max Drawdown, Win Rate, and Profit Factor.
"""
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum


@dataclass
class TradeResult:
    """Individual trade result for analytics."""
    pnl: float
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    symbol: str = ""
    side: str = "BUY"
    
    @property
    def return_pct(self) -> float:
        """Calculate percentage return."""
        if self.entry_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) / self.entry_price * 100


@dataclass
class EquityPoint:
    """Point on equity curve."""
    timestamp: datetime
    equity: float
    drawdown: float = 0.0


@dataclass
class PerformanceReport:
    """Complete performance report."""
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    avg_win: float
    avg_loss: float
    calmar_ratio: float
    period_days: int


class PerformanceAnalytics:
    """
    Service for calculating trading performance metrics.
    
    Supports both in-memory trade lists and ClickHouse integration.
    """
    
    # Risk-free rate (annual, e.g., 2% treasury)
    RISK_FREE_RATE = 0.02
    TRADING_DAYS_PER_YEAR = 252
    
    def __init__(
        self,
        clickhouse_client: Optional[Any] = None,
        risk_free_rate: float = 0.02
    ):
        """
        Initialize analytics service.
        
        Args:
            clickhouse_client: Optional ClickHouse client for DB queries
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.clickhouse = clickhouse_client
        self.risk_free_rate = risk_free_rate
        self._trades: List[TradeResult] = []
    
    def add_trade(self, trade: TradeResult) -> None:
        """Add a trade result for analysis."""
        self._trades.append(trade)
    
    def add_trades(self, trades: List[TradeResult]) -> None:
        """Add multiple trade results."""
        self._trades.extend(trades)
    
    def clear_trades(self) -> None:
        """Clear all stored trades."""
        self._trades = []
    
    def _get_returns(self, trades: Optional[List[TradeResult]] = None) -> List[float]:
        """Get list of returns from trades."""
        trades = trades or self._trades
        return [t.pnl for t in trades]
    
    def _get_daily_returns(self, trades: Optional[List[TradeResult]] = None) -> Dict[str, float]:
        """Aggregate returns by day."""
        trades = trades or self._trades
        daily: Dict[str, float] = {}
        
        for t in trades:
            if t.exit_time:
                day = t.exit_time.strftime("%Y-%m-%d")
            else:
                day = datetime.utcnow().strftime("%Y-%m-%d")
            daily[day] = daily.get(day, 0) + t.pnl
        
        return daily
    
    def calculate_sharpe_ratio(
        self,
        trades: Optional[List[TradeResult]] = None,
        period_days: int = 30
    ) -> float:
        """
        Calculate annualized Sharpe Ratio.
        
        Sharpe = (mean_return - risk_free) / std_dev * sqrt(252)
        
        Args:
            trades: Optional trade list (uses stored trades if None)
            period_days: Period for calculation
            
        Returns:
            Annualized Sharpe Ratio
        """
        returns = self._get_returns(trades)
        
        if len(returns) < 2:
            return 0.0
        
        try:
            mean_return = statistics.mean(returns)
            std_dev = statistics.stdev(returns)
            
            if std_dev == 0:
                return 0.0
            
            # Daily risk-free rate
            daily_rf = self.risk_free_rate / self.TRADING_DAYS_PER_YEAR
            
            # Sharpe calculation
            sharpe = (mean_return - daily_rf) / std_dev
            
            # Annualize (sqrt of trading days)
            return sharpe * (self.TRADING_DAYS_PER_YEAR ** 0.5)
        except Exception:
            return 0.0
    
    def calculate_sortino_ratio(
        self,
        trades: Optional[List[TradeResult]] = None,
        period_days: int = 30
    ) -> float:
        """
        Calculate annualized Sortino Ratio.
        
        Like Sharpe but only penalizes downside volatility.
        
        Args:
            trades: Optional trade list
            period_days: Period for calculation
            
        Returns:
            Annualized Sortino Ratio
        """
        returns = self._get_returns(trades)
        
        if len(returns) < 2:
            return 0.0
        
        try:
            mean_return = statistics.mean(returns)
            
            # Only negative returns for downside deviation
            negative_returns = [r for r in returns if r < 0]
            
            if len(negative_returns) < 2:
                return float('inf') if mean_return > 0 else 0.0
            
            downside_dev = statistics.stdev(negative_returns)
            
            if downside_dev == 0:
                return float('inf') if mean_return > 0 else 0.0
            
            daily_rf = self.risk_free_rate / self.TRADING_DAYS_PER_YEAR
            sortino = (mean_return - daily_rf) / downside_dev
            
            return sortino * (self.TRADING_DAYS_PER_YEAR ** 0.5)
        except Exception:
            return 0.0
    
    def calculate_max_drawdown(
        self,
        trades: Optional[List[TradeResult]] = None
    ) -> float:
        """
        Calculate Maximum Drawdown.
        
        Largest peak-to-trough decline in equity curve.
        
        Args:
            trades: Optional trade list
            
        Returns:
            Max drawdown as percentage (0.15 = 15%)
        """
        equity_curve = self.get_equity_curve(trades)
        
        if not equity_curve:
            return 0.0
        
        peak = equity_curve[0].equity
        max_dd = 0.0
        
        for point in equity_curve:
            if point.equity > peak:
                peak = point.equity
            
            if peak > 0:
                drawdown = (peak - point.equity) / peak
                max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def calculate_win_rate(
        self,
        trades: Optional[List[TradeResult]] = None
    ) -> float:
        """
        Calculate win rate percentage.
        
        Args:
            trades: Optional trade list
            
        Returns:
            Win rate (0.6 = 60%)
        """
        trades = trades or self._trades
        
        if not trades:
            return 0.0
        
        winners = sum(1 for t in trades if t.pnl > 0)
        return winners / len(trades)
    
    def calculate_profit_factor(
        self,
        trades: Optional[List[TradeResult]] = None
    ) -> float:
        """
        Calculate Profit Factor.
        
        Gross Profit / Gross Loss
        
        Args:
            trades: Optional trade list
            
        Returns:
            Profit factor (>1 is profitable)
        """
        trades = trades or self._trades
        
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def get_equity_curve(
        self,
        trades: Optional[List[TradeResult]] = None,
        initial_equity: float = 10000.0
    ) -> List[EquityPoint]:
        """
        Generate equity curve from trades.
        
        Args:
            trades: Optional trade list
            initial_equity: Starting equity
            
        Returns:
            List of equity points with drawdown
        """
        trades = trades or self._trades
        
        if not trades:
            return []
        
        curve = []
        equity = initial_equity
        peak = initial_equity
        
        # Sort by exit time if available
        sorted_trades = sorted(
            trades,
            key=lambda t: t.exit_time or datetime.utcnow()
        )
        
        for trade in sorted_trades:
            equity += trade.pnl
            
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak if peak > 0 else 0.0
            
            curve.append(EquityPoint(
                timestamp=trade.exit_time or datetime.utcnow(),
                equity=equity,
                drawdown=drawdown
            ))
        
        return curve
    
    def generate_report(
        self,
        trades: Optional[List[TradeResult]] = None,
        period_days: int = 30
    ) -> PerformanceReport:
        """
        Generate complete performance report.
        
        Args:
            trades: Optional trade list
            period_days: Period for time-based metrics
            
        Returns:
            PerformanceReport with all metrics
        """
        trades = trades or self._trades
        
        winners = [t for t in trades if t.pnl > 0]
        losers = [t for t in trades if t.pnl < 0]
        
        avg_win = statistics.mean([t.pnl for t in winners]) if winners else 0.0
        avg_loss = statistics.mean([t.pnl for t in losers]) if losers else 0.0
        
        max_dd = self.calculate_max_drawdown(trades)
        total_pnl = sum(t.pnl for t in trades)
        
        # Calmar ratio: Annual return / Max Drawdown
        annual_return = (total_pnl / 10000) * (365 / max(period_days, 1))
        calmar = annual_return / max_dd if max_dd > 0 else 0.0
        
        return PerformanceReport(
            sharpe_ratio=self.calculate_sharpe_ratio(trades, period_days),
            sortino_ratio=self.calculate_sortino_ratio(trades, period_days),
            max_drawdown=max_dd,
            win_rate=self.calculate_win_rate(trades),
            profit_factor=self.calculate_profit_factor(trades),
            total_trades=len(trades),
            winning_trades=len(winners),
            losing_trades=len(losers),
            total_pnl=total_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            calmar_ratio=calmar,
            period_days=period_days
        )
