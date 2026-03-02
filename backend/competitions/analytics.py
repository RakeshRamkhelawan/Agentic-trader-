"""Performance analytics for competitions."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .models.tournament import TournamentEntry


@dataclass
class PerformanceMetrics:
    """Performance metrics for a competitor."""

    competitor_id: str
    period: str  # "daily", "weekly", "monthly", "all_time"

    # Trading metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # P&L metrics
    total_pnl: float = 0.0
    avg_pnl_per_trade: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0

    # Risk metrics
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0

    # Consistency
    daily_pnls: list[float] = None
    streak_current: int = 0
    streak_max: int = 0


class AnalyticsEngine:
    """
    Analytics engine for competition performance.

    Provides:
    - Performance metrics calculation
    - Trend analysis
    - Comparative analytics
    - Predictive insights
    """

    def __init__(self):
        self._trade_history: dict[str, list[dict]] = defaultdict(list)
        self._daily_stats: dict[str, dict[str, Any]] = defaultdict(dict)

    def record_trade(
        self,
        competitor_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
        pnl: float,
        timestamp: datetime | None = None,
    ) -> None:
        """Record a trade for analytics."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        trade = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "timestamp": timestamp.isoformat(),
        }

        self._trade_history[competitor_id].append(trade)

    def calculate_metrics(
        self,
        competitor_id: str,
        period: str = "all_time",
    ) -> PerformanceMetrics:
        """Calculate performance metrics for a competitor."""
        trades = self._get_trades_for_period(competitor_id, period)

        if not trades:
            return PerformanceMetrics(
                competitor_id=competitor_id,
                period=period,
            )

        pnls = [t["pnl"] for t in trades]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p <= 0]

        metrics = PerformanceMetrics(
            competitor_id=competitor_id,
            period=period,
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=(len(winning) / len(trades) * 100) if trades else 0,
            total_pnl=sum(pnls),
            avg_pnl_per_trade=sum(pnls) / len(trades) if trades else 0,
            best_trade=max(pnls) if pnls else 0,
            worst_trade=min(pnls) if pnls else 0,
            daily_pnls=self._calculate_daily_pnls(trades),
        )

        # Risk metrics
        metrics.sharpe_ratio = self._calculate_sharpe_ratio(pnls)
        metrics.max_drawdown = self._calculate_max_drawdown(pnls)
        metrics.profit_factor = self._calculate_profit_factor(winning, losing)

        # Streaks
        metrics.streak_current, metrics.streak_max = self._calculate_streaks(pnls)

        return metrics

    def _get_trades_for_period(
        self,
        competitor_id: str,
        period: str,
    ) -> list[dict]:
        """Get trades filtered by period."""
        all_trades = self._trade_history.get(competitor_id, [])

        if period == "all_time":
            return all_trades

        now = datetime.utcnow()

        if period == "daily":
            cutoff = now - timedelta(days=1)
        elif period == "weekly":
            cutoff = now - timedelta(weeks=1)
        elif period == "monthly":
            cutoff = now - timedelta(days=30)
        else:
            return all_trades

        return [t for t in all_trades if datetime.fromisoformat(t["timestamp"]) >= cutoff]

    def _calculate_sharpe_ratio(self, returns: list[float], risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0.0

        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance**0.5

        if std_dev == 0:
            return 0.0

        return (avg_return - risk_free_rate) / std_dev

    def _calculate_max_drawdown(self, returns: list[float]) -> float:
        """Calculate maximum drawdown."""
        if not returns:
            return 0.0

        peak = returns[0]
        max_dd = 0.0

        for r in returns:
            if r > peak:
                peak = r
            dd = (peak - r) / peak if peak != 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd * 100  # As percentage

    def _calculate_profit_factor(self, winning: list[float], losing: list[float]) -> float:
        """Calculate profit factor."""
        gross_profit = sum(winning) if winning else 0
        gross_loss = abs(sum(losing)) if losing else 0

        if gross_loss == 0:
            return gross_profit if gross_profit > 0 else 0

        return gross_profit / gross_loss

    def _calculate_daily_pnls(self, trades: list[dict]) -> list[float]:
        """Aggregate P&L by day."""
        daily = defaultdict(float)

        for trade in trades:
            date = datetime.fromisoformat(trade["timestamp"]).date()
            daily[date] += trade["pnl"]

        return list(daily.values())

    def _calculate_streaks(self, pnls: list[float]) -> tuple:
        """Calculate current and max win streaks."""
        if not pnls:
            return 0, 0

        current = 0
        max_streak = 0

        for pnl in reversed(pnls):  # Start from most recent
            if pnl > 0:
                current += 1
                max_streak = max(max_streak, current)
            else:
                if current == 0:  # Current streak is losses
                    current = -1
                else:
                    break

        # Calculate overall max streak
        overall_max = 0
        streak = 0
        for pnl in pnls:
            if pnl > 0:
                streak += 1
                overall_max = max(overall_max, streak)
            else:
                streak = 0

        return current, overall_max

    def get_leaderboard_analytics(self, competitor_ids: list[str]) -> dict[str, Any]:
        """Get comparative analytics for leaderboard."""
        metrics = [self.calculate_metrics(cid, "all_time") for cid in competitor_ids]

        # Sort by total P&L
        metrics.sort(key=lambda m: m.total_pnl, reverse=True)

        return {
            "rankings": [
                {
                    "rank": i + 1,
                    "competitor_id": m.competitor_id,
                    "total_pnl": m.total_pnl,
                    "win_rate": m.win_rate,
                    "sharpe_ratio": m.sharpe_ratio,
                    "max_drawdown": m.max_drawdown,
                    "profit_factor": m.profit_factor,
                }
                for i, m in enumerate(metrics)
            ],
            "averages": {
                "avg_win_rate": sum(m.win_rate for m in metrics) / len(metrics) if metrics else 0,
                "avg_sharpe": sum(m.sharpe_ratio for m in metrics) / len(metrics) if metrics else 0,
                "avg_trades": sum(m.total_trades for m in metrics) / len(metrics) if metrics else 0,
            },
            "best_performers": {
                "highest_pnl": max((m.total_pnl for m in metrics), default=0),
                "best_win_rate": max((m.win_rate for m in metrics), default=0),
                "best_sharpe": max((m.sharpe_ratio for m in metrics), default=0),
            },
        }

    def get_tournament_analytics(self, entries: list[TournamentEntry]) -> dict[str, Any]:
        """Get analytics for a tournament."""
        if not entries:
            return {"error": "No entries"}

        pnls = [e.pnl for e in entries]
        balances = [e.current_balance for e in entries]

        return {
            "participants": len(entries),
            "avg_pnl": sum(pnls) / len(pnls),
            "best_pnl": max(pnls),
            "worst_pnl": min(pnls),
            "avg_balance": sum(balances) / len(balances),
            "leader": max(entries, key=lambda e: e.pnl).competitor_id if entries else None,
            "profitability": {
                "profitable": len([p for p in pnls if p > 0]),
                "unprofitable": len([p for p in pnls if p <= 0]),
            },
        }

    def generate_insights(self, competitor_id: str) -> list[dict[str, str]]:
        """Generate personalized insights."""
        metrics = self.calculate_metrics(competitor_id, "all_time")
        insights = []

        if metrics.win_rate > 60:
            insights.append(
                {
                    "type": "strength",
                    "message": f"Strong win rate of {metrics.win_rate:.1f}% - you're good at picking winners!",
                }
            )
        elif metrics.win_rate < 40:
            insights.append(
                {
                    "type": "improvement",
                    "message": "Consider reviewing your entry criteria - win rate is below 40%.",
                }
            )

        if metrics.profit_factor > 2:
            insights.append(
                {
                    "type": "strength",
                    "message": f"Excellent profit factor of {metrics.profit_factor:.2f} - profits outweigh losses significantly.",
                }
            )

        if metrics.max_drawdown > 20:
            insights.append(
                {
                    "type": "warning",
                    "message": f"High drawdown of {metrics.max_drawdown:.1f}% - consider tighter risk management.",
                }
            )

        if metrics.sharpe_ratio > 1.5:
            insights.append(
                {
                    "type": "strength",
                    "message": f"Great Sharpe ratio of {metrics.sharpe_ratio:.2f} - excellent risk-adjusted returns!",
                }
            )

        if metrics.streak_max >= 5:
            insights.append(
                {
                    "type": "achievement",
                    "message": f"Longest win streak: {metrics.streak_max} trades - impressive consistency!",
                }
            )

        return insights


# Global analytics engine
analytics_engine = AnalyticsEngine()
