
import asyncio
import logging
from typing import List
from backend.market_data.interfaces import ExchangeProvider, DataNormalizer, EventSink
# Typings for sinks - using Protocol or just Duck Types if not strictly inheriting common base
# But we have EventSink interface. 
# RedisPublisher is EventSink.
# ClickHouseWriter is NOT EventSink (it has enqueue).
# Let's adjust typing.

logger = logging.getLogger(__name__)

class MarketDataPipeline:
    """
    Orchestrates data flow:
    Providers -> raw_queue -> Normalizer -> Sinks (Redis, ClickHouse)
    """
    def __init__(self, 
                 providers: List[ExchangeProvider] = None,
                 normalizer: DataNormalizer = None,
                 redis_publisher: EventSink = None,
                 clickhouse_writer = None): 
        self.providers = providers if providers else []
        self.normalizer = normalizer
        self.redis_publisher = redis_publisher
        self.clickhouse_writer = clickhouse_writer
        
        self.raw_queue: asyncio.Queue = asyncio.Queue()
        self._tasks: List[asyncio.Task] = []
        self._stopped = False

        # Assign raw_queue to providers if they exist
        for p in self.providers:
            p.out_queue = self.raw_queue

    def add_provider(self, provider: ExchangeProvider):
        """Add a provider to the pipeline."""
        provider.out_queue = self.raw_queue
        self.providers.append(provider)

    def set_normalizer(self, normalizer: DataNormalizer):
        """Set the data normalizer."""
        self.normalizer = normalizer

    def add_sink(self, sink):
        """
        Add a sink (RedisPublisher or ClickHouseWriter).
        Duck typing based on methods.
        """
        if hasattr(sink, 'publish'):
            self.redis_publisher = sink
        elif hasattr(sink, 'enqueue'):
            self.clickhouse_writer = sink
        else:
            logger.warning(f"Unknown sink type: {type(sink)}")

    async def start(self):
        """Start all components."""
        logger.info("Starting MarketDataPipeline...")
        self._stopped = False
        
        # 1. Start ClickHouse Writer
        if hasattr(self.clickhouse_writer, 'run'):
            self._tasks.append(asyncio.create_task(self.clickhouse_writer.run()))

        # 2. Start Normalization Loop
        self._tasks.append(asyncio.create_task(self._normalization_loop()))

        # 3. Start Providers
        for p in self.providers:
            self._tasks.append(asyncio.create_task(p.run_forever()))

    async def _normalization_loop(self):
        """Consume raw events, normalize, and distribute."""
        logger.info("Starting Normalization Loop...")
        while not self._stopped:
            try:
                # Get raw event
                # (venue, raw_dict)
                venue, raw_event = await self.raw_queue.get()
                
                try:
                    # Normalize
                    event = self.normalizer.normalize(venue, raw_event)
                    
                    # Publish to Redis (Fire and Forget? w/ await)
                    await self.redis_publisher.publish(event)
                    
                    # Persist to ClickHouse (Enqueue)
                    # Convert to dict for writer
                    # Writer expects dict compatible with schema
                    await self.clickhouse_writer.enqueue(event.to_dict())
                    
                except Exception as e:
                    logger.error(f"Error processing event from {venue}: {e}", exc_info=True)
                finally:
                    self.raw_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Critical error in normalization loop: {e}")
                await asyncio.sleep(1) # Backoff

    async def stop(self):
        """Stop all components."""
        logger.info("Stopping MarketDataPipeline...")
        self._stopped = True
        
        # Stop Providers
        for p in self.providers:
            p.stop()
        
        # Stop Writer
        if hasattr(self.clickhouse_writer, 'stop'):
            self.clickhouse_writer.stop()
            
        # Cancel tasks
        for t in self._tasks:
            t.cancel()
        
        # Wait for cancellation?
        # await asyncio.gather(*self._tasks, return_exceptions=True)
        # Or just let them die. 
        # ClickHouseWriter handles graceful exit on stop() if not cancelled instantly?
        # If we cancel the task, it might raise CancelledError.
        # ClickHouseWriter catches CancelledError and breaks.
