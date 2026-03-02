"""Enable_RLS

Revision ID: 55ecaf0e6516
Revises: 86b433c9e782
Create Date: 2026-02-06 01:36:21.389041+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "55ecaf0e6516"
down_revision: str | None = "86b433c9e782"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Users Table
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_users ON users
        USING (tenant_id = current_setting('app.current_tenant')::text)
    """
    )

    # 2. User Profiles
    # Join with users to check tenant_id, OR rely on simple implicit joins if tenant_id was on profile.
    # But currently UserProfile does NOT have tenant_id, it has user_id.
    # So we must join via user_id.
    op.execute("ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_profiles ON user_profiles
        USING (
            user_id IN (
                SELECT id FROM users
                WHERE tenant_id = current_setting('app.current_tenant')::text
            )
        )
    """
    )

    # 3. User Security
    op.execute("ALTER TABLE user_security ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_security ON user_security
        USING (
            user_id IN (
                SELECT id FROM users
                WHERE tenant_id = current_setting('app.current_tenant')::text
            )
        )
    """
    )

    # 4. User Preferences
    op.execute("ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_preferences ON user_preferences
        USING (
            user_id IN (
                SELECT id FROM users
                WHERE tenant_id = current_setting('app.current_tenant')::text
            )
        )
    """
    )

    # 5. API Keys
    op.execute("ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_api_keys ON api_keys
        USING (
            user_id IN (
                SELECT id FROM users
                WHERE tenant_id = current_setting('app.current_tenant')::text
            )
        )
    """
    )


def downgrade() -> None:
    # Drop Policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_api_keys ON api_keys")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_preferences ON user_preferences")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_security ON user_security")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_profiles ON user_profiles")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")

    # Disable RLS
    op.execute("ALTER TABLE api_keys DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_preferences DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_security DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
