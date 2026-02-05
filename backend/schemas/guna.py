from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any

class GunaVector(BaseModel):
    """
    Represents the Guna composition of a data point or system state.
    Each component (Sattva, Rajas, Tamas) sums to 1.0 (or is normalized).
    """
    sattva: float = Field(ge=0.0, le=1.0, description="Clarity, harmony, balance")
    rajas: float = Field(ge=0.0, le=1.0, description="Activity, change, passion")
    tamas: float = Field(ge=0.0, le=1.0, description="Inertia, darkness, stability, resistance")

    def __post_init__(self):
        # Ensure the sum is approximately 1.0
        total = self.sattva + self.rajas + self.tamas
        if not (0.99 <= total <= 1.01): # Allow for float precision errors
            # Normalize if sum is not 1.0
            factor = 1.0 / total
            self.sattva *= factor
            self.rajas *= factor
            self.tamas *= factor

    def to_dict(self) -> Dict[str, float]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GunaVector':
        return cls(**data)
