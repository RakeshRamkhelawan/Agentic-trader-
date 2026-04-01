"""
Test configuration for wiring integration tests with SQLite fallback.
"""

import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

# Set test environment variables BEFORE importing backend
os.environ["JWT_SECRET_KEY"] = (
    "test-secret-key-for-integration-tests-12345-minimum-32-chars"
)
os.environ["AUTH_DISABLED"] = "true"
os.environ["ENV"] = "test"

# Use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["POSTGRES_USER"] = "test"
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["POSTGRES_DB"] = "test"

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
async def async_client() -> AsyncClient:
    """Async HTTPX client for FastAPI app with SQLite database."""
    # Import inside fixture to avoid circular imports
    from backend.api.main import app
    from backend.core.database import Base

    # Create SQLite engine for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Patch the app's session
    _ = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )  # noqa: F841

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await engine.dispose()


@pytest.fixture
def unique_email():
    """Generate unique email for tests."""
    from uuid import uuid4

    return f"test_user_{uuid4().hex[:8]}@example.com"
