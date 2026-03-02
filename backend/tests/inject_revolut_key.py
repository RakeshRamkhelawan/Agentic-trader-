import asyncio

from sqlalchemy.future import select

from backend.core.database import SessionManager
from backend.models.user_settings import APIKey, User
from backend.schemas.user_settings import ExchangeType
from backend.services.user_settings_service import cipher_suite


async def inject():
    async with SessionManager.system_admin_session() as db:
        res = await db.execute(select(User).where(User.tenant_id == "demo-tenant"))
        user = res.scalars().first()
        if not user:
            print("User demo-tenant not found")
            return

        # Check if already exists
        res = await db.execute(
            select(APIKey).where(APIKey.user_id == user.id, APIKey.exchange == ExchangeType.REVOLUT)
        )
        if res.scalars().first():
            print("Revolut key already exists for demo-tenant")
            return

        key_enc = cipher_suite.encrypt(b"dummy_key").decode()
        sec_enc = cipher_suite.encrypt(b"dummy_secret").decode()

        new_key = APIKey(
            user_id=user.id,
            name="REVOLUT_DEMO",
            exchange=ExchangeType.REVOLUT,
            api_key_encrypted=key_enc,
            api_secret_encrypted=sec_enc,
            is_valid=True,
        )
        db.add(new_key)
        await db.commit()
        print("Revolut key injected for demo-tenant")


if __name__ == "__main__":
    asyncio.run(inject())
