
# Explicitly set env before imports
import os
import sys
# Set DB URL directly if needed or ensure loading
# sys.path.append(...) is handled by PYTHONPATH

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
from backend.models.user_settings import User
from backend.core.config.settings import settings

async def check():
    print(f"Checking DB: {settings.DATABASE_URL}")
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            await session.execute(text("SET app.current_tenant = 'system_admin'"))
            result = await session.execute(select(User).where(User.email == 'admin@agentic-trader.com'))
            user = result.scalar_one_or_none()
            if user:
                print(f"FOUND: ID={user.id}")
            else:
                print("NOT FOUND")
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await session.close()
    
    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check())
