"""
Unit tests for Unit of Work pattern.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.unit_of_work import (
    PendingClickHouseOperation,
    UnitOfWork,
    UnitOfWorkError,
    create_unit_of_work,
)


@pytest.fixture
def mock_postgres_session():
    """Create a mock PostgreSQL session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_clickhouse_client():
    """Create a mock ClickHouse client."""
    client = AsyncMock()
    client.insert = AsyncMock()
    return client


@pytest.fixture
def unit_of_work(mock_postgres_session, mock_clickhouse_client):
    """Create a UnitOfWork instance with mocked dependencies."""
    return UnitOfWork(
        postgres_session=mock_postgres_session,
        clickhouse_client=mock_clickhouse_client,
        enable_clickhouse=True,
    )


class TestUnitOfWork:
    """Test cases for UnitOfWork."""

    @pytest.mark.asyncio
    async def test_successful_commit(
        self, unit_of_work, mock_postgres_session, mock_clickhouse_client
    ):
        """Test successful two-phase commit."""
        # Add a ClickHouse operation
        unit_of_work.add_clickhouse_operation("trades", {"symbol": "BTC-EUR", "price": 50000})

        # Commit
        async with unit_of_work:
            pass  # Context manager handles commit

        # Verify PostgreSQL commit was called
        mock_postgres_session.commit.assert_called_once()

        # Verify ClickHouse insert was called
        mock_clickhouse_client.insert.assert_called_once()

        # Verify state
        assert unit_of_work.is_committed is True

    @pytest.mark.asyncio
    async def test_rollback_on_exception(
        self, unit_of_work, mock_postgres_session, mock_clickhouse_client
    ):
        """Test rollback when exception occurs."""
        with pytest.raises(ValueError):
            async with unit_of_work:
                unit_of_work.add_clickhouse_operation("trades", {"symbol": "BTC-EUR"})
                raise ValueError("Test error")

        # Verify PostgreSQL rollback was called
        mock_postgres_session.rollback.assert_called_once()

        # Verify ClickHouse insert was NOT called
        mock_clickhouse_client.insert.assert_not_called()

        # Verify buffer was cleared
        assert len(unit_of_work._clickhouse_buffer) == 0

    @pytest.mark.asyncio
    async def test_clickhouse_disabled(self, mock_postgres_session, mock_clickhouse_client):
        """Test that ClickHouse operations are skipped when disabled."""
        uow = UnitOfWork(
            postgres_session=mock_postgres_session,
            clickhouse_client=mock_clickhouse_client,
            enable_clickhouse=False,
        )

        async with uow:
            uow.add_clickhouse_operation("trades", {"symbol": "BTC-EUR"})

        # PostgreSQL should still commit
        mock_postgres_session.commit.assert_called_once()

        # But ClickHouse should not be called
        mock_clickhouse_client.insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_clickhouse_operations(
        self, unit_of_work, mock_postgres_session, mock_clickhouse_client
    ):
        """Test multiple ClickHouse operations in one transaction."""
        async with unit_of_work:
            uow = unit_of_work  # Reference for clarity
            uow.add_clickhouse_operation("trades", {"id": 1})
            uow.add_clickhouse_operation("trades", {"id": 2})
            uow.add_clickhouse_operation("orders", {"id": 3})

        # Verify all operations were executed
        assert mock_clickhouse_client.insert.call_count == 3

    @pytest.mark.asyncio
    async def test_postgres_access(self, unit_of_work, mock_postgres_session):
        """Test access to PostgreSQL session."""
        # Add entity through postgres session
        mock_entity = MagicMock()

        async with unit_of_work:
            unit_of_work.postgres.add(mock_entity)

        # Verify entity was added to session
        mock_postgres_session.add.assert_called_once_with(mock_entity)

    @pytest.mark.asyncio
    async def test_compensation_on_clickhouse_failure(self, mock_postgres_session):
        """Test compensation execution when ClickHouse fails."""
        # Create client that fails on second insert
        failing_client = AsyncMock()
        failing_client.insert = AsyncMock(side_effect=[None, Exception("CH Error")])

        uow = UnitOfWork(
            postgres_session=mock_postgres_session,
            clickhouse_client=failing_client,
            enable_clickhouse=True,
        )

        # Register compensation
        compensation_mock = AsyncMock()
        uow.register_compensation(compensation_mock)

        async with uow:
            uow.add_clickhouse_operation("trades", {"id": 1})
            uow.add_clickhouse_operation("trades", {"id": 2})  # This will fail

        # PostgreSQL should still commit (eventual consistency)
        mock_postgres_session.commit.assert_called_once()

        # Compensation should be called
        compensation_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_double_commit_raises_error(self, unit_of_work):
        """Test that double commit raises error."""
        async with unit_of_work:
            pass

        # Second commit should raise
        with pytest.raises(UnitOfWorkError, match="already finalized"):
            await unit_of_work.commit()

    @pytest.mark.asyncio
    async def test_factory_context_manager(self, mock_postgres_session, mock_clickhouse_client):
        """Test the factory context manager."""
        async with create_unit_of_work(mock_postgres_session, mock_clickhouse_client) as uow:
            uow.add_clickhouse_operation("trades", {"symbol": "BTC-EUR"})

        mock_postgres_session.commit.assert_called_once()
        mock_clickhouse_client.insert.assert_called_once()


class TestPendingClickHouseOperation:
    """Test cases for PendingClickHouseOperation."""

    def test_creation(self):
        """Test creation of pending operation."""
        op = PendingClickHouseOperation(
            table="trades", data={"symbol": "BTC-EUR", "price": 50000}, operation="insert"
        )

        assert op.table == "trades"
        assert op.data == {"symbol": "BTC-EUR", "price": 50000}
        assert op.operation == "insert"

    def test_default_operation(self):
        """Test default operation is 'insert'."""
        op = PendingClickHouseOperation(table="trades", data={})
        assert op.operation == "insert"
