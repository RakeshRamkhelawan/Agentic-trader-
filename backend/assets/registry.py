from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Asset, AssetStatus


class AssetRegistry:
    """Fully asynchronous registry for asset discovery and retrieval."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_all_active(self) -> list[Asset]:
        """Retrieve all active assets."""
        result = await self.db_session.execute(
            select(Asset).where(Asset.status != AssetStatus.INACTIVE)
        )
        return list(result.scalars().all())

    async def get_by_symbol(self, symbol: str) -> Asset | None:
        """Retrieve asset by symbol."""
        result = await self.db_session.execute(select(Asset).where(Asset.symbol == symbol))
        return result.scalar_one_or_none()

    async def search(self, query: str) -> list[Asset]:
        """Search assets by symbol or category."""
        result = await self.db_session.execute(
            select(Asset).where(
                or_(Asset.symbol.ilike(f"%{query}%"), Asset.category.ilike(f"%{query}%"))
            )
        )
        return list(result.scalars().all())
