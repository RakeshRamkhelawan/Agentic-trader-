"""relax_user_rls_policy

Revision ID: 6b8f8b42b4f3
Revises: b6b48ed2be8a
Create Date: 2026-02-06 21:51:03.393666+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b8f8b42b4f3"
down_revision: Union[str, None] = "b6b48ed2be8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Relax RLS to allow Login/Seeding (Global Access via system_admin)
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
    op.execute(
        """
        CREATE POLICY tenant_isolation_users ON users
        USING (
            tenant_id = current_setting('app.current_tenant', true)::text 
            OR current_setting('app.current_tenant', true)::text = 'system_admin'
        )
    """
    )


def downgrade() -> None:
    # Revert to strict policy
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
    op.execute(
        """
        CREATE POLICY tenant_isolation_users ON users
        USING (tenant_id = current_setting('app.current_tenant')::text)
    """
    )
