
import asyncio
import sys
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

import os

# Setup async loop for windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from backend.data.repository import BaseRepository
from backend.data.models import DecisionAuditLog
from backend.core.database import SessionManager

# Define Pydantic schemas for the test
class DecisionAuditLogCreate(BaseModel):
    trace_id: str
    symbol: str
    trading_mode: str
    strategy_id: str
    timestamp: datetime
    observation_data: dict
    price: float
    volume: float

    model_config = ConfigDict(from_attributes=True)

class DecisionAuditLogUpdate(BaseModel):
    execution_status: str
    execution_data: dict

    model_config = ConfigDict(from_attributes=True)

async def test_repository():
    print("\n[START] Testing BaseRepository with DecisionAuditLog...")
    
    # 1. Initialize Repository
    repo = BaseRepository(DecisionAuditLog)
    
    # 2. Setup Test Data
    trace_id = f"test-trace-{uuid.uuid4()}"
    tenant_id = "test-tenant-001"
    
    create_data = DecisionAuditLogCreate(
        trace_id=trace_id,
        symbol="BTC/USD",
        trading_mode="MANUAL",
        strategy_id="test-strat",
        timestamp=datetime.utcnow(),
        observation_data={"price": 50000},
        price=50000.0,
        volume=1.5
    )
    
    print(f"\n[INFO] Tenant ID: {tenant_id}")
    
    # 3. Test Create
    async with SessionManager.tenant_session(tenant_id) as session:
        print("[TEST] Creating record...")
        try:
            record = await repo.create(session, create_data)
            print(f"[SUCCESS] Created record with ID: {record.id}")
            record_id = record.id
        except Exception as e:
            print(f"[FAILED] Create failed: {e}")
            return

    # 4. Test Get
    async with SessionManager.tenant_session(tenant_id) as session:
        print("[TEST] Getting record...")
        fetched = await repo.get(session, record_id)
        if fetched and fetched.trace_id == trace_id:
             print(f"[SUCCESS] Fetched record: {fetched.trace_id}")
        else:
             print(f"[FAILED] Fetch failed or mismatch")

    # 5. Test Update
    async with SessionManager.tenant_session(tenant_id) as session:
        print("[TEST] Updating record...")
        # Fetch first
        db_obj = await repo.get(session, record_id)
        if not db_obj:
            print("[FAILED] Could not fetch record for update")
            return

        update_data = DecisionAuditLogUpdate(
            execution_status="FILLED",
            execution_data={"filled_price": 50001}
        )
        updated = await repo.update(session, db_obj, update_data)
        if updated and updated.execution_status == "FILLED":
            print(f"[SUCCESS] Updated status: {updated.execution_status}")
        else:
            print(f"[FAILED] Update failed")

    # 6. Test Delete
    async with SessionManager.tenant_session(tenant_id) as session:
        print("[TEST] Deleting record...")
        deleted = await repo.delete(session, record_id)
        print(f"[SUCCESS] Deleted: {deleted}")
        
        # Verify deletion
        check = await repo.get(session, record_id)
        if check is None:
            print("[SUCCESS] Verified deletion (record is None)")
        else:
            print("[FAILED] Record still exists!")

    print("\n[DONE] Repository Test Complete")

if __name__ == "__main__":
    asyncio.run(test_repository())
