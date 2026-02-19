import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.core.database import Base
import asyncio

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a new database session for a test."""
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        yield session
        
    await engine.dispose()
