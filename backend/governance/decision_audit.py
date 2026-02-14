"""
Decision Audit Log - Persistent tracking van OODA decisions.

Voor compliance, debugging, en post-mortem analysis.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, Float, DateTime, JSON, Text, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import Base

logger = logging.getLogger(__name__)


class DecisionAuditLog(Base):
    """
    Audit log voor OODA cycle decisions.

    Tracks complete decision trail:
    - Observation data
    - Orientation output
    - Trade proposals
    - Risk assessments
    - Execution outcomes
    """

    __tablename__ = "decision_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(64), nullable=False, index=True, unique=True)
    symbol = Column(String(32), nullable=False, index=True)

    # OBSERVE
    observation_data = Column(JSON, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # ORIENT
    orientation_data = Column(JSON, nullable=True)
    market_regime = Column(String(32), nullable=True)
    core_sentiment = Column(Float, nullable=True)

    # DECIDE
    proposal_data = Column(JSON, nullable=True)
    proposed_side = Column(String(8), nullable=True)  # buy/sell
    proposed_size = Column(Float, nullable=True)

    risk_assessment_data = Column(JSON, nullable=True)
    risk_decision = Column(String(16), nullable=True)  # approve/reject/reduce
    risk_score = Column(Float, nullable=True)
    risk_rationale = Column(Text, nullable=True)

    # ACT
    execution_data = Column(JSON, nullable=True)
    execution_status = Column(String(32), nullable=True)

    # Meta
    decision_summary = Column(String(256), nullable=True)
    trading_mode = Column(String(16), nullable=False)  # notify_only/auto
    strategy_id = Column(String(64), nullable=False)

    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return (
            f"<DecisionAuditLog {self.trace_id}: "
            f"{self.symbol} {self.decision_summary}>"
        )


class AuditLogger:
    """
    Service voor audit logging van OODA decisions.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialiseer AuditLogger.

        Args:
            db_session: Async database session
        """
        self.db_session = db_session

    async def log_decision(
        self,
        trace_id: str,
        symbol: str,
        observation: Optional[Dict[str, Any]] = None,
        orientation: Optional[Dict[str, Any]] = None,
        proposal: Optional[Dict[str, Any]] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        execution: Optional[Dict[str, Any]] = None,
        decision_summary: str = "",
        trading_mode: str = "notify_only",
        strategy_id: str = "unknown",
    ) -> DecisionAuditLog:
        """
        Log complete OODA decision cycle.

        Args:
            trace_id: Unique trace ID
            symbol: Trading pair
            observation: Observation data dict
            orientation: Orientation data dict
            proposal: TradeProposal data dict
            risk_assessment: RiskAssessment data dict
            execution: Execution result dict
            decision_summary: Human-readable summary
            trading_mode: notify_only / auto
            strategy_id: Strategy identifier

        Returns:
            Created DecisionAuditLog record
        """
        try:
            # Extract key fields
            price = observation.get("price", 0.0) if observation else 0.0
            volume = observation.get("volume", 0.0) if observation else 0.0

            market_regime = orientation.get("regime") if orientation else None
            core_sentiment = orientation.get("core_sentiment") if orientation else None

            proposed_side = proposal.get("side") if proposal else None
            proposed_size = proposal.get("size") if proposal else None

            risk_decision = risk_assessment.get("decision") if risk_assessment else None
            risk_score = risk_assessment.get("risk_score") if risk_assessment else None
            risk_rationale = (
                risk_assessment.get("rationale") if risk_assessment else None
            )

            execution_status = execution.get("status") if execution else None

            # Create audit record
            audit_log = DecisionAuditLog(
                trace_id=trace_id,
                symbol=symbol,
                observation_data=observation or {},
                price=price,
                volume=volume,
                orientation_data=orientation,
                market_regime=market_regime,
                core_sentiment=core_sentiment,
                proposal_data=proposal,
                proposed_side=proposed_side,
                proposed_size=proposed_size,
                risk_assessment_data=risk_assessment,
                risk_decision=risk_decision,
                risk_score=risk_score,
                risk_rationale=risk_rationale,
                execution_data=execution,
                execution_status=execution_status,
                decision_summary=decision_summary,
                trading_mode=trading_mode,
                strategy_id=strategy_id,
            )

            self.db_session.add(audit_log)
            await self.db_session.commit()
            await self.db_session.refresh(audit_log)

            logger.info(f"Audit logged: {trace_id} - {symbol} - {decision_summary}")

            return audit_log

        except Exception as e:
            logger.error(f"Failed to log audit: {e}", exc_info=True)
            await self.db_session.rollback()
            raise

    async def get_by_trace_id(self, trace_id: str) -> Optional[DecisionAuditLog]:
        """
        Retrieve audit log by trace ID.

        Args:
            trace_id: Trace ID

        Returns:
            DecisionAuditLog or None
        """
        result = await self.db_session.execute(
            select(DecisionAuditLog).where(DecisionAuditLog.trace_id == trace_id)
        )
        return result.scalar_one_or_none()

    async def get_recent(
        self, symbol: Optional[str] = None, limit: int = 100
    ) -> List[DecisionAuditLog]:
        """
        Get recente audit logs.

        Args:
            symbol: Optional filter op symbol
            limit: Max aantal records

        Returns:
            List van DecisionAuditLog records
        """
        query = (
            select(DecisionAuditLog)
            .order_by(DecisionAuditLog.timestamp.desc())
            .limit(limit)
        )

        if symbol:
            query = query.where(DecisionAuditLog.symbol == symbol)

        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_statistics(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get audit statistics.

        Args:
            symbol: Optional filter op symbol

        Returns:
            Statistics dict
        """
        query = select(DecisionAuditLog)

        if symbol:
            query = query.where(DecisionAuditLog.symbol == symbol)

        result = await self.db_session.execute(query)
        logs = list(result.scalars().all())

        if not logs:
            return {
                "total_decisions": 0,
                "approved": 0,
                "rejected": 0,
                "approval_rate": 0.0,
            }

        total = len(logs)
        approved = sum(1 for log in logs if log.risk_decision == "approve")
        rejected = sum(1 for log in logs if log.risk_decision == "reject")

        return {
            "total_decisions": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / total if total > 0 else 0.0,
            "symbols": list(set(log.symbol for log in logs)),
        }
