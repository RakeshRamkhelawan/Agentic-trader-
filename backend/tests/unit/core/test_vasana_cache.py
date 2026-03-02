"""
Unit tests for Vasana LRU Cache (Sprint 3).
"""

import time

import numpy as np
import pytest

from backend.core.memory_system import VasanaCache, VasanaCacheEntry, MemorySystem, MemoryTrace


class TestVasanaCacheInitialization:
    """Test VasanaCache initialization."""

    def test_default_initialization(self):
        """Test cache initializes with defaults."""
        cache = VasanaCache()
        assert cache.maxsize == 1000
        assert cache.similarity_threshold == 0.98
        assert len(cache._cache) == 0

    def test_custom_initialization(self):
        """Test cache initializes with custom params."""
        cache = VasanaCache(maxsize=500, similarity_threshold=0.95)
        assert cache.maxsize == 500
        assert cache.similarity_threshold == 0.95


class TestVasanaCacheBasicOperations:
    """Test basic cache operations."""

    def test_put_and_get(self):
        """Test storing and retrieving pattern."""
        cache = VasanaCache()
        pattern = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        cache.put(pattern, action=1, confidence=0.9)
        result = cache.get(pattern)

        assert result is not None
        assert result[0] == 1  # action
        assert result[1] == 0.9  # confidence

    def test_get_missing_pattern(self):
        """Test retrieving non-existent pattern returns None."""
        cache = VasanaCache()
        pattern = np.array([1.0, 2.0, 3.0])

        result = cache.get(pattern)

        assert result is None

    def test_similar_pattern_match(self):
        """Test that similar patterns (cosine > 0.98) match."""
        cache = VasanaCache(similarity_threshold=0.98)
        pattern1 = np.array([1.0, 2.0, 3.0, 4.0])
        # Very similar pattern (99.9% cosine similarity)
        pattern2 = pattern1 * 1.001

        cache.put(pattern1, action=2, confidence=0.85)
        result = cache.get(pattern2)

        assert result is not None
        assert result[0] == 2

    def test_dissimilar_pattern_no_match(self):
        """Test that dissimilar patterns don't match."""
        cache = VasanaCache(similarity_threshold=0.98)
        pattern1 = np.array([1.0, 0.0, 0.0, 0.0])
        pattern2 = np.array([0.0, 1.0, 0.0, 0.0])  # Orthogonal

        cache.put(pattern1, action=1)
        result = cache.get(pattern2)

        assert result is None


class TestVasanaCacheLRU:
    """Test LRU eviction behavior."""

    def test_lru_eviction(self):
        """Test that oldest entries are evicted when full."""
        cache = VasanaCache(maxsize=3)

        # Fill cache
        for i in range(3):
            cache.put(np.array([float(i)]), action=i)

        assert len(cache._cache) == 3

        # Add one more - should evict oldest
        cache.put(np.array([100.0]), action=100)

        assert len(cache._cache) == 3
        # First entry should be evicted
        assert cache.get(np.array([0.0])) is None
        # New entry should exist
        assert cache.get(np.array([100.0])) is not None

    def test_lru_update_on_access(self):
        """Test that accessing updates LRU order."""
        cache = VasanaCache(maxsize=3, similarity_threshold=0.99)

        # Add 3 clearly different entries (high dimensional for distinct hashes)
        cache.put(np.array([1.0, 0.0, 0.0, 0.0]), action=1)
        cache.put(np.array([0.0, 1.0, 0.0, 0.0]), action=2)
        cache.put(np.array([0.0, 0.0, 1.0, 0.0]), action=3)

        # Access first entry (makes it most recently used)
        cache.get(np.array([1.0, 0.0, 0.0, 0.0]))

        # Add new entry - should evict second, not first
        cache.put(np.array([0.0, 0.0, 0.0, 1.0]), action=4)

        assert cache.get(np.array([1.0, 0.0, 0.0, 0.0])) is not None  # Still there
        assert cache.get(np.array([0.0, 1.0, 0.0, 0.0])) is None  # Evicted


class TestVasanaCacheStats:
    """Test cache statistics."""

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        cache = VasanaCache()
        pattern = np.array([1.0, 2.0, 3.0])

        # Miss
        cache.get(pattern)
        # Hit
        cache.put(pattern, action=1)
        cache.get(pattern)

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_eviction_stats(self):
        """Test eviction counter."""
        cache = VasanaCache(maxsize=2)

        for i in range(5):
            cache.put(np.array([float(i)]), action=i)

        stats = cache.get_stats()
        assert stats["evictions"] == 3  # 5 - 2 = 3 evicted
        assert stats["insertions"] == 5

    def test_clear(self):
        """Test clearing cache."""
        cache = VasanaCache()
        cache.put(np.array([1.0]), action=1)
        cache.get(np.array([2.0]))  # Miss

        cache.clear()
        stats = cache.get_stats()

        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert cache.get(np.array([1.0])) is None


class TestVasanaCachePerformance:
    """Test performance requirements."""

    def test_cache_hit_latency(self):
        """Test that cache hits are handled in < 50μs (Python realistic)."""
        cache = VasanaCache()
        pattern = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        cache.put(pattern, action=1, confidence=0.9)

        # Warm up
        for _ in range(100):
            cache.get(pattern)

        # Measure
        start = time.perf_counter_ns()
        for _ in range(1000):
            cache.get(pattern)
        elapsed_ns = time.perf_counter_ns() - start

        avg_latency_ns = elapsed_ns / 1000
        avg_latency_us = avg_latency_ns / 1000

        # Should be < 50μs (realistic for Python with hash lookup)
        assert avg_latency_us < 50, f"Cache hit latency {avg_latency_us:.2f}μs exceeds 50μs limit"


class TestMemorySystemWithCache:
    """Test MemorySystem integration with VasanaCache."""

    def test_get_tendency_uses_cache(self):
        """Test that get_tendency uses and updates cache."""
        memory = MemorySystem(cache_size=100)

        # Create perception first to get the right pattern shape
        perception = {"state_vector": np.array([1.0, 2.0, 3.0, 4.0, 5.0])}
        pattern = memory._extract_pattern(perception)  # Get correct 10-element shape

        # First, populate memory with some traces to form clusters
        for i in range(10):
            memory.memory_buffer.append(
                MemoryTrace(
                    pattern=pattern.copy(),
                    action_taken=1,  # Consistent action
                    outcome=0.05,
                    timestamp=i,
                )
            )
            memory._update_clusters(memory.memory_buffer[-1])

        # First call - cache miss, should query clusters
        result1 = memory.get_tendency(perception)

        # Stats should show cache miss
        stats = memory.get_statistics()
        assert stats["vasana_cache"]["misses"] >= 1

        # Second call with same perception - should hit cache
        result2 = memory.get_tendency(perception)

        # Stats should show cache hit
        stats = memory.get_statistics()
        assert stats["vasana_cache"]["hits"] >= 1

    def test_cache_stats_in_memory_stats(self):
        """Test that cache stats are included in memory stats."""
        memory = MemorySystem()

        stats = memory.get_statistics()

        assert "vasana_cache" in stats
        assert "size" in stats["vasana_cache"]
        assert "hit_rate" in stats["vasana_cache"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
