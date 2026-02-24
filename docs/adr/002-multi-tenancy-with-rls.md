# ADR 002: Multi-Tenancy with PostgreSQL RLS

## Status
Accepted

## Context

The Agentic Trader Platform is a SaaS serving multiple organizations (tenants). Each tenant has multiple users (accounts) who should only see their own data. We need strict data isolation with minimal code complexity.

## Decision

We will implement **multi-tenancy using PostgreSQL Row-Level Security (RLS)**.

### Architecture

```
┌─────────────────────────────────────────┐
│           Application Layer             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  User   │ │  Admin  │ │  API    │  │
│  │  Web    │ │  Panel  │ │  Client │  │
│  └────┬────┘ └────┬────┘ └────┬────┘  │
└───────┼───────────┼───────────┼───────┘
        │           │           │
        └───────────┼───────────┘
                    │ JWT + tenant context
                    ▼
┌─────────────────────────────────────────┐
│           Service Layer                 │
│    (All queries filtered by RLS)        │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│       PostgreSQL with RLS               │
│                                         │
│  CREATE POLICY tenant_isolation ON      │
│  orders FOR ALL TO app_user             │
│  USING (tenant_id = current_tenant());  │
│                                         │
└─────────────────────────────────────────┘
```

### Implementation

```python
# Base model with RLS columns
class TenantMixin:
    tenant_id = Column(String, nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)

# RLS Policy (PostgreSQL)
"""
CREATE POLICY tenant_isolation ON orders
    FOR ALL
    TO app_user
    USING (tenant_id = current_setting('app.current_tenant')::text);
"""

# Application-level enforcement
class RLSEnforcer:
    def __init__(self, tenant_id: str, account_id: str):
        self.tenant_id = tenant_id
        self.account_id = account_id

    def apply_to_query(self, query, model):
        if hasattr(model, 'tenant_id'):
            query = query.filter(model.tenant_id == self.tenant_id)
        return query
```

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| **RLS (Chosen)** | Database-enforced, impossible to bypass | PostgreSQL-specific |
| Schema per tenant | Complete isolation | Migration complexity |
| Application filtering | Database agnostic | Easy to bypass, error-prone |
| Separate databases | Maximum isolation | Cost, complexity |

## Consequences

### Positive
- **Enforced at database level**: Cannot accidentally expose tenant data
- **Simpler application code**: No manual filtering needed
- **Audit friendly**: RLS policies are documented in schema
- **Performance**: Index on tenant_id columns

### Negative
- **PostgreSQL-specific**: Ties us to PostgreSQL
- **Complex migrations**: RLS policies must be managed
- **Testing overhead**: Need to set tenant context in tests
- **Debugging**: RLS can make query debugging harder

### Migration Strategy
```python
# Alembic migration for RLS
from alembic import op

# Enable RLS on table
op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY")

# Create policy
op.execute("""
    CREATE POLICY tenant_isolation ON orders
    FOR ALL
    TO app_user
    USING (tenant_id = current_setting('app.current_tenant')::text)
""")
```

## Related Decisions
- ADR 005: PostgreSQL as Primary Database

## References
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
