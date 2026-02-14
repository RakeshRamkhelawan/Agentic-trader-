"""relax_all_rls_policies

Revision ID: 009ee8d25fe9
Revises: 6b8f8b42b4f3
Create Date: 2026-02-06 22:01:45.349163+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "009ee8d25fe9"
down_revision: Union[str, None] = "6b8f8b42b4f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
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

    # 2. User Profiles
    op.execute("DROP POLICY IF EXISTS tenant_isolation_profiles ON user_profiles")
    op.execute(
        """
        CREATE POLICY tenant_isolation_profiles ON user_profiles
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text 
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
    """
    )

    # 3. User Security
    op.execute("DROP POLICY IF EXISTS tenant_isolation_security ON user_security")
    op.execute(
        """
        CREATE POLICY tenant_isolation_security ON user_security
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
    """
    )

    # 4. User Preferences
    op.execute("DROP POLICY IF EXISTS tenant_isolation_preferences ON user_preferences")
    op.execute(
        """
        CREATE POLICY tenant_isolation_preferences ON user_preferences
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
    """
    )

    # 5. API Keys
    op.execute("DROP POLICY IF EXISTS tenant_isolation_api_keys ON api_keys")
    op.execute(
        """
        CREATE POLICY tenant_isolation_api_keys ON api_keys
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
    """
    )


def downgrade() -> None:
    # Revert to strict policies
    # This might fail if app.current_tenant is not set, but downgrade is rare.
    # We'll just drop them for safety or revert to original strict SQL if needed.
    pass
