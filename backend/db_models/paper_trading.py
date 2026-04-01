"""
Paper Trading Models for V18

Database schema for persistent paper trading storage.
Includes trades, sessions, analytics, and agent performance tracking.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.core.database import Base


class PaperTradingSession(Base):
    """Paper trading session metadata."""

    __tablename__ = "paper_trading_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(String(50), nullable=False, default="paper_v18")

    # Session config
    initial_capital = Column(Float, nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_hours = Column(Integer, nullable=False, default=8)

    # Session status
    is_active = Column(Boolean, default=True)
    stopped_reason = Column(String(100), nullable=True)  # completed, manual, circuit_breaker

    # Final results (updated when session ends)
    final_capital = Column(Float, nullable=True)
    total_pnl = Column(Float, nullable=True)
    total_pnl_pct = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    # Performance metrics
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trades = relationship("PaperTrade", back_populates="session", cascade="all, delete-orphan")
    analytics = relationship(
        "PaperTradingAnalytics", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_session_account", "account_id", "started_at"),
        Index("idx_session_active", "is_active", "account_id"),
    )


class PaperTrade(Base):
    """Individual paper trade record."""

    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(50),
        ForeignKey("paper_trading_sessions.session_id"),
        nullable=False,
        index=True,
    )

    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy/sell
    order_type = Column(String(20), nullable=False, default="market")  # market/limit

    # Quantities
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    value = Column(Float, nullable=False)  # quantity * price
    commission = Column(Float, default=0.0)

    # P&L (for exits)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)

    # Agent info
    agent = Column(String(50), nullable=False, default="V18_Elemental")
    strategy = Column(String(100), nullable=True)

    # Consensus data
    consensus_score = Column(Float, nullable=True)
    dominant_agent = Column(String(50), nullable=True)  # VEDASTRO, EARTH, FIRE, WATER
    entry_type = Column(String(10), nullable=True)  # HARD/SOFT

    # VedAstro data
    vedastro_signal = Column(String(20), nullable=True)
    vedastro_confidence = Column(Float, nullable=True)
    vedastro_score = Column(Float, nullable=True)
    dominant_planet = Column(String(20), nullable=True)

    # Elemental votes (stored as JSON for flexibility)
    elemental_votes = Column(JSON, nullable=True)  # {"earth": 0.5, "fire": 0.3, ...}
    regime = Column(String(20), nullable=True)  # expansion/contraction/neutral

    # Timestamps
    entry_time = Column(DateTime, nullable=True)  # For exits: when position was opened
    exit_time = Column(DateTime, nullable=True)  # For exits: when position was closed
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Trade type
    trade_type = Column(String(10), nullable=False, default="entry")  # entry/exit
    exit_reason = Column(String(200), nullable=True)  # For exits: why we exited
    is_hard_exit = Column(Boolean, default=False)

    # Exchange info
    exchange = Column(String(50), default="Bitvavo")

    # Raw analysis data (for debugging/research)
    analysis_data = Column(JSON, nullable=True)

    # Relationships
    session = relationship("PaperTradingSession", back_populates="trades")

    __table_args__ = (
        Index("idx_trade_session_symbol", "session_id", "symbol"),
        Index("idx_trade_symbol_time", "symbol", "executed_at"),
        Index("idx_trade_agent", "agent", "executed_at"),
        Index("idx_trade_type", "trade_type", "session_id"),
    )


class PaperTradingAnalytics(Base):
    """Per-cycle analytics for machine learning."""

    __tablename__ = "paper_trading_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(50),
        ForeignKey("paper_trading_sessions.session_id"),
        nullable=False,
        index=True,
    )

    # Cycle info
    cycle = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Symbol being analyzed
    symbol = Column(String(20), nullable=False, index=True)
    analysis_type = Column(String(10), nullable=False)  # entry/exit

    # Price data
    current_price = Column(Float, nullable=False)

    # VedAstro analysis
    vedastro_signal = Column(String(20), nullable=True)
    vedastro_confidence = Column(Float, nullable=True)
    vedastro_score = Column(Float, nullable=True)
    vedastro_vote = Column(Float, nullable=True)
    dominant_planet = Column(String(20), nullable=True)

    # Elemental analysis
    earth_vote = Column(Float, nullable=True)
    earth_can_enter = Column(Boolean, nullable=True)
    fire_vote = Column(Float, nullable=True)
    fire_position_size = Column(Float, nullable=True)
    water_vote = Column(Float, nullable=True)
    water_regime = Column(String(20), nullable=True)

    # Gunas
    sattva = Column(Float, nullable=True)
    rajas = Column(Float, nullable=True)
    tamas = Column(Float, nullable=True)
    guna_multiplier = Column(Float, nullable=True)

    # Vayu
    vayu_dampener = Column(Float, nullable=True)
    vayu_sentiment = Column(String(20), nullable=True)

    # Consensus
    total_vote = Column(Float, nullable=True)
    raw_consensus = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    dominant_agent = Column(String(50), nullable=True)

    # Portfolio state at analysis time
    portfolio_value = Column(Float, nullable=True)
    cash = Column(Float, nullable=True)
    open_positions_count = Column(Integer, nullable=True)

    # Decision
    action = Column(String(10), nullable=True)  # BUY/SELL/HOLD/SKIP
    decision_reason = Column(Text, nullable=True)

    # Full analysis JSON (for research)
    full_analysis = Column(JSON, nullable=True)

    # Relationships
    session = relationship("PaperTradingSession", back_populates="analytics")

    __table_args__ = (
        Index("idx_analytics_session_cycle", "session_id", "cycle"),
        Index("idx_analytics_symbol_decision", "symbol", "action"),
        UniqueConstraint(
            "session_id", "cycle", "symbol", "analysis_type", name="uq_analytics_cycle"
        ),
    )


class AgentPerformance(Base):
    """Track agent performance per symbol/regime."""

    __tablename__ = "agent_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Key
    agent = Column(String(50), nullable=False)  # VEDASTRO, EARTH, FIRE, WATER
    symbol = Column(String(20), nullable=True)  # Can be NULL for overall
    regime = Column(String(20), nullable=True)  # expansion/contraction/neutral

    # Stats
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)

    # P&L
    total_pnl = Column(Float, default=0.0)
    avg_pnl_per_trade = Column(Float, nullable=True)
    max_profit = Column(Float, nullable=True)
    max_loss = Column(Float, nullable=True)

    # Performance score (updated periodically)
    performance_score = Column(Float, default=1.0)  # 0.0-2.0 multiplier

    # Last updated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_performance_agent_symbol", "agent", "symbol", "regime"),
        UniqueConstraint("agent", "symbol", "regime", name="uq_agent_performance"),
    )


class ChittaExperience(Base):
    """Agent experiences for learning (separate from Chitta memory system)."""

    __tablename__ = "chitta_experiences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(50),
        ForeignKey("paper_trading_sessions.session_id"),
        nullable=False,
        index=True,
    )

    # Experience context
    symbol = Column(String(20), nullable=False, index=True)
    regime = Column(String(20), nullable=False, index=True)
    dominant_planet = Column(String(20), nullable=True, index=True)

    # Decision context
    agent = Column(String(50), nullable=False)  # Which agent made the decision
    consensus_score = Column(Float, nullable=True)

    # Outcome
    action = Column(String(10), nullable=False)  # BUY/SELL
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    was_profitable = Column(Boolean, nullable=True)

    # Learning value (calculated)
    experience_value = Column(Float, nullable=True)  # How valuable is this experience

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Full context for retrieval
    context = Column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_experience_symbol_regime", "symbol", "regime"),
        Index("idx_experience_agent_outcome", "agent", "was_profitable"),
    )
