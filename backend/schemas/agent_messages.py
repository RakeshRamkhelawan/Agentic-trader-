import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AgentMessage:
    """Standardized Message for Inter-Agent Communication (IACP)."""

    source: str
    target: str
    type: str  # SIGNAL, BROADCAST, QUERY, RESPONSE, TIMER_TICK, DATA_STREAM
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    tenant_id: Optional[str] = None  # Added for multi-tenancy context propagation

    def __post_init__(self):
        valid_types = {
            "SIGNAL",
            "BROADCAST",
            "QUERY",
            "RESPONSE",
            "GUNA_SIGNAL",
            "NEWS_DATA",
            "TICK_DATA",
            "TIMER_TICK_1MIN",
            "TIMER_TICK_1HOUR",
            "ORDER_INTENT",
        }
        if self.type not in valid_types:
            raise ValueError(f"Invalid message type: {self.type}")

    def to_json(self) -> str:
        return json.dumps(self.__dict__)


class AgentProtocol:
    @staticmethod
    def parse(json_str: str) -> AgentMessage:
        data = json.loads(json_str)
        return AgentMessage(**data)
