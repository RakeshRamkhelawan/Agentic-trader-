"""
ClickHouse Client for Analytics Storage.

Provides async connection pooling and query execution for ClickHouse.
"""

import os
from typing import Any

import clickhouse_connect

from backend.core.auth.context import get_current_tenant_optional


class ClickHouseClient:
    """Async ClickHouse client with connection pooling."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str = "agentic_trading",
        username: str | None = None,
        password: str | None = None,
        url: str | None = None,
    ):
        """
        Initialize ClickHouse client.

        Args:
            host: ClickHouse host (default: localhost or CLICKHOUSE_HOST env)
            port: ClickHouse port (default: 8123 or CLICKHOUSE_PORT env)
            database: Database name (default: agentic_trading)
            username: Username (default: CLICKHOUSE_USER env or 'default')
            password: Password (default: CLICKHOUSE_PASSWORD env)
            url: Full connection URL (overrides other params)
        """
        self.host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = port or int(os.getenv("CLICKHOUSE_PORT", "8123"))
        self.database = database
        self.username = username or os.getenv("CLICKHOUSE_USER", "default")
        self.password = password or os.getenv("CLICKHOUSE_PASSWORD", "")

        # Build URL if provided or from components
        if url:
            self.url = url
        else:
            self.url = f"http://{self.host}:{self.port}"

        self.client: Any | None = None

    async def connect(self) -> None:
        """Establish connection to ClickHouse."""
        print(
            f"DEBUG: ClickHouseClient connecting to {self.host}:{self.port} as user='{self.username}' with password='{self.password}'"
        )
        try:
            self.client = await clickhouse_connect.get_async_client(
                host=self.host,
                port=self.port,
                database=self.database,
                username=self.username,
                password=self.password,
            )
            print("DEBUG: ClickHouseClient connected successfully.")
        except Exception as e:
            print(f"DEBUG: ClickHouseClient connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to ClickHouse."""
        if self.client:
            await self.client.close()
            self.client = None

    async def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """
        Execute SQL query.

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            Query result
        """
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")

        tenant_id = get_current_tenant_optional()
        if tenant_id:
            if parameters is None:
                parameters = {}
            # Auto-inject tenant_id parameter for binding
            if "tenant_id" not in parameters:
                parameters["tenant_id"] = tenant_id

        return await self.client.query(query, parameters=parameters)

    async def insert(
        self,
        table: str,
        data: list[dict[str, Any]],
        column_names: list[str] | None = None,
    ) -> None:
        """
        Insert data into table.

        Args:
            table: Table name
            data: List of dictionaries with data
            column_names: Optional column names (inferred from data if not provided)
        """
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")

        if not data:
            return

        # Automatic Tenant Injection
        tenant_id = get_current_tenant_optional()
        if tenant_id:
            for item in data:
                if "tenant_id" not in item:
                    item["tenant_id"] = tenant_id

        # Filter out None values from data
        data = [item for item in data if item is not None]
        if not data:
            return

        # Extract column names from first data item to ensure consistency
        if column_names is None:
            column_names = list(data[0].keys())

        # Convert data to list of tuples for clickhouse-connect
        # This ensures proper column alignment
        data_tuples = []
        for item in data:
            row = tuple(item.get(col) for col in column_names)
            data_tuples.append(row)

        await self.client.insert(table, data_tuples, column_names=column_names)

    async def create_table(self, schema: str) -> None:
        """
        Create table with given schema.

        Args:
            schema: CREATE TABLE statement
        """
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")

        await self.client.command(schema)

    async def ping(self) -> bool:
        """
        Check if connection is alive.

        Returns:
            True if connected and responsive
        """
        if not self.client:
            return False

        try:
            return await self.client.ping()
        except Exception:
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
