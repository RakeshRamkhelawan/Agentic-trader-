"""
Alembic migration: Fix timestamp column type for decision_audit_logs.

Changes TIMESTAMP -> TIMESTAMPTZ to match timezone-aware Python datetimes
used by the DecisionAuditLog model (datetime.now(UTC)).

Revision ID: fix_audit_timestamp_tz
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'fix_audit_ts_tz'
down_revision = 'a026789ec63d'  # add_decision_audit_logs_table
branch_labels = None
depends_on = None


def upgrade():
    """Alter timestamp column to TIMESTAMPTZ."""
    op.alter_column(
        'decision_audit_logs',
        'timestamp',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False,
        postgresql_using="timestamp AT TIME ZONE 'UTC'"
    )


def downgrade():
    """Revert to TIMESTAMP without timezone."""
    op.alter_column(
        'decision_audit_logs',
        'timestamp',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False
    )
