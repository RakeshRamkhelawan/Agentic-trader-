#!/usr/bin/env python3
"""
Consciousness-Based Multi-Agent Backtest
Uses 6 specialized agents with Vedic philosophy (36 Tattvas, 9 Navagrahas, 3 Gunas)
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import our consciousness system
from consciousness_agents import (ConsciousnessLLMFactory,
                                  TattvaState)


class ConsciousnessBacktestEngine:
    """
    Backtest engine using the 6-agent consciousness system:
    - Orchestrator (Ahamkara - I-maker)
    - Bull Researcher (Jupiter/Guru)
    - Bear Researcher (Saturn/Shani)
    - Macro Analyst (Sun/Surya)
    - Fund Manager (Mercury/Budha)
    - Risk Manager (Mars/Mangala)
    """

    def __init__(self, initial_capital: float = 100000.0, symbols: List[str] = None):
        self.initial_capital = initial_capital
        self.symbols = symbols or ["BTC-EUR", "ETH-EUR"]

        # Portfolio state
        self.cash = initial_capital
        self.positions: Dict[str, Dict] = {}  # symbol -> position info
        self.equity_curve: List[Dict] = []
        self.trades: List[Dict] = []

        # Multi-agent system
        logger.info("🧠 Initializing Multi-Agent Consciousness System...")
        self.consciousness = ConsciousnessLLMFactory.create_multi_agent_system()

        # Tattva tracking
        self.tattva_history: List[TattvaState] = []
        self.guna_history: List[Dict] = []

    async def run_backtest(
        self, data: Dict[str, pd.DataFrame], days: int = 365
    ) -> Dict:
        """
        Run backtest with multi-agent consciousness system

        Args:
            data: Dict of symbol -> DataFrame with OHLCV data
            days: Number of days to backtest
        """
        logger.info("🔮 CONSCIOUSNESS BACKTEST")
        logger.info(f"   Symbols: {', '.join(self.symbols)}")
        logger.info(f"   Period: {days} days")
        logger.info(f"   Capital: €{self.initial_capital:,.2f}")
        logger.info("   Agents: 6 (Orchestrator + 5 Specialists)")

        # Align data to common date range
        aligned_data = self._align_data(data, days)
        if not aligned_data:
            return {"error": "No data available"}

        dates = list(aligned_data[self.symbols[0]].index)

        # Run simulation
        for i, date in enumerate(dates):
            progress = (i / len(dates)) * 100

            if i % 10 == 0:  # Log every 10th candle
                current_equity = self._calculate_equity(aligned_data, date)
                date_str = (
                    date.strftime("%Y-%m-%d")
                    if hasattr(date, "strftime")
                    else str(date)
                )
                logger.info(
                    f"   {progress:5.1f}% | {date_str} | Equity: €{current_equity:,.2f}"
                )

            # Ensure date is datetime
            if isinstance(date, (int, float)):
                date = pd.to_datetime(date)

            # Process each symbol
            for symbol in self.symbols:
                if symbol not in aligned_data:
                    continue

                row = aligned_data[symbol].loc[date]

                # Build market context for agents
                market_context = self._build_market_context(
                    symbol, aligned_data, date, i
                )

                # Build portfolio context
                portfolio_context = {
                    "cash": self.cash,
                    "total_equity": self._calculate_equity(aligned_data, date),
                    symbol: self.positions.get(symbol, {}),
                    "unrealized_pnl": self._calculate_unrealized_pnl(
                        aligned_data, date
                    ),
                }

                # Run multi-agent analysis
                try:
                    decision = await self.consciousness.analyze_market(
                        symbol=symbol,
                        market_data=market_context,
                        portfolio=portfolio_context,
                    )

                    # Execute decision
                    await self._execute_decision(
                        decision, symbol, row, date, aligned_data
                    )

                    # Track Tattva state
                    if "tattva_state" in decision:
                        self.tattva_history.append(decision["tattva_state"])

                except Exception as e:
                    logger.error(f"Agent analysis failed for {symbol}: {e}")
                    continue

            # Record equity
            equity = self._calculate_equity(aligned_data, date)
            self.equity_curve.append(
                {
                    "date": date,
                    "equity": equity,
                    "cash": self.cash,
                    "positions": len(self.positions),
                }
            )

        # Generate results
        return self._generate_results(aligned_data)

    def _align_data(
        self, data: Dict[str, pd.DataFrame], days: int
    ) -> Dict[str, pd.DataFrame]:
        """Align all symbols to common date range"""
        aligned = {}

        for symbol, df in data.items():
            if df is None or df.empty:
                continue

            # Ensure index is datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                if "timestamp" in df.columns:
                    df = df.copy()
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df.set_index("timestamp", inplace=True)
                elif "date" in df.columns:
                    df = df.copy()
                    df["date"] = pd.to_datetime(df["date"])
                    df.set_index("date", inplace=True)
                else:
                    # Try to convert index
                    df = df.copy()
                    df.index = pd.to_datetime(df.index, unit="ms")

            # Use last N days
            if len(df) > days:
                df = df.iloc[-days:].copy()

            aligned[symbol] = df

        return aligned

    def _build_market_context(
        self, symbol: str, data: Dict, date: datetime, idx: int
    ) -> Dict:
        """Build rich market context for agents"""
        df = data[symbol]

        # Current price data
        current = df.loc[date]

        # Technical indicators
        context = {
            "symbol": symbol,
            "date": date.isoformat(),
            "price": float(current["close"]),
            "open": float(current["open"]),
            "high": float(current["high"]),
            "low": float(current["low"]),
            "volume": float(current["volume"]) if "volume" in current else 0,
            "candle": {
                "bullish": current["close"] > current["open"],
                "body_pct": abs(current["close"] - current["open"])
                / current["open"]
                * 100
                if current["open"] > 0
                else 0,
                "range_pct": (current["high"] - current["low"]) / current["low"] * 100
                if current["low"] > 0
                else 0,
            },
        }

        # Add recent history (last 20 candles)
        if idx >= 20:
            hist = df.iloc[idx - 20 : idx]
            context["history"] = {
                "sma_20": float(hist["close"].mean()),
                "volatility_20d": float(
                    hist["close"].std() / hist["close"].mean() * 100
                ),
                "trend_20d": "UP"
                if hist["close"].iloc[-1] > hist["close"].iloc[0]
                else "DOWN",
                "highest_20d": float(hist["high"].max()),
                "lowest_20d": float(hist["low"].min()),
            }

        # Add regime info
        if idx >= 50:
            hist_50 = df.iloc[idx - 50 : idx]
            sma_50 = hist_50["close"].mean()
            context["regime"] = {
                "sma_50": float(sma_50),
                "above_sma50": current["close"] > sma_50,
                "regime": "BULL" if current["close"] > sma_50 else "BEAR",
            }

        # Multi-symbol context if available
        if len(self.symbols) > 1:
            context["relative_strength"] = {}
            for other_sym in self.symbols:
                if (
                    other_sym != symbol
                    and other_sym in data
                    and date in data[other_sym].index
                ):
                    other_price = data[other_sym].loc[date, "close"]
                    other_prev = (
                        data[other_sym].iloc[idx - 1]["close"]
                        if idx > 0
                        else other_price
                    )
                    context["relative_strength"][other_sym] = {
                        "price": float(other_price),
                        "change_pct": (other_price - other_prev) / other_prev * 100
                        if other_prev > 0
                        else 0,
                    }

        return context

    async def _execute_decision(
        self,
        decision: Dict,
        symbol: str,
        price_data: pd.Series,
        date: datetime,
        all_data: Dict,
    ):
        """Execute the multi-agent decision"""
        action = decision.get("action", {})
        action_type = action.get("type", "HOLD")
        confidence = action.get("confidence", 0.5)

        price = float(price_data["close"])

        # Skip if confidence too low
        if confidence < 0.4:
            return

        # Execute based on action type
        if action_type == "BUY" and symbol not in self.positions:
            # Calculate position size
            size_pct = min(action.get("size_pct", 10.0), 20.0)  # Max 20%
            position_value = self.cash * (size_pct / 100) * confidence

            if position_value > 100:  # Min trade size
                quantity = position_value / price
                cost = position_value

                self.positions[symbol] = {
                    "entry_date": date,
                    "entry_price": price,
                    "quantity": quantity,
                    "value": position_value,
                    "confidence": confidence,
                    "agents": decision.get("agents", {}),
                    "tattva": self._tattva_to_dict(decision.get("tattva_state")),
                }

                self.cash -= cost

                logger.info(
                    f"   📥 BOUGHT {symbol} @ €{price:,.2f} "
                    f"(size: {size_pct:.1f}%, conf: {confidence:.2f})"
                )

                self.trades.append(
                    {
                        "date": date,
                        "symbol": symbol,
                        "action": "BUY",
                        "price": price,
                        "quantity": quantity,
                        "value": position_value,
                        "confidence": confidence,
                        "reason": action.get("reason", ""),
                        "tattva": self._tattva_to_dict(decision.get("tattva_state")),
                    }
                )

        elif action_type == "SELL" and symbol in self.positions:
            position = self.positions[symbol]
            quantity = position["quantity"]
            sale_value = quantity * price
            entry_value = position["value"]
            pnl = sale_value - entry_value
            pnl_pct = (pnl / entry_value) * 100

            self.cash += sale_value

            logger.info(
                f"   📤 SOLD {symbol} @ €{price:,.2f} "
                f"(P&L: €{pnl:,.2f}, {pnl_pct:+.2f}%)"
            )

            self.trades.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "action": "SELL",
                    "price": price,
                    "quantity": quantity,
                    "value": sale_value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "hold_days": (date - position["entry_date"]).days,
                    "reason": action.get("reason", ""),
                    "tattva": position.get("tattva", {}),
                }
            )

            del self.positions[symbol]

        elif action_type == "SWITCH":
            # Close current position and open in another symbol
            target = action.get("target_symbol", symbol)
            if symbol in self.positions and target != symbol:
                # Close current
                await self._execute_decision(
                    {
                        "action": {
                            "type": "SELL",
                            "confidence": confidence,
                            "reason": f"Switch to {target}",
                        }
                    },
                    symbol,
                    price_data,
                    date,
                    all_data,
                )
                # Open new will happen in next iteration

    def _tattva_to_dict(self, tattva: Optional[TattvaState]) -> Dict:
        """Convert TattvaState to dict"""
        if not tattva:
            return {}
        return {
            "guna": {
                "sattva": tattva.sattva,
                "rajas": tattva.rajas,
                "tamas": tattva.tamas,
            },
            "elements": {
                "ether": tattva.ether,
                "air": tattva.air,
                "fire": tattva.fire,
                "water": tattva.water,
                "earth": tattva.earth,
            },
            "navagrahas": {
                "surya": tattva.surya,
                "chandra": tattva.chandra,
                "mangala": tattva.mangala,
                "budha": tattva.budha,
                "guru": tattva.guru,
                "shukra": tattva.shukra,
                "shani": tattva.shani,
                "rahu": tattva.rahu,
                "ketu": tattva.ketu,
            },
        }

    def _calculate_equity(self, data: Dict, date: datetime) -> float:
        """Calculate total equity (cash + positions)"""
        equity = self.cash

        for symbol, position in self.positions.items():
            if symbol in data and date in data[symbol].index:
                price = data[symbol].loc[date, "close"]
                equity += position["quantity"] * price

        return equity

    def _calculate_unrealized_pnl(self, data: Dict, date: datetime) -> float:
        """Calculate unrealized P&L"""
        pnl = 0

        for symbol, position in self.positions.items():
            if symbol in data and date in data[symbol].index:
                price = data[symbol].loc[date, "close"]
                current_value = position["quantity"] * price
                entry_value = position["value"]
                pnl += current_value - entry_value

        return pnl

    def _generate_results(self, data: Dict) -> Dict:
        """Generate backtest results"""
        if not self.equity_curve:
            return {"error": "No equity data"}

        equity_df = pd.DataFrame(self.equity_curve)

        # Basic metrics
        final_equity = equity_df["equity"].iloc[-1]
        total_return = (
            (final_equity - self.initial_capital) / self.initial_capital * 100
        )

        # Calculate daily returns
        equity_df["daily_return"] = equity_df["equity"].pct_change()

        # Volatility (annualized)
        volatility = equity_df["daily_return"].std() * np.sqrt(365) * 100

        # Sharpe ratio (assuming 0% risk-free rate for simplicity)
        sharpe = (
            (equity_df["daily_return"].mean() / equity_df["daily_return"].std())
            * np.sqrt(365)
            if equity_df["daily_return"].std() > 0
            else 0
        )

        # Max drawdown
        equity_df["peak"] = equity_df["equity"].cummax()
        equity_df["drawdown"] = (equity_df["equity"] - equity_df["peak"]) / equity_df[
            "peak"
        ]
        max_drawdown = equity_df["drawdown"].min() * 100

        # Trade statistics
        closed_trades = [t for t in self.trades if t["action"] == "SELL"]
        winning_trades = [t for t in closed_trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in closed_trades if t.get("pnl", 0) <= 0]

        win_rate = (
            len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
        )
        avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
        profit_factor = (
            abs(
                sum(t["pnl"] for t in winning_trades)
                / sum(t["pnl"] for t in losing_trades)
            )
            if losing_trades and sum(t["pnl"] for t in losing_trades) != 0
            else float("inf")
        )

        # Tattva analysis
        tattva_analysis = self._analyze_tattva_history()

        results = {
            "backtest_type": "CONSCIOUSNESS_MULTI_AGENT",
            "agents": [
                "Orchestrator",
                "Bull(Jupiter)",
                "Bear(Saturn)",
                "Macro(Sun)",
                "Fund(Mercury)",
                "Risk(Mars)",
            ],
            "philosophy": "36 Tattvas, 9 Navagrahas, 3 Gunas",
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_return_pct": total_return,
            "cagr_pct": (
                (final_equity / self.initial_capital) ** (365 / len(equity_df)) - 1
            )
            * 100
            if len(equity_df) > 0
            else 0,
            "volatility_pct": volatility,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_drawdown,
            "total_trades": len(closed_trades),
            "win_rate": win_rate,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "tattva_analysis": tattva_analysis,
            "equity_curve": self.equity_curve,
            "trades": self.trades,
        }

        return results

    def _analyze_tattva_history(self) -> Dict:
        """Analyze Tattva states throughout backtest"""
        if not self.tattva_history:
            return {}

        # Average Guna states
        avg_sattva = np.mean([t.sattva for t in self.tattva_history])
        avg_rajas = np.mean([t.rajas for t in self.tattva_history])
        avg_tamas = np.mean([t.tamas for t in self.tattva_history])

        # Most common dominant Guna
        dominant_gunas = []
        for t in self.tattva_history:
            if t.sattva > t.rajas and t.sattva > t.tamas:
                dominant_gunas.append("sattva")
            elif t.rajas > t.sattva and t.rajas > t.tamas:
                dominant_gunas.append("rajas")
            else:
                dominant_gunas.append("tamas")

        from collections import Counter

        guna_counts = Counter(dominant_gunas)

        # Planetary influences
        avg_guru = np.mean([t.guru for t in self.tattva_history])
        avg_shani = np.mean([t.shani for t in self.tattva_history])

        return {
            "dominant_guna": guna_counts.most_common(1)[0][0],
            "guna_distribution": dict(guna_counts),
            "avg_guna_balance": {
                "sattva": avg_sattva,
                "rajas": avg_rajas,
                "tamas": avg_tamas,
            },
            "jupiter_influence": avg_guru,
            "saturn_influence": avg_shani,
            "tattva_states_recorded": len(self.tattva_history),
        }


async def main():
    """Run consciousness backtest"""

    # Load data
    data_dir = Path("/app/data/historical_6year")
    symbols = ["BTC-EUR", "ETH-EUR"]

    data = {}
    for symbol in symbols:
        # Try different filename patterns
        file_patterns = [
            f"{symbol}_1d_2020-2026_binance.pkl",
            f"{symbol.replace('-', '_')}_1d.pkl",
            f"{symbol}_1d.pkl",
        ]

        for pattern in file_patterns:
            file_path = data_dir / pattern
            if file_path.exists():
                df = pd.read_pickle(file_path)
                data[symbol] = df
                logger.info(f"✓ Loaded {symbol}: {len(df)} rows from {pattern}")
                break
        else:
            logger.warning(f"✗ {symbol} data not found")

    if not data:
        logger.error("No data available!")
        return

    # Create engine and run
    engine = ConsciousnessBacktestEngine(
        initial_capital=100000.0, symbols=list(data.keys())
    )

    results = await engine.run_backtest(data, days=90)  # Start with 90 days for testing

    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("🕉️  CONSCIOUSNESS BACKTEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Philosophy: {results['philosophy']}")
    logger.info(f"Agents: {', '.join(results['agents'])}")
    logger.info("\n📊 Performance:")
    logger.info(f"   Final Equity: €{results['final_equity']:,.2f}")
    logger.info(f"   Total Return: {results['total_return_pct']:+.2f}%")
    logger.info(f"   CAGR: {results['cagr_pct']:.2f}%")
    logger.info(f"   Sharpe: {results['sharpe_ratio']:.2f}")
    logger.info(f"   Max DD: {results['max_drawdown_pct']:.2f}%")
    logger.info("\n📈 Trading:")
    logger.info(f"   Total Trades: {results['total_trades']}")
    logger.info(f"   Win Rate: {results['win_rate']:.1f}%")
    logger.info(f"   Profit Factor: {results['profit_factor']:.2f}")

    if results.get("tattva_analysis"):
        ta = results["tattva_analysis"]
        logger.info("\n🕉️  Tattva Analysis:")
        logger.info(f"   Dominant Guna: {ta['dominant_guna']}")
        logger.info(
            f"   Guna Balance: S={ta['avg_guna_balance']['sattva']:.2f}, "
            f"R={ta['avg_guna_balance']['rajas']:.2f}, "
            f"T={ta['avg_guna_balance']['tamas']:.2f}"
        )
        logger.info(f"   Jupiter Influence: {ta['jupiter_influence']:.2f}")
        logger.info(f"   Saturn Influence: {ta['saturn_influence']:.2f}")

    # Save results
    import json

    output_file = f"/app/data/backtest_results/consciousness_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
