"""
Parallel Processing - Lightweight Asyncio-based.

NO Ray, NO clusters - just pure asyncio for SaaS deployment.

For 50-500 symbols, asyncio + NumPy is MORE than fast enough.
Ray/cupy is overkill and makes deployment a nightmare.
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""
    max_workers: int = 4  # Number of parallel tasks
    chunk_size: int = 10  # Symbols per chunk
    timeout_seconds: float = 30.0


class ParallelProcessor:
    """
    Lightweight parallel processor using asyncio.
    
    NO external dependencies - just Python standard library + asyncio.
    Perfect for SaaS: simple, fast, easy to deploy.
    """
    
    def __init__(self, config: Optional[ParallelConfig] = None, max_workers: int = 4):
        if config:
            self.config = config
        else:
            self.config = ParallelConfig(max_workers=max_workers)
        self._semaphore = asyncio.Semaphore(self.config.max_workers)
    
    async def process_symbols(
        self,
        symbols: List[str],
        process_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process multiple symbols in parallel using asyncio.
        
        Args:
            symbols: List of symbols to process
            process_func: Async function to call for each symbol
            *args, **kwargs: Additional arguments for process_func
            
        Returns:
            Dict mapping symbols to results
        """
        async def _process_one(symbol: str) -> tuple:
            async with self._semaphore:
                try:
                    result = await process_func(symbol, *args, **kwargs)
                    return symbol, result
                except Exception as e:
                    return symbol, {"error": str(e)}
        
        # Create tasks for all symbols
        tasks = [_process_one(s) for s in symbols]
        
        # Run all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        output = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            symbol, data = result
            output[symbol] = data
        
        return output
    
    def partition_symbols(self, symbols: List[str]) -> List[List[str]]:
        """Partition symbols into chunks for processing."""
        chunks = []
        for i in range(0, len(symbols), self.config.chunk_size):
            chunks.append(symbols[i:i + self.config.chunk_size])
        return chunks


class SimpleBacktestRunner:
    """
    Simple backtest runner using asyncio.
    
    No Ray, no distributed - just clean asyncio.
    """
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        self.config = config or ParallelConfig()
        self.processor = ParallelProcessor(config)
    
    async def run_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        backtest_func,
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Run backtest for multiple symbols in parallel.
        
        Args:
            symbols: List of symbols
            start_date: Start date
            end_date: End date
            backtest_func: Async function(symbol, start, end, capital) -> result
            initial_capital: Initial capital per symbol
            
        Returns:
            Combined backtest results
        """
        import time
        start_time = time.time()
        
        # Process all symbols in parallel
        capital_per_symbol = initial_capital / len(symbols)
        
        results = await self.processor.process_symbols(
            symbols,
            backtest_func,
            start_date,
            end_date,
            capital_per_symbol
        )
        
        # Aggregate results
        all_trades = []
        errors = []
        
        for symbol, result in results.items():
            if "error" in result:
                errors.append(f"{symbol}: {result['error']}")
            else:
                all_trades.extend(result.get("trades", []))
        
        total_time = time.time() - start_time
        
        return {
            "status": "completed",
            "symbols": symbols,
            "total_trades": len(all_trades),
            "trades": all_trades,
            "errors": errors,
            "performance": {
                "total_time_seconds": total_time,
                "symbols_per_second": len(symbols) / total_time if total_time > 0 else 0
            }
        }


# Convenience function for simple parallel processing
async def run_parallel(
    items: List[Any],
    process_func,
    max_workers: int = 4
) -> List[Any]:
    """
    Simple parallel processing using asyncio.
    
    Args:
        items: List of items to process
        process_func: Async function to apply to each item
        max_workers: Maximum concurrent tasks
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_workers)
    
    async def _process(item):
        async with semaphore:
            return await process_func(item)
    
    tasks = [_process(item) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=True)
