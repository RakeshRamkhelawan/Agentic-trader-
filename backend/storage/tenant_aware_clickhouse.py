"""
Tenant-Aware ClickHouse Client.

Wraps ClickHouseClient to automatically inject tenant_id filters,
enforcing multi-tenant data isolation at the query level.
"""

import logging
import re
from typing import Any

from backend.core.auth.context import get_current_tenant_optional
from backend.storage.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)


class TenantIsolationError(Exception):
    """Raised when tenant isolation cannot be enforced."""

    pass


class TenantAwareClickHouseClient(ClickHouseClient):
    """
    ClickHouse client with automatic tenant isolation.

    Features:
    - Automatically injects `WHERE tenant_id = :tid` into SELECT queries
    - Validates tenant_id on INSERT operations
    - Prevents raw queries without tenant context in production
    """

    # Tables that require tenant isolation
    TENANT_TABLES = {
        "trades",
        "orders",
        "positions",
        "metrics",
        "alerts",
        "agent_messages",
        "workflow_executions",
        "memories",
    }

    # Tables exempt from tenant filtering (system tables, lookups)
    EXEMPT_TABLES = {
        "system",
        "information_schema",
        "exchange_config",
        "asset_metadata",
    }

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str = "agentic_trading",
        username: str | None = None,
        password: str | None = None,
        url: str | None = None,
        enforce_tenant: bool = True,
    ):
        """
        Initialize tenant-aware client.

        Args:
            enforce_tenant: If True, require tenant context for all queries.
                           Set to False for migrations/admin operations.
        """
        super().__init__(host, port, database, username, password, url)
        self.enforce_tenant = enforce_tenant

    def inject_tenant_filter(self, sql: str, tenant_id: str) -> str:
        """
        Inject tenant_id filter into SQL query.

        Handles:
        - Simple SELECT statements
        - WHERE clause extension
        - Subqueries (basic support)

        Args:
            sql: Original SQL query
            tenant_id: Tenant identifier

        Returns:
            Modified SQL with tenant filter
        """
        sql = sql.strip()
        upper_sql = sql.upper()

        # Skip non-SELECT statements (handled separately)
        if not upper_sql.startswith("SELECT"):
            return sql

        # Skip if tenant_id already present
        if "tenant_id" in sql.lower():
            return sql

        # Detect table name from FROM clause
        table_match = re.search(r"\bFROM\s+(\w+)", sql, re.IGNORECASE)
        if not table_match:
            return sql

        table_name = table_match.group(1).lower()

        # Skip exempt tables
        if table_name in self.EXEMPT_TABLES:
            return sql

        # Build tenant filter clause (parameterized to prevent injection)
        # Note: ClickHouse doesn't support :param style, so we validate tenant_id
        if not tenant_id or not isinstance(tenant_id, str):
            raise ValueError("Invalid tenant_id")
        # Validate tenant_id format (alphanumeric, hyphens, underscores only)
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", tenant_id):
            raise ValueError(f"Invalid tenant_id format: {tenant_id}")
        tenant_filter = f"tenant_id = '{tenant_id}'"

        # Check if WHERE clause exists
        where_match = re.search(r"\bWHERE\b", sql, re.IGNORECASE)

        if where_match:
            # Insert after WHERE
            pos = where_match.end()
            sql = sql[:pos] + f" {tenant_filter} AND" + sql[pos:]
        else:
            # Find position before ORDER BY, GROUP BY, LIMIT, or end
            insert_pos = len(sql)
            for keyword in ["ORDER BY", "GROUP BY", "LIMIT", "HAVING"]:
                match = re.search(rf"\b{keyword}\b", sql, re.IGNORECASE)
                if match and match.start() < insert_pos:
                    insert_pos = match.start()

            sql = sql[:insert_pos] + f" WHERE {tenant_filter} " + sql[insert_pos:]

        logger.debug(f"Injected tenant filter for tenant_id={tenant_id}")
        return sql.strip()

    async def query(
        self,
        sql: str,
        parameters: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> Any:
        """
        Execute query with automatic tenant filtering.

        Args:
            sql: SQL query
            parameters: Query parameters
            tenant_id: Optional explicit tenant_id (uses context if not provided)

        Returns:
            Query result
        """
        # Get tenant_id from context or parameter
        if tenant_id is None:
            tenant_id = get_current_tenant_optional()

        if self.enforce_tenant and tenant_id is None:
            raise TenantIsolationError(
                "No tenant context available. Use set_current_tenant() or provide tenant_id."
            )

        # Inject tenant filter if we have a tenant_id
        if tenant_id:
            sql = self.inject_tenant_filter(sql, tenant_id)

        return await self.execute(sql, parameters)

    async def insert_with_tenant(
        self,
        table: str,
        data: list[dict[str, Any]],
        column_names: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """
        Insert data with automatic tenant_id injection.

        Args:
            table: Table name
            data: List of row dictionaries
            column_names: Column names
            tenant_id: Optional explicit tenant_id
        """
        # Get tenant_id from context or parameter
        if tenant_id is None:
            tenant_id = get_current_tenant_optional()

        if self.enforce_tenant and tenant_id is None:
            raise TenantIsolationError("No tenant context for INSERT operation.")

        # Inject tenant_id into each row
        if tenant_id:
            for row in data:
                if "tenant_id" not in row:
                    row["tenant_id"] = tenant_id
                elif row["tenant_id"] != tenant_id:
                    raise TenantIsolationError(
                        f"Row tenant_id mismatch: expected {tenant_id}, got {row['tenant_id']}"
                    )

        await self.insert(table, data, column_names)

    async def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """Execute raw SQL (use with caution, no automatic filtering)."""
        return await super().execute(query, parameters)
