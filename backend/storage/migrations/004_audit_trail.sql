CREATE TABLE IF NOT EXISTS audit_trail (
    tenant_id UUID,
    audit_id UUID,
    timestamp DateTime64(6) DEFAULT now(),
    actor_id String,
    action String,
    resource_type String,
    resource_id String,
    details String, -- JSON string
    status LowCardinality(String), -- SUCCESS, FAILURE
    ip_address String,
    user_agent String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (tenant_id, timestamp, action);
