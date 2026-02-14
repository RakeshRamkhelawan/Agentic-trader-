import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.core.database import Base


class AgentExperience(Base):
    """
    Stores Reinforcement Learning 'Experience Tuples' (State, Action, Reward, Next State).
    Used for persistent Experience Replay and offline training.
    """

    __tablename__ = "agent_experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # State and Next State stored as JSON arrays or objects
    state_vector = Column(JSONB, nullable=False)
    next_state_vector = Column(JSONB, nullable=False)

    action = Column(Integer, nullable=False)  # or String depending on action space
    reward = Column(Float, nullable=False)
    done = Column(Boolean, default=False)

    # Extra metadata (e.g., model version, specific pattern capabilities detected)
    meta_info = Column(JSONB, nullable=True)
