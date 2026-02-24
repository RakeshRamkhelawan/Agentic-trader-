"""
Data processing optimizations for the prediction market intelligence service.

This module provides utilities for:
- Batch processing
- Query optimization
- Memory efficiency
- Caching strategies
"""

import logging
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# BATCH PROCESSING
# =============================================================================


@dataclass
class BatchConfig:
    """Configuration for batch processing operations."""

    batch_size: int = 1000
    timeout_seconds: int = 30
    max_retries: int = 3


def batch_iterator(items: list[Any], batch_size: int = 100) -> Generator[list[Any]]:
    """
    Yield successive batches from a list.

    Args:
        items: List to batch
        batch_size: Size of each batch

    Yields:
        Batches of items

    Example:
        for batch in batch_iterator(large_list, batch_size=1000):
            process_batch(batch)
    """
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


async def async_batch_processor(
    items: list[Any], processor_func, batch_size: int = 100, max_concurrent: int = 3
):
    """
    Process items in batches with async support.

    Args:
        items: Items to process
        processor_func: Async function to process each batch
        batch_size: Size of each batch
        max_concurrent: Maximum concurrent batches

    Returns:
        List of results
    """
    import asyncio

    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(batch):
        async with semaphore:
            return await processor_func(batch)

    tasks = []
    for batch in batch_iterator(items, batch_size):
        task = process_with_semaphore(batch)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return [item for batch in results for item in batch]


# =============================================================================
# QUERY OPTIMIZATION
# =============================================================================


class QueryCache:
    """
    Simple query result cache with TTL and size limits.

    For production use with millions of queries, use Redis or Memcached.
    This is useful for development and small-scale deployments.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: dict[str, tuple[Any, float]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        """Get cached result if not expired."""
        if key not in self.cache:
            self.misses += 1
            return None

        value, timestamp = self.cache[key]

        # Check TTL
        if datetime.now().timestamp() - timestamp > self.default_ttl:
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return value

    def set(self, key: str, value: Any) -> None:
        """Cache a query result."""
        # Remove oldest entry if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (value, datetime.now().timestamp())

    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate(),
            "max_size": self.max_size,
        }


# =============================================================================
# MEMORY EFFICIENCY
# =============================================================================


class StreamingProcessor:
    """
    Process large datasets without loading entire dataset into memory.

    Useful for processing market data, signals, and analysis results.
    """

    @staticmethod
    def process_large_file(file_path: str, processor_func, batch_size: int = 1000):
        """
        Process large file line by line in batches.

        Args:
            file_path: Path to file
            processor_func: Function to process each batch
            batch_size: Batch size for processing
        """
        batch = []

        with open(file_path) as f:
            for line in f:
                batch.append(line.strip())

                if len(batch) >= batch_size:
                    processor_func(batch)
                    batch = []

            # Process remaining items
            if batch:
                processor_func(batch)

    @staticmethod
    def chunked_processing(data: list[Any], chunk_size: int = 1000) -> Generator[list[Any]]:
        """
        Yield chunks of data for streaming processing.

        Args:
            data: Input data
            chunk_size: Size of each chunk

        Yields:
            Chunks of data
        """
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]


# =============================================================================
# INDEXING & DEDUPLICATION
# =============================================================================


class DeduplicationIndex:
    """
    Track and deduplicate data efficiently using a hash-based index.

    Useful for avoiding duplicate signals, trades, or market data ingestion.
    """

    def __init__(self, max_size: int = 100000):
        self.seen: set = set()
        self.max_size = max_size

    def add_and_check(self, item_hash: str) -> bool:
        """
        Check if item is duplicate and add to index.

        Args:
            item_hash: Hash of item to track

        Returns:
            True if item is new, False if duplicate
        """
        if item_hash in self.seen:
            return False

        # Prevent unbounded growth
        if len(self.seen) < self.max_size:
            self.seen.add(item_hash)

        return True

    def is_duplicate(self, item_hash: str) -> bool:
        """Check if item has been seen before."""
        return item_hash in self.seen

    def clear(self) -> None:
        """Clear all tracked items."""
        self.seen.clear()


# =============================================================================
# DATABASE QUERY PATTERNS
# =============================================================================


class OptimizedQueries:
    """
    Collection of optimized query patterns for common operations.

    These patterns reduce database round-trips and improve performance.
    """

    @staticmethod
    def bulk_insert_pattern(items: list[dict[str, Any]]) -> str:
        """
        Generate optimized bulk insert query.

        Instead of:
            INSERT INTO table VALUES (...)
            INSERT INTO table VALUES (...)
            INSERT INTO table VALUES (...)

        Use:
            INSERT INTO table VALUES (...), (...), (...)

        Args:
            items: List of dictionaries to insert

        Returns:
            Optimized insert query
        """
        if not items:
            return ""

        keys = list(items[0].keys())
        values_list = [f"({', '.join(str(item.get(k, 'NULL')) for k in keys)})" for item in items]

        return f"INSERT INTO table ({', '.join(keys)}) VALUES {', '.join(values_list)}"

    @staticmethod
    def batch_update_pattern(updates: list[dict[str, Any]]) -> str:
        """
        Generate optimized batch update query using CASE.

        Args:
            updates: List of update dictionaries with 'id' and other fields

        Returns:
            Optimized update query
        """
        if not updates:
            return ""

        ids = [str(u["id"]) for u in updates]
        return f"UPDATE table WHERE id IN ({', '.join(ids)})"


# =============================================================================
# MONITORING & STATISTICS
# =============================================================================


class OperationStats:
    """Track and report statistics for data operations."""

    def __init__(self):
        self.operations: dict[str, dict[str, Any]] = {}

    def record_operation(
        self,
        operation_name: str,
        duration_ms: float,
        item_count: int,
        status: str = "success",
    ):
        """Record metrics for an operation."""
        if operation_name not in self.operations:
            self.operations[operation_name] = {
                "count": 0,
                "total_duration": 0,
                "total_items": 0,
                "errors": 0,
            }

        stats = self.operations[operation_name]
        stats["count"] += 1
        stats["total_duration"] += duration_ms
        stats["total_items"] += item_count

        if status != "success":
            stats["errors"] += 1

    def get_stats(self, operation_name: str) -> dict[str, float]:
        """Get statistics for an operation."""
        if operation_name not in self.operations:
            return {}

        stats = self.operations[operation_name]
        return {
            "count": stats["count"],
            "avg_duration_ms": stats["total_duration"] / stats["count"],
            "total_items": stats["total_items"],
            "items_per_second": (
                (stats["total_items"] / stats["total_duration"]) * 1000
                if stats["total_duration"] > 0
                else 0
            ),
            "error_rate": stats["errors"] / stats["count"] if stats["count"] > 0 else 0,
        }

    def print_report(self):
        """Print performance report."""
        logger.info("=== Data Processing Performance Report ===")
        for op_name in self.operations:
            stats = self.get_stats(op_name)
            logger.info(f"\n{op_name}:")
            logger.info(f"  Count: {stats.get('count', 0)}")
            logger.info(f"  Avg Duration: {stats.get('avg_duration_ms', 0):.2f}ms")
            logger.info(f"  Items/second: {stats.get('items_per_second', 0):.2f}")
            logger.info(f"  Error Rate: {stats.get('error_rate', 0):.2%}")
