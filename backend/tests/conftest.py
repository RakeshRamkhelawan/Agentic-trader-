"""
Test configuration for integration tests.
Adds project root to Python path to allow 'backend' module imports.
"""

import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

# Add project root (two levels up from this file) to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Verify backend module is importable
try:
    import backend

    print(f"[OK] Successfully imported backend module from {backend.__file__}")
except ImportError as e:
    print(f"[FAIL] Failed to import backend module: {e}")
    print(f"  Python path: {sys.path}")


@pytest.fixture
async def async_client() -> AsyncClient:
    """Async HTTPX client for FastAPI app with auto lifespan."""
    # Import inside fixture to avoid circular imports during collection
    from backend.api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


from uuid import uuid4

# ============================================================================
# SHARED DATABASE FIXTURES
# ============================================================================
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import backend.core.database
from backend.core.database import SessionManager


@pytest.fixture(scope="function", autouse=True)
async def patch_database_engine():
    # Use the same URL as the app uses
    db_url = backend.core.database.DATABASE_URL
    # Ensure it's using asyncpg
    if "postgresql://" in db_url and "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    TestingSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Patch
    original = backend.core.database.AsyncSessionLocal
    backend.core.database.AsyncSessionLocal = TestingSessionLocal

    yield

    # Restore
    backend.core.database.AsyncSessionLocal = original
    await engine.dispose()


@pytest.fixture
async def system_db():
    async with SessionManager.system_admin_session() as session:
        yield session


@pytest.fixture
def unique_email():
    return f"test_user_{uuid4().hex[:8]}@example.com"


# ============================================================================
# SHARED AGENT FIXTURES
# ============================================================================
from backend.core.schemas.ooda_types import (MarketRegime, Observation,
                                             Orientation, TradeProposal)


@pytest.fixture
def sample_observation():
    """Sample observation for tests."""
    return Observation(
        symbol="BTC/USDT",
        price=50000.0,
        volume=100.5,
        orderbook={
            "bids": [[49999, 10.0], [49998, 5.0]],
            "asks": [[50001, 8.0], [50002, 3.0]],
        },
        funding_rate=0.0001,
        social_sentiment=0.5,
    )


@pytest.fixture
def bullish_orientation():
    """Bullish orientation fixture."""
    return Orientation(
        symbol="BTC/USDT",
        regime=MarketRegime.TRENDING_UP,
        indicators={"rsi": 65.0, "macd": 100.0},
        core_sentiment=0.8,
        rag_context=["Historical bull run pattern detected"],
        confidence=0.75,
    )


@pytest.fixture
def bearish_orientation():
    """Bearish orientation fixture."""
    return Orientation(
        symbol="BTC/USDT",
        regime=MarketRegime.TRENDING_DOWN,
        indicators={"rsi": 35.0, "macd": -50.0},
        core_sentiment=0.3,
        confidence=0.70,
    )


@pytest.fixture
def sample_proposal():
    """Sample trade proposal."""
    return TradeProposal(
        symbol="BTC/USDT",
        side="buy",
        size=0.5,
        entry_price=50000.0,
        leverage=2.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        rationale="Bullish momentum",
        strategy_id="momentum_v1",
        confidence=0.75,
    )


from unittest.mock import AsyncMock, Mock

from backend.agents.fund_manager_agent import FundManagerAgent
from backend.core.schemas.ooda_types import (PortfolioState, RiskAssessment,
                                             RiskDecision)


@pytest.fixture
def mock_data_source():
    """Mock data source."""
    source = Mock()
    source.fetch_ticker = AsyncMock(
        return_value={
            "last": 50000.0,
            "volume": 100.5,
            "bid": 49999.0,
            "ask": 50001.0,
            "timestamp": 1234567890.0,
        }
    )
    source.fetch_orderbook = AsyncMock(
        return_value={
            "bids": [[49999, 10.0], [49998, 5.0]],
            "asks": [[50001, 8.0], [50002, 3.0]],
        }
    )
    source.fetch_funding_rate = AsyncMock(return_value=0.0001)
    return source


@pytest.fixture
def mock_event_bus():
    """Mock event bus."""
    bus = Mock()
    bus.publish = AsyncMock(return_value="msg-id-123")
    return bus


@pytest.fixture
def fund_manager():
    """Create FundManager instance."""
    return FundManagerAgent(
        max_position_pct=0.10, max_total_exposure=0.90, kelly_multiplier=0.5
    )


@pytest.fixture
def sample_portfolio():
    """Sample portfolio state."""
    return PortfolioState(
        total_equity=10000.0,
        available_capital=5000.0,
        total_exposure_pct=0.50,
        num_open_positions=2,
    )


@pytest.fixture
def sample_risk_assessment():
    """Sample risk assessment."""
    return RiskAssessment(
        trade_id="test-trade-001",
        decision=RiskDecision.APPROVE,
        rationale="Low risk trade with strong risk/reward ratio",
        risk_score=0.3,
        win_probability=0.6,
    )


from backend.agents.researcher_agents import BearResearcher, BullResearcher


@pytest.fixture
def bull_researcher():
    """Create BullResearcher instance."""
    return BullResearcher()


@pytest.fixture
def bear_researcher():
    """Create BearResearcher instance."""
    return BearResearcher()
