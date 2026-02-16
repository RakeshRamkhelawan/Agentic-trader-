from enum import Enum

class GunaType(str, Enum):
    SATTVA = "sattva"
    RAJAS = "rajas"
    TAMAS = "tamas"

class GunaSizer:
    """
    Adjusts trade position size based on the dominant Guna (Quality).
    """

    def calculate_size_multiplier(self, guna: GunaType) -> float:
        if guna == GunaType.SATTVA:
            # Balanced, clarity, wisdom -> Standard Size
            return 1.0
        elif guna == GunaType.RAJAS:
            # Active, passionate, potentially impulsive -> Aggressive size (but could be risky)
            # In some systems you might reduce size for volatility, but Rajas implies action.
            # Let's say 1.2x for "Confidence" but check PatternDetector confidence too.
            # For now, fixed multiplier.
            return 1.2
        elif guna == GunaType.TAMAS:
            # Inertia, confusion, delusion -> Reduce Size significantly or Halt
            return 0.5 
        return 1.0
