
import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://trader:trading_secure@localhost:5455/trading_db")

@pytest_asyncio.fixture
async def manual_session():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_manual_execute(manual_session):
    print(f"Session Type: {type(manual_session)}")
    res = await manual_session.execute(text("SELECT 1"))
    assert res.scalar() == 1
    print("Manual Execute Success")
