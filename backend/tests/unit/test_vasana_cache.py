"""
Unit tests for Vasana Cache (Sprint 3).
"""

import asyncio
import time
from unittest.mock import MagicMock

import numpy as np
import pytest

from backend.core.vasana_cache import VasanaCache, CachedPattern, OptimizedMemorySystem


class TestVasanaCache:
    """Test cases for VasanaCache."""

    def test_initialization(self):
        """Test cache initialization."""
        cache = VasanaCache(capacity=500)

        assert cache.capacity == 500
        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    @pytest.mark.asyncio
    async def test_put_and_get(self):
        """Test basic put and get operations."""
        cache = VasanaCache()

        pattern = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        # Put pattern
        await cache.put(pattern, action=1, confidence=0.8)

        # Get pattern
        cached = await cache.get(pattern)

        assert cached is not None
        assert cached.action == 1
        assert cached.confidence == 0.8

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self):
        """Test cache hit rate tracking."""
        cache = VasanaCache()

        pattern = np.array([0.1, 0.2, 0.3])

        # First access - miss
        await cache.get(pattern)

        # Add to cache
        await cache.put(pattern, action=1)

        # Second access - hit
        await cache.get(pattern)

        stats = cache.get_statistics()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = VasanaCache(capacity=3)

        # Add 3 patterns
        for i in range(3):
            await cache.put(np.array([i]), action=i)

        assert len(cache._cache) == 3

        # Access pattern 0 (makes it most recent)
        await cache.get(np.array([0]))

        # Add pattern 3 (should evict pattern 1 - LRU)
        await cache.put(np.array([3]), action=3)

        assert len(cache._cache) == 3
        assert await cache.get(np.array([1])) is None  # Evicted
        assert await cache.get(np.array([0])) is not None  # Still there

    @pytest.mark.asyncio
    async def test_warm_cache(self):
        """Test cache warming."""
        cache = VasanaCache()

        patterns = [
            (np.array([0.1]), 1, 0.8),
            (np.array([0.2]), 0, 0.7),
            (np.array([0.3]), 2, 0.9),
        ]

        count = await cache.warm(patterns)

        assert count == 3
        assert len(cache._cache) == 3

    def test_clear(self):
        """Test cache clearing."""
        cache = VasanaCache()
        cache._cache["key1"] = CachedPattern("key1", 1, 0.5, [], 1, time.time(), time.time())
        cache._hits = 10

        cache.clear()

        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_get_statistics(self):
        """Test statistics retrieval."""
        cache = VasanaCache(capacity=1000)
        cache._hits = 80
        cache._misses = 20

        stats = cache.get_statistics()

        assert stats["capacity"] == 1000
        assert stats["hits"] == 80
        assert stats["misses"] == 20
        assert stats["hit_rate"] == 0.8


class TestVasanaCachePerformance:
    """Performance tests for VasanaCache."""

    @pytest.mark.asyncio
    async def test_get_performance(self):
        """Benchmark cache get operation."""
        cache = VasanaCache()

        # Pre-populate
        for i in range(100):
            await cache.put(np.array([i * 0.01]), action=i % 3)

        # Benchmark
        start = time.perf_counter()

        for i in range(1000):
            await cache.get(np.array([0.5]))

        elapsed = time.perf_counter() - start
        avg_time = elapsed / 1000

        print(f"\nCache get avg time: {avg_time*1e6:.2f}μs")

        # Should be < 10μs
        assert avg_time < 1e-5  # Relaxed for CI

    @pytest.mark.asyncio
    async def test_put_performance(self):
        """Benchmark cache put operation."""
        cache = VasanaCache()

        start = time.perf_counter()

        for i in range(100):
            await cache.put(np.array([i * 0.01]), action=i % 3)

        elapsed = time.perf_counter() - start
        avg_time = elapsed / 100

        print(f"\nCache put avg time: {avg_time*1e6:.2f}μs")

        # Should be < 100μs
        assert avg_time < 1e-4


class TestOptimizedMemorySystem:
    """Test cases for OptimizedMemorySystem with cache."""

    def test_initialization(self):
        """Test optimized memory system initialization."""
        mem = OptimizedMemorySystem(capacity=5000, cache_capacity=500)

        assert mem.capacity == 5000
        assert mem.vasana_cache.capacity == 500

    def test_cache_integration(self):
        """Test that cache is integrated with memory system."""
        mem = OptimizedMemorySystem()

        assert hasattr(mem, "vasana_cache")
        assert isinstance(mem.vasana_cache, VasanaCache)
