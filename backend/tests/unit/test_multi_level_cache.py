from unittest.mock import AsyncMock

import pytest

from backend.core.cache.adapters import MemoryAdapter
from backend.core.cache.multi_level_cache import MultiLevelCache


class TestMultiLevelCache:
    @pytest.fixture
    async def cache(self):
        l1 = MemoryAdapter(max_size=100)
        l2_mock = AsyncMock()
        l3_mock = AsyncMock()

        return MultiLevelCache(
            adapters=[l1, l2_mock, l3_mock], default_ttls=[300, 900, 86400]
        )

    @pytest.mark.asyncio
    async def test_get_from_l1(self, cache):
        await cache._adapters[0].set("test_key", "test_value", 300)
        value = await cache.get("namespace", "test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_with_backfill(self, cache):
        cache._adapters[1].get = AsyncMock(return_value="l2_value")
        cache._adapters[1].set = AsyncMock(return_value=True)

        value = await cache.get("namespace", "key")
        assert value == "l2_value"

        cache._adapters[0].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_all_levels(self, cache):
        cache._adapters[1].set = AsyncMock(return_value=True)
        cache._adapters[2].set = AsyncMock(return_value=True)

        result = await cache.set("namespace", "value", "key")
        assert result is True

        cache._adapters[1].set.assert_called_once()
        cache._adapters[2].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_all_levels(self, cache):
        cache._adapters[1].delete = AsyncMock(return_value=True)
        cache._adapters[2].delete = AsyncMock(return_value=True)

        result = await cache.delete("namespace", "key")
        assert result is True

        cache._adapters[1].delete.assert_called_once()
        cache._adapters[2].delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_hit(self, cache):
        await cache._adapters[0].set("compute_key", "cached_value", 300)

        compute_fn = AsyncMock(return_value="computed_value")
        value = await cache.get_or_compute("namespace", compute_fn, "compute_key")

        assert value == "cached_value"
        compute_fn.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_miss(self, cache):
        async def compute_fn(*args, **kwargs):
            return "computed_value"

        cache._adapters[1].set = AsyncMock(return_value=True)
        cache._adapters[2].set = AsyncMock(return_value=True)

        value = await cache.get_or_compute("namespace", compute_fn, "new_key")

        assert value == "computed_value"
        cache._adapters[1].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_specific_level(self, cache):
        cache._adapters[1].clear = AsyncMock(return_value=True)

        result = await cache.clear(level=1)
        assert result is True
        cache._adapters[1].clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_all_levels(self, cache):
        cache._adapters[1].clear = AsyncMock(return_value=True)
        cache._adapters[2].clear = AsyncMock(return_value=True)

        result = await cache.clear()
        assert result is True

    @pytest.mark.asyncio
    async def test_key_generation_consistency(self, cache):
        key1 = cache._generate_key("ns", "arg1", "arg2", param="value")
        key2 = cache._generate_key("ns", "arg1", "arg2", param="value")
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_custom_ttls(self, cache):
        cache._adapters[1].set = AsyncMock(return_value=True)
        cache._adapters[2].set = AsyncMock(return_value=True)

        custom_ttls = [60, 180, 3600]
        await cache.set("namespace", "value", "key", ttls=custom_ttls)

        cache._adapters[1].set.assert_called_once()
