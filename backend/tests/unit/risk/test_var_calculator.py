import pytest
import pandas as pd
import numpy as np
from backend.risk.var_calculator import VaRCalculator, VaRCalculationError

# --- FIXTURES ---

@pytest.fixture
def mock_portfolio_data():
    """Mock portfolio return data."""
    # Simuleer dagelijkse rendementen van een portfolio
    # 99 waarden die rond 0 liggen, en 1 extreme waarde
    returns = np.random.normal(0, 0.01, 99).tolist() # Normaal 1% rendement
    returns.append(-0.10) # 10% verliesdag
    return pd.Series(returns)

@pytest.fixture
def calculator():
    return VaRCalculator()

# --- TESTS ---

def test_calculate_var_95_percent_confidence(calculator, mock_portfolio_data):
    """Happy Path: Bereken VaR met 95% betrouwbaarheid."""
    var_95 = calculator.calculate_historical_var(mock_portfolio_data, confidence_level=0.95)
    
    # Met een 10% verliesdag in 100 dagen, zal 95% VaR ergens tussen 0% en -10% liggen
    # We checken of het negatief is (verlies)
    assert var_95 < 0
    assert var_95 >= -0.10  # Niet meer negatief dan het extreme geval

def test_calculate_var_99_percent_confidence(calculator, mock_portfolio_data):
    """Happy Path: Bereken VaR met 99% betrouwbaarheid."""
    var_99 = calculator.calculate_historical_var(mock_portfolio_data, confidence_level=0.99)
    
    # Met 100 datapoints, zal 99% VaR veel negatiever zijn dan 95%
    assert var_99 < 0

def test_insufficient_data_for_var(calculator):
    """Unhappy Path: Zeer kleine dataset voor VaR berekening."""
    small_data = pd.Series([0.01, -0.02, 0.005])
    
    # De calculator werkt nog met kleine data, geeft alleen een waarschuwing
    var = calculator.calculate_historical_var(small_data, confidence_level=0.95)
    assert var < 0  # Should still calculate something

def test_invalid_confidence_level(calculator, mock_portfolio_data):
    """Unhappy Path: Ongeldige betrouwbaarheidsniveau."""
    with pytest.raises(VaRCalculationError, match="Confidence level must be between 0 and 1"):
        calculator.calculate_historical_var(mock_portfolio_data, confidence_level=1.5)
