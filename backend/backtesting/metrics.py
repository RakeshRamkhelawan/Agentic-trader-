import numpy as np
import pandas as pd

from backend.backtesting.models import BacktestMetrics, Trade


class MetricsCalculator:
    """Calculates financial performance metrics from equity curve and trades."""

    RISK_FREE_RATE = 0.02  # 2% annually for crypto/stock analysis
    TRADING_DAYS_PER_YEAR = 365  # Default to 365 for crypto (24/7), use 252 for stocks

    @staticmethod
    def calculate(
        equity_curve: list[dict],
        initial_capital: float,
        trades: list[Trade] = None,
        trading_days_per_year: int = 365,
    ) -> BacktestMetrics:
        """Calculate comprehensive backtesting metrics.

        Args:
            equity_curve: List of {'timestamp', 'equity'} dicts
            initial_capital: Starting capital
            trades: List of Trade objects for detailed analysis
            trading_days_per_year: Trading days per year (365 for crypto, 252 for stocks)

        Returns:
            BacktestMetrics with all performance indicators
        """
        if not equity_curve:
            return BacktestMetrics(
                total_return=0.0,
                cagr=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_trades=0,
            )

        df = pd.DataFrame(equity_curve)
        df["returns"] = df["equity"].pct_change().fillna(0)

        # Total Return
        final_equity = df["equity"].iloc[-1]
        total_return = (final_equity - initial_capital) / initial_capital

        # CAGR (Compound Annual Growth Rate)
        days = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).days
        if days > 0:
            cagr = (final_equity / initial_capital) ** (365 / days) - 1
        else:
            cagr = 0.0

        # Sharpe Ratio (annualized, assuming daily data)
        mean_return = df["returns"].mean()
        std_return = df["returns"].std()

        if std_return == 0:
            sharpe = 0.0
        else:
            annual_return = mean_return * trading_days_per_year
            annual_std = std_return * np.sqrt(trading_days_per_year)
            sharpe = (annual_return - MetricsCalculator.RISK_FREE_RATE) / annual_std

        # Sortino Ratio (only penalizes downside volatility)
        downside_returns = df[df["returns"] < 0]["returns"]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std()
            sortino = (
                (annual_return - MetricsCalculator.RISK_FREE_RATE)
                / (downside_std * np.sqrt(trading_days_per_year))
                if downside_std > 0
                else 0.0
            )
        else:
            sortino = sharpe  # No downside volatility = same as Sharpe

        # Max Drawdown
        df["cummax"] = df["equity"].cummax()
        df["drawdown"] = (df["equity"] - df["cummax"]) / df["cummax"]
        max_drawdown = df["drawdown"].min()

        # Calmar Ratio = CAGR / |Max Drawdown|
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0.0

        # Trade analysis
        win_rate = 0.0
        total_trades = 0
        if trades:
            total_trades = len([t for t in trades if t.pnl is not None])
            winning_trades = len([t for t in trades if t.pnl is not None and t.pnl > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        return BacktestMetrics(
            total_return=round(total_return, 4),
            cagr=round(cagr, 4),
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            calmar_ratio=round(calmar, 4),
            max_drawdown=round(max_drawdown, 4),
            win_rate=round(win_rate, 4),
            total_trades=total_trades,
        )

    @staticmethod
    def calculate_trade_statistics(trades: list[Trade]) -> dict:
        """Calculate detailed trade-level statistics.

        Args:
            trades: List of closed Trade objects

        Returns:
            Dict with trade statistics
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
            }

        closed_trades = [t for t in trades if t.pnl is not None]
        if not closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
            }

        pnls = [t.pnl for t in closed_trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]

        gross_profit = sum(winning_trades) if winning_trades else 0.0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        avg_win = np.mean(winning_trades) if winning_trades else 0.0
        avg_loss = np.mean(losing_trades) if losing_trades else 0.0

        # Consecutive streaks
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0

        for pnl in pnls:
            if pnl > 0:
                current_wins += 1
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
                current_losses = 0
            else:
                current_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
                current_wins = 0

        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (len(winning_trades) / len(closed_trades) if closed_trades else 0.0),
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": max(winning_trades) if winning_trades else 0.0,
            "largest_loss": min(losing_trades) if losing_trades else 0.0,
            "consecutive_wins": max_consecutive_wins,
            "consecutive_losses": max_consecutive_losses,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
        }
