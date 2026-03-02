import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from backend.assets.models import Asset, AssetStatus, Base
from backend.assets.manager import AssetManager
import os
import time

# Use the environment URL or a default for testing
DATABASE_URL = os.getenv(
    "POSTGRES_ASYNC_URL", "postgresql+asyncpg://trader:trading_secure@localhost:5456/trading_db"
)


@pytest_asyncio.fixture(scope="function")
async def engine():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_asset_persistence_and_transitions(db_session):
    """Subtask 1: Validate database state persistence and basic transitions."""
    asset_id = uuid.uuid4()
    asset = Asset(id=asset_id, symbol="BTC/USDT", exchange="BINANCE", status=AssetStatus.DISCOVERED)
    db_session.add(asset)
    await db_session.commit()

    # Verify persistence
    result = await db_session.execute(select(Asset).where(Asset.id == asset_id))
    persisted_asset = result.scalar_one()
    assert persisted_asset.symbol == "BTC/USDT"
    assert persisted_asset.status == AssetStatus.DISCOVERED

    # Test multi-component interaction via Manager
    manager = AssetManager(db_session)
    start_time = time.time()
    updated_asset = await manager.update_status(str(asset_id), AssetStatus.ACTIVE)
    latency = time.time() - start_time

    assert updated_asset.status == AssetStatus.ACTIVE
    assert latency < 1.0  # Performance benchmark check

    # Verify update in DB
    result = await db_session.execute(select(Asset).where(Asset.id == asset_id))
    final_asset = result.scalar_one()
    assert final_asset.status == AssetStatus.ACTIVE


@pytest.mark.asyncio
async def test_complex_state_transitions(db_session):
    """Subtask 2: Focus on complex state transitions like POOLED to INACTIVE and WATCHED to ACTIVE."""
    manager = AssetManager(db_session)

    # 1. POOLED -> INACTIVE
    asset_pooled = Asset(
        id=uuid.uuid4(), symbol="ETH/USDT", exchange="BINANCE", status=AssetStatus.POOLED
    )
    db_session.add(asset_pooled)
    await db_session.commit()

    await manager.update_status(str(asset_pooled.id), AssetStatus.INACTIVE)
    result = await db_session.execute(select(Asset).where(Asset.id == asset_pooled.id))
    assert result.scalar_one().status == AssetStatus.INACTIVE

    # 2. WATCHED -> ACTIVE
    asset_watched = Asset(
        id=uuid.uuid4(), symbol="SOL/USDT", exchange="BINANCE", status=AssetStatus.WATCHED
    )
    db_session.add(asset_watched)
    await db_session.commit()

    await manager.update_status(str(asset_watched.id), AssetStatus.ACTIVE)
    result = await db_session.execute(select(Asset).where(Asset.id == asset_watched.id))
    assert result.scalar_one().status == AssetStatus.ACTIVE


@pytest.mark.asyncio
async def test_invalid_transitions(db_session):
    """Verify enforcement of invalid transitions."""
    manager = AssetManager(db_session)
    asset = Asset(
        id=uuid.uuid4(), symbol="ADA/USDT", exchange="BINANCE", status=AssetStatus.DISCOVERED
    )
    db_session.add(asset)
    await db_session.commit()

    # DISCOVERED cannot go directly to WATCHED (based on manager logic)
    with pytest.raises(ValueError, match="Invalid transition"):
        await manager.update_status(str(asset.id), AssetStatus.WATCHED)
