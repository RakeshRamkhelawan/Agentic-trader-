"""
Performance optimization module for MCP Backtest Engine V18.

SaaS-friendly optimizations:
- Caching (Redis)
- Parallel processing (asyncio)
- Vectorization (NumPy)
- Incremental processing

NO GPU, NO Ray, NO heavy dependencies.
"""

from .batch_processor import BatchProcessor, VectorizedElementalCalculator
from .cache import BacktestCache, cached_market_data, cached_vedastro_calculation
from .distributed import ParallelProcessor, SimpleBacktestRunner, run_parallel
from .metrics import BacktestProfiler, PerformanceMetricsCollector
from .parallel_engine import ParallelBacktestEngine, SymbolPartitioner
from .ultra_mode import IncrementalBacktest, UltraPerformanceMode, get_ultra_mode

__all__ = [
    # Core
    "BacktestCache",
    "cached_vedastro_calculation",
    "cached_market_data",
    "BatchProcessor",
    "VectorizedElementalCalculator",
    "ParallelBacktestEngine",
    "SymbolPartitioner",
    "PerformanceMetricsCollector",
    "BacktestProfiler",
    # Ultra mode (SaaS friendly)
    "UltraPerformanceMode",
    "IncrementalBacktest",
    "get_ultra_mode",
    # Parallel processing (asyncio-based)
    "ParallelProcessor",
    "SimpleBacktestRunner",
    "run_parallel",
]
