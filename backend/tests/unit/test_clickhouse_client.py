"""
Tests for ClickHouse Client.

TDD Test Suite - Write tests FIRST before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


pytestmark = pytest.mark.unit


def test_clickhouse_client_exists():
    """RED: ClickHouseClient class should exist."""
    from backend.storage.clickhouse_client import ClickHouseClient
    assert ClickHouseClient is not None


def test_clickhouse_client_init_with_url():
    """RED: ClickHouseClient should accept connection URL."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client'):
        client = ClickHouseClient(url="http://localhost:8123")
        assert client.url == "http://localhost:8123"


def test_clickhouse_client_init_with_database():
    """RED: ClickHouseClient should accept database name."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client'):
        client = ClickHouseClient(database="trading")
        assert client.database == "trading"


def test_clickhouse_client_default_database():
    """RED: ClickHouseClient should have default database."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client'):
        client = ClickHouseClient()
        assert client.database == "agentic_trading"


@pytest.mark.asyncio
async def test_clickhouse_client_connect():
    """RED: ClickHouseClient should have async connect method."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        
        assert client.client is not None
        mock_get_client.assert_called_once()


@pytest.mark.asyncio
async def test_clickhouse_client_disconnect():
    """RED: ClickHouseClient should cleanup on disconnect."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        await client.disconnect()
        
        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_clickhouse_execute_query():
    """RED: Should execute SQL queries."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_result = MagicMock()
        mock_result.result_rows = [[1, "test"]]
        
        mock_client = AsyncMock()
        mock_client.query = AsyncMock(return_value=mock_result)
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        result = await client.execute("SELECT 1, 'test'")
        
        assert result.result_rows == [[1, "test"]]
        # Verify query was called (with parameters kwarg)
        assert mock_client.query.called


@pytest.mark.asyncio
async def test_clickhouse_execute_with_parameters():
    """RED: Should support parameterized queries."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_result = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.query = AsyncMock(return_value=mock_result)
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        await client.execute("SELECT * FROM trades WHERE symbol = {symbol:String}", parameters={'symbol': 'BTC'})
        
        mock_client.query.assert_called_once()


@pytest.mark.asyncio
async def test_clickhouse_insert_data():
    """RED: Should insert data into table."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.insert = AsyncMock()
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        
        data = [
            {"timestamp": datetime.now(timezone.utc), "symbol": "BTC", "price": 50000.0}
        ]
        await client.insert("market_ticks", data)
        
        mock_client.insert.assert_called_once()


@pytest.mark.asyncio
async def test_clickhouse_create_table():
    """RED: Should create table with schema."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.command = AsyncMock()
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        
        schema = """
        CREATE TABLE IF NOT EXISTS test_table (
            timestamp DateTime64(3),
            value Float64
        ) ENGINE = MergeTree()
        ORDER BY timestamp
        """
        await client.create_table(schema)
        
        mock_client.command.assert_called_once()


@pytest.mark.asyncio
async def test_clickhouse_ping():
    """RED: Should check connection health."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        result = await client.ping()
        
        assert result is True
        mock_client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_clickhouse_handles_connection_error():
    """RED: Should handle connection errors gracefully."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_get_client.side_effect = Exception("Connection refused")
        
        client = ClickHouseClient()
        
        with pytest.raises(Exception) as exc_info:
            await client.connect()
        
        assert "Connection refused" in str(exc_info.value)


@pytest.mark.asyncio
async def test_clickhouse_handles_query_error():
    """RED: Should handle query errors gracefully."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.query = AsyncMock(side_effect=Exception("Syntax error"))
        mock_get_client.return_value = mock_client
        
        client = ClickHouseClient()
        await client.connect()
        
        with pytest.raises(Exception) as exc_info:
            await client.execute("INVALID SQL")
        
        assert "Syntax error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_clickhouse_context_manager():
    """RED: Should support async context manager."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        mock_get_client.return_value = mock_client
        
        async with ClickHouseClient() as client:
            assert client.client is not None
        
        mock_client.close.assert_called_once()


def test_clickhouse_from_env():
    """RED: Should read connection settings from environment."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch.dict('os.environ', {'CLICKHOUSE_HOST': 'custom-host', 'CLICKHOUSE_PORT': '9000'}):
        with patch('clickhouse_connect.get_async_client'):
            client = ClickHouseClient()
            assert client.host == 'custom-host' or 'custom-host' in client.url


@pytest.mark.asyncio
async def test_clickhouse_insert_injects_tenant_id():
    """RED: Should inject tenant_id during insert if context is set."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.insert = AsyncMock()
        mock_get_client.return_value = mock_client
        
        with patch('backend.storage.clickhouse_client.get_current_tenant_optional', return_value="tenant-123"):
            client = ClickHouseClient()
            await client.connect()
            
            data = [{"symbol": "BTC"}] # Missing tenant_id
            await client.insert("table", data)
            
            # Check if tenant_id was injected
            call_args = mock_client.insert.call_args
            assert call_args is not None
            # args[1] is data
            inserted_data = call_args[0][1]
            assert inserted_data[0]["tenant_id"] == "tenant-123"


@pytest.mark.asyncio
async def test_clickhouse_execute_injects_tenant_id_parameter():
    """RED: Should inject tenant_id parameter during execute if context is set."""
    from backend.storage.clickhouse_client import ClickHouseClient
    
    with patch('clickhouse_connect.get_async_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.query = AsyncMock()
        mock_get_client.return_value = mock_client
        
        with patch('backend.storage.clickhouse_client.get_current_tenant_optional', return_value="tenant-123"):
            client = ClickHouseClient()
            await client.connect()
            
            await client.execute("SELECT * FROM table WHERE tenant_id = {tenant_id:String}")
            
            # Check parameters
            mock_client.query.assert_called_with(
                "SELECT * FROM table WHERE tenant_id = {tenant_id:String}", 
                parameters={"tenant_id": "tenant-123"}
            )

