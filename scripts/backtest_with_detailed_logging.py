"""
Detailed Logging Backtest
Logs every agent action, decision, reasoning, and motivation to a text file
Provides complete insight from entry to exit
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ["TRADING_MODE"] = "paper"


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    TRADE = "TRADE"  # Special level for trade events
    AGENT = "AGENT"  # Special level for agent decisions
    VEDIC = "VEDIC"  # Special level for vedic context


@dataclass
class AgentDecision:
    """Records an agent's decision with full reasoning"""
    timestamp: str
    agent_name: str
    agent_type: str  # ResearchAgent, RiskAgent, etc.
    symbol: str
    decision: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 to 1.0
    
    # Reasoning components
    market_analysis: str
    technical_indicators: Dict[str, float]
    fundamental_factors: List[str]
    sentiment_score: float
    
    # Motivation
    primary_motivation: str
    secondary_motivations: List[str]
    risk_assessment: str
    
    # Vedic context
    vedic_harmony: float
    rahu_kala_active: bool
    dominant_element: str
    prana_level: float
    
    # Execution details
    suggested_position_size: float
    suggested_entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    
    def to_log_entry(self) -> str:
        """Format decision as readable log entry"""
        lines = [
            "=" * 80,
            f"AGENT DECISION: {self.agent_name} ({self.agent_type})",
            "=" * 80,
            f"Timestamp:        {self.timestamp}",
            f"Symbol:           {self.symbol}",
            f"Decision:         {self.decision} (confidence: {self.confidence:.2%})",
            "",
            "MARKET ANALYSIS:",
            f"  {self.market_analysis}",
            "",
            "TECHNICAL INDICATORS:",
        ]
        for indicator, value in self.technical_indicators.items():
            lines.append(f"  {indicator}: {value:.4f}")
        
        lines.extend([
            "",
            "FUNDAMENTAL FACTORS:",
        ])
        for factor in self.fundamental_factors:
            lines.append(f"  • {factor}")
        
        lines.extend([
            "",
            f"SENTIMENT SCORE:  {self.sentiment_score:.2f}",
            "",
            "MOTIVATION:",
            f"  Primary:   {self.primary_motivation}",
            "  Secondary:",
        ])
        for motivation in self.secondary_motivations:
            lines.append(f"    • {motivation}")
        
        lines.extend([
            "",
            f"RISK ASSESSMENT:  {self.risk_assessment}",
            "",
            "VEDIC CONTEXT:",
            f"  Harmony Score:    {self.vedic_harmony:.2f}",
            f"  Rahu Kala:        {'ACTIVE ⚠️' if self.rahu_kala_active else 'Inactive'}",
            f"  Dominant Element: {self.dominant_element}",
            f"  Prana Level:      {self.prana_level:.2f}",
            "",
            "EXECUTION PARAMETERS:",
            f"  Position Size:    {self.suggested_position_size:.4f}",
            f"  Entry Price:      ${self.suggested_entry_price:,.2f}",
        ])
        
        if self.stop_loss:
            lines.append(f"  Stop Loss:        ${self.stop_loss:,.2f}")
        if self.take_profit:
            lines.append(f"  Take Profit:      ${self.take_profit:,.2f}")
        
        lines.append("")
        return "\n".join(lines)


@dataclass
class TradeExecution:
    """Records trade execution details"""
    timestamp: str
    symbol: str
    action: str  # BUY, SELL
    quantity: float
    price: float
    value: float
    
    # Pre-trade context
    account_balance_before: float
    portfolio_value_before: float
    
    # Post-trade result
    account_balance_after: float
    portfolio_value_after: float
    realized_pnl: Optional[float]
    
    # Decision chain
    agent_decisions: List[AgentDecision]
    final_decision_rationale: str
    
    # Execution quality
    slippage: float
    execution_time_ms: float
    
    def to_log_entry(self) -> str:
        """Format trade as readable log entry"""
        lines = [
            ">>>" * 26,
            f"TRADE EXECUTED: {self.action} {self.symbol}",
            ">>>" * 26,
            f"Timestamp:    {self.timestamp}",
            f"Quantity:     {self.quantity:.4f}",
            f"Price:        ${self.price:,.2f}",
            f"Total Value:  ${self.value:,.2f}",
            "",
            "ACCOUNT STATUS:",
            f"  Before Trade:  Cash: ${self.account_balance_before:,.2f} | Portfolio: ${self.portfolio_value_before:,.2f}",
            f"  After Trade:   Cash: ${self.account_balance_after:,.2f} | Portfolio: ${self.portfolio_value_after:,.2f}",
        ]
        
        if self.realized_pnl is not None:
            pnl_emoji = "🟢" if self.realized_pnl > 0 else "🔴"
            lines.append(f"  Realized P&L:  {pnl_emoji} ${self.realized_pnl:,.2f}")
        
        lines.extend([
            "",
            f"EXECUTION QUALITY: Slippage: {self.slippage:.4f} | Time: {self.execution_time_ms:.2f}ms",
            "",
            "DECISION CHAIN:",
        ])
        
        for i, decision in enumerate(self.agent_decisions, 1):
            lines.append(f"  {i}. {decision.agent_name}: {decision.decision} (confidence: {decision.confidence:.2%})")
        
        lines.extend([
            "",
            "FINAL RATIONALE:",
            f"  {self.final_decision_rationale}",
            "",
        ])
        
        return "\n".join(lines)


@dataclass
class BacktestSession:
    """Complete backtest session with all logs"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    
    # Configuration
    symbols: List[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 0.0
    strategy: str = ""
    
    # Logs
    agent_decisions: List[AgentDecision] = field(default_factory=list)
    trades: List[TradeExecution] = field(default_factory=list)
    vedic_contexts: List[Dict] = field(default_factory=list)
    market_regime_changes: List[Dict] = field(default_factory=list)
    system_events: List[Dict] = field(default_factory=list)
    
    # Results
    final_capital: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    
    def to_summary(self) -> str:
        """Generate session summary"""
        lines = [
            "\n" + "=" * 80,
            "BACKTEST SESSION SUMMARY",
            "=" * 80,
            f"Session ID:       {self.session_id}",
            f"Start Time:       {self.start_time}",
            f"End Time:         {self.end_time or 'In Progress'}",
            "",
            "CONFIGURATION:",
            f"  Symbols:        {', '.join(self.symbols)}",
            f"  Date Range:     {self.start_date} to {self.end_date}",
            f"  Initial Capital: ${self.initial_capital:,.2f}",
            f"  Strategy:       {self.strategy}",
            "",
            "STATISTICS:",
            f"  Agent Decisions:  {len(self.agent_decisions)}",
            f"  Trades Executed:  {len(self.trades)}",
            f"  Vedic Snapshots:  {len(self.vedic_contexts)}",
            "",
            "PERFORMANCE:",
            f"  Final Capital:    ${self.final_capital:,.2f}",
            f"  Total Return:     {self.total_return_pct:+.2f}%",
            f"  Max Drawdown:     {self.max_drawdown_pct:.2f}%",
            f"  Sharpe Ratio:     {self.sharpe_ratio:.2f}",
            "=" * 80,
        ]
        return "\n".join(lines)


class DetailedBacktestLogger:
    """
    Comprehensive logger for backtest activities
    Writes to both console and detailed text file
    """
    
    def __init__(self, session_id: str, output_dir: str = "backtest_logs"):
        self.session_id = session_id
        self.output_dir = output_dir
        self.session = BacktestSession(
            session_id=session_id,
            start_time=datetime.now().isoformat()
        )
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Main log file
        self.log_file = os.path.join(output_dir, f"{session_id}_DETAILED_LOG.txt")
        
        # Write header
        self._write_header()
        
        print(f"[LOG] Detailed logging to: {self.log_file}")
    
    def _write_header(self):
        """Write log file header"""
        header = f"""
{'#' * 100}
AGENTIC TRADER PLATFORM - DETAILED BACKTEST LOG
{'#' * 100}

Session ID: {self.session_id}
Started: {self.session.start_time}
Mode: PAPER TRADING (No Real Orders)

This file contains complete trace of all agent decisions, reasoning, and trade executions.
Each entry includes:
  - Agent identity and type
  - Market analysis and technical indicators
  - Decision motivation and risk assessment
  - Vedic context (harmony, elements, prana)
  - Trade execution details with P&L

{'#' * 100}

"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(header)
    
    def log_event(self, level: LogLevel, category: str, message: str, details: Dict = None):
        """Log a general event"""
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{level.value}] [{category}] {message}"
        
        if details:
            entry += f"\n  Details: {json.dumps(details, indent=2, default=str)}"
        
        entry += "\n"
        
        # Write to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(entry + "\n")
        
        # Print to console for important events
        if level in [LogLevel.TRADE, LogLevel.AGENT, LogLevel.ERROR, LogLevel.CRITICAL]:
            print(entry)
    
    def log_agent_decision(self, decision: AgentDecision):
        """Log an agent decision with full details"""
        self.session.agent_decisions.append(decision)
        
        # Write detailed entry
        entry = decision.to_log_entry()
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(entry + "\n")
        
        # Print summary to console
        action_tag = f"[{decision.decision}]"
        print(f"{action_tag} {decision.agent_name}: {decision.symbol} @ ${decision.suggested_entry_price:,.2f} "
              f"(confidence: {decision.confidence:.1%})")
    
    def log_trade(self, trade: TradeExecution):
        """Log a trade execution"""
        self.session.trades.append(trade)
        
        # Write detailed entry
        entry = trade.to_log_entry()
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(entry + "\n")
        
        # Print summary
        emoji = "[BUY]" if trade.action == "BUY" else "[SELL]"
        pnl_str = f" | PnL: ${trade.realized_pnl:,.2f}" if trade.realized_pnl else ""
        print(f"{emoji} EXECUTED: {trade.action} {trade.quantity:.4f} {trade.symbol} @ ${trade.price:,.2f}{pnl_str}")
    
    def log_vedic_context(self, timestamp: str, context: Dict):
        """Log vedic context snapshot"""
        self.session.vedic_contexts.append({"timestamp": timestamp, "context": context})
        
        entry = f"""
{'===' * 13}
VEDIC CONTEXT SNAPSHOT
{'===' * 13}
Timestamp:        {timestamp}
Market Regime:    {context.get('market_regime', 'unknown')}
Harmony Score:    {context.get('harmony_score', 0):.2f}
Rahu Kala:        {'ACTIVE ⚠️' if context.get('rahu_kala_active') else 'Inactive'}
Dominant Element: {context.get('dominant_element', 'unknown')}
Navagraha:        {context.get('navagraha_dominant', 'unknown')}

Elemental Prana Levels:
  Earth (Value):   {context.get('prana', {}).get('earth', 0):.2f}
  Water (Flow):    {context.get('prana', {}).get('water', 0):.2f}
  Fire (Momentum): {context.get('prana', {}).get('fire', 0):.2f}
  Air (Volatility):{context.get('prana', {}).get('air', 0):.2f}
  Ether (Sentiment):{context.get('prana', {}).get('ether', 0):.2f}

{'☸' * 40}
"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(entry + "\n")
        
        # Only print warnings
        if context.get('rahu_kala_active'):
            print("[!] RAHU KALA ACTIVE - Trading restricted")
    
    def log_market_regime_change(self, timestamp: str, old_regime: str, new_regime: str, factors: List[str]):
        """Log market regime transition"""
        self.session.market_regime_changes.append({
            "timestamp": timestamp,
            "old_regime": old_regime,
            "new_regime": new_regime,
            "factors": factors
        })
        
        entry = f"""
{'***' * 13}
MARKET REGIME CHANGE
{'***' * 13}
Timestamp:    {timestamp}
Transition:   {old_regime} → {new_regime}

Contributing Factors:
"""
        for factor in factors:
            entry += f"  • {factor}\n"
        
        entry += f"\n{'🔄' * 40}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(entry + "\n")
        
        print(f"🔄 Market Regime: {old_regime} → {new_regime}")
    
    def finalize(self, results: Dict):
        """Finalize the session with results"""
        self.session.end_time = datetime.now().isoformat()
        self.session.final_capital = results.get('final_value', 0)
        self.session.total_return_pct = results.get('total_return_pct', 0)
        self.session.max_drawdown_pct = results.get('max_drawdown_pct', 0)
        self.session.sharpe_ratio = results.get('sharpe_ratio', 0)
        
        # Write summary
        summary = self.session.to_summary()
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(summary)
        
        # Also save as JSON for programmatic access
        json_file = os.path.join(self.output_dir, f"{self.session_id}_STRUCTURED.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.session), f, indent=2, default=str)
        
        print(f"\n[OK] Detailed log saved: {self.log_file}")
        print(f"[OK] Structured data saved: {json_file}")
        
        return self.log_file, json_file


# Example usage and test function
def create_sample_agent_decision(symbol: str, timestamp: str) -> AgentDecision:
    """Create a sample agent decision for demonstration"""
    import random
    
    decisions = ["BUY", "SELL", "HOLD"]
    elements = ["earth", "water", "fire", "air", "ether"]
    
    decision = random.choice(decisions)
    
    return AgentDecision(
        timestamp=timestamp,
        agent_name=f"Agent_{random.randint(1, 5)}",
        agent_type=random.choice(["ResearchAgent", "RiskAgent", "SentimentAgent"]),
        symbol=symbol,
        decision=decision,
        confidence=random.uniform(0.6, 0.95),
        market_analysis=f"Price showing {'bullish' if decision == 'BUY' else 'bearish' if decision == 'SELL' else 'neutral'} momentum with volume confirmation",
        technical_indicators={
            "rsi": random.uniform(30, 70),
            "macd": random.uniform(-0.5, 0.5),
            "sma_20": random.uniform(40000, 50000),
            "sma_50": random.uniform(40000, 50000),
            "volume_sma": random.uniform(1000000, 5000000)
        },
        fundamental_factors=[
            "Strong network growth",
            "Institutional adoption increasing",
            "Regulatory clarity improving"
        ],
        sentiment_score=random.uniform(-1, 1),
        primary_motivation="Technical breakout with volume confirmation" if decision == "BUY" else "Overbought conditions" if decision == "SELL" else "Awaiting clearer signal",
        secondary_motivations=[
            "Funding rates positive",
            "Social sentiment improving"
        ],
        risk_assessment="Low volatility regime, position size appropriate" if decision != "HOLD" else "High uncertainty, reducing exposure",
        vedic_harmony=random.uniform(0.5, 0.9),
        rahu_kala_active=random.random() < 0.1,
        dominant_element=random.choice(elements),
        prana_level=random.uniform(0.6, 1.0),
        suggested_position_size=random.uniform(0.1, 0.5),
        suggested_entry_price=random.uniform(40000, 50000),
        stop_loss=random.uniform(38000, 42000) if decision == "BUY" else None,
        take_profit=random.uniform(55000, 60000) if decision == "BUY" else None
    )


def create_sample_trade(symbol: str, timestamp: str, decisions: List[AgentDecision]) -> TradeExecution:
    """Create a sample trade for demonstration"""
    import random
    
    action = random.choice(["BUY", "SELL"])
    price = random.uniform(40000, 50000)
    qty = random.uniform(0.1, 0.5)
    value = price * qty
    
    return TradeExecution(
        timestamp=timestamp,
        symbol=symbol,
        action=action,
        quantity=qty,
        price=price,
        value=value,
        account_balance_before=random.uniform(90000, 100000),
        portfolio_value_before=random.uniform(90000, 100000),
        account_balance_after=random.uniform(85000, 95000),
        portfolio_value_after=random.uniform(95000, 105000),
        realized_pnl=random.uniform(-500, 2000) if action == "SELL" else None,
        agent_decisions=decisions,
        final_decision_rationale="Consensus reached among 3 of 5 agents with strong technical confirmation",
        slippage=random.uniform(0.0001, 0.001),
        execution_time_ms=random.uniform(50, 200)
    )


if __name__ == "__main__":
    # Demo: Create sample detailed log
    session_id = f"demo_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger = DetailedBacktestLogger(session_id)
    
    # Configure session
    logger.session.symbols = ["BTC", "ETH", "SOL"]
    logger.session.start_date = "2024-01-01"
    logger.session.end_date = "2024-12-31"
    logger.session.initial_capital = 10000.0
    logger.session.strategy = "Multi-Agent Vedic Strategy"
    
    # Simulate some activity
    print("\n📝 Generating sample detailed log...\n")
    
    for day in range(1, 6):
        timestamp = f"2024-01-{day:02d}T10:00:00"
        
        # Log vedic context
        logger.log_vedic_context(timestamp, {
            "market_regime": "expansion" if day % 2 == 0 else "neutral",
            "harmony_score": 0.75,
            "rahu_kala_active": day == 3,
            "dominant_element": "fire" if day % 2 == 0 else "water",
            "navagraha_dominant": "Jupiter",
            "prana": {
                "earth": 0.7,
                "water": 0.8,
                "fire": 0.9,
                "air": 0.6,
                "ether": 0.75
            }
        })
        
        # Log agent decisions
        for symbol in ["BTC", "ETH"]:
            decision = create_sample_agent_decision(symbol, timestamp)
            logger.log_agent_decision(decision)
            
            # Occasionally execute trade
            if decision.decision in ["BUY", "SELL"] and decision.confidence > 0.7:
                trade = create_sample_trade(symbol, timestamp, [decision])
                logger.log_trade(trade)
    
    # Finalize
    results = {
        "final_value": 12500.0,
        "total_return_pct": 25.0,
        "max_drawdown_pct": 15.0,
        "sharpe_ratio": 1.8
    }
    
    log_file, json_file = logger.finalize(results)
    
    print(f"\n📄 Sample log created successfully!")
    print(f"View detailed log:  {log_file}")
    print(f"View structured JSON: {json_file}")
