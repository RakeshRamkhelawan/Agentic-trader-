"""
Kelly Position Sizing Strategy for optimal compounding.

Uses the fractional Kelly criterion to determine the optimal
capital allocation for a trade based on historical win rates
and win/loss ratios, capping maximum exposure to prevent ruin.
"""

class KellyPositionSizer:
    """
    Calculates the optimal position size allocation percentage.
    Formula: f* = (p * b - q) / b
    where:
    p = probability of winning
    q = probability of losing (1 - p)
    b = ratio of average win to average loss
    """
    
    def __init__(self, default_kelly_fraction: float = 0.25, max_position: float = 0.1):
        """
        Args:
            default_kelly_fraction: What fraction of the full Kelly to apply (e.g., 0.25 means Quarter-Kelly).
                                    A fraction < 1.0 reduces volatility and prevents ruin if stats are noisy.
            max_position: Maximum fraction of total account capital to commit to a single trade.
        """
        self.default_kelly_fraction = default_kelly_fraction
        self.max_position = max_position
        
    def calculate_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        kelly_fraction: float = None,
        max_position: float = None,
    ) -> float:
        """
        Calculate the ideal position size as a fraction of total portfolio equity.
        
        Args:
            win_rate: Historical or estimated probability of the trade winning (0.0 to 1.0)
            avg_win: The average absolute or relative profit from winning trades
            avg_loss: The average absolute or relative loss from losing trades (must be positive)
            kelly_fraction: Optional override for the fractional Kelly multiplier
            max_position: Optional override for the maximum position cap
            
        Returns:
            The fraction of the portfolio to allocate to this trade.
            Returns 0.0 if the calculated edge is negative or if average loss is 0.
        """
        fraction = kelly_fraction if kelly_fraction is not None else self.default_kelly_fraction
        cap = max_position if max_position is not None else self.max_position
        
        if avg_loss <= 0:
            # Cannot calculate risk-reward accurately if we expect no loss (divide by zero risk)
            return 0.0
            
        b = avg_win / avg_loss
        
        if b <= 0:
            return 0.0
            
        p = win_rate
        q = 1.0 - p
        
        # Kelly Formula
        kelly_pct = (p * b - q) / b
        
        # Apply Fractional Kelly constraint
        fractional_kelly = kelly_pct * fraction
        
        # We only take trades with a positive mathematical expectancy
        if fractional_kelly <= 0.0:
            return 0.0
            
        # Cap the position size at the risk limit
        return min(fractional_kelly, cap)
