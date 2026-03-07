-- MIGRATION: 002_agent_decisions
-- DESCRIPTION: Tabel voor het opslaan van alle agent beslissingen en analyses.

CREATE TABLE IF NOT EXISTS agent_decisions (
    tenant_id UUID,
    agent_id LowCardinality(String),
    session_id UUID,
    timestamp DateTime64(6) DEFAULT now(),

    symbol LowCardinality(String),
    action LowCardinality(String), -- e.g. 'propose', 'analyze', 'orient', 'decide'

    confidence Decimal(5, 4),
    perspective LowCardinality(String), -- e.g. 'bullish', 'bearish', 'neutral'

    rationale String,
    data String CODEC(ZSTD), -- Volledige context/features in JSON

    metadata String CODEC(ZSTD) -- Optionele extra info
) ENGINE = MergeTree()
PARTITION BY (tenant_id, toYYYYMM(timestamp))
ORDER BY (tenant_id, agent_id, timestamp, symbol);
