from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Awaitable, Optional


class MessageBroker(ABC):
    """
    Abstract Base Class for Enterprise Message Brokers (Kafka/Redpanda).
    """

    @abstractmethod
    async def connect(self):
        """Establish connection to the broker."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection cleanly."""
        pass

    @abstractmethod
    async def publish(self, topic: str, key: str, payload: Dict[str, Any]):
        """
        Publish a message to a specific topic.

        Args:
            topic: The stream/topic name (e.g. 'market_data', 'orders').
            key: Partition key (e.g. symbol 'BTC-EUR') for ordering guarantees.
            payload: The data dictionary.
        """
        pass

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        group_id: str,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ):
        """
        Subscribe to a topic and process messages via a callback.

        Args:
            topic: The topic to listen to.
            group_id: Consumer group ID (for load balancing).
            callback: Async function to handle incoming messages.
        """
        pass
