import pandas as pd
import numpy as np
import logging
from typing import Union

class VaRCalculationError(Exception):
    """Custom exception for VaR calculation errors."""
    pass

class VaRCalculator:
    """
    Berekent Value at Risk (VaR) van een portfolio met behulp van historische simulatie.
    """
    def __init__(self):
        self.logger = logging.getLogger("VaRCalculator")

    def calculate_historical_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """
        Berekent Historical VaR van een reeks rendementen.
        
        Args:
            returns: Een Pandas Series van dagelijkse (of periodieke) rendementen.
            confidence_level: De betrouwbaarheidsniveau (bijv. 0.95 voor 95% VaR).
            
        Returns:
            De berekende VaR als een negatief getal (verliespercentage).
            
        Raises:
            VaRCalculationError: Als de input ongeldig is.
        """
        if not isinstance(returns, pd.Series):
            raise VaRCalculationError("Input 'returns' must be a Pandas Series.")
        if not 0 < confidence_level < 1:
            raise VaRCalculationError("Confidence level must be between 0 and 1 (exclusive).")
        if len(returns) < 100: # Minimaal 100 observaties aanbevolen
            self.logger.warning(f"Insufficient data ({len(returns)} points) for robust VaR calculation. At least 100 recommended.")
            # raise VaRCalculationError("Insufficient data for VaR calculation.") # Hard error for now, can be warning later
            
        # Sorteer de rendementen van laag naar hoog
        sorted_returns = returns.sort_values(ascending=True)
        
        # Bepaal de index voor het gewenste percentiel
        # Bij 95% betrouwbaarheid, zoeken we naar het 5e percentiel (1 - 0.95)
        var_index = int(np.floor(len(returns) * (1 - confidence_level)))
        
        if var_index < 0 or var_index >= len(returns):
            raise VaRCalculationError("Calculated VaR index out of bounds, likely due to insufficient data or extreme confidence level.")
            
        # De VaR is het rendement op die index
        var = sorted_returns.iloc[var_index]
        
        self.logger.info(f"Calculated VaR at {confidence_level*100}% confidence: {var:.4f}")
        
        return var
