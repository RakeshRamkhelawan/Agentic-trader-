import json
from typing import Any, Awaitable, Callable, Dict, Optional

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None
    AIOKafkaConsumer = None

from backend.events.message_broker import MessageBroker


class KafkaBroker(MessageBroker):
    """
    Enterprise-grade Kafka/Redpanda Broker implementation.
    Uses AIOKafka for high-performance async I/O.
    """

    def __init__(self, bootstrap_servers: str = "localhost:6000"  # Zie PORT_ALLOCATION.md):
        if AIOKafkaProducer is None:
            raise ImportError("aiokafka not installed. Run: pip install aiokafka")

        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None

    async def connect(self):
        """Connect producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self.producer.start()

    async def disconnect(self):
        """Disconnect producer (and consumer if active)."""
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()

    async def publish(self, topic: str, key: str, payload: Dict[str, Any]):
        """Publish message with strict guarantees."""
        if not self.producer:
            raise RuntimeError("Producer not connected. Call connect() first.")

        # send_and_wait guarantees the broker acknowledged receipt (Durability)
        await self.producer.send_and_wait(topic, value=payload, key=key)

    async def subscribe(
        self,
        topic: str,
        group_id: str,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ):
        """
        Subscribe loop (runs forever).
        Note: This blocks the current task, so run it with asyncio.create_task()
        """
        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
        )

        await self.consumer.start()

        try:
            async for msg in self.consumer:
                await callback(msg.value)
        finally:
            await self.consumer.stop()
