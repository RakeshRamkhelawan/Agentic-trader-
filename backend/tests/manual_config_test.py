import asyncio
import os
import sys

# Setup async loop for windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv

from backend.core.database import SessionManager
from backend.services.config_service import config_service

load_dotenv()


async def test_config_service():
    print("\n[START] Testing ConfigService...")

    tenant_id = "test-tenant-config"
    key = "test.risk_limit_daily"
    value = {"amount": 5000, "currency": "USD"}

    async with SessionManager.tenant_session(tenant_id) as session:
        # 1. Test Set Setting
        print("[TEST] Setting configuration...")
        config = await config_service.set_setting(
            session,
            key=key,
            value=value,
            description="Daily risk limit test",
            group="risk",
        )
        print(f"[SUCCESS] Set config: {config.key} = {config.value}")

        # 2. Test Get Setting (Cache miss logic handled internally or by fresh session)
        print("[TEST] Getting configuration...")
        fetched_value = await config_service.get_setting(session, key)
        if fetched_value == value:
            print(f"[SUCCESS] Fetched value matches: {fetched_value}")
        else:
            print(f"[FAILED] Fetched value mismatch: {fetched_value} != {value}")

        # 3. Test Update Setting
        print("[TEST] Updating configuration...")
        new_value = {"amount": 10000, "currency": "USD"}
        updated = await config_service.set_setting(session, key=key, value=new_value)
        print(f"[SUCCESS] Updated config: {updated.value}")

        # 4. Verify Update
        check_val = await config_service.get_setting(session, key)
        if check_val == new_value:
            print(f"[SUCCESS] Verified update: {check_val}")
        else:
            print("[FAILED] Update verification failed")

    print("[DONE] ConfigService Test Complete")


if __name__ == "__main__":
    asyncio.run(test_config_service())
