from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Asset, AssetStatus


class AssetManager:
    """Manages asset lifecycle states and transitions."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def update_status(self, asset_id: str, new_status: AssetStatus):
        """
        Updates the status of an asset with transition validation.

        ALLOWED TRANSITIONS:
        - DISCOVERED -> ACTIVE
        - ACTIVE -> POOLED, WATCHED, INACTIVE
        - POOLED -> ACTIVE, WATCHED, INACTIVE
        - WATCHED -> ACTIVE, POOLED, INACTIVE
        - INACTIVE -> DISCOVERED (Re-discovery)
        """
        result = await self.db_session.execute(select(Asset).where(Asset.id == asset_id))
        asset = result.scalar_one_or_none()

        if not asset:
            raise ValueError(f"Asset with id {asset_id} not found.")

        current_status = asset.status

        # Validation Matrix
        allowed_transitions = {
            AssetStatus.DISCOVERED: [AssetStatus.ACTIVE, AssetStatus.INACTIVE],
            AssetStatus.ACTIVE: [AssetStatus.POOLED, AssetStatus.WATCHED, AssetStatus.INACTIVE],
            AssetStatus.POOLED: [AssetStatus.ACTIVE, AssetStatus.WATCHED, AssetStatus.INACTIVE],
            AssetStatus.WATCHED: [AssetStatus.ACTIVE, AssetStatus.POOLED, AssetStatus.INACTIVE],
            AssetStatus.INACTIVE: [AssetStatus.DISCOVERED],
        }

        if new_status not in allowed_transitions.get(current_status, []):
            raise ValueError(f"Invalid transition from {current_status} to {new_status}")

        asset.status = new_status
        await self.db_session.commit()
        return asset
