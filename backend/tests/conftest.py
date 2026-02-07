"""
Test configuration for integration tests.
Adds project root to Python path to allow 'backend' module imports.
"""
import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

# Add project root (two levels up from this file) to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
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

# ============================================================================
# SHARED DATABASE FIXTURES
# ============================================================================
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import backend.core.database
from backend.core.database import SessionManager
from uuid import uuid4

@pytest.fixture(scope="function", autouse=True)
async def patch_database_engine():
    # Use the same URL as the app uses
    db_url = backend.core.database.DATABASE_URL
    # Ensure it's using asyncpg
    if "postgresql://" in db_url and "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        
    engine = create_async_engine(db_url, echo=False)
    TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
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
