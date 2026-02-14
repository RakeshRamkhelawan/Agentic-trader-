"""Force_RLS_On_Owner

Revision ID: dfc9b5beeeb6
Revises: 55ecaf0e6516
Create Date: 2026-02-06 01:37:54.055000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dfc9b5beeeb6"
down_revision: Union[str, None] = "55ecaf0e6516"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tables = ["users", "user_profiles", "user_security", "user_preferences", "api_keys"]
    for table in tables:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    tables = ["users", "user_profiles", "user_security", "user_preferences", "api_keys"]
    for table in tables:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
