
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ClickHouseWriter:
    """
    Async Batch Writer for ClickHouse.
    Collects events in a queue and flushes them in batches.
    """
    def __init__(self, client, table: str = "market_events", batch_size: int = 1000, flush_interval: float = 1.0):
        self.client = client
        self.table = table
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue: asyncio.Queue = asyncio.Queue()
        self._stopped = asyncio.Event()

    async def enqueue(self, row: Dict[str, Any]):
        """Add row to the processing queue."""
        await self.queue.put(row)

    async def run(self):
        """
        Main loop: consume queue, batch, and flush.
        """
        batch = []
        last_flush = time.time()
        
        while not self._stopped.is_set():
            try:
                # Calculate time until next mandatory flush
                now = time.time()
                time_since_flush = now - last_flush
                remaining = self.flush_interval - time_since_flush
                
                # If we are overdue or close, set timeout small
                wait_timeout = max(0.01, remaining)

                try:
                    # Wait for items with timeout
                    # We should also wake up if stopped.
                    # But Python asyncio.Queue doesn't support waking on Event easily in get().
                    # Solution: Use wait_for with small timeout if needed, or stick to short wakeups.
                    # Or use asyncio.wait([queue_get_task, stopped_task])
                    
                    # Simple approach: Wait for min(remaining, 0.1) to allow checking _stopped frequently?
                    # No, that's polling.
                    # Let's use wait_for(queue.get(), timeout=wait_timeout).
                    # If wait_timeout is large (10s), we block stop().
                    # We should cap the timeout to e.g. 1.0s to allow reasonable stop latency?
                    # Or just rely on .cancel() of the run task? 
                    # The test calls writer.stop() then awaits task.
                    # If I cancel the task, it works. But standard graceful stop usually involves flag.
                    
                    # Enhanced approach:
                    get_task = asyncio.create_task(self.queue.get())
                    stop_task = asyncio.create_task(self._stopped.wait())
                    
                    done, pending = await asyncio.wait(
                        [get_task, stop_task], 
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=wait_timeout
                    )
                    
                    if get_task in done:
                        item = get_task.result()
                        batch.append(item)
                        self.queue.task_done()
                    else:
                        # Timeout or Stopped
                        get_task.cancel() # Cancel the get if we didn't use it
                    
                    if stop_task in done:
                        # Stopped was set
                        break
                    else:
                        stop_task.cancel() # Cancel stop wait if we continue or got item
                        try:
                            await stop_task
                        except asyncio.CancelledError:
                            pass
                        
                except Exception as e:
                    # Ignore cancels on get_task
                    pass

                # Check Logic
                is_batch_full = len(batch) >= self.batch_size
                is_time_to_flush = (time.time() - last_flush) >= self.flush_interval
                
                if (batch and (is_batch_full or is_time_to_flush)):
                    await self._flush(batch)
                    batch = []
                    last_flush = time.time()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ClickHouseWriter loop: {e}")
                await asyncio.sleep(1) # Backoff on error
                
        # Flush remaining on stop
        # Drain queue first?
        while not self.queue.empty():
            try:
                batch.append(self.queue.get_nowait())
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        if batch:
            await self._flush(batch)

    async def _flush(self, batch: List[Dict[str, Any]]):
        """
        Insert batch into ClickHouse.
        """
        if not batch:
            return
            
        # Transform batch for ClickHouse (Split bids/asks into arrays)
        # UnifiedMarketEvent.to_dict() gives 'bids': [(px, sz), ...], 'asks': ...
        # ClickHouse table expects 'bids_price': [], 'bids_size': []
        
        transformed_batch = []
        for item in batch:
            # Shallow copy to avoid mutating original if used elsewhere
            row = item.copy()
            
            bids = row.pop('bids', []) or []
            asks = row.pop('asks', []) or []
            
            # Unzip bids
            if bids:
                # list(zip(*bids)) -> [(p1, p2), (s1, s2)]
                unzipped_bids = list(zip(*bids))
                row['bids_price'] = list(unzipped_bids[0])
                row['bids_size'] = list(unzipped_bids[1])
            else:
                row['bids_price'] = []
                row['bids_size'] = []
                
            # Unzip asks
            if asks:
                unzipped_asks = list(zip(*asks))
                row['asks_price'] = list(unzipped_asks[0])
                row['asks_size'] = list(unzipped_asks[1])
            else:
                row['asks_price'] = []
                row['asks_size'] = []
            
            # Remove checksum if present (not in schema)
            row.pop('checksum', None)
            
            # Convert timestamps to datetime objects if they are floats/ints
            # ClickHouse connect prefers datetime for DateTime64
            # We need to import datetime from datetime
            from datetime import datetime
            
            if isinstance(row.get('ts_exchange'), (int, float)):
                 row['ts_exchange'] = datetime.fromtimestamp(row['ts_exchange'])
                 
            if isinstance(row.get('ts_received'), (int, float)):
                 row['ts_received'] = datetime.fromtimestamp(row['ts_received'])

            transformed_batch.append(row)

        if not transformed_batch:
            return

        try:
            # Extract column names from first row to ensure consistency
            first_row = transformed_batch[0]
            column_names = list(first_row.keys())
            
            # Convert dicts to list of lists, ensuring order matches column_names
            data = [[row.get(col) for col in column_names] for row in transformed_batch]
            
            self.client.insert(self.table, data, column_names=column_names)
        except Exception as e:
            logger.error(f"Failed to flush batch to ClickHouse: {type(e).__name__} {repr(e)}")
            raise e

    def stop(self):
        """Signal to stop."""
        self._stopped.set()
