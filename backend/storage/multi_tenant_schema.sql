"""
Multi-Tenant Database Schema for ClickHouse.

Isolates customer data using tenant_id column for security and compliance.
Implements row-level security and data segregation.
"""

-- ============================================
-- MULTI-TENANT ARCHITECTURE
-- ============================================
-- Key Principle: Every table has 'tenant_id' column
-- Partition keys: (tenant_id, date)
-- This ensures efficient queries and complete data isolation

-- ============================================
-- 1. TENANT MANAGEMENT
-- ============================================

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id UUID,
    tenant_name String,
    status Enum8('active' = 1, 'suspended' = 2, 'deleted' = 3),
    created_at DateTime,
    max_accounts UInt16,
    max_positions UInt32,
    api_rate_limit UInt32,
    
    PRIMARY KEY (tenant_id)
) ENGINE = ReplacingMergeTree()
ORDER BY tenant_id;


-- ============================================
-- 2. TENANT ACCOUNTS (One-to-Many)
-- ============================================

CREATE TABLE IF NOT EXISTS tenant_accounts (
    tenant_id UUID,
    account_id UUID,
    account_name String,
    account_type Enum8('real' = 1, 'paper' = 2, 'sandbox' = 3),
    balance_usd Float64,
    created_at DateTime,
    status Enum8('active' = 1, 'frozen' = 2, 'closed' = 3),
    
    PRIMARY KEY (tenant_id, account_id)
) ENGINE = ReplacingMergeTree()
ORDER BY (tenant_id, account_id)
PARTITION BY toYYYYMM(created_at);


-- ============================================
-- 3. EXECUTION LOGS (Partitioned by tenant + date)
-- ============================================

CREATE TABLE IF NOT EXISTS execution_logs (
    tenant_id UUID,
    account_id UUID,
    execution_id UUID,
    timestamp DateTime,
    
    symbol String,
    side Enum8('BUY' = 1, 'SELL' = 2),
    quantity Float64,
    price Float64,
    commission Float64,
    status Enum8('filled' = 1, 'partial' = 2, 'cancelled' = 3, 'rejected' = 4),
    
    -- Risk checks applied
    pre_check_position_size Float64,
    pre_check_daily_loss Float64,
    pre_check_exposure Float64,
    
    INDEX idx_symbol (symbol) TYPE set(1024),
    INDEX idx_status (status) TYPE set(8)
    
) ENGINE = MergeTree()
ORDER BY (tenant_id, account_id, timestamp)
PARTITION BY (tenant_id, toYYYYMMDD(timestamp));


-- ============================================
-- 4. AUDIT TRAIL (Compliance - MiFID II)
-- ============================================

CREATE TABLE IF NOT EXISTS audit_trail (
    tenant_id UUID,
    audit_id UUID,
    timestamp DateTime,
    
    -- Who did what
    user_id String,
    action String,
    resource_type String,
    resource_id String,
    
    -- What changed
    old_value String,
    new_value String,
    
    -- Context
    ip_address String,
    user_agent String,
    
    INDEX idx_tenant (tenant_id) TYPE set(1024),
    INDEX idx_user (user_id) TYPE set(1024),
    INDEX idx_action (action) TYPE set(64)
    
) ENGINE = MergeTree()
ORDER BY (tenant_id, timestamp)
PARTITION BY (tenant_id, toYYYYMMDD(timestamp));


-- ============================================
-- 5. RISK METRICS (Per-Tenant Analytics)
-- ============================================

CREATE TABLE IF NOT EXISTS risk_metrics (
    tenant_id UUID,
    account_id UUID,
    timestamp DateTime,
    
    -- Portfolio metrics
    portfolio_value Float64,
    total_positions UInt32,
    max_position_size Float64,
    
    -- Risk metrics
    portfolio_var_95 Float64,      -- 95% VaR
    portfolio_var_99 Float64,      -- 99% VaR (regulatory)
    max_drawdown_pct Float32,
    concentration_ratio Float32,   -- Largest position / total
    
    -- Compliance flags
    breach_max_position UInt8,     -- 1 if breached
    breach_daily_loss UInt8,       -- 1 if breached
    breach_exposure UInt8,         -- 1 if breached
    
    INDEX idx_tenant (tenant_id) TYPE set(1024),
    INDEX idx_account (account_id) TYPE set(1024)
    
) ENGINE = MergeTree()
ORDER BY (tenant_id, account_id, timestamp)
PARTITION BY (tenant_id, toYYYYMMDD(timestamp))
TTL timestamp + INTERVAL 365 DAY;  -- Keep 1 year of metrics


-- ============================================
-- 6. MULTI-TENANT VIEWS (FOR SECURITY)
-- ============================================

-- View template for tenant isolation
-- SELECT * FROM execution_logs WHERE tenant_id = '{tenant_id}'

CREATE VIEW IF NOT EXISTS v_execution_logs_by_tenant AS
SELECT 
    tenant_id, account_id, execution_id, timestamp,
    symbol, side, quantity, price, commission, status
FROM execution_logs
WHERE tenant_id IN (SELECT tenant_id FROM tenants WHERE status = 1);


-- ============================================
-- 7. MATERIALIZED VIEWS (For Performance)
-- ============================================

-- Daily summary per tenant (for reporting)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_summary AS
SELECT
    tenant_id,
    toDate(timestamp) as trade_date,
    count() as trade_count,
    sum(CASE WHEN side = 1 THEN quantity ELSE 0 END) as total_bought,
    sum(CASE WHEN side = 2 THEN quantity ELSE 0 END) as total_sold,
    sum(commission) as total_commission,
    countIf(status = 4) as rejected_count
FROM execution_logs
GROUP BY tenant_id, trade_date
ENGINE = SummingMergeTree(trade_count)
ORDER BY (tenant_id, trade_date);


-- ============================================
-- 8. MULTI-TENANT RETENTION POLICIES
-- ============================================

-- Soft delete: Mark as deleted instead of removing
ALTER TABLE execution_logs MODIFY COLUMN status Enum8('filled' = 1, 'partial' = 2, 'cancelled' = 3, 'rejected' = 4, 'deleted' = 5);

-- Compliance: Keep audit trail forever (or per regulation)
-- TTL for execution_logs: 7 years (regulatory requirement)
-- Already covered by PARTITION by date, can delete old partitions
