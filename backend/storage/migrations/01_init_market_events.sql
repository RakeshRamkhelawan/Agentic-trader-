
CREATE TABLE IF NOT EXISTS market_events (
    event_type LowCardinality(String),
    venue LowCardinality(String),
    symbol LowCardinality(String),
    ts_exchange DateTime64(3),
    ts_received DateTime64(3),
    price Nullable(Float64),
    size Nullable(Float64),
    side Nullable(String),
    bid Nullable(Float64),
    ask Nullable(Float64),
    bids_price Array(Float64),
    bids_size Array(Float64),
    asks_price Array(Float64),
    asks_size Array(Float64)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(ts_received)
ORDER BY (symbol, ts_received, event_type);
