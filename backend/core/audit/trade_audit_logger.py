"""
Trade Audit Logger - Complete Decision Trail
Logs every agent's decision, reasoning, and contribution to final trade
"""

import json
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class DecisionType(Enum):
    AGENT_SIGNAL = "agent_signal"
    COLLECTIVE_DELIBERATION = "collective_deliberation"
    STRATEGIC_MCTS = "strategic_mcts"
    RISK_CHECK = "risk_check"
    POSITION_SIZING = "position_sizing"
    TRADE_EXECUTION = "trade_execution"
    TRADE_EXIT = "trade_exit"


@dataclass
class AgentDecisionLog:
    """Individual agent's decision"""

    timestamp: str
    agent_name: str
    agent_element: str
    symbol: str
    action: str
    confidence: float
    strength: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    prana_level: float = 0.0
    guna_state: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CollectiveDecisionLog:
    """Collective consciousness deliberation"""

    timestamp: str
    session_id: str
    symbol: str

    # Input signals
    participating_agents: List[str]
    agent_signals: List[AgentDecisionLog]

    # Output decision
    final_action: str
    final_confidence: float
    coherence: float
    harmony_score: float
    weighted_strength: float
    dominant_element: str
    suppressed_element: Optional[str]

    # Guna analysis
    collective_guna: Dict[str, float]
    guna_dominant: str
    guna_purity: float

    # Maya detection
    is_maya: bool
    maya_score: float
    maya_reason: str

    # Strategic layer (v9)
    strategic_override: bool = False
    mcts_action: str = ""
    mcts_confidence: float = 0.0
    expected_sharpe: float = 0.0
    strategic_rationale: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RiskCheckLog:
    """Risk management decision"""

    timestamp: str
    session_id: str
    symbol: str
    sector: str

    # Checks
    passed: bool
    harmony_check: bool
    harmony_score: float
    maya_check: bool
    drawdown_check: bool
    current_drawdown: float
    position_limit_check: bool
    active_positions: int
    sector_exposure: int

    # Failure reason
    rejection_reason: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PositionSizingLog:
    """Position sizing calculation"""

    timestamp: str
    session_id: str
    symbol: str

    # Inputs
    capital: float
    base_risk: float
    confidence: float
    harmony: float
    guna_dominant: str
    atr: float
    price: float

    # Multipliers
    confidence_mult: float
    harmony_mult: float
    guna_mult: float
    strategic_mult: float

    # Output
    calculated_size: float
    max_position: float
    final_size: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TradeExecutionLog:
    """Trade execution record"""

    timestamp: str
    session_id: str
    trade_id: str
    symbol: str

    # Trade details
    side: str
    size: float
    price: float
    atr: float

    # Entry context
    stop_price: float
    tp_price: float
    trailing_mult: float

    # Costs
    transaction_cost: float
    slippage_cost: float
    total_cost: float

    # Market context
    market_regime: str
    trend_1d: float
    adx: float
    rsi: float

    # Decision chain reference
    collective_decision_id: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TradeExitLog:
    """Trade exit record"""

    timestamp: str
    trade_id: str
    symbol: str

    # Exit details
    exit_price: float
    exit_reason: str
    bars_held: int

    # PnL
    gross_pnl: float
    exit_costs: float
    net_pnl: float
    return_pct: float

    # Post-trade analysis
    max_favorable_excursion: float
    max_adverse_excursion: float
    entry_harmony: float

    def to_dict(self) -> Dict:
        return asdict(self)


class TradeAuditLogger:
    """
    Central audit logger for all trading decisions

    Usage:
        logger = TradeAuditLogger()

        # Log agent signal
        logger.log_agent_signal(agent, market, signal)

        # Log collective decision
        logger.log_collective_decision(signals, market, decision)

        # Log trade execution
        logger.log_trade_execution(decision, position, market)

        # Save to file
        logger.save_session()
    """

    def __init__(self, output_dir: str = "backend/data/audit_logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Session tracking
        self.session_id = str(uuid.uuid4())[:8]
        self.session_start = datetime.now().isoformat()

        # Logs storage
        self.agent_logs: List[AgentDecisionLog] = []
        self.collective_logs: List[CollectiveDecisionLog] = []
        self.risk_logs: List[RiskCheckLog] = []
        self.sizing_logs: List[PositionSizingLog] = []
        self.execution_logs: List[TradeExecutionLog] = []
        self.exit_logs: List[TradeExitLog] = []

        # Metrics
        self.decision_count = 0
        self.trade_count = 0
        self.rejection_count = 0

        print(f"[AUDIT] Session {self.session_id} started")

    def log_agent_signal(
        self,
        agent_name: str,
        agent_element: str,
        market_state: Any,
        signal: Any,
        prana_level: float = 0.0,
        guna_state: Optional[Dict] = None,
    ) -> None:
        """Log individual agent's signal"""
        log = AgentDecisionLog(
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            agent_element=agent_element,
            symbol=getattr(market_state, "symbol", "unknown"),
            action=(signal.action.name if hasattr(signal.action, "name") else str(signal.action)),
            confidence=signal.confidence,
            strength=signal.strength,
            reasoning=signal.reasoning,
            metadata=getattr(signal, "metadata", {}),
            prana_level=prana_level,
            guna_state=guna_state or {},
        )
        self.agent_logs.append(log)

    def log_collective_decision(
        self,
        agent_signals: List[Any],
        market_state: Any,
        decision: Any,
        mcts_result: Optional[Dict] = None,
    ) -> str:
        """Log collective deliberation result, returns log ID"""
        self.decision_count += 1

        # Convert agent signals to logs
        signal_logs = []
        for sig in agent_signals:
            signal_logs.append(
                AgentDecisionLog(
                    timestamp=datetime.now().isoformat(),
                    agent_name=sig.agent_name,
                    agent_element=(
                        sig.element.value if hasattr(sig.element, "value") else str(sig.element)
                    ),
                    symbol=getattr(market_state, "symbol", "unknown"),
                    action=(sig.action.name if hasattr(sig.action, "name") else str(sig.action)),
                    confidence=sig.confidence,
                    strength=sig.strength,
                    reasoning=sig.reasoning,
                    metadata=getattr(sig, "metadata", {}),
                    prana_level=0.0,
                    guna_state={},
                )
            )

        # Determine Maya score
        maya_score = getattr(decision, "maya_score", 0.0)
        maya_reason = ""
        if getattr(decision, "is_maya", False):
            maya_reason = f"Low coherence ({getattr(decision, 'coherence', 0):.2f}) + High conflict"

        log = CollectiveDecisionLog(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            symbol=getattr(market_state, "symbol", "unknown"),
            participating_agents=[s.agent_name for s in agent_signals],
            agent_signals=signal_logs,
            final_action=(
                decision.action.name if hasattr(decision.action, "name") else str(decision.action)
            ),
            final_confidence=decision.confidence,
            coherence=getattr(decision, "coherence", 0.0),
            harmony_score=getattr(decision, "harmony_score", 0.0),
            weighted_strength=getattr(decision, "weighted_strength", 0.0),
            dominant_element=getattr(decision, "dominant_element", "unknown"),
            suppressed_element=getattr(decision, "suppressed_element", None),
            collective_guna=(
                getattr(decision.guna_state, "__dict__", {})
                if hasattr(decision, "guna_state")
                else {}
            ),
            guna_dominant=(
                getattr(decision.guna_state, "dominant", lambda: "unknown")()
                if hasattr(decision, "guna_state")
                else "unknown"
            ),
            guna_purity=(
                getattr(decision.guna_state, "purity_index", lambda: 0.0)()
                if hasattr(decision, "guna_state")
                else 0.0
            ),
            is_maya=getattr(decision, "is_maya", False),
            maya_score=maya_score,
            maya_reason=maya_reason,
            strategic_override=getattr(decision, "is_strategic_override", False),
            mcts_action=mcts_result.get("action", "") if mcts_result else "",
            mcts_confidence=mcts_result.get("confidence", 0.0) if mcts_result else 0.0,
            expected_sharpe=(mcts_result.get("expected_sharpe", 0.0) if mcts_result else 0.0),
            strategic_rationale=getattr(decision, "strategic_rationale", ""),
        )
        self.collective_logs.append(log)
        return f"{self.session_id}_{self.decision_count}"

    def log_risk_check(
        self,
        symbol: str,
        sector: str,
        decision: Any,
        risk_manager: Any,
        passed: bool,
        rejection_reason: str = "",
    ) -> None:
        """Log risk management check"""
        if not passed:
            self.rejection_count += 1

        log = RiskCheckLog(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            symbol=symbol,
            sector=sector,
            passed=passed,
            harmony_check=getattr(decision, "harmony_score", 0.0) >= 0.5,
            harmony_score=getattr(decision, "harmony_score", 0.0),
            maya_check=not getattr(decision, "is_maya", False),
            drawdown_check=getattr(risk_manager, "current_drawdown", 0.0) <= 0.15,
            current_drawdown=getattr(risk_manager, "current_drawdown", 0.0),
            position_limit_check=len(getattr(risk_manager, "active_positions", {}))
            < getattr(risk_manager, "max_total", 5),
            active_positions=len(getattr(risk_manager, "active_positions", {})),
            sector_exposure=getattr(risk_manager, "sector_exposure", {}).get(sector, 0),
            rejection_reason=rejection_reason,
        )
        self.risk_logs.append(log)

    def log_position_sizing(
        self,
        symbol: str,
        capital: float,
        decision: Any,
        atr: float,
        price: float,
        calculated_size: float,
        final_size: float,
        strategic_mult: float = 1.0,
    ) -> None:
        """Log position sizing calculation"""
        guna = getattr(decision, "guna_state", None)
        guna_mult = 1.0
        if guna:
            dominant = guna.dominant() if hasattr(guna, "dominant") else "unknown"
            if dominant == "sattva":
                guna_mult = 1.2
            elif dominant == "rajas":
                guna_mult = 0.9
            else:
                guna_mult = 0.6

        log = PositionSizingLog(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            symbol=symbol,
            capital=capital,
            base_risk=0.022,
            confidence=decision.confidence,
            harmony=getattr(decision, "harmony_score", 0.0),
            guna_dominant=(guna.dominant() if guna and hasattr(guna, "dominant") else "unknown"),
            atr=atr,
            price=price,
            confidence_mult=decision.confidence,
            harmony_mult=0.5 + getattr(decision, "harmony_score", 0.0),
            guna_mult=guna_mult,
            strategic_mult=strategic_mult,
            calculated_size=calculated_size,
            max_position=capital * 0.25,
            final_size=final_size,
        )
        self.sizing_logs.append(log)

    def log_trade_execution(
        self,
        decision: Any,
        position: Any,
        market_state: Any,
        collective_decision_id: str,
    ) -> str:
        """Log trade execution"""
        self.trade_count += 1
        trade_id = f"{self.session_id}_T{self.trade_count}"

        # Calculate costs
        tx_fee = 0.0010
        slippage = 0.0003
        total_cost_pct = tx_fee + slippage

        log = TradeExecutionLog(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            trade_id=trade_id,
            symbol=getattr(market_state, "symbol", "unknown"),
            side=position.side if hasattr(position, "side") else "unknown",
            size=getattr(position, "position", 0) * getattr(market_state, "price", 0),
            price=getattr(market_state, "price", 0),
            atr=getattr(market_state, "atr", 0),
            stop_price=getattr(position, "stop_price", 0),
            tp_price=getattr(position, "tp_price", 0),
            trailing_mult=1.3,
            transaction_cost=tx_fee,
            slippage_cost=slippage,
            total_cost=total_cost_pct,
            market_regime="unknown",  # Would need regime detection
            trend_1d=getattr(market_state, "trend_1d", 0),
            adx=getattr(market_state, "adx", 0),
            rsi=getattr(market_state, "rsi", 0),
            collective_decision_id=collective_decision_id,
        )
        self.execution_logs.append(log)
        return trade_id

    def log_trade_exit(
        self,
        trade_id: str,
        symbol: str,
        position: Any,
        exit_price: float,
        exit_reason: str,
        gross_pnl: float,
        net_pnl: float,
    ) -> None:
        """Log trade exit"""
        entry_price = getattr(position, "entry_price", exit_price)
        return_pct = (exit_price - entry_price) / entry_price if entry_price > 0 else 0

        log = TradeExitLog(
            timestamp=datetime.now().isoformat(),
            trade_id=trade_id,
            symbol=symbol,
            exit_price=exit_price,
            exit_reason=exit_reason,
            bars_held=getattr(position, "bars_in_trade", 0),
            gross_pnl=gross_pnl,
            exit_costs=gross_pnl - net_pnl,
            net_pnl=net_pnl,
            return_pct=return_pct,
            max_favorable_excursion=0.0,  # Would need tracking
            max_adverse_excursion=0.0,
            entry_harmony=getattr(position, "entry_harmony", 0.0),
        )
        self.exit_logs.append(log)

    def save_session(self, filename: Optional[str] = None) -> str:
        """Save complete audit trail to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_{self.session_id}_{timestamp}.json"

        filepath = self.output_dir / filename

        audit_data = {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.session_start,
                "end_time": datetime.now().isoformat(),
                "decision_count": self.decision_count,
                "trade_count": self.trade_count,
                "rejection_count": self.rejection_count,
            },
            "agent_decisions": [log.to_dict() for log in self.agent_logs],
            "collective_deliberations": [log.to_dict() for log in self.collective_logs],
            "risk_checks": [log.to_dict() for log in self.risk_logs],
            "position_sizing": [log.to_dict() for log in self.sizing_logs],
            "trade_executions": [log.to_dict() for log in self.execution_logs],
            "trade_exits": [log.to_dict() for log in self.exit_logs],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=2, default=str)

        print(f"[AUDIT] Saved to {filepath}")
        return str(filepath)

    def get_summary(self) -> Dict[str, Any]:
        """Get audit summary"""
        return {
            "session_id": self.session_id,
            "agent_decisions": len(self.agent_logs),
            "collective_deliberations": len(self.collective_logs),
            "risk_checks": len(self.risk_logs),
            "trades_executed": len(self.execution_logs),
            "trades_exited": len(self.exit_logs),
            "rejection_rate": self.rejection_count / max(1, self.decision_count),
        }
