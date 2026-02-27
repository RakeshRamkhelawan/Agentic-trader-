# Database Schema - Agentic Trader

Database schema reference for the Agentic Trader platform.

## Databases

### PostgreSQL (Primary)
- User accounts, auth, settings
- Trading orders, positions
- Portfolio data

### ClickHouse (Analytics)
- Market data ticks
- Trading history
- Performance metrics
- LLM usage logs

### Redis (Cache)
- Session cache
- Rate limiting
- Real-time data

## Key Tables

### PostgreSQL

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### orders
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    tenant_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- BUY or SELL
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    status VARCHAR(50) DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### portfolios
```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    tenant_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    quantity DECIMAL(20, 8) DEFAULT 0,
    avg_price DECIMAL(20, 8) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### audit_logs (SOC2)
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id UUID,
    tenant_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
```

### ClickHouse

#### market_ticks
```sql
CREATE TABLE market_ticks (
    symbol String,
    price Float64,
    volume Float64,
    timestamp DateTime64(3),
    exchange String
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp);
```

#### trades
```sql
CREATE TABLE trades (
    id UUID,
    order_id UUID,
    symbol String,
    side String,
    quantity Float64,
    price Float64,
    timestamp DateTime64(3),
    tenant_id String
) ENGINE = MergeTree()
ORDER BY (tenant_id, timestamp);
```

#### llm_usage_logs
```sql
CREATE TABLE llm_usage_logs (
    tenant_id String,
    model String,
    tokens_input UInt32,
    tokens_output UInt32,
    cost_usd Float64,
    timestamp DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (tenant_id, timestamp);
```

## Query Patterns

### Insert Order
```python
from backend.core.database import get_db_session

async def create_order(user_id: str, symbol: str, side: str, qty: float):
    async with get_db_session() as session:
        result = await session.execute(
            """
            INSERT INTO orders (id, user_id, symbol, side, quantity, status)
            VALUES (gen_random_uuid(), :user_id, :symbol, :side, :qty, 'submitted')
            RETURNING id
            """,
            {"user_id": user_id, "symbol": symbol, "side": side, "qty": qty}
        )
        return result.scalar()
```

### Get Portfolio
```python
async def get_portfolio(user_id: str):
    async with get_db_session() as session:
        result = await session.execute(
            """
            SELECT symbol, quantity, avg_price
            FROM portfolios
            WHERE user_id = :user_id
            """,
            {"user_id": user_id}
        )
        return result.fetchall()
```

### Market Data Query (ClickHouse)
```python
async def get_price_history(symbol: str, hours: int = 24):
    query = """
    SELECT 
        toStartOfInterval(timestamp, INTERVAL 1 MINUTE) as minute,
        argMax(price, timestamp) as close,
        min(price) as low,
        max(price) as high,
        sum(volume) as volume
    FROM market_ticks
    WHERE symbol = %(symbol)s
      AND timestamp >= now() - INTERVAL %(hours)s HOUR
    GROUP BY minute
    ORDER BY minute
    """
    result = await clickhouse_client.execute(query, {
        "symbol": symbol,
        "hours": hours
    })
    return result
```

### SOC2 Audit Log Query
```python
async def get_audit_logs(start_date: datetime, end_date: datetime, tenant_id: str):
    async with get_db_session() as session:
        result = await session.execute(
            """
            SELECT timestamp, user_id, action, details, ip_address
            FROM audit_logs
            WHERE tenant_id = :tenant_id
              AND timestamp BETWEEN :start_date AND :end_date
            ORDER BY timestamp DESC
            """,
            {
                "tenant_id": tenant_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        return result.fetchall()
```

## Migrations

Use Alembic for PostgreSQL migrations:

```bash
# Create migration
alembic revision --autogenerate -m "add user preferences"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Best Practices

1. **Always use parameterized queries** (never f-strings with user input)
2. **Use transactions** for multi-step operations
3. **Index frequently queried columns**
4. **Partition large tables** by time (ClickHouse)
5. **Archive old data** to cold storage
6. **Log all sensitive operations** for SOC2 audit trail

## SOC2 Data Retention

| Data Type | Retention | Storage |
|-----------|-----------|---------|
| Audit logs | 7 years | PostgreSQL + cold storage |
| Trade history | 7 years | ClickHouse |
| User data | Duration of account + 2 years | PostgreSQL |
| Market data | 2 years | ClickHouse |
