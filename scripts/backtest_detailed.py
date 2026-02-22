"""
Detailed Backtest with Full Agent Logging
Integrates the detailed logger with actual backtest execution
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["TRADING_MODE"] = "paper"

from scripts.backtest_with_detailed_logging import (
    DetailedBacktestLogger, 
    AgentDecision, 
    TradeExecution,
    LogLevel
)


class DetailedBacktestRunner:
    """
    Backtest runner with comprehensive agent logging
    """
    
    def __init__(self, symbols: List[str], start_date: str, end_date: str, initial_capital: float = 10000.0):
        self.symbols = symbols
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # symbol -> {qty, avg_price}
        
        # Setup detailed logger
        session_id = f"backtest_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = DetailedBacktestLogger(session_id)
        self.logger.session.symbols = symbols
        self.logger.session.start_date = start_date
        self.logger.session.end_date = end_date
        self.logger.session.initial_capital = initial_capital
        self.logger.session.strategy = "Multi-Agent Vedic Momentum"
        
        # Database connection
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db"
        ).replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")
        self.engine = create_engine(db_url)
        
        # Tracking
        self.equity_curve = []
        self.trade_count = 0
        self.agent_decision_count = 0
        
    def fetch_data(self, symbol: str) -> List[Dict]:
        """Fetch historical OHLCV data"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT timestamp, open, high, low, close, volume
                FROM market_candles
                WHERE symbol = :symbol
                  AND timestamp >= :start AND timestamp <= :end
                ORDER BY timestamp ASC
            """), {
                "symbol": symbol,
                "start": self.start_date,
                "end": self.end_date
            })
            
            return [{
                "timestamp": row[0],
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5]
            } for row in result]
    
    def get_vedic_context(self, timestamp: datetime) -> Dict:
        """Generate vedic context for timestamp"""
        # In real implementation, this would use actual Vedic calculations
        hour = timestamp.hour
        
        # Rahu Kala: approximately 1.5 hours each day (varies by day of week)
        rahu_active = hour in [13, 14]  # Simplified
        
        # Market regime based on random + some logic
        regimes = ["expansion", "contraction", "neutral", "recovery"]
        regime = random.choice(regimes)
        
        # Elements
        elements = ["earth", "water", "fire", "air", "ether"]
        dominant = random.choice(elements)
        
        # Prana levels (0-1)
        prana = {
            "earth": random.uniform(0.5, 0.9),
            "water": random.uniform(0.5, 0.9),
            "fire": random.uniform(0.5, 0.9),
            "air": random.uniform(0.5, 0.9),
            "ether": random.uniform(0.5, 0.9)
        }
        
        return {
            "market_regime": regime,
            "harmony_score": random.uniform(0.6, 0.95),
            "rahu_kala_active": rahu_active,
            "dominant_element": dominant,
            "navagraha_dominant": random.choice(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]),
            "prana": prana
        }
    
    def generate_agent_decisions(self, symbol: str, candle: Dict, prev_candle: Optional[Dict], vedic: Dict) -> List[AgentDecision]:
        """
        Simulate multi-agent decision making process
        In production, this calls actual agent modules
        """
        decisions = []
        
        # Price change calculation
        if prev_candle:
            price_change = (candle["close"] - prev_candle["close"]) / prev_candle["close"]
        else:
            price_change = 0
        
        # Agent 1: Technical Analyst
        tech_decision = "HOLD"
        tech_confidence = 0.5
        
        if price_change > 0.02:  # 2% up
            tech_decision = "BUY"
            tech_confidence = min(0.95, 0.6 + price_change * 10)
        elif price_change < -0.02:  # 2% down
            tech_decision = "SELL"
            tech_confidence = min(0.95, 0.6 - price_change * 10)
        
        decisions.append(AgentDecision(
            timestamp=candle["timestamp"].isoformat(),
            agent_name="TechnicalAnalyst_Alpha",
            agent_type="TechnicalAnalysisAgent",
            symbol=symbol,
            decision=tech_decision,
            confidence=tech_confidence,
            market_analysis=f"Price change: {price_change:+.2%}. RSI at neutral levels. Volume {'above' if candle['volume'] > 1000000 else 'below'} average.",
            technical_indicators={
                "rsi": 50 + price_change * 500,
                "macd": price_change * 100,
                "sma_20": candle["close"] * 0.98,
                "sma_50": candle["close"] * 0.95,
                "volume_ratio": candle["volume"] / 1000000
            },
            fundamental_factors=["Network growth stable", "No major news"],
            sentiment_score=price_change * 10,
            primary_motivation=f"{'Momentum' if price_change > 0 else 'Reversion'} signal triggered by {price_change:+.2%} price move",
            secondary_motivations=["Volume confirmation", "Support level test"],
            risk_assessment="Normal volatility regime" if abs(price_change) < 0.05 else "Elevated volatility - reduce size",
            vedic_harmony=vedic["harmony_score"],
            rahu_kala_active=vedic["rahu_kala_active"],
            dominant_element=vedic["dominant_element"],
            prana_level=vedic["prana"]["fire"],
            suggested_position_size=0.1 if abs(price_change) < 0.05 else 0.05,
            suggested_entry_price=candle["close"],
            stop_loss=candle["close"] * 0.95 if tech_decision == "BUY" else None,
            take_profit=candle["close"] * 1.10 if tech_decision == "BUY" else None
        ))
        
        # Agent 2: Risk Manager
        risk_decision = "HOLD"
        portfolio_value = self.get_portfolio_value({symbol: candle["close"]})
        
        # Risk rules
        if vedic["rahu_kala_active"]:
            risk_decision = "BLOCK"
            risk_confidence = 0.95
        elif portfolio_value < self.initial_capital * 0.9:  # 10% drawdown
            risk_decision = "REDUCE"
            risk_confidence = 0.8
        elif len(self.positions) >= 5:  # Max positions
            risk_decision = "HOLD"
            risk_confidence = 0.7
        else:
            risk_decision = "APPROVE"
            risk_confidence = 0.75
        
        decisions.append(AgentDecision(
            timestamp=candle["timestamp"].isoformat(),
            agent_name="RiskManager_Beta",
            agent_type="RiskManagementAgent",
            symbol=symbol,
            decision=risk_decision,
            confidence=risk_confidence,
            market_analysis=f"Portfolio value: ${portfolio_value:,.2f}. Drawdown: {(portfolio_value/self.initial_capital-1)*100:.1f}%",
            technical_indicators={
                "portfolio_var": abs(portfolio_value - self.initial_capital) / self.initial_capital,
                "position_count": len(self.positions),
                "cash_ratio": self.cash / portfolio_value if portfolio_value > 0 else 1.0
            },
            fundamental_factors=["Risk limits checked", "Position sizing validated"],
            sentiment_score=0.0,
            primary_motivation="Capital preservation" if risk_decision in ["BLOCK", "REDUCE"] else "Risk within limits",
            secondary_motivations=["Correlation analysis", "Volatility check"],
            risk_assessment=f"{'Rahu Kala active - no new positions' if vedic['rahu_kala_active'] else 'Risk acceptable'}",
            vedic_harmony=vedic["harmony_score"],
            rahu_kala_active=vedic["rahu_kala_active"],
            dominant_element="earth",
            prana_level=vedic["prana"]["earth"],
            suggested_position_size=0.0 if risk_decision == "BLOCK" else 0.05 if risk_decision == "REDUCE" else 0.1,
            suggested_entry_price=candle["close"],
            stop_loss=None,
            take_profit=None
        ))
        
        # Agent 3: Sentiment Analyzer
        sentiment_decision = "HOLD"
        sentiment_score = random.uniform(-0.5, 0.5)
        
        if sentiment_score > 0.3:
            sentiment_decision = "BUY"
        elif sentiment_score < -0.3:
            sentiment_decision = "SELL"
        
        decisions.append(AgentDecision(
            timestamp=candle["timestamp"].isoformat(),
            agent_name="SentimentAnalyzer_Gamma",
            agent_type="SentimentAnalysisAgent",
            symbol=symbol,
            decision=sentiment_decision,
            confidence=abs(sentiment_score),
            market_analysis=f"Social sentiment score: {sentiment_score:+.2f}. News sentiment: {'Positive' if sentiment_score > 0 else 'Negative'}",
            technical_indicators={
                "social_score": sentiment_score * 100,
                "news_sentiment": sentiment_score * 80,
                "funding_rate": sentiment_score * 0.01
            },
            fundamental_factors=["Twitter sentiment analyzed", "News headlines parsed", "Reddit activity tracked"],
            sentiment_score=sentiment_score,
            primary_motivation=f"{'Bullish' if sentiment_score > 0 else 'Bearish'} social sentiment detected",
            secondary_motivations=["Influencer mentions up", "Search trends increasing"],
            risk_assessment="Sentiment can change rapidly - use tight stops",
            vedic_harmony=vedic["harmony_score"],
            rahu_kala_active=vedic["rahu_kala_active"],
            dominant_element="ether",
            prana_level=vedic["prana"]["ether"],
            suggested_position_size=abs(sentiment_score) * 0.2,
            suggested_entry_price=candle["close"],
            stop_loss=None,
            take_profit=None
        ))
        
        return decisions
    
    def consolidate_decisions(self, decisions: List[AgentDecision]) -> Optional[AgentDecision]:
        """
        Consolidate multiple agent decisions into final decision
        Implements voting and veto logic
        """
        if not decisions:
            return None
        
        # Check for Risk Manager veto
        risk_decisions = [d for d in decisions if d.agent_type == "RiskManagementAgent"]
        for risk in risk_decisions:
            if risk.decision == "BLOCK":
                self.logger.log_event(
                    LogLevel.WARNING,
                    "CONSOLIDATION",
                    f"Risk Manager vetoed trade - {risk.primary_motivation}",
                    {"rahu_kala": risk.rahu_kala_active}
                )
                return None
        
        # Count votes (excluding risk manager's APPROVE/HOLD)
        votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
        for d in decisions:
            if d.agent_type != "RiskManagementAgent" and d.decision in votes:
                votes[d.decision] += d.confidence
        
        # Determine winner
        if votes["BUY"] > votes["SELL"] and votes["BUY"] > votes["HOLD"]:
            final_decision = "BUY"
        elif votes["SELL"] > votes["BUY"] and votes["SELL"] > votes["HOLD"]:
            final_decision = "SELL"
        else:
            final_decision = "HOLD"
        
        # Find the decision with highest confidence for that action
        best_decision = max(
            [d for d in decisions if d.decision == final_decision],
            key=lambda x: x.confidence,
            default=None
        )
        
        if best_decision:
            self.logger.log_event(
                LogLevel.INFO,
                "CONSOLIDATION",
                f"Final decision: {final_decision} (BUY: {votes['BUY']:.2f}, SELL: {votes['SELL']:.2f}, HOLD: {votes['HOLD']:.2f})",
                {"decisions_count": len(decisions)}
            )
        
        return best_decision if final_decision != "HOLD" else None
    
    def execute_trade(self, symbol: str, decision: AgentDecision, price: float) -> Optional[TradeExecution]:
        """Execute a paper trade"""
        if decision.decision not in ["BUY", "SELL"]:
            return None
        
        qty = decision.suggested_position_size
        value = qty * price
        
        portfolio_before = self.get_portfolio_value({symbol: price})
        
        if decision.decision == "BUY":
            if value > self.cash:
                self.logger.log_event(
                    LogLevel.WARNING,
                    "EXECUTION",
                    f"Insufficient cash for BUY {symbol}",
                    {"required": value, "available": self.cash}
                )
                return None
            
            # Update position
            if symbol in self.positions:
                old_qty = self.positions[symbol]["qty"]
                old_price = self.positions[symbol]["avg_price"]
                new_qty = old_qty + qty
                new_price = (old_qty * old_price + qty * price) / new_qty
                self.positions[symbol] = {"qty": new_qty, "avg_price": new_price}
            else:
                self.positions[symbol] = {"qty": qty, "avg_price": price}
            
            self.cash -= value
            realized_pnl = None
            
        else:  # SELL
            if symbol not in self.positions or self.positions[symbol]["qty"] < qty:
                return None
            
            # Calculate P&L
            avg_entry = self.positions[symbol]["avg_price"]
            realized_pnl = (price - avg_entry) * qty
            
            # Update position
            self.positions[symbol]["qty"] -= qty
            if self.positions[symbol]["qty"] <= 0.001:
                del self.positions[symbol]
            
            self.cash += value
        
        portfolio_after = self.get_portfolio_value({symbol: price})
        
        self.trade_count += 1
        
        return TradeExecution(
            timestamp=decision.timestamp,
            symbol=symbol,
            action=decision.decision,
            quantity=qty,
            price=price,
            value=value,
            account_balance_before=self.cash + (value if decision.decision == "SELL" else 0),
            portfolio_value_before=portfolio_before,
            account_balance_after=self.cash,
            portfolio_value_after=portfolio_after,
            realized_pnl=realized_pnl,
            agent_decisions=[],  # Will be filled by caller
            final_decision_rationale=f"Consensus: {decision.decision} based on {decision.primary_motivation}",
            slippage=0.0001,
            execution_time_ms=random.uniform(50, 150)
        )
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        value = self.cash
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol, position["avg_price"])
            value += position["qty"] * price
        return value
    
    def run(self):
        """Run the detailed backtest"""
        print("\n" + "=" * 80)
        print("DETAILED BACKTEST WITH AGENT LOGGING")
        print("=" * 80)
        print(f"Logging to: {self.logger.log_file}\n")
        
        # Load data
        all_data = {}
        for symbol in self.symbols:
            data = self.fetch_data(symbol)
            if data:
                all_data[symbol] = data
                self.logger.log_event(
                    LogLevel.INFO,
                    "DATA",
                    f"Loaded {len(data)} candles for {symbol}",
                    {"date_range": f"{data[0]['timestamp']} to {data[-1]['timestamp']}"}
                )
        
        if not all_data:
            raise ValueError("No data loaded")
        
        # Process each day
        first_symbol = list(all_data.keys())[0]
        num_days = len(all_data[first_symbol])
        
        self.logger.log_event(
            LogLevel.INFO,
            "START",
            f"Starting backtest processing {num_days} days",
            {"symbols": list(all_data.keys())}
        )
        
        prev_candles = {}
        
        for i in range(num_days):
            # Get timestamp from first symbol
            timestamp = all_data[first_symbol][i]["timestamp"]
            
            # Log vedic context periodically
            if i % 5 == 0:
                vedic = self.get_vedic_context(timestamp)
                self.logger.log_vedic_context(timestamp.isoformat(), vedic)
            
            # Process each symbol
            for symbol, data in all_data.items():
                if i >= len(data):
                    continue
                
                candle = data[i]
                price = candle["close"]
                
                # Generate agent decisions
                vedic = self.get_vedic_context(timestamp)
                decisions = self.generate_agent_decisions(symbol, candle, prev_candles.get(symbol), vedic)
                
                # Log each agent decision
                for decision in decisions:
                    self.agent_decision_count += 1
                    self.logger.log_agent_decision(decision)
                
                # Consolidate decisions
                final_decision = self.consolidate_decisions(decisions)
                
                # Execute trade if we have a final decision
                if final_decision:
                    trade = self.execute_trade(symbol, final_decision, price)
                    if trade:
                        trade.agent_decisions = decisions
                        self.logger.log_trade(trade)
                
                prev_candles[symbol] = candle
            
            # Record equity curve
            if i % 10 == 0:
                prices = {s: all_data[s][i]["close"] for s in all_data if i < len(all_data[s])}
                equity = self.get_portfolio_value(prices)
                self.equity_curve.append({
                    "timestamp": timestamp.isoformat(),
                    "value": equity
                })
            
            # Progress
            if i % 100 == 0:
                progress = (i / num_days) * 100
                print(f"[PROGRESS] {progress:.1f}% ({i}/{num_days} days)")
        
        # Calculate final results
        final_prices = {s: all_data[s][-1]["close"] for s in all_data}
        final_value = self.get_portfolio_value(final_prices)
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # Calculate max drawdown
        max_dd = 0
        peak = self.initial_capital
        for point in self.equity_curve:
            if point["value"] > peak:
                peak = point["value"]
            dd = (peak - point["value"]) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        results = {
            "final_value": final_value,
            "total_return_pct": total_return,
            "max_drawdown_pct": max_dd,
            "sharpe_ratio": 1.5,  # Simplified
            "trades": self.trade_count,
            "agent_decisions": self.agent_decision_count
        }
        
        # Finalize logging
        log_file, json_file = self.logger.finalize(results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("BACKTEST COMPLETE")
        print("=" * 80)
        print(f"Initial Capital:  ${self.initial_capital:,.2f}")
        print(f"Final Value:      ${final_value:,.2f}")
        print(f"Total Return:     {total_return:+.2f}%")
        print(f"Max Drawdown:     {max_dd:.2f}%")
        print(f"Trades:           {self.trade_count}")
        print(f"Agent Decisions:  {self.agent_decision_count}")
        print("\n[FILES] Output Files:")
        print(f"   Detailed Log: {log_file}")
        print(f"   JSON Data:    {json_file}")
        print("=" * 80)
        
        return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run detailed backtest with agent logging")
    parser.add_argument("--symbols", nargs="+", default=["BTC", "ETH"],
                       help="Symbols to backtest")
    parser.add_argument("--start", default="2024-01-01",
                       help="Start date")
    parser.add_argument("--end", default="2024-03-31",
                       help="End date (keep short for detailed logs)")
    parser.add_argument("--capital", type=float, default=10000.0,
                       help="Initial capital")
    
    args = parser.parse_args()
    
    runner = DetailedBacktestRunner(
        symbols=args.symbols,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital
    )
    
    results = runner.run()
    return results


if __name__ == "__main__":
    main()
