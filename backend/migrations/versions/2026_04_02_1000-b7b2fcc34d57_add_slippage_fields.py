"""add_slippage_fields

Revision ID: b7b2fcc34d57
Revises: a7a1fcc234b4
Create Date: 2026-04-02 10:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7b2fcc34d57"
down_revision: str | None = "a7a1fcc234b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add slippage fields to paper_trades
    op.add_column("paper_trades", sa.Column("intended_price", sa.Float(), nullable=True))
    op.add_column("paper_trades", sa.Column("slippage_pct", sa.Float(), nullable=True))

    # Add expected_slippage to paper_trading_analytics
    op.add_column(
        "paper_trading_analytics", sa.Column("expected_slippage", sa.Float(), nullable=True)
    )


def downgrade() -> None:
    # Remove slippage fields from paper_trades
    op.drop_column("paper_trades", "slippage_pct")
    op.drop_column("paper_trades", "intended_price")

    # Remove expected_slippage from paper_trading_analytics
    op.drop_column("paper_trading_analytics", "expected_slippage")
