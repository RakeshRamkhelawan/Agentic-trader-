CREATE TABLE IF NOT EXISTS llm_usage_logs (
    tenant_id UUID,
    timestamp DateTime,
    model String,
    prompt_tokens UInt32,
    completion_tokens UInt32,
    cost_usd Float64,
    agent_name String,
    request_id UUID,

    INDEX idx_tenant (tenant_id) TYPE set(100)
) ENGINE = MergeTree()
ORDER BY (tenant_id, timestamp)
PARTITION BY toYYYYMM(timestamp);
