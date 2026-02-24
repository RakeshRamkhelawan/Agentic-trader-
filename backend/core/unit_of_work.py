"""
Unit of Work Pattern for Cross-Database Transaction Consistency.

Ensures atomic operations across PostgreSQL (state) and ClickHouse (analytics).
Uses two-phase commit logic: PostgreSQL commits first, ClickHouse follows.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from backend.storage.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)

T = TypeVar("T")


class UnitOfWorkError(Exception):
    """Base exception for Unit of Work errors."""

    pass


class TransactionRollbackError(UnitOfWorkError):
    """Raised when transaction rollback fails."""

    pass


@dataclass
class PendingClickHouseOperation:
    """Represents a deferred ClickHouse operation."""

    table: str
    data: dict[str, Any]
    operation: str = "insert"  # insert, update, delete


class UnitOfWork:
    """
    Async Unit of Work for cross-database transactions.

    Guarantees:
    - PostgreSQL transactions are ACID compliant
    - ClickHouse writes only occur after PostgreSQL commit
    - Automatic rollback on PostgreSQL failure
    - Manual compensation for ClickHouse failures

    Usage:
        async with UnitOfWork(pg_session, ch_client) as uow:
            uow.postgres.add(entity)
            uow.clickhouse_buffer.append(PendingClickHouseOperation(...))
            # Commit happens automatically on exit if no exception
    """

    def __init__(
        self,
        postgres_session: AsyncSession,
        clickhouse_client: ClickHouseClient | None = None,
        enable_clickhouse: bool = True,
    ):
        self.postgres_session = postgres_session
        self.clickhouse_client = clickhouse_client
        self.enable_clickhouse = enable_clickhouse

        # Buffer for ClickHouse operations (deferred until PG commit)
        self._clickhouse_buffer: list[PendingClickHouseOperation] = []

        # Transaction state
        self._is_committed = False
        self._is_rolled_back = False
        self._postgres_committed = False

        # Compensation log for ClickHouse failures
        self._compensation_log: list[Callable] = []

    async def __aenter__(self) -> "UnitOfWork":
        """Enter context - transaction begins."""
        logger.debug("UnitOfWork: Beginning transaction")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit context - commit or rollback.

        Returns:
            True if exception was handled, False otherwise
        """
        if exc_type is not None:
            # Exception occurred - rollback
            logger.warning(f"UnitOfWork: Exception occurred ({exc_type.__name__}), rolling back")
            await self.rollback()
            return False  # Re-raise the exception
        else:
            # No exception - commit
            try:
                await self.commit()
                return True
            except Exception as e:
                logger.error(f"UnitOfWork: Commit failed: {e}")
                await self.rollback()
                raise

    def add_clickhouse_operation(
        self, table: str, data: dict[str, Any], operation: str = "insert"
    ) -> None:
        """
        Buffer a ClickHouse operation (deferred until PostgreSQL commit).

        Args:
            table: ClickHouse table name
            data: Data to write
            operation: Type of operation (insert/update/delete)
        """
        if not self.enable_clickhouse:
            logger.debug(f"ClickHouse disabled, skipping {operation} to {table}")
            return

        pending = PendingClickHouseOperation(table=table, data=data, operation=operation)
        self._clickhouse_buffer.append(pending)
        logger.debug(f"Buffered {operation} operation for {table}")

    def register_compensation(self, compensation_fn: Callable) -> None:
        """
        Register a compensation function to run if ClickHouse fails.

        Args:
            compensation_fn: Async callable to compensate for failure
        """
        self._compensation_log.append(compensation_fn)

    async def commit(self) -> None:
        """
        Two-phase commit:
        1. Commit PostgreSQL
        2. If successful, flush ClickHouse buffer
        3. If ClickHouse fails, run compensations
        """
        if self._is_committed or self._is_rolled_back:
            raise UnitOfWorkError("Transaction already finalized")

        try:
            # Phase 1: Commit PostgreSQL
            logger.debug("UnitOfWork: Committing PostgreSQL")
            await self.postgres_session.commit()
            self._postgres_committed = True

            # Phase 2: Flush ClickHouse buffer (only if PG succeeded)
            if self.enable_clickhouse and self.clickhouse_client:
                await self._flush_clickhouse_buffer()

            self._is_committed = True
            logger.info("UnitOfWork: Transaction committed successfully")

        except Exception as e:
            logger.error(f"UnitOfWork: Commit failed: {e}")
            # PostgreSQL rollback happens in __aexit__
            raise UnitOfWorkError(f"Transaction commit failed: {e}") from e

    async def rollback(self) -> None:
        """
        Rollback PostgreSQL transaction.
        Clear ClickHouse buffer (no writes occurred).
        """
        if self._is_rolled_back:
            return

        try:
            logger.debug("UnitOfWork: Rolling back PostgreSQL")
            await self.postgres_session.rollback()
            self._is_rolled_back = True

            # Clear ClickHouse buffer (never write on rollback)
            buffer_size = len(self._clickhouse_buffer)
            self._clickhouse_buffer.clear()

            logger.info(f"UnitOfWork: Rollback complete (cleared {buffer_size} CH operations)")

        except Exception as e:
            logger.error(f"UnitOfWork: Rollback failed: {e}")
            raise TransactionRollbackError(f"Rollback failed: {e}") from e

    async def _flush_clickhouse_buffer(self) -> None:
        """
        Flush buffered ClickHouse operations.
        If any fail, run compensations for already-completed operations.
        """
        if not self._clickhouse_buffer:
            return

        completed_operations = []
        failed_operations = []

        for operation in self._clickhouse_buffer:
            try:
                await self._execute_clickhouse_operation(operation)
                completed_operations.append(operation)
            except Exception as e:
                logger.error(f"ClickHouse operation failed for {operation.table}: {e}")
                failed_operations.append((operation, e))
                break  # Stop on first failure

        if failed_operations:
            # Run compensations for completed operations
            logger.warning(f"Running {len(self._compensation_log)} compensations")
            for comp_fn in self._compensation_log:
                try:
                    await comp_fn()
                except Exception as comp_e:
                    logger.error(f"Compensation failed: {comp_e}")

            # Log the failure but don't raise - PG is already committed
            # This is the "eventual consistency" scenario
            logger.error(
                f"ClickHouse write failed for {len(failed_operations)} operations. "
                "Data may be inconsistent. Manual intervention required."
            )

        # Clear buffer after processing
        self._clickhouse_buffer.clear()

    async def _execute_clickhouse_operation(self, operation: PendingClickHouseOperation) -> None:
        """Execute a single ClickHouse operation."""
        if operation.operation == "insert":
            await self.clickhouse_client.insert(operation.table, operation.data)
        elif operation.operation == "update":
            # ClickHouse doesn't support updates well, use insert with version
            await self.clickhouse_client.insert(operation.table, operation.data)
        elif operation.operation == "delete":
            # ClickHouse uses mutations for deletes - avoid if possible
            logger.warning(f"Delete operation requested for {operation.table} - use soft deletes")
        else:
            raise ValueError(f"Unknown operation: {operation.operation}")

    @property
    def postgres(self) -> AsyncSession:
        """Access to PostgreSQL session."""
        return self.postgres_session

    @property
    def is_committed(self) -> bool:
        """Check if transaction is committed."""
        return self._is_committed

    @property
    def is_active(self) -> bool:
        """Check if transaction is still active (not committed/rolled back)."""
        return not (self._is_committed or self._is_rolled_back)


class Repository(ABC):
    """Abstract base for repositories using Unit of Work."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @abstractmethod
    async def add(self, entity: Any) -> Any:
        """Add entity to repository."""
        pass

    @abstractmethod
    async def get(self, id: Any) -> Any | None:
        """Get entity by ID."""
        pass


# Convenience factory for creating UoW with default dependencies
@asynccontextmanager
async def create_unit_of_work(
    postgres_session: AsyncSession,
    clickhouse_client: ClickHouseClient | None = None,
    enable_clickhouse: bool = True,
) -> AsyncGenerator[UnitOfWork]:
    """
    Factory context manager for Unit of Work.

    Usage:
        async with create_unit_of_work(session, ch_client) as uow:
            uow.postgres.add(order)
            uow.add_clickhouse_operation("trades", trade_data)
    """
    uow = UnitOfWork(
        postgres_session=postgres_session,
        clickhouse_client=clickhouse_client,
        enable_clickhouse=enable_clickhouse,
    )
    async with uow:
        yield uow
