import pytest

from backend.schemas.guna import GunaVector
from backend.services.intent_monitor import IntentMonitor

# --- CONFIG ---
IDEAL_GUNA_BALANCE = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3) # Gewenste balans

@pytest.fixture
def monitor():
    return IntentMonitor(ideal_balance=IDEAL_GUNA_BALANCE)

# --- TESTS ---

def test_measure_no_deviation(monitor):
    """Happy Path: Geen afwijking van ideale balans."""
    # Huidige balans is precies de ideale
    current_balance = GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)
    deviation_score = monitor.measure_deviation(current_balance)
    
    assert deviation_score == pytest.approx(0.0)

def test_measure_sattva_deviation(monitor):
    """Happy Path: Te veel Sattva (misschien te passief)."""
    current_balance = GunaVector(sattva=0.6, rajas=0.2, tamas=0.2) # Meer Sattva
    deviation_score = monitor.measure_deviation(current_balance)
    
    assert deviation_score > 0.0

def test_measure_rajas_deviation(monitor):
    """Happy Path: Te veel Rajas (misschien te agressief)."""
    current_balance = GunaVector(sattva=0.2, rajas=0.5, tamas=0.3) # Meer Rajas
    deviation_score = monitor.measure_deviation(current_balance)
    
    assert deviation_score > 0.0

def test_measure_tamas_deviation(monitor):
    """Happy Path: Te veel Tamas (misschien te inert)."""
    current_balance = GunaVector(sattva=0.2, rajas=0.2, tamas=0.6) # Meer Tamas
    deviation_score = monitor.measure_deviation(current_balance)
    
    assert deviation_score > 0.0

def test_monitor_logs_deviation(monitor, caplog):
    """Happy Path: Monitor logt afwijking."""
    import logging
    caplog.set_level(logging.INFO)
    
    current_balance = GunaVector(sattva=0.5, rajas=0.2, tamas=0.3)
    monitor.monitor_balance(current_balance)
    
    assert "Deviation from ideal Guna balance" in caplog.text
    assert "Deviation Score:" in caplog.text
