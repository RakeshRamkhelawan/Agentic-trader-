"""enable_rls_orders

Revision ID: 9ae422ce3d22
Revises: 009ee8d25fe9
Create Date: 2026-02-07 08:14:26.427669+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ae422ce3d22"
down_revision: str | None = "009ee8d25fe9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable RLS on orders
    op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY")

    # Create Policy
    # Allow tenant matching OR system_admin bypass
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON orders
        USING (
            tenant_id = current_setting('app.current_tenant', true)::VARCHAR
            OR
            current_setting('app.current_tenant', true)::VARCHAR = 'system_admin'
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON orders")
    op.execute("ALTER TABLE orders DISABLE ROW LEVEL SECURITY")
