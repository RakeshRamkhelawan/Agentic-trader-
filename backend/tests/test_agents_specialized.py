"""
Aggregated Test Suite for Specialized Agents.

This suite consolidates validation for the entire "Trading Firm" layer:
- DataScout: Observation
- Analyst: Orientation
- RiskManager: Constraints
- Trader: Decision
- FundManager: Allocation
- Researchers: Thesis Generation
"""

import pytest

from backend.tests.test_analyst_agent import TestAnalystAgent

# Import test classes from individual files
# Pytest will discover and run these classes
from backend.tests.test_data_scout_agent import TestDataScoutAgent
from backend.tests.test_fund_manager_agent import (
    TestHalfKellySafety,
    TestKellyCriterion,
    TestPositionSizing,
)
from backend.tests.test_researcher_agents import (
    TestBearResearcher,
    TestBullResearcher,
    TestConrarianDivergence,
)
from backend.tests.test_risk_manager_agent import TestRiskManagerAgent
from backend.tests.test_trader_agent import TestTraderAgent
