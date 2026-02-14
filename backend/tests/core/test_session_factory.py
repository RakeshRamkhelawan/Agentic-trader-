
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import the (yet to be created) SessionManager and context managers
# This import will fail initially, which is part of the Red phase
try:
    from backend.core.database import (SessionManager, system_admin_session,
                                       tenant_session)
except ImportError:
    SessionManager = None
    system_admin_session = None
    tenant_session = None

@pytest.mark.asyncio
async def test_session_manager_exists():
    """Test that SessionManager class exists."""
    assert SessionManager is not None, "SessionManager class should exist in backend.core.database"

@pytest.mark.asyncio
async def test_system_admin_session_sets_context():
    """Test that system_admin_session executes the correct SQL command."""
    if not system_admin_session:
        pytest.fail("system_admin_session not implemented")

    # Mock the Session object itself
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Mock the Context Manager behavior of AsyncSessionLocal()
    # When AsyncSessionLocal() is called, it returns a context manager usually
    # In database.py: async with AsyncSessionLocal() as session:
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None
    
    # We need to patch the AsyncSessionLocal in database.py
    with patch("backend.core.database.AsyncSessionLocal", return_value=mock_cm):
        async with system_admin_session() as session:
            assert session == mock_session
            
            # Verify that execute was called
            assert session.execute.called, "Execute was not called on session"
            
            # Verify the arguments passed to execute
            # backend.core.context checks: SELECT set_config('app.current_tenant', 'system_admin', false)
            call_args = session.execute.call_args
            assert call_args is not None
            
            # The first argument should be a TextClause
            sql_clause = call_args[0][0]
            # Use string matching as strict equality on TextClause is tricky
            assert "set_config" in str(sql_clause)
            assert "system_admin" in str(sql_clause)

@pytest.mark.asyncio
async def test_tenant_session_sets_context():
    """Test that tenant_session executes the correct SQL command with tenant_id."""
    if not tenant_session:
        pytest.fail("tenant_session not implemented")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.close = AsyncMock()
    
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None
    
    tenant_id = "tenant-123"
    
    with patch("backend.core.database.AsyncSessionLocal", return_value=mock_cm):
        async with tenant_session(tenant_id) as session:
            assert session == mock_session
            
            # Verify execute called
            assert session.execute.called
            
            call_args = session.execute.call_args
            sql_clause = call_args[0][0]
            
            # Verify parameterized logic from backend.core.context
            assert "set_config" in str(sql_clause)
            assert tenant_id in str(sql_clause)

            
