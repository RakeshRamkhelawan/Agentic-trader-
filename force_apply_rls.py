from sqlalchemy import create_engine, text

from backend.core.config.settings import settings


def apply_rls_fix():
    print("🔧 Applying RLS Fix (Sync)...")

    # Candidate URLs (SYNC)
    # Default settings.DATABASE_URL is likely sync "postgresql://..."
    urls = [
        "postgresql://trader:trading_secure@localhost:5455/trading_db",
        "postgresql://app:app_secure@localhost:5455/trading_db",
        "postgresql://rsram@localhost:5432/agentic_trader",  # Default
        "postgresql://postgres@localhost:5432/agentic_trader",  # Root fallback
        str(settings.DATABASE_URL),  # From settings
    ]

    engine = None
    connected = False

    for url in urls:
        print(f"Trying connection: {url}")
        try:
            # Use psycopg2 (default for postgresql://)
            curr_engine = create_engine(url)
            with curr_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Connected successfully using: {url}")
            engine = curr_engine
            connected = True
            break
        except Exception as e:
            print(f"❌ Failed: {e}")
            curr_engine.dispose()

    if not connected:
        print("CRITICAL: All connection attempts failed. Cannot apply RLS fix.")
        return

    # SQL to relax ALL policies
    sqls = [
        # 1. Users
        "DROP POLICY IF EXISTS tenant_isolation_users ON users",
        """
        CREATE POLICY tenant_isolation_users ON users
        USING (
            tenant_id = current_setting('app.current_tenant', true)::text 
            OR current_setting('app.current_tenant', true)::text = 'system_admin'
        )
        """,
        # 2. User Profiles
        "DROP POLICY IF EXISTS tenant_isolation_profiles ON user_profiles",
        """
        CREATE POLICY tenant_isolation_profiles ON user_profiles
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text 
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
        """,
        # 3. User Security
        "DROP POLICY IF EXISTS tenant_isolation_security ON user_security",
        """
        CREATE POLICY tenant_isolation_security ON user_security
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
        """,
        # 4. User Preferences
        "DROP POLICY IF EXISTS tenant_isolation_preferences ON user_preferences",
        """
        CREATE POLICY tenant_isolation_preferences ON user_preferences
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
        """,
        # 5. API Keys
        "DROP POLICY IF EXISTS tenant_isolation_api_keys ON api_keys",
        """
        CREATE POLICY tenant_isolation_api_keys ON api_keys
        USING (
            user_id IN (
                SELECT id FROM users 
                WHERE tenant_id = current_setting('app.current_tenant', true)::text
                OR current_setting('app.current_tenant', true)::text = 'system_admin'
            )
        )
        """,
    ]

    with engine.begin() as conn:
        for sql in sqls:
            print(f"Executing: {sql[:50]}...")
            conn.execute(text(sql))

    engine.dispose()
    print("✅ RLS Policies Updated Successfully")


if __name__ == "__main__":
    apply_rls_fix()
