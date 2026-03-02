"""Report generator for comprehensive analytics reports."""

from datetime import datetime, timedelta
from typing import Any


class ReportGenerator:
    """
    Generates comprehensive trading reports.

    Report types:
    - Weekly summary
    - Monthly performance
    - Tournament recap
    - Strategy performance
    """

    def __init__(self):
        pass

    def generate_weekly_report(
        self,
        user_id: str,
        user_name: str,
        trades: list[dict[str, Any]],
        tournaments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate weekly trading report."""
        # Get trades from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_trades = [
            t for t in trades if datetime.fromisoformat(t.get("timestamp", "2000-01-01")) > week_ago
        ]

        # Calculate metrics
        pnls = [t.get("pnl", 0) for t in recent_trades]

        report = {
            "type": "weekly",
            "period": {
                "start": week_ago.isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "user": {
                "id": user_id,
                "name": user_name,
            },
            "summary": {
                "total_trades": len(recent_trades),
                "winning_trades": len([p for p in pnls if p > 0]),
                "losing_trades": len([p for p in pnls if p <= 0]),
                "total_pnl": sum(pnls),
                "avg_pnl": sum(pnls) / len(pnls) if pnls else 0,
                "best_day": max(pnls) if pnls else 0,
                "worst_day": min(pnls) if pnls else 0,
            },
            "tournaments": {
                "entered": len(tournaments),
                "won": len([t for t in tournaments if t.get("rank", 99) == 1]),
                "total_prizes": sum(t.get("prize", 0) for t in tournaments),
            },
            "trades": recent_trades,
        }

        return report

    def generate_tournament_report(
        self,
        tournament_id: str,
        tournament_name: str,
        entries: list[dict[str, Any]],
        trades: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate tournament recap report."""
        # Sort by rank
        sorted_entries = sorted(entries, key=lambda e: e.get("rank", 999))

        # Calculate stats
        pnls = [e.get("pnl", 0) for e in entries]

        report = {
            "type": "tournament",
            "tournament": {
                "id": tournament_id,
                "name": tournament_name,
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "participants": len(entries),
                "profitable": len([p for p in pnls if p > 0]),
                "unprofitable": len([p for p in pnls if p <= 0]),
                "avg_pnl": sum(pnls) / len(pnls) if pnls else 0,
                "best_performance": max(pnls) if pnls else 0,
            },
            "top_performers": [
                {
                    "rank": e.get("rank"),
                    "competitor_id": e.get("competitor_id"),
                    "pnl": e.get("pnl"),
                    "pnl_percent": e.get("pnl_percentage"),
                }
                for e in sorted_entries[:10]
            ],
        }

        return report

    def generate_strategy_report(
        self,
        strategy_id: str,
        strategy_name: str,
        trades: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate strategy performance report."""
        pnls = [t.get("pnl", 0) for t in trades]

        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p <= 0]

        report = {
            "type": "strategy",
            "strategy": {
                "id": strategy_id,
                "name": strategy_name,
            },
            "generated_at": datetime.utcnow().isoformat(),
            "performance": {
                "total_trades": len(trades),
                "winning_trades": len(winning),
                "losing_trades": len(losing),
                "win_rate": (len(winning) / len(trades) * 100) if trades else 0,
                "total_pnl": sum(pnls),
                "avg_pnl": sum(pnls) / len(pnls) if pnls else 0,
                "profit_factor": (
                    sum(winning) / abs(sum(losing)) if losing and sum(losing) != 0 else float("inf")
                ),
            },
            "trades_by_symbol": self._aggregate_by_symbol(trades),
        }

        return report

    def _aggregate_by_symbol(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate trades by symbol."""
        by_symbol = {}

        for trade in trades:
            symbol = trade.get("symbol", "UNKNOWN")
            if symbol not in by_symbol:
                by_symbol[symbol] = {
                    "trades": 0,
                    "total_pnl": 0,
                    "winning_trades": 0,
                }

            by_symbol[symbol]["trades"] += 1
            by_symbol[symbol]["total_pnl"] += trade.get("pnl", 0)
            if trade.get("pnl", 0) > 0:
                by_symbol[symbol]["winning_trades"] += 1

        # Calculate win rates
        for symbol in by_symbol:
            data = by_symbol[symbol]
            data["win_rate"] = (
                (data["winning_trades"] / data["trades"] * 100) if data["trades"] > 0 else 0
            )

        return by_symbol


# Global report generator
report_generator = ReportGenerator()
