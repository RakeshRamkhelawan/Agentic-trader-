"""add_paper_trading_and_rag_tables

Revision ID: a7a1fcc234b4
Revises: d8a9e0b6f807
Create Date: 2026-03-06 00:21:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7a1fcc234b4"
down_revision: str | None = "d8a9e0b6f807"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ==========================================
    # Paper Trading Tables
    # ==========================================

    # Paper Trading Sessions
    op.create_table(
        "paper_trading_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(50), nullable=False),
        sa.Column("account_id", sa.String(50), nullable=False, server_default="paper_v18"),
        sa.Column("initial_capital", sa.Float(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_hours", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("stopped_reason", sa.String(100), nullable=True),
        sa.Column("final_capital", sa.Float(), nullable=True),
        sa.Column("total_pnl", sa.Float(), nullable=True),
        sa.Column("total_pnl_pct", sa.Float(), nullable=True),
        sa.Column("total_trades", sa.Integer(), default=0),
        sa.Column("winning_trades", sa.Integer(), default=0),
        sa.Column("losing_trades", sa.Integer(), default=0),
        sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        sa.Column("max_drawdown", sa.Float(), nullable=True),
        sa.Column("max_drawdown_pct", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("idx_session_account", "paper_trading_sessions", ["account_id", "started_at"])
    op.create_index("idx_session_active", "paper_trading_sessions", ["is_active", "account_id"])

    # Paper Trades
    op.create_table(
        "paper_trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "session_id",
            sa.String(50),
            sa.ForeignKey("paper_trading_sessions.session_id"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("order_type", sa.String(20), nullable=False, server_default="market"),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("commission", sa.Float(), server_default="0.0"),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("pnl_pct", sa.Float(), nullable=True),
        sa.Column("agent", sa.String(50), nullable=False, server_default="V18_Elemental"),
        sa.Column("strategy", sa.String(100), nullable=True),
        sa.Column("consensus_score", sa.Float(), nullable=True),
        sa.Column("dominant_agent", sa.String(50), nullable=True),
        sa.Column("entry_type", sa.String(10), nullable=True),
        sa.Column("vedastro_signal", sa.String(20), nullable=True),
        sa.Column("vedastro_confidence", sa.Float(), nullable=True),
        sa.Column("vedastro_score", sa.Float(), nullable=True),
        sa.Column("dominant_planet", sa.String(20), nullable=True),
        sa.Column("elemental_votes", sa.JSON(), nullable=True),
        sa.Column("regime", sa.String(20), nullable=True),
        sa.Column("entry_time", sa.DateTime(), nullable=True),
        sa.Column("exit_time", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("trade_type", sa.String(10), nullable=False, server_default="entry"),
        sa.Column("exit_reason", sa.String(200), nullable=True),
        sa.Column("is_hard_exit", sa.Boolean(), default=False),
        sa.Column("exchange", sa.String(50), server_default="Bitvavo"),
        sa.Column("analysis_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_trade_session_symbol", "paper_trades", ["session_id", "symbol"])
    op.create_index("idx_trade_symbol_time", "paper_trades", ["symbol", "executed_at"])
    op.create_index("idx_trade_agent", "paper_trades", ["agent", "executed_at"])
    op.create_index("idx_trade_type", "paper_trades", ["trade_type", "session_id"])

    # Paper Trading Analytics
    op.create_table(
        "paper_trading_analytics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "session_id",
            sa.String(50),
            sa.ForeignKey("paper_trading_sessions.session_id"),
            nullable=False,
        ),
        sa.Column("cycle", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("analysis_type", sa.String(10), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=False),
        sa.Column("vedastro_signal", sa.String(20), nullable=True),
        sa.Column("vedastro_confidence", sa.Float(), nullable=True),
        sa.Column("vedastro_score", sa.Float(), nullable=True),
        sa.Column("vedastro_vote", sa.Float(), nullable=True),
        sa.Column("dominant_planet", sa.String(20), nullable=True),
        sa.Column("earth_vote", sa.Float(), nullable=True),
        sa.Column("earth_can_enter", sa.Boolean(), nullable=True),
        sa.Column("fire_vote", sa.Float(), nullable=True),
        sa.Column("fire_position_size", sa.Float(), nullable=True),
        sa.Column("water_vote", sa.Float(), nullable=True),
        sa.Column("water_regime", sa.String(20), nullable=True),
        sa.Column("sattva", sa.Float(), nullable=True),
        sa.Column("rajas", sa.Float(), nullable=True),
        sa.Column("tamas", sa.Float(), nullable=True),
        sa.Column("guna_multiplier", sa.Float(), nullable=True),
        sa.Column("vayu_dampener", sa.Float(), nullable=True),
        sa.Column("vayu_sentiment", sa.String(20), nullable=True),
        sa.Column("total_vote", sa.Float(), nullable=True),
        sa.Column("raw_consensus", sa.Float(), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("dominant_agent", sa.String(50), nullable=True),
        sa.Column("portfolio_value", sa.Float(), nullable=True),
        sa.Column("cash", sa.Float(), nullable=True),
        sa.Column("open_positions_count", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(10), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("full_analysis", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id", "cycle", "symbol", "analysis_type", name="uq_analytics_cycle"
        ),
    )
    op.create_index(
        "idx_analytics_session_cycle",
        "paper_trading_analytics",
        ["session_id", "cycle"],
    )
    op.create_index(
        "idx_analytics_symbol_decision", "paper_trading_analytics", ["symbol", "action"]
    )

    # Agent Performance
    op.create_table(
        "agent_performance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=True),
        sa.Column("regime", sa.String(20), nullable=True),
        sa.Column("total_trades", sa.Integer(), server_default="0"),
        sa.Column("winning_trades", sa.Integer(), server_default="0"),
        sa.Column("losing_trades", sa.Integer(), server_default="0"),
        sa.Column("win_rate", sa.Float(), nullable=True),
        sa.Column("total_pnl", sa.Float(), server_default="0.0"),
        sa.Column("avg_pnl_per_trade", sa.Float(), nullable=True),
        sa.Column("max_profit", sa.Float(), nullable=True),
        sa.Column("max_loss", sa.Float(), nullable=True),
        sa.Column("performance_score", sa.Float(), server_default="1.0"),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent", "symbol", "regime", name="uq_agent_performance"),
    )
    op.create_index(
        "idx_performance_agent_symbol",
        "agent_performance",
        ["agent", "symbol", "regime"],
    )

    # Chitta Experiences
    op.create_table(
        "chitta_experiences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "session_id",
            sa.String(50),
            sa.ForeignKey("paper_trading_sessions.session_id"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("regime", sa.String(20), nullable=False),
        sa.Column("dominant_planet", sa.String(20), nullable=True),
        sa.Column("agent", sa.String(50), nullable=False),
        sa.Column("consensus_score", sa.Float(), nullable=True),
        sa.Column("action", sa.String(10), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("pnl_pct", sa.Float(), nullable=True),
        sa.Column("was_profitable", sa.Boolean(), nullable=True),
        sa.Column("experience_value", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_experience_symbol_regime", "chitta_experiences", ["symbol", "regime"])
    op.create_index(
        "idx_experience_agent_outcome",
        "chitta_experiences",
        ["agent", "was_profitable"],
    )

    # Note: trading_knowledge table skipped - using ChromaDB for RAG instead


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("chitta_experiences")
    op.drop_table("agent_performance")
    op.drop_table("paper_trading_analytics")
    op.drop_table("paper_trades")
    op.drop_table("paper_trading_sessions")
