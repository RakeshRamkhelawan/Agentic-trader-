# ADR-005: Multi-Tenant Isolatie End-to-End

**Status**: Proposed  
**Date**: 2026-02-20  
**Author**: Architecture Team  
**Scope**: Auth, API, Storage, Caching, Rate Limiting  

---

## Context

Het Agentic Trader Platform moet meerdere tenants (organisaties/users) ondersteunen met volledige isolatie:

- **Data isolatie**: Tenant A kan geen data van Tenant B zien
- **Rate limiting**: Per-tenant quotas om resource abuse te voorkomen
- **Audit trails**: Wie deed wat, voor welke tenant
- **Resource scoping**: Compute/resources per tenant beperkt

Huidige situatie:
- Tenant-aware ClickHouse/Chroma genoemd in docs
- Geen expliciete tenant context propagation
- Geen rate limiting implementatie
- Geen tenant-scoped audit logging

---

## Decision

### 1. Tenant Identificatie

**Bron**: Auth0 JWT `tenant_id` claim

```json
{
  "sub": "user-123",
  "tenant_id": "acme-corp",
  "permissions": ["trading:execute", "portfolio:read"],
  "quota_tier": "professional"
}
```

**Propagation flow**:
```
Auth0 JWT → API Gateway → Request Context → Services → Storage
                ↓
         Correlation Context (trace_id + tenant_id)
                ↓
         Redis Cache Key: "tenant:{id}:resource"
         ClickHouse: WHERE tenant_id = '...'
         PostgreSQL: RLS policies
```

### 2. Tenant Context Model

```python
@dataclass
class TenantContext:
    tenant_id: str              # Unique tenant identifier
    tier: str                   # free/professional/enterprise
    quotas: TenantQuotas        # Resource limits
    features: List[str]         # Enabled features
    settings: Dict[str, Any]    # Tenant-specific config
```

### 3. Isolatie Lagen

| Laag | Mechanisme | Implementatie |
|------|------------|---------------|
| **API** | JWT validatie + context | `TenantMiddleware` |
| **Cache** | Key prefixing | `tenant:{id}:*` |
| **Database** | Row Level Security | PostgreSQL RLS |
| **Analytics** | Query filtering | ClickHouse WHERE clause |
| **Storage** | Collection prefix | ChromaDB collection names |
| **Events** | Topic routing | `tenant.{id}.events` |

### 4. Rate Limiting & Quotas

**Quotas per Tier**:

| Resource | Free | Professional | Enterprise |
|----------|------|--------------|------------|
| Requests/min | 60 | 600 | 6000 |
| Orders/day | 10 | 1000 | Unlimited |
| WS connections | 1 | 10 | 100 |
| API calls/month | 10K | 1M | Unlimited |
| Storage (orders) | 1K | 100K | Unlimited |
| Agents | 1 | 5 | Unlimited |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 599
X-RateLimit-Reset: 1645623600
X-RateLimit-Policy: professional
```

---

## Implementation

### 1. Tenant Context Manager

```python
# backend/core/tenant/context.py
from dataclasses import dataclass
from typing import Dict, List, Optional
import contextvars

_tenant_context: contextvars.ContextVar[Optional["TenantContext"]] = contextvars.ContextVar(
    'tenant_context', default=None
)

@dataclass
class TenantQuotas:
    requests_per_minute: int
    orders_per_day: int
    ws_connections: int
    api_calls_per_month: int
    max_agents: int

@dataclass
class TenantContext:
    tenant_id: str
    tier: str  # free, professional, enterprise
    quotas: TenantQuotas
    features: List[str]
    settings: Dict[str, any]
    
    # Tier definitions
    TIERS = {
        'free': TenantQuotas(60, 10, 1, 10_000, 1),
        'professional': TenantQuotas(600, 1000, 10, 1_000_000, 5),
        'enterprise': TenantQuotas(6000, 999_999, 100, 999_999_999, 999)
    }
    
    @classmethod
    def from_jwt(cls, jwt_claims: dict) -> "TenantContext":
        tenant_id = jwt_claims.get('tenant_id', 'default')
        tier = jwt_claims.get('quota_tier', 'free')
        
        return cls(
            tenant_id=tenant_id,
            tier=tier,
            quotas=cls.TIERS.get(tier, cls.TIERS['free']),
            features=jwt_claims.get('features', []),
            settings=jwt_claims.get('settings', {})
        )
    
    def set_current(self):
        _tenant_context.set(self)
    
    @classmethod
    def get_current(cls) -> Optional["TenantContext"]:
        return _tenant_context.get()
```

### 2. Tenant Middleware

```python
# backend/core/tenant/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Extracts tenant context from JWT and validates access.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Extract tenant from JWT (set by auth middleware)
        jwt_claims = getattr(request.state, 'jwt_claims', {})
        
        tenant_ctx = TenantContext.from_jwt(jwt_claims)
        tenant_ctx.set_current()
        
        # Store in request state
        request.state.tenant = tenant_ctx
        
        # Add tenant to correlation context
        from backend.core.telemetry.correlation import CorrelationContext
        corr_ctx = CorrelationContext.get_current()
        corr_ctx.tenant_id = tenant_ctx.tenant_id
        corr_ctx.set_current()
        
        # Check if tenant is active
        if not await self._is_tenant_active(tenant_ctx.tenant_id):
            raise HTTPException(status_code=403, detail="Tenant inactive or suspended")
        
        response = await call_next(request)
        
        # Add tenant headers
        response.headers['X-Tenant-ID'] = tenant_ctx.tenant_id
        response.headers['X-Tenant-Tier'] = tenant_ctx.tier
        
        return response
    
    async def _is_tenant_active(self, tenant_id: str) -> bool:
        # Check tenant status in database
        # Cache result for 60 seconds
        pass
```

### 3. Rate Limiter

```python
# backend/core/tenant/rate_limiter.py
import time
from typing import Optional
import redis

class TenantRateLimiter:
    """
    Sliding window rate limiter per tenant.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(
        self, 
        tenant_id: str, 
        resource: str,  # 'api', 'orders', 'ws'
        limit: int,
        window_seconds: int = 60
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.
        
        Returns:
            (allowed, headers_dict)
        """
        key = f"ratelimit:{tenant_id}:{resource}"
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old entries
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current entries
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        
        results = pipe.execute()
        current_count = results[1]
        
        allowed = current_count <= limit
        
        headers = {
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(max(0, limit - current_count)),
            'X-RateLimit-Reset': str(int(now + window_seconds)),
            'X-RateLimit-Resource': resource
        }
        
        return allowed, headers
    
    async def check_quota(
        self,
        tenant_id: str,
        quota_type: str,  # 'orders_per_day', 'api_calls_month'
        limit: int
    ) -> bool:
        """Check daily/monthly quota."""
        key = f"quota:{tenant_id}:{quota_type}"
        current = int(self.redis.get(key) or 0)
        
        if current >= limit:
            return False
        
        # Increment with TTL
        pipe = self.redis.pipeline()
        pipe.incr(key)
        
        # Set expiry based on quota type
        if 'day' in quota_type:
            pipe.expire(key, 86400)
        elif 'month' in quota_type:
            pipe.expire(key, 2592000)
        
        pipe.execute()
        return True
```

### 4. Tenant-Aware Storage

```python
# backend/storage/tenant_storage.py
class TenantAwareStorage:
    """
    Storage wrapper that enforces tenant isolation.
    """
    
    def __init__(self, storage_backend):
        self.backend = storage_backend
    
    def _get_tenant_id(self) -> str:
        from backend.core.tenant.context import TenantContext
        ctx = TenantContext.get_current()
        if not ctx:
            raise PermissionError("No tenant context")
        return ctx.tenant_id
    
    # PostgreSQL with RLS
    async def query_postgres(self, query: str, params: tuple):
        tenant_id = self._get_tenant_id()
        
        # RLS automatically filters by tenant_id
        # Query must include tenant_id or use RLS-enabled tables
        async with self.backend.acquire() as conn:
            # Set tenant context for RLS
            await conn.execute(
                "SET app.current_tenant = %s", (tenant_id,)
            )
            return await conn.fetch(query, *params)
    
    # ClickHouse with filtering
    async def query_clickhouse(self, query: str, params: dict):
        tenant_id = self._get_tenant_id()
        
        # Inject tenant filter
        if 'WHERE' in query:
            query = query.replace('WHERE', f'WHERE tenant_id = %(tenant_id)s AND')
        else:
            query += f' WHERE tenant_id = %(tenant_id)s'
        
        params['tenant_id'] = tenant_id
        return await self.backend.query(query, params)
    
    # Redis with key prefixing
    async def get_cache(self, key: str):
        tenant_id = self._get_tenant_id()
        tenant_key = f"tenant:{tenant_id}:{key}"
        return await self.backend.get(tenant_key)
    
    async def set_cache(self, key: str, value, ttl: int = 3600):
        tenant_id = self._get_tenant_id()
        tenant_key = f"tenant:{tenant_id}:{key}"
        return await self.backend.set(tenant_key, value, ex=ttl)
    
    # ChromaDB with collection prefix
    async def query_chroma(self, collection: str, query: str):
        tenant_id = self._get_tenant_id()
        tenant_collection = f"tenant_{tenant_id}_{collection}"
        return await self.backend.query(tenant_collection, query)
```

### 5. Tenant Decorators

```python
# backend/core/tenant/decorators.py
from functools import wraps
from fastapi import HTTPException

def require_tenant():
    """Decorator to ensure tenant context exists."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from backend.core.tenant.context import TenantContext
            if not TenantContext.get_current():
                raise HTTPException(403, "Tenant context required")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_feature(feature: str):
    """Decorator to require specific tenant feature."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from backend.core.tenant.context import TenantContext
            ctx = TenantContext.get_current()
            if not ctx or feature not in ctx.features:
                raise HTTPException(403, f"Feature '{feature}' not available")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(resource: str, limit_override: int = None):
    """Decorator to apply rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            from backend.core.tenant.context import TenantContext
            from backend.core.tenant.rate_limiter import limiter
            
            ctx = TenantContext.get_current()
            if not ctx:
                raise HTTPException(403, "Tenant context required")
            
            limit = limit_override or getattr(ctx.quotas, f"{resource}_per_minute", 60)
            
            allowed, headers = await limiter.check_rate_limit(
                ctx.tenant_id, resource, limit
            )
            
            if not allowed:
                raise HTTPException(429, "Rate limit exceeded", headers=headers)
            
            # Store headers for response
            request.state.rate_limit_headers = headers
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## Audit Logging

```python
# backend/core/tenant/audit.py
class TenantAuditLogger:
    """
    Audit logging per tenant for compliance.
    """
    
    async def log_event(
        self,
        event_type: str,      # 'trade_executed', 'settings_changed'
        resource_type: str,   # 'order', 'portfolio', 'settings'
        resource_id: str,
        action: str,          # 'create', 'update', 'delete', 'execute'
        details: dict,
        user_id: Optional[str] = None
    ):
        from backend.core.tenant.context import TenantContext
        ctx = TenantContext.get_current()
        
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'tenant_id': ctx.tenant_id if ctx else 'unknown',
            'user_id': user_id or 'system',
            'event_type': event_type,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'details': details,
            'ip_address': self._get_client_ip(),
            'user_agent': self._get_user_agent()
        }
        
        # Write to ClickHouse for analytics
        await self._write_to_clickhouse(audit_entry)
        
        # Write to secure PostgreSQL table
        await self._write_to_postgres(audit_entry)
```

---

## Monitoring

### Grafana Dashboard: "Multi-Tenant Overview"

**Panels**:
1. **Active Tenants**: Per tier, over tijd
2. **Rate Limit Hits**: 429 responses per tenant
3. **Resource Usage**: API calls, orders, storage per tenant
4. **Top Tenants**: By usage/volume
5. **Tenant Errors**: Errors per tenant

### Alerts

```yaml
- alert: HighRateLimitHits
  expr: rate(http_requests_total{status="429"}[5m]) > 10
  severity: warning
  
- alert: TenantResourceExhaustion
  expr: tenant_resource_usage / tenant_resource_limit > 0.9
  severity: critical
```

---

## Migration Plan

### Phase 1: Foundation
1. Implement TenantContext
2. Add TenantMiddleware
3. Update JWT claims

### Phase 2: Storage
1. Add RLS to PostgreSQL
2. Update ClickHouse queries
3. Implement cache prefixing

### Phase 3: Rate Limiting
1. Deploy Redis rate limiter
2. Add rate limit headers
3. Implement quota tracking

### Phase 4: Audit
1. Create audit tables
2. Instrument key operations
3. Create compliance reports

---

## Consequences

### Positief
- Volledige data isolatie
- Resource abuse preventie
- Compliance audit trails
- Scalable per-tenant pricing

### Negatief
- Query performance overhead (10-20%)
- Complexiteit in storage layer
- Rate limiting kan false positives geven

---

## Decision Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-20 | Initial draft | Architecture Team |
