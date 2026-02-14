import asyncio
import asyncpg
import sys

# Connecting as the application user (trader)
DB_URL = "postgresql://trader:trading_secure@localhost:5455/trading_db"


async def diagnose_rls():
    print("--- Diagnosing RLS Configuration ---")

    conn = await asyncpg.connect(DB_URL)
    try:
        # 1. Check Current User and Roles
        user_info = await conn.fetchrow(
            """
            SELECT 
                current_user,
                r.rolsuper,
                r.rolbypassrls,
                r.rolcreaterole
            FROM pg_roles r
            WHERE r.rolname = current_user
        """
        )
        print(f"Current User: {user_info['current_user']}")
        print(f"Is Superuser? {user_info['rolsuper']}")
        print(f"Bypass RLS? {user_info['rolbypassrls']}")

        if user_info["rolsuper"] or user_info["rolbypassrls"]:
            print(
                "\n[!] CRITICAL: User is Superuser or has BYPASSRLS. RLS will NOT work for this user."
            )
            print(
                "    Solution: Create a separate non-superuser account for the application."
            )
        else:
            print("\n[OK] User is not Superuser/BypassRLS.")

        # 2. Check Policy Existence
        policies = await conn.fetch(
            """
            SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check 
            FROM pg_policies 
            WHERE tablename = 'users'
        """
        )
        print(f"\nPolicies on 'users' table ({len(policies)} found):")
        for p in policies:
            print(f"- {p['policyname']}: {p['qual']}")

        # 3. Test Context Setting
        print("\nTesting Context Variable...")
        await conn.execute(
            "SELECT set_config('app.current_tenant', 'debug-tenant', false)"
        )
        setting = await conn.fetchval(
            "SELECT current_setting('app.current_tenant', true)"
        )
        print(f"Context set to: {setting}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(diagnose_rls())
