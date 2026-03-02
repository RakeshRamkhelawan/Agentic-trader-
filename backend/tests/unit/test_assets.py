import pytest
import asyncio
import time
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from backend.assets.models import Asset, AssetStatus
from backend.assets.manager import AssetManager


@pytest.mark.asyncio
class TestAssetLifecycle:
    async def test_initial_state_discovered(self, db_session: AsyncSession):
        """Test that a new asset starts in DISCOVERED state."""
        asset = Asset(symbol="BTC", exchange="bitvavo", status=AssetStatus.DISCOVERED)
        db_session.add(asset)
        await db_session.commit()
        assert asset.status == AssetStatus.DISCOVERED

    async def test_valid_state_transitions(self, db_session: AsyncSession):
        """Test allowed state transitions with performance check."""
        manager = AssetManager(db_session)
        asset = Asset(symbol="ETH", exchange="bitvavo", status=AssetStatus.DISCOVERED)
        db_session.add(asset)
        await db_session.commit()

        start_time = time.time()
        # DISCOVERED -> ACTIVE
        await manager.update_status(asset.id, AssetStatus.ACTIVE)
        assert asset.status == AssetStatus.ACTIVE

        # ACTIVE -> POOLED
        await manager.update_status(asset.id, AssetStatus.POOLED)
        assert asset.status == AssetStatus.POOLED

        # POOLED -> WATCHED
        await manager.update_status(asset.id, AssetStatus.WATCHED)
        assert asset.status == AssetStatus.WATCHED

        # WATCHED -> INACTIVE
        await manager.update_status(asset.id, AssetStatus.INACTIVE)
        assert asset.status == AssetStatus.INACTIVE

        end_time = time.time()
        assert (end_time - start_time) < 1.0  # Latency target < 1s

    async def test_invalid_transition_matrix(self, db_session: AsyncSession):
        """Test disallowed transitions throw validation errors."""
        manager = AssetManager(db_session)
        asset = Asset(symbol="SOL", exchange="bitvavo", status=AssetStatus.INACTIVE)
        db_session.add(asset)
        await db_session.commit()

        # INACTIVE cannot go back to POOLED directly in this spec
        with pytest.raises(ValueError, match="Invalid transition"):
            await manager.update_status(asset.id, AssetStatus.POOLED)
