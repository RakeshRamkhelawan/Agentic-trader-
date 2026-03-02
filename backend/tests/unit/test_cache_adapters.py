import asyncio

import pytest

from backend.core.cache.adapters import MemoryAdapter


class TestMemoryAdapter:
    @pytest.fixture
    async def adapter(self):
        return MemoryAdapter(max_size=100)

    @pytest.mark.asyncio
    async def test_set_and_get(self, adapter):
        await adapter.set("test_key", "test_value", ttl=60)
        value = await adapter.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, adapter):
        value = await adapter.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, adapter):
        await adapter.set("expire_key", "expire_value", ttl=1)
        await asyncio.sleep(2)
        value = await adapter.get("expire_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, adapter):
        await adapter.set("delete_key", "delete_value", ttl=60)
        assert await adapter.exists("delete_key")
        await adapter.delete("delete_key")
        assert not await adapter.exists("delete_key")

    @pytest.mark.asyncio
    async def test_clear(self, adapter):
        await adapter.set("key1", "value1", ttl=60)
        await adapter.set("key2", "value2", ttl=60)
        await adapter.clear()
        assert await adapter.get("key1") is None
        assert await adapter.get("key2") is None

    @pytest.mark.asyncio
    async def test_max_size_eviction(self):
        adapter = MemoryAdapter(max_size=3)
        await adapter.set("key1", "value1", ttl=60)
        await adapter.set("key2", "value2", ttl=60)
        await adapter.set("key3", "value3", ttl=60)
        await adapter.set("key4", "value4", ttl=60)

        assert await adapter.get("key1") is None
        assert await adapter.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_lru_ordering(self, adapter):
        await adapter.set("key1", "value1", ttl=60)
        await adapter.set("key2", "value2", ttl=60)

        await adapter.get("key1")
        await adapter.set("key3", "value3", ttl=60)

        assert await adapter.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_update_existing(self, adapter):
        await adapter.set("update_key", "old_value", ttl=60)
        await adapter.set("update_key", "new_value", ttl=60)
        value = await adapter.get("update_key")
        assert value == "new_value"
