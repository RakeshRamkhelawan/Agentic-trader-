from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ElementType(str, Enum):
    EARTH = "earth"  # Prithvi
    WATER = "water"  # Jala
    FIRE = "fire"    # Agni
    AIR = "air"      # Vayu
    ETHER = "ether"  # Akasha


class ElementalAgent(ABC):
    """
    Abstract base class for Elemental Agents (Mahabhutas).
    
    Each agent represents one of the 5 elements and manages a specific
    aspect of the trading system (Risk, Liquidity, Execution, Strategy, Context).
    """

    def __init__(self, name: str, element: ElementType):
        self.name = name
        self.element = element
        self.prana: float = 1.0  # Energy level (0.0 - 1.0)
        self.is_active: bool = True
        self.state: Dict[str, Any] = {}

    @abstractmethod
    def process_cycle(self, perception: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a market cycle.
        
        Args:
            perception: Current system perception (from SensoryProcessor)
            system_state: Current overall system state
            
        Returns:
            Dict containing agent's decision/output for this cycle.
        """
        pass

    def regenerate_prana(self, amount: float) -> None:
        """Recover energy (e.g., during rest periods or successful actions)."""
        self.prana = min(1.0, self.prana + amount)

    def expend_prana(self, amount: float) -> None:
        """Expend energy (e.g., during complex calculations or stress)."""
        self.prana = max(0.0, self.prana - amount)
        if self.prana < 0.1:
            self.is_active = False  # Exhaustion

    def wake_up(self) -> None:
        """Recover from exhaustion."""
        if self.prana > 0.2:
            self.is_active = True

    def get_parameters(self) -> Dict[str, Any]:
        """Return tunable parameters."""
        return self.state

    def update_parameters(self, params: Dict[str, Any]) -> None:
        """Update tunable parameters."""
        self.state.update(params)
