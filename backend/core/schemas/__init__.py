"""
Core schemas for the OODA-driven Multi-Agent Trading AGI.

This package contains type-safe Pydantic models that define the
data contracts between agents in the OODA loop.
"""

from .ooda_types import (
    MarketRegime,
    Observation,
    Orientation,
    TradeProposal,
    RiskAssessment,
    ExecutionPlan,
    ExecutionOutcome,
)

__all__ = [
    "MarketRegime",
    "Observation",
    "Orientation",
    "TradeProposal",
    "RiskAssessment",
    "ExecutionPlan",
    "ExecutionOutcome",
]
