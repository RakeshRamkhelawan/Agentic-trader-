from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.backtesting.exchange import SimulatedExchange
from backend.backtesting.position_sizing import PositionSizer, FixedQuantitySizer
from backend.backtesting.fill_models import FillModel, FullFillModel
from backend.backtesting.slippage_models import SlippageModel, FixedSlippageModel

class Strategy(ABC):
    """
    Base class for trading strategies.
    Supports advanced position sizing, slippage models, and fill models.
    """
    
    def __init__(self, exchange: SimulatedExchange,
                 position_sizer: Optional[PositionSizer] = None,
                 slippage_model: Optional[SlippageModel] = None,
                 fill_model: Optional[FillModel] = None):
        self.exchange = exchange
        self.position_sizer = position_sizer or FixedQuantitySizer(base_quantity=1.0)
        self.slippage_model = slippage_model or FixedSlippageModel(basis_points=5.0)
        self.fill_model = fill_model or FullFillModel()
        self.portfolio_value = exchange.initial_cash if hasattr(exchange, 'initial_cash') else 10000.0
    
    def calculate_position_size(self, price: float, signal_strength: float = 1.0, 
                               risk_per_trade: float = 0.01) -> float:
        """
        Calculate position size using the configured position sizer.
        
        Args:
            price: Current market price
            signal_strength: Signal strength (0.0-1.0+)
            risk_per_trade: Risk percentage per trade
            
        Returns:
            Quantity to trade
        """
        return self.position_sizer.calculate_quantity(
            signal_strength=signal_strength,
            price=price,
            portfolio_value=self.portfolio_value,
            risk_per_trade=risk_per_trade
        )
    
    def update_portfolio_value(self, new_value: float) -> None:
        """Update portfolio value (called after each bar or trade)."""
        self.portfolio_value = new_value
