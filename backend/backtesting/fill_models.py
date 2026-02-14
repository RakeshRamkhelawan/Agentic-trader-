"""
Fill Models for Backtesting Engine.

Provides realistic order fill simulation (full fills vs partial fills).
"""
from abc import ABC, abstractmethod


class FillModel(ABC):
    """Abstract base for fill models."""
    
    @abstractmethod
    def compute_fill(self, order_quantity: float, available_volume: float) -> tuple:
        """Compute filled vs unfilled quantity.
        
        Args:
            order_quantity: Total quantity requested
            available_volume: Available market volume at price level
            
        Returns:
            Tuple of (filled_quantity, unfilled_quantity)
        """
        pass


class FullFillModel(FillModel):
    """All or nothing fill model.
    
    Order either fills completely or not at all.
    Realistic for small orders or liquid markets.
    """
    
    def compute_fill(self, order_quantity: float, available_volume: float) -> tuple:
        """Compute full fill (all or nothing)."""
        if available_volume >= order_quantity:
            filled = order_quantity
            unfilled = 0.0
        else:
            filled = 0.0
            unfilled = order_quantity
        
        return filled, unfilled


class RealisticFillModel(FillModel):
    """Partial fill model based on participation rate.
    
    Fills up to a maximum participation rate of market volume.
    Typical for larger orders that can't fill immediately.
    """
    
    def __init__(self, max_participation_rate: float = 0.1):
        """Initialize realistic fill model.
        
        Args:
            max_participation_rate: Maximum % of bar volume to fill (default 10%)
        """
        self.max_participation_rate = max_participation_rate
    
    def compute_fill(self, order_quantity: float, available_volume: float) -> tuple:
        """Compute partial fill based on max participation."""
        max_fillable = available_volume * self.max_participation_rate
        filled = min(order_quantity, max_fillable)
        unfilled = order_quantity - filled
        
        return filled, unfilled


class ProportionalFillModel(FillModel):
    """Proportional fill model.
    
    Fills proportional to the ratio of order size to available volume.
    """
    
    def __init__(self, max_participation_rate: float = 0.5):
        """Initialize proportional fill model.
        
        Args:
            max_participation_rate: Maximum % of volume (default 50%)
        """
        self.max_participation_rate = max_participation_rate
    
    def compute_fill(self, order_quantity: float, available_volume: float) -> tuple:
        """Compute proportional fill."""
        if available_volume <= 0:
            return 0.0, order_quantity
        
        # Fill ratio = min(order_qty / available_vol, max_participation_rate)
        fill_ratio = min(order_quantity / available_volume, self.max_participation_rate)
        filled = order_quantity * fill_ratio
        unfilled = order_quantity - filled
        
        return filled, unfilled
