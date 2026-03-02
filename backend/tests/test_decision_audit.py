"""
Tests voor Decision Audit Log.

Test audit logging, retrieval, en statistics.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.governance.decision_audit import AuditLogger, DecisionAuditLog


@pytest.fixture
async def db_session():
    """In-memory test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_observation():
    """Sample observation data."""
    return {
        "symbol": "BTC/USDT",
        "price": 50000.0,
        "volume": 1000.0,
        "orderbook": {"bids": [], "asks": []},
        "timestamp": datetime.now(UTC).timestamp(),
    }


@pytest.fixture
def sample_orientation():
    """Sample orientation data."""
    return {
        "symbol": "BTC/USDT",
        "regime": "trending_up",
        "indicators": {"rsi": 65.0},
        "core_sentiment": 0.75,
        "confidence": 0.75,
    }


@pytest.fixture
def sample_proposal():
    """Sample trade proposal."""
    return {
        "symbol": "BTC/USDT",
        "side": "buy",
        "size": 0.1,
        "entry_price": 50000.0,
        "stop_loss": 49000.0,
        "take_profit": 52000.0,
    }


@pytest.fixture
def sample_risk_assessment():
    """Sample risk assessment."""
    return {"decision": "approve", "rationale": "All checks passed", "risk_score": 0.2}


class TestDecisionAuditLog:
    """Tests for DecisionAuditLog."""

    @pytest.mark.asyncio
    async def test_log_complete_decision(
        self,
        db_session,
        sample_observation,
        sample_orientation,
        sample_proposal,
        sample_risk_assessment,
    ):
        """Happy path: Log complete decision cycle."""
        logger = AuditLogger(db_session)

        audit_log = await logger.log_decision(
            trace_id="test-trace-123",
            symbol="BTC/USDT",
            observation=sample_observation,
            orientation=sample_orientation,
            proposal=sample_proposal,
            risk_assessment=sample_risk_assessment,
            decision_summary="APPROVED: BUY BTC/USDT",
            trading_mode="notify_only",
            strategy_id="momentum_v1",
        )

        assert audit_log.trace_id == "test-trace-123"
        assert audit_log.symbol == "BTC/USDT"
        assert audit_log.price == 50000.0
        assert audit_log.volume == 1000.0
        assert audit_log.market_regime == "trending_up"
        assert audit_log.proposed_side == "buy"
        assert audit_log.risk_decision == "approve"
        assert audit_log.risk_score == 0.2
        assert audit_log.decision_summary == "APPROVED: BUY BTC/USDT"

    @pytest.mark.asyncio
    async def test_log_partial_decision(self, db_session, sample_observation):
        """Log partial decision (no proposal)."""
        logger = AuditLogger(db_session)

        audit_log = await logger.log_decision(
            trace_id="test-trace-456",
            symbol="ETH/USDT",
            observation=sample_observation,
            decision_summary="NO_SIGNAL",
            trading_mode="auto",
            strategy_id="test",
        )

        assert audit_log.trace_id == "test-trace-456"
        assert audit_log.proposal_data is None
        assert audit_log.risk_assessment_data is None
        assert audit_log.decision_summary == "NO_SIGNAL"

    @pytest.mark.asyncio
    async def test_retrieve_by_trace_id(self, db_session, sample_observation):
        """Retrieve audit log by trace ID."""
        logger = AuditLogger(db_session)

        # Log decision
        await logger.log_decision(
            trace_id="retrieve-test-789",
            symbol="BTC/USDT",
            observation=sample_observation,
            decision_summary="TEST",
            strategy_id="test",
        )

        # Retrieve
        retrieved = await logger.get_by_trace_id("retrieve-test-789")

        assert retrieved is not None
        assert retrieved.trace_id == "retrieve-test-789"
        assert retrieved.symbol == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_get_recent_logs(self, db_session, sample_observation):
        """Get recent audit logs."""
        logger = AuditLogger(db_session)

        # Log 3 decisions
        for i in range(3):
            await logger.log_decision(
                trace_id=f"recent-{i}",
                symbol="BTC/USDT",
                observation=sample_observation,
                decision_summary=f"Decision {i}",
                strategy_id="test",
            )

        # Get recent
        recent = await logger.get_recent(limit=10)

        assert len(recent) == 3
        # Most recent first
        assert recent[0].trace_id == "recent-2"

    @pytest.mark.asyncio
    async def test_get_recent_filtered_by_symbol(self, db_session, sample_observation):
        """Filter recent logs by symbol."""
        logger = AuditLogger(db_session)

        # Log for BTC
        await logger.log_decision(
            trace_id="btc-1",
            symbol="BTC/USDT",
            observation=sample_observation,
            decision_summary="BTC decision",
            strategy_id="test",
        )

        # Log for ETH
        await logger.log_decision(
            trace_id="eth-1",
            symbol="ETH/USDT",
            observation={**sample_observation, "symbol": "ETH/USDT"},
            decision_summary="ETH decision",
            strategy_id="test",
        )

        # Filter BTC only
        btc_logs = await logger.get_recent(symbol="BTC/USDT")

        assert len(btc_logs) == 1
        assert btc_logs[0].symbol == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_statistics_calculation(
        self, db_session, sample_observation, sample_risk_assessment
    ):
        """Calculate audit statistics."""
        logger = AuditLogger(db_session)

        # Log 2 approved
        for i in range(2):
            await logger.log_decision(
                trace_id=f"approved-{i}",
                symbol="BTC/USDT",
                observation=sample_observation,
                risk_assessment=sample_risk_assessment,
                decision_summary="APPROVED",
                strategy_id="test",
            )

        # Log 1 rejected
        rejected = {**sample_risk_assessment, "decision": "reject"}
        await logger.log_decision(
            trace_id="rejected-1",
            symbol="BTC/USDT",
            observation=sample_observation,
            risk_assessment=rejected,
            decision_summary="REJECTED",
            strategy_id="test",
        )

        # Get stats
        stats = await logger.get_statistics()

        assert stats["total_decisions"] == 3
        assert stats["approved"] == 2
        assert stats["rejected"] == 1
        assert stats["approval_rate"] == pytest.approx(2 / 3)
        assert "BTC/USDT" in stats["symbols"]

    @pytest.mark.asyncio
    async def test_statistics_empty(self, db_session):
        """Statistics with no logs."""
        logger = AuditLogger(db_session)

        stats = await logger.get_statistics()

        assert stats["total_decisions"] == 0
        assert stats["approval_rate"] == 0.0
