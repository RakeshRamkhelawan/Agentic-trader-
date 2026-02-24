from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.data.repository import BaseRepository
from backend.execution.fast_config import FastConfig
from backend.models.config import RuntimeConfig


class ConfigService:
    """
    Service for managing dynamic system configuration.

    Features:
    - Persistent storage via RuntimeConfig (DB)
    - Caching for fast read access
    - Integration with FastConfig for hot-path settings
    """

    def __init__(self):
        self.repo = BaseRepository(RuntimeConfig)
        # Simple in-memory cache
        self._cache = {}

    async def get_setting(self, session: AsyncSession, key: str, default: Any = None) -> Any:
        """
        Get a configuration setting by key.
        """
        # 1. Check Cache
        if key in self._cache:
            return self._cache[key]

        # 2. Check DB
        # TODO: Add find_by_key to BaseRepository to avoid raw SQL here
        result = await session.execute(select(RuntimeConfig).where(RuntimeConfig.key == key))
        config = result.scalar_one_or_none()

        if config:
            self._cache[key] = config.value
            return config.value

        return default

    async def set_setting(
        self,
        session: AsyncSession,
        key: str,
        value: Any,
        description: str = None,
        group: str = "general",
    ) -> RuntimeConfig:
        """
        Set a configuration setting. Creates if not exists, updates otherwise.
        """
        # Check if exists
        result = await session.execute(select(RuntimeConfig).where(RuntimeConfig.key == key))
        existing = result.scalar_one_or_none()

        if existing:
            update_data = {
                "value": value,
                "updated_at": datetime.now(UTC).replace(tzinfo=None).replace(tzinfo=None),
            }
            if description:
                update_data["description"] = description

            # Use repository update
            updated = await self.repo.update(session, existing, update_data)
            self._cache[key] = value
            return updated
        else:
            # Create new via repository
            create_data = {
                "key": key,
                "value": value,
                "description": description,
                "group": group,
                "updated_at": datetime.now(UTC).replace(tzinfo=None),
            }
            new_config = await self.repo.create(session, create_data)
            self._cache[key] = value
            return new_config

    async def get_all_settings(
        self, session: AsyncSession, group: str = None
    ) -> list[RuntimeConfig]:
        """
        Get all settings, optionally filtered by group.
        """
        query = select(RuntimeConfig)
        if group:
            query = query.where(RuntimeConfig.group == group)

        result = await session.execute(query)
        return result.scalars().all()

    def get_hot_path_config(self) -> dict:
        """
        Read the current FastConfig (Hot Path).
        """
        try:
            return FastConfig.read()
        except RuntimeError:
            # Not initialized
            return {}


# Singleton instance
config_service = ConfigService()
