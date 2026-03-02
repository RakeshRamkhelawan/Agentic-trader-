"""
Advanced Risk Management module.

Features:
- Value at Risk (VaR) calculation
- Stress testing
- Drawdown monitoring
- Position sizing
- Risk validation
"""

from .drawdown_monitor import DrawdownMonitor, DrawdownStatus
from .kelly_criterion import KellyCriterion
from .position_sizer import IntegratedPositionSizer
from .risk_orchestrator import RiskOrchestrator
from .stress_tester import StressScenario, StressTester, StressTestResult, stress_tester
from .validators import RiskValidator, RiskViolationError
from .var_calculator import VaRCalculationError, VaRCalculator, VaRMethod, VaRResult, var_calculator
from .var_calculator_optimized import VaRCalculatorOptimized

__all__ = [
    # VaR
    "VaRCalculationError",
    "VaRCalculator",
    "VaRCalculatorOptimized",
    "VaRMethod",
    "VaRResult",
    "var_calculator",
    # Stress Testing
    "StressTester",
    "StressScenario",
    "StressTestResult",
    "stress_tester",
    # Drawdown
    "DrawdownMonitor",
    "DrawdownStatus",
    # Position Sizing
    "IntegratedPositionSizer",
    "KellyCriterion",
    # Validation
    "RiskValidator",
    "RiskViolationError",
    # Orchestration
    "RiskOrchestrator",
]
