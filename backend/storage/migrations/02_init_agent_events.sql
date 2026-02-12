CREATE TABLE IF NOT EXISTS agent_events (
    id UUID,
    ts DateTime64(3),
    type LowCardinality(String),
    source LowCardinality(String),
    target LowCardinality(String),
    tenant_id Nullable(String),
    conversation_id Nullable(String),
    symbol Nullable(String),
    price Nullable(Float64),
    payload String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(ts)
ORDER BY (type, ts);
