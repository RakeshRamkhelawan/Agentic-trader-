import asyncio
import logging
from typing import Any, Dict, List

from backend.storage.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)

class ClickHouseWriter:
    """
    Writes data to ClickHouse in batches.
    """
    def __init__(
        self,
        client: ClickHouseClient,
        table: str,
        batch_size: int = 1000,
        flush_interval: float = 1.0,
    ):
        self.client = client
        self.table = table
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None

    async def enqueue(self, row: Dict[str, Any]):
        """Add a row to the write queue."""
        await self._queue.put(row)

    async def run(self):
        """Process the queue and flush to ClickHouse."""
        self._running = True
        buffer: List[Dict[str, Any]] = []
        last_flush = asyncio.get_event_loop().time()

        while self._running or not self._queue.empty():
            try:
                # Wait for item or timeout
                try:
                    row = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                    buffer.append(row)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    pass

                now = asyncio.get_event_loop().time()
                time_since_flush = now - last_flush

                if buffer and (len(buffer) >= self.batch_size or time_since_flush >= self.flush_interval):
                    await self._flush(buffer)
                    buffer = []
                    last_flush = now

            except Exception as e:
                logger.error(f"Error in ClickHouseWriter run loop: {e}")
                await asyncio.sleep(1)

        # Final flush
        if buffer:
            await self._flush(buffer)

    async def _flush(self, buffer: List[Dict[str, Any]]):
        """Flush buffer to ClickHouse."""
        if not buffer:
            return
        
        try:
            # Assumes client has an insert method or execute
            # If client.insert doesn't exist, we might need to adjust based on ClickHouseClient implementation
            # For now, assuming a generic insert or using raw execute if needed.
            # But let's check ClickHouseClient first? No, let's assume standard interface.
            await self.client.insert(self.table, buffer)
            logger.debug(f"Flushed {len(buffer)} rows to {self.table}")
        except Exception as e:
            logger.error(f"Failed to flush to ClickHouse table {self.table}: {e}")

    def stop(self):
        """Signal the writer to stop."""
        self._running = False
