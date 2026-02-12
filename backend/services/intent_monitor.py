import logging
from math import sqrt
from backend.schemas.guna import GunaVector
from backend.core.telemetry.metrics import PrometheusMetrics # NIEUW

# Initialiseer metrics voor deze service
metrics = PrometheusMetrics("intent_monitor") # NIEUW

class IntentMonitor:
    """
    De 'Purusha' laag van het systeem.
    Deze service monitort passief de Guna-balans van de manifeste Prakriti
    en logt afwijkingen van de ideale, gewenste staat (de 'intentie').
    Het initieert geen actie, maar reflecteert de 'waarheid' van de Guna-balans.
    """
    
    def __init__(self, ideal_balance: GunaVector):
        self.ideal_balance = ideal_balance
        self.logger = logging.getLogger("IntentMonitor")

    def measure_deviation(self, current_balance: GunaVector) -> float:
        """
        Meet de 'afstand' tussen de huidige en de ideale Guna-balans
        met behulp van Euclidische afstand (als een simpele metrick).
        """
        s_diff = current_balance.sattva - self.ideal_balance.sattva
        r_diff = current_balance.rajas - self.ideal_balance.rajas
        t_diff = current_balance.tamas - self.ideal_balance.tamas
        
        # Euclidische afstand in 3D Guna-ruimte
        deviation = sqrt(s_diff**2 + r_diff**2 + t_diff**2)
        return deviation

    def monitor_balance(self, current_balance: GunaVector):
        """
        Observeert de huidige Guna-balans en logt afwijkingen.
        """
        deviation = self.measure_deviation(current_balance)
        
        metrics.guna_deviation_score.set(deviation) # NIEUW: Update metric
        metrics.global_guna_sattva.set(current_balance.sattva) # NIEUW: Update metric
        metrics.global_guna_rajas.set(current_balance.rajas)
        metrics.global_guna_tamas.set(current_balance.tamas)
        
        if deviation > 0.05: # Arbitrary threshold for logging
            self.logger.warning(
                f"Deviation from ideal Guna balance detected. "
                f"Current: S={current_balance.sattva:.2f}, R={current_balance.rajas:.2f}, T={current_balance.tamas:.2f}. "
                f"Ideal: S={self.ideal_balance.sattva:.2f}, R={self.ideal_balance.rajas:.2f}, T={self.ideal_balance.tamas:.2f}. "
                f"Deviation Score: {deviation:.4f}"
            )
        else:
            self.logger.info(f"Guna balance within acceptable limits. Deviation: {deviation:.4f}")