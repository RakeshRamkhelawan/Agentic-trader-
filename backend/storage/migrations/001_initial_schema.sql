-- MIGRATION: 001_initial_schema
-- DESCRIPTION: Setup core TimeSeries tables for Market Data and Execution Audit Trail.

-- 1. Schema Versions Table
-- Tracks which migrations have been applied.
CREATE TABLE IF NOT EXISTS schema_versions (
    version UInt32,
    applied_at DateTime64(3) DEFAULT now(),
    description String
) ENGINE = MergeTree()
ORDER BY version;

-- 2. Market Ticks (High Frequency Data)
-- Optimized for read speed and compression ratio.
CREATE TABLE IF NOT EXISTS market_ticks (
    symbol LowCardinality(String),
    
    -- DoubleDelta is perfect for prices that change slightly (e.g. 100.01 -> 100.02)
    price Decimal(18, 8) CODEC(DoubleDelta, LZ4),
    
    -- Delta is perfect for sequential timestamps
    timestamp DateTime64(6) CODEC(Delta, LZ4),
    
    volume Decimal(18, 8) DEFAULT 0,
    source LowCardinality(String) DEFAULT 'revolut_x'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp) -- Partition per month to keep parts manageable
ORDER BY (symbol, timestamp)     -- Primary Sort Key for fast retrieval per symbol
TTL timestamp + INTERVAL 1 YEAR; -- Auto-delete ticks older than 1 year (optional, cost saving)

-- 3. Execution Logs (The Audit Trail)
-- Immutable record of every trading action.
CREATE TABLE IF NOT EXISTS execution_logs (
    client_order_id UUID,
    symbol LowCardinality(String),
    side Enum8('BUY' = 1, 'SELL' = 2),
    order_type Enum8('MARKET' = 1, 'LIMIT' = 2, 'STOP' = 3),
    
    qty Decimal(18, 8),
    price Decimal(18, 8) DEFAULT 0, -- 0 for Market Orders until filled
    limit_price Nullable(Decimal(18, 8)),
    
    status LowCardinality(String), -- 'PENDING', 'FILLED', 'REJECTED'
    
    timestamp DateTime64(6) DEFAULT now(),
    strategy_id LowCardinality(String) DEFAULT 'manual',
    
    -- Links to Vector DB for reasoning
    thought_id Nullable(UUID),
    
    raw_response String CODEC(ZSTD) -- Store full JSON response compressed, just in case
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp, client_order_id);

-- 4. Risk Events (Guardrails)
-- Log every time the system BLOCKED a trade.
CREATE TABLE IF NOT EXISTS risk_events (
    timestamp DateTime64(6) DEFAULT now(),
    check_name LowCardinality(String), -- e.g. 'max_daily_loss'
    symbol LowCardinality(String),
    attempted_qty Decimal(18, 8),
    limit_value Decimal(18, 8),
    current_value Decimal(18, 8),
    action_blocked Bool DEFAULT true
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY timestamp;
