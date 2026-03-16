"""
Paper Trading Database Service

Handles all database operations for paper trading:
- Session management
- Trade storage
- Analytics logging
- Performance tracking
- Experience learning
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import SessionManager
from backend.db_models.paper_trading import (
    AgentPerformance,
    ChittaExperience,
    PaperTrade,
    PaperTradingAnalytics,
    PaperTradingSession,
)

logger = logging.getLogger("PaperTradingDB")


class PaperTradingDB:
    """Database service for paper trading operations."""

    def __init__(self):
        self.session: Optional[AsyncSession] = None
        self.session_manager = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session_manager = SessionManager.system_admin_session()
        self.session = await self.session_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session_manager:
            await self.session_manager.__aexit__(exc_type, exc_val, exc_tb)
            self.session = None
            self.session_manager = None

    # ========================================================================
    # Session Management
    # ========================================================================

    async def create_session(
        self,
        session_id: str,
        initial_capital: float,
        duration_hours: int = 8,
        account_id: str = "paper_v18",
    ) -> PaperTradingSession:
        """Create a new paper trading session."""
        session = PaperTradingSession(
            session_id=session_id,
            account_id=account_id,
            initial_capital=initial_capital,
            duration_hours=duration_hours,
            started_at=datetime.utcnow(),
            is_active=True,
        )

        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)

        logger.info(f"[DB] Created session {session_id} with €{initial_capital:,.2f}")
        return session

    async def get_session(self, session_id: str) -> Optional[PaperTradingSession]:
        """Get session by ID."""
        result = await self.session.execute(
            select(PaperTradingSession).where(PaperTradingSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_session(
        self, account_id: str = "paper_v18"
    ) -> Optional[PaperTradingSession]:
        """Get currently active session for account."""
        result = await self.session.execute(
            select(PaperTradingSession)
            .where(
                and_(
                    PaperTradingSession.account_id == account_id,
                    PaperTradingSession.is_active.is_(True),
                )
            )
            .order_by(desc(PaperTradingSession.started_at))
        )
        return result.scalar_one_or_none()

    async def end_session(
        self, session_id: str, final_capital: float, reason: str = "completed"
    ) -> None:
        """End a session and update final stats."""
        session = await self.get_session(session_id)
        if not session:
            logger.warning(f"[DB] Session {session_id} not found")
            return

        # Calculate final stats
        total_pnl = final_capital - session.initial_capital
        total_pnl_pct = (
            (total_pnl / session.initial_capital) * 100 if session.initial_capital > 0 else 0
        )

        # Get trade stats
        trade_stats = await self.get_session_trade_stats(session_id)

        session.ended_at = datetime.utcnow()
        session.is_active = False
        session.stopped_reason = reason
        session.final_capital = final_capital
        session.total_pnl = total_pnl
        session.total_pnl_pct = total_pnl_pct
        session.total_trades = trade_stats["total_trades"]
        session.winning_trades = trade_stats["winning_trades"]
        session.losing_trades = trade_stats["losing_trades"]

        await self.session.commit()
        logger.info(
            f"[DB] Ended session {session_id}: P&L €{total_pnl:+.2f} ({total_pnl_pct:+.2f}%)"
        )

    # ========================================================================
    # Trade Storage
    # ========================================================================

    async def save_trade(self, trade_data: Dict[str, Any]) -> PaperTrade:
        """Save a trade to database."""
        trade = PaperTrade(
            session_id=trade_data["session_id"],
            symbol=trade_data["symbol"],
            side=trade_data["side"],
            order_type=trade_data.get("order_type", "market"),
            quantity=trade_data["quantity"],
            price=trade_data["price"],
            value=trade_data.get("value", trade_data["quantity"] * trade_data["price"]),
            commission=trade_data.get("commission", 0.0),
            pnl=trade_data.get("pnl"),
            pnl_pct=trade_data.get("pnl_pct"),
            agent=trade_data.get("agent", "V18_Elemental"),
            strategy=trade_data.get("strategy"),
            consensus_score=trade_data.get("consensus_score"),
            dominant_agent=trade_data.get("dominant_agent"),
            entry_type=trade_data.get("entry_type"),
            vedastro_signal=trade_data.get("vedastro_signal"),
            vedastro_confidence=trade_data.get("vedastro_confidence"),
            vedastro_score=trade_data.get("vedastro_score"),
            dominant_planet=trade_data.get("dominant_planet"),
            elemental_votes=trade_data.get("elemental_votes"),
            regime=trade_data.get("regime"),
            entry_time=trade_data.get("entry_time"),
            exit_time=trade_data.get("exit_time"),
            trade_type=trade_data.get("trade_type", "entry"),
            exit_reason=trade_data.get("exit_reason"),
            is_hard_exit=trade_data.get("is_hard_exit", False),
            exchange=trade_data.get("exchange", "Bitvavo"),
            analysis_data=trade_data.get("analysis_data"),
            executed_at=trade_data.get("executed_at", datetime.utcnow()),
        )

        self.session.add(trade)
        await self.session.commit()
        await self.session.refresh(trade)

        logger.debug(f"[DB] Saved trade {trade.id}: {trade.side} {trade.symbol} @ €{trade.price}")
        return trade

    async def get_trades(
        self,
        session_id: Optional[str] = None,
        symbol: Optional[str] = None,
        trade_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[PaperTrade]:
        """Get trades with optional filters."""
        query = select(PaperTrade).order_by(desc(PaperTrade.executed_at))

        if session_id:
            query = query.where(PaperTrade.session_id == session_id)
        if symbol:
            query = query.where(PaperTrade.symbol == symbol)
        if trade_type:
            query = query.where(PaperTrade.trade_type == trade_type)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_session_trade_stats(self, session_id: str) -> Dict[str, Any]:
        """Get trade statistics for a session."""
        # Total trades
        total_result = await self.session.execute(
            select(func.count(PaperTrade.id)).where(
                and_(PaperTrade.session_id == session_id, PaperTrade.trade_type == "exit")
            )
        )
        total_trades = total_result.scalar() or 0

        # Winning trades
        wins_result = await self.session.execute(
            select(func.count(PaperTrade.id)).where(
                and_(
                    PaperTrade.session_id == session_id,
                    PaperTrade.trade_type == "exit",
                    PaperTrade.pnl > 0,
                )
            )
        )
        winning_trades = wins_result.scalar() or 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
        }

    # ========================================================================
    # Analytics Storage
    # ========================================================================

    async def save_analytics(self, analysis_data: Dict[str, Any]) -> PaperTradingAnalytics:
        """Save per-cycle analytics."""
        analysis = PaperTradingAnalytics(
            session_id=analysis_data["session_id"],
            cycle=analysis_data["cycle"],
            timestamp=analysis_data.get("timestamp", datetime.utcnow()),
            symbol=analysis_data["symbol"],
            analysis_type=analysis_data["analysis_type"],
            current_price=analysis_data["current_price"],
            vedastro_signal=analysis_data.get("vedastro_signal"),
            vedastro_confidence=analysis_data.get("vedastro_confidence"),
            vedastro_score=analysis_data.get("vedastro_score"),
            vedastro_vote=analysis_data.get("vedastro_vote"),
            dominant_planet=analysis_data.get("dominant_planet"),
            earth_vote=analysis_data.get("earth_vote"),
            earth_can_enter=analysis_data.get("earth_can_enter"),
            fire_vote=analysis_data.get("fire_vote"),
            fire_position_size=analysis_data.get("fire_position_size"),
            water_vote=analysis_data.get("water_vote"),
            water_regime=analysis_data.get("water_regime"),
            sattva=analysis_data.get("sattva"),
            rajas=analysis_data.get("rajas"),
            tamas=analysis_data.get("tamas"),
            guna_multiplier=analysis_data.get("guna_multiplier"),
            vayu_dampener=analysis_data.get("vayu_dampener"),
            vayu_sentiment=analysis_data.get("vayu_sentiment"),
            total_vote=analysis_data.get("total_vote"),
            raw_consensus=analysis_data.get("raw_consensus"),
            threshold=analysis_data.get("threshold"),
            passed=analysis_data.get("passed"),
            dominant_agent=analysis_data.get("dominant_agent"),
            portfolio_value=analysis_data.get("portfolio_value"),
            cash=analysis_data.get("cash"),
            open_positions_count=analysis_data.get("open_positions_count"),
            action=analysis_data.get("action"),
            decision_reason=analysis_data.get("decision_reason"),
            full_analysis=analysis_data.get("full_analysis"),
        )

        self.session.add(analysis)
        await self.session.commit()
        return analysis

    # ========================================================================
    # Agent Performance
    # ========================================================================

    async def update_agent_performance(
        self, agent: str, symbol: Optional[str], regime: Optional[str], pnl: float, was_win: bool
    ) -> None:
        """Update agent performance metrics."""
        # Get or create performance record
        result = await self.session.execute(
            select(AgentPerformance).where(
                and_(
                    AgentPerformance.agent == agent,
                    AgentPerformance.symbol == symbol,
                    AgentPerformance.regime == regime,
                )
            )
        )
        performance = result.scalar_one_or_none()

        if not performance:
            performance = AgentPerformance(
                agent=agent,
                symbol=symbol,
                regime=regime,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                total_pnl=0.0,
            )
            self.session.add(performance)

        # Update stats
        performance.total_trades = (performance.total_trades or 0) + 1
        if was_win:
            performance.winning_trades = (performance.winning_trades or 0) + 1
        else:
            performance.losing_trades = (performance.losing_trades or 0) + 1

        performance.total_pnl = (performance.total_pnl or 0) + pnl
        performance.win_rate = (
            performance.winning_trades / performance.total_trades * 100
            if performance.total_trades > 0
            else 0
        )
        performance.avg_pnl_per_trade = (
            performance.total_pnl / performance.total_trades if performance.total_trades > 0 else 0
        )

        # Update max profit/loss
        if pnl > (performance.max_profit or 0):
            performance.max_profit = pnl
        if pnl < (performance.max_loss or 0):
            performance.max_loss = pnl

        # Calculate performance score (0.0 - 2.0)
        # Based on win rate and average P&L
        if performance.total_trades >= 5:
            win_rate_score = min(1.0, performance.win_rate / 100)
            pnl_score = min(1.0, max(0, performance.avg_pnl_per_trade / 100))
            performance.performance_score = 0.5 + win_rate_score + pnl_score

        await self.session.commit()
        logger.debug(f"[DB] Updated {agent} performance: {performance.win_rate:.1f}% win rate")

    async def get_agent_performance(
        self,
        agent: Optional[str] = None,
        symbol: Optional[str] = None,
        regime: Optional[str] = None,
    ) -> List[AgentPerformance]:
        """Get agent performance metrics."""
        query = select(AgentPerformance)

        if agent:
            query = query.where(AgentPerformance.agent == agent)
        if symbol:
            query = query.where(AgentPerformance.symbol == symbol)
        if regime:
            query = query.where(AgentPerformance.regime == regime)

        result = await self.session.execute(query)
        return result.scalars().all()

    # ========================================================================
    # Chitta Experience (Learning)
    # ========================================================================

    async def save_experience(self, experience_data: Dict[str, Any]) -> ChittaExperience:
        """Save an experience for learning."""
        experience = ChittaExperience(
            session_id=experience_data["session_id"],
            symbol=experience_data["symbol"],
            regime=experience_data["regime"],
            dominant_planet=experience_data.get("dominant_planet"),
            agent=experience_data["agent"],
            consensus_score=experience_data.get("consensus_score"),
            action=experience_data["action"],
            pnl=experience_data.get("pnl"),
            pnl_pct=experience_data.get("pnl_pct"),
            was_profitable=experience_data.get("was_profitable"),
            experience_value=experience_data.get("experience_value"),
            context=experience_data.get("context"),
        )

        self.session.add(experience)
        await self.session.commit()
        await self.session.refresh(experience)

        logger.debug(
            f"[DB] Saved experience {experience.id}: {experience.symbol} {experience.action} = {experience.pnl:+.2f}"
        )
        return experience

    async def get_similar_experiences(
        self,
        symbol: str,
        regime: str,
        dominant_planet: Optional[str] = None,
        agent: Optional[str] = None,
        was_profitable: Optional[bool] = None,
        limit: int = 10,
    ) -> List[ChittaExperience]:
        """Get similar past experiences for learning."""
        query = select(ChittaExperience).where(
            and_(ChittaExperience.symbol == symbol, ChittaExperience.regime == regime)
        )

        if dominant_planet:
            query = query.where(ChittaExperience.dominant_planet == dominant_planet)
        if agent:
            query = query.where(ChittaExperience.agent == agent)
        if was_profitable is not None:
            query = query.where(ChittaExperience.was_profitable == was_profitable)

        query = query.order_by(desc(ChittaExperience.created_at)).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def calculate_experience_adjustment(
        self, symbol: str, regime: str, dominant_planet: Optional[str] = None
    ) -> float:
        """Calculate consensus adjustment based on past experiences."""
        # Get profitable experiences
        profitable = await self.get_similar_experiences(
            symbol=symbol,
            regime=regime,
            dominant_planet=dominant_planet,
            was_profitable=True,
            limit=20,
        )

        # Get unprofitable experiences
        unprofitable = await self.get_similar_experiences(
            symbol=symbol,
            regime=regime,
            dominant_planet=dominant_planet,
            was_profitable=False,
            limit=20,
        )

        if not profitable and not unprofitable:
            return 0.0  # No data, no adjustment

        # Calculate adjustment
        profitable_count = len(profitable)
        unprofitable_count = len(unprofitable)
        total = profitable_count + unprofitable_count

        if total < 3:
            return 0.0  # Not enough data

        # Win rate based adjustment
        win_rate = profitable_count / total

        # Scale based on number of samples (more samples = more confident)
        confidence = min(1.0, total / 10)  # Max confidence at 10+ samples

        # Adjustment range: -0.1 to +0.1
        adjustment = (win_rate - 0.5) * 0.2 * confidence

        logger.debug(
            f"[DB] Experience adjustment for {symbol}: {adjustment:+.3f} (win rate: {win_rate:.1%})"
        )
        return adjustment


# Singleton instance
_paper_trading_db: Optional[PaperTradingDB] = None


def get_paper_trading_db() -> PaperTradingDB:
    """Get singleton PaperTradingDB instance."""
    global _paper_trading_db
    if _paper_trading_db is None:
        _paper_trading_db = PaperTradingDB()
    return _paper_trading_db
