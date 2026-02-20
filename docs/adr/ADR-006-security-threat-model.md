# ADR-006: Security Boundaries & Threat Model (STRIDE)

**Status**: Proposed  
**Date**: 2026-02-20  
**Author**: Architecture Team  
**Scope**: Security architecture, threat modeling, mitigations  

---

## Context

Het Agentic Trader Platform verwerkt:
- **Gevoelige data**: Portfolio's, trades, PII (KYC)
- **Financiële transacties**: Order execution, geldstromen
- **API keys**: Exchange credentials, LLM tokens
- **AI/ML models**: Strategieën, proprietary algoritmes

Huidige security maatregelen:
- Auth0 JWT authentication
- HTTPS/WSS endpoints
- PostgreSQL RLS (basis)
- Geen expliciet threat model
- Geen gedocumenteerde security boundaries

**Doel**: Systematische security analyse met STRIDE + concrete mitigaties.

---

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRUST ZONES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Untrusted Zone]        [Semi-Trusted]          [Trusted Zone]             │
│                                                                             │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────────┐        │
│  │   Browser    │       │   CDN/WAF    │       │   API Gateway    │        │
│  │   Mobile     │◄─────►│   Auth0      │◄─────►│   Load Balancer  │        │
│  │   External   │       │   CloudFlare │       │                  │        │
│  └──────────────┘       └──────────────┘       └────────┬─────────┘        │
│                                                         │                   │
│                               ┌─────────────────────────┼─────────┐        │
│                               │    [Trusted Internal]   │         │        │
│                               │                         ▼         │        │
│                               │    ┌─────────────────────────┐    │        │
│                               │    │   FastAPI Services    │    │        │
│                               │    │   - Trading API       │    │        │
│                               │    │   - Agent API         │    │        │
│                               │    │   - Auth middleware   │    │        │
│                               │    └──────────┬────────────┘    │        │
│                               │               │                 │        │
│                               │    ┌──────────┴────────────┐    │        │
│                               │    │   Business Logic      │    │        │
│                               │    │   - Execution         │    │        │
│                               │    │   - Risk Engine       │    │        │
│                               │    │   - Agents            │    │        │
│                               │    └──────────┬────────────┘    │        │
│                               │               │                 │        │
│                               │    ┌──────────┴────────────┐    │        │
│                               │    │   [Critical Zone]     │    │        │
│                               │    │   - Secrets Vault     │    │        │
│                               │    │   - Private Keys      │    │        │
│                               │    │   - Exchange APIs     │    │        │
│                               │    └─────────────────────────┘    │        │
│                               └───────────────────────────────────┘        │
│                                                                             │
│  External APIs: [Bitvavo] [Revolut] [LLM Providers] [Auth0]                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Boundary Rules**:
1. **Untrusted → Semi-Trusted**: TLS, WAF, rate limiting
2. **Semi-Trusted → Trusted**: JWT validation, tenant context
3. **Trusted → Critical**: Additional MFA, audit logging, least privilege

---

## STRIDE Analysis

### S - Spoofing (Identity)

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| JWT forgery | Critical | RS256 + JWKS validation | ✅ Implemented |
| Stolen credentials | High | Auth0 MFA, session mgmt | ✅ Implemented |
| API key theft | High | HashiCorp Vault, key rotation | 🔄 In Progress |
| Impersonation | Medium | Audit trails, anomaly detection | ⚠️ Planned |

**Controls**:
```python
# JWT validation
@require_valid_jwt()
async def protected_endpoint():
    pass

# API key rotation (every 90 days)
class KeyRotationService:
    async def rotate_exchange_keys(self):
        # Generate new key
        # Update exchanges
        # Invalidate old key after grace period
```

---

### T - Tampering (Data Integrity)

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| Order manipulation | Critical | Digital signatures, audit logs | ✅ Implemented |
| Config tampering | High | GitOps, config validation | ✅ Implemented |
| Database injection | Critical | Parameterized queries, ORM | ✅ Implemented |
| Cache poisoning | Medium | Signed cache entries, TTL | ⚠️ Planned |

**Controls**:
```python
# Order signing
class OrderSigner:
    def sign_order(self, order: OrderRequest) -> str:
        payload = f"{order.id}:{order.symbol}:{order.price}:{order.timestamp}"
        return hmac_sha256(self.secret, payload)
    
    def verify_order(self, order: OrderRequest, signature: str) -> bool:
        expected = self.sign_order(order)
        return hmac.compare_digest(expected, signature)

# Database protection
@require_sql_injection_check()
async def query_database(query: str, params: tuple):
    # Use ORM, never raw SQL with string interpolation
    pass
```

---

### R - Repudiation (Accountability)

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| Denied trades | High | Immutable audit logs | ✅ Implemented |
| Unauthorized access | High | Session logging, IP tracking | ✅ Implemented |
| Data deletion | Medium | Append-only storage, backups | ✅ Implemented |

**Controls**:
```python
# Immutable audit logging
class ImmutableAuditLog:
    async def log_trade(self, trade: Trade):
        entry = {
            'timestamp': utc_now(),
            'hash': self._calculate_hash(trade),
            'previous_hash': self._get_last_hash(),
            'data': trade.to_dict()
        }
        # Write to append-only storage
        await self._write_to_worm_storage(entry)
        # Replicate to multiple locations
        await self._replicate(entry)
```

---

### I - Information Disclosure

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| Data breach | Critical | Encryption at rest/transit | ✅ Implemented |
| Tenant leakage | Critical | Tenant isolation (ADR-005) | 🔄 In Progress |
| Log exposure | Medium | Log sanitization, PII masking | ✅ Implemented |
| Side-channel | Low | Constant-time algorithms | ⚠️ Planned |

**Controls**:
```python
# PII masking in logs
class PIIMasker:
    MASK_PATTERNS = [
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[MASKED_CC]'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[MASKED_EMAIL]'),
    ]
    
    def mask(self, text: str) -> str:
        for pattern, replacement in self.MASK_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

# Encryption
class DataEncryption:
    def __init__(self, key_provider: KeyProvider):
        self.key_provider = key_provider
    
    def encrypt_sensitive(self, data: bytes) -> EncryptedData:
        key = self.key_provider.get_data_key()
        return self._encrypt_aes_gcm(data, key)
```

---

### D - Denial of Service

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| API flooding | High | Rate limiting (ADR-005) | 🔄 In Progress |
| Resource exhaustion | Medium | Quotas, circuit breakers | ✅ Implemented |
| Compute abuse | Medium | Request timeouts, limits | ✅ Implemented |
| DDoS | High | CloudFlare, WAF | ✅ Implemented |

**Controls**:
```python
# Circuit breaker
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_exchange_api():
    # Auto-opens on failures
    pass

# Resource quotas
@require_quota('compute_ms', max_ms=1000)
async def heavy_computation():
    pass
```

---

### E - Elevation of Privilege

| Threat | Risk | Mitigation | Status |
|--------|------|------------|--------|
| Privilege escalation | Critical | RBAC, least privilege | ✅ Implemented |
| Admin abuse | High | MFA, approval workflows | ✅ Implemented |
| Container escape | Medium | Non-root containers, seccomp | ✅ Implemented |
| Supply chain | Medium | SBOM, dependency scanning | 🔄 In Progress |

**Controls**:
```python
# RBAC enforcement
class RBACEnforcer:
    PERMISSIONS = {
        'trader': ['trading:execute', 'portfolio:read'],
        'admin': ['*'],
        'readonly': ['portfolio:read', 'analytics:read']
    }
    
    def check_permission(self, user: User, resource: str, action: str):
        required = f"{resource}:{action}"
        user_perms = self.PERMISSIONS.get(user.role, [])
        
        if '*' not in user_perms and required not in user_perms:
            raise PermissionDenied(f"Missing permission: {required}")

# Approval workflows for sensitive operations
class ApprovalWorkflow:
    async def request_large_trade(self, order: OrderRequest):
        if order.value > LARGE_TRADE_THRESHOLD:
            # Require second approval
            approval = await self.create_approval_request(order)
            await self.notify_approvers(approval)
            raise ApprovalRequired("Trade requires approval")
```

---

## Security Controls Matrix

| Control | Threats | Implementation | Priority |
|---------|---------|----------------|----------|
| **Authentication** | Spoofing | Auth0 JWT + MFA | P0 |
| **Authorization** | Elevation | RBAC + ABAC | P0 |
| **Encryption** | Disclosure | TLS 1.3, AES-256-GCM | P0 |
| **Audit Logging** | Repudiation | Immutable logs | P0 |
| **Input Validation** | Tampering | Pydantic, parameterized queries | P0 |
| **Rate Limiting** | DoS | Token bucket per tenant | P1 |
| **Circuit Breakers** | DoS | Fail-fast on errors | P1 |
| **Secrets Mgmt** | Spoofing | HashiCorp Vault | P1 |
| **WAF** | DoS, Tampering | CloudFlare rules | P1 |
| **Supply Chain** | Elevation | SBOM, Snyk scanning | P2 |
| **Pen Testing** | All | Quarterly assessments | P2 |

---

## Secrets Management

```python
# backend/core/security/secrets.py
class SecretsManager:
    """
    Centralized secrets management with HashiCorp Vault.
    """
    
    def __init__(self, vault_addr: str, vault_token: str):
        self.vault = hvac.Client(url=vault_addr, token=vault_token)
    
    async def get_exchange_api_key(self, exchange: str, tenant_id: str) -> str:
        """Get API key for specific exchange and tenant."""
        path = f"secret/data/exchanges/{exchange}/{tenant_id}"
        response = self.vault.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']['api_key']
    
    async def rotate_exchange_key(self, exchange: str, tenant_id: str):
        """Rotate API key with zero downtime."""
        # 1. Generate new key at exchange
        # 2. Store in Vault
        # 3. Update services
        # 4. Revoke old key after grace period
        pass
    
    async def get_database_credentials(self, role: str) -> dict:
        """Get dynamic database credentials."""
        return self.vault.secrets.database.generate_credentials(
            name=role
        )
```

---

## Network Security

```yaml
# Network policies (Kubernetes)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-server-policy
spec:
  podSelector:
    matchLabels:
      app: api-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

---

## Security Monitoring

### Detection Rules

```yaml
# SIEM detection rules
- name: SuspiciousLogin
  condition: |
    auth.event == "login" AND
    (auth.source_ip NOT IN user.known_ips OR
     auth.user_agent != user.known_agent)
  severity: high
  
- name: LargeTradeAnomaly
  condition: |
    trade.value > user.avg_trade_value * 10 AND
    trade.timestamp WITHIN 1h
  severity: medium
  
- name: APIKeyAbuse
  condition: |
    api.requests_per_minute > user.quota * 5
  severity: critical
```

---

## Compliance Mapping

| Requirement | Control | Evidence |
|-------------|---------|----------|
| SOC 2 | Audit logs, access controls | ADR-002, ADR-005 |
| GDPR | PII masking, data retention | ADR-008 |
| MiFID II | Order audit trails, best execution | ADR-001, ADR-007 |
| PCI DSS | Encryption, access controls | This ADR |

---

## Security Checklist

### Development
- [ ] Static analysis (bandit, semgrep)
- [ ] Dependency scanning (snyk, safety)
- [ ] Secret scanning (git-secrets)
- [ ] Container scanning (trivy)

### Deployment
- [ ] Non-root containers
- [ ] Read-only filesystems
- [ ] Security contexts
- [ ] Network policies

### Runtime
- [ ] WAF rules active
- [ ] Rate limiting enabled
- [ ] Anomaly detection
- [ ] Incident response plan

---

## Decision Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-20 | Initial STRIDE analysis | Architecture Team |
