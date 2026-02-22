"""
Performance optimization module for MCP Backtest Engine V18.

SaaS-friendly optimizations:
- Caching (Redis)
- Parallel processing (asyncio)
- Vectorization (NumPy)
- Incremental processing

NO GPU, NO Ray, NO heavy dependencies.
"""

from .cache import BacktestCache, cached_vedastro_calculation, cached_market_data
from .batch_processor import BatchProcessor, VectorizedElementalCalculator
from .parallel_engine import ParallelBacktestEngine, SymbolPartitioner
from .metrics import PerformanceMetricsCollector, BacktestProfiler
from .ultra_mode import UltraPerformanceMode, IncrementalBacktest, get_ultra_mode
from .distributed import ParallelProcessor, SimpleBacktestRunner, run_parallel

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
