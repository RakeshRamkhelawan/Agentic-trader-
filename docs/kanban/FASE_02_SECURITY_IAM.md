# Fase 2: Security & IAM

> **Prioriteit**: 🔴 CRITICAL
> **Afhankelijkheden**: Geen (parallel met Fase 1)
> **Geschatte effort**: 5-7 dagen
> **Master document**: [SAMKHYA_MASTER_KANBAN_TDD.md](./SAMKHYA_MASTER_KANBAN_TDD.md)

---

## Overzicht

Beveiligingslaag: OAuth2/OIDC via Auth0, multi-tenant RLS, en HashiCorp Vault secret rotation. Na deze fase is iedere API-call geauthenticeerd, tenant-geïsoleerd, en zijn secrets veilig geroteerd.

```
Request → Auth0 JWT Validation → Tenant Extraction → RLS Policy → Handler
                                                          ↓
                                                   Vault Secret Rotation
                                                   (API keys, DB creds)
```

---

## Bestaande Code Referenties

| Bestand | Regels | Status |
|---------|--------|--------|
| [backend/api/gateway.py](../../backend/api/gateway.py) | 372 | JWTManager ✅, RateLimiter ✅ |
| [backend/api/auth_api.py](../../backend/api/auth_api.py) | 313 | JWT create/verify ✅, register/login ✅ |
| [backend/api/metrics_middleware.py](../../backend/api/metrics_middleware.py) | 80 | MetricsMiddleware ✅ |
| [backend/core/config/settings.py](../../backend/core/config/settings.py) | 135 | Vault-aware props, Auth0 config |
| [backend/api/websocket_endpoints.py](../../backend/api/websocket_endpoints.py) | 85 | TODO L45: JWT validation |
| [backend/governance/permission_service.py](../../backend/governance/permission_service.py) | 221 | Bestaand permissiesysteem |

**Opmerking**: `backend/api/middleware.py` bestaat NIET. Middleware zit in `metrics_middleware.py` en `gateway.py`.

---

## Taken & Microtaken

---

### TAAK 2.1: OAuth2 / OIDC via Auth0

**Doel**: Vervang custom JWT auth door Auth0 met PKCE + RS256 validatie.

**Bestanden te wijzigen**:
- `backend/api/gateway.py` (JWTManager op L148)
- `backend/api/auth_api.py` (register/login flows)
- `backend/core/config/settings.py` (Auth0 config)

**Bestanden te creëren**:
- `backend/api/auth0_middleware.py`
- `backend/tests/unit/test_auth0_middleware.py`

---

#### Microtaak 2.1.1: Auth0 JWT Validator Middleware

**Masterprompt**:
```
Bouw Auth0JWTMiddleware die RS256-signed tokens valideert via Auth0 JWKS endpoint.
Bestaande JWTManager (gateway.py:148) gebruikt HS256 met statisch secret —
vervang door RS256 met JWKS discovery. Gebruik python-jose[cryptography] of PyJWT.
Auth0 config al deels aanwezig in settings.py (AUTH0_DOMAIN, AUTH0_API_AUDIENCE).
Flow: Request → Extract Bearer → Decode RS256 → Validate aud/iss → Inject tenant_id claim.
```

**Bestaande code gateway.py:148-190**:
```python
class JWTManager:
    def __init__(self, settings):
        self.secret_key = settings.JWT_SECRET_KEY  # HS256 → moet RS256 worden
    def create_token(self, user_id, expires_delta=None):
        ...
    def verify_token(self, token):
        ...
```

**Test FIRST (TDD Red)**:
```python
# backend/tests/unit/test_auth0_middleware.py

import pytest
from unittest.mock import patch, MagicMock
from backend.api.auth0_middleware import Auth0JWTMiddleware


class TestAuth0JWTMiddleware:

    @pytest.fixture
    def middleware(self):
        return Auth0JWTMiddleware(
            domain="test.eu.auth0.com",
            api_audience="https://api.samkhya-trader.io",
            algorithms=["RS256"]
        )

    def test_valid_token_passes(self, middleware):
        """Happy: Geldig Auth0 token → request gaat door."""
        # Mock JWKS + token validation
        pass

    def test_expired_token_returns_401(self, middleware):
        """Unhappy: Verlopen token → 401 Unauthorized."""
        pass

    def test_wrong_audience_returns_401(self, middleware):
        """Unhappy: Token voor verkeerd audience → 401."""
        pass

    def test_missing_bearer_returns_401(self, middleware):
        """Unhappy: Geen Bearer header → 401."""
        pass

    def test_malformed_token_returns_401(self, middleware):
        """Unhappy: Geen geldig JWT formaat → 401."""
        pass

    def test_tenant_id_extracted_from_claims(self, middleware):
        """Happy: tenant_id uit custom claim geëxtraheerd."""
        pass

    def test_role_based_access_admin(self, middleware):
        """Happy: Admin role in claims → volledige toegang."""
        pass

    def test_role_based_access_viewer(self, middleware):
        """Unhappy: Viewer role → geen write access."""
        pass
```

---

#### Microtaak 2.1.2: WebSocket JWT Validatie (fix TODO)

**Masterprompt**:
```
Fix TODO op websocket_endpoints.py:45: "TODO: Validate JWT token and extract tenant/account".
WebSocket handshake moet Auth0 token valideren vóór connection upgrade.
Token kan via query parameter of Sec-WebSocket-Protocol header.
```

**Test FIRST**:
```python
class TestWebSocketJWTValidation:

    def test_ws_with_valid_token_connects(self):
        """Happy: WS met geldig token → connectie succesvol."""
        pass

    def test_ws_without_token_rejects(self):
        """Unhappy: WS zonder token → close 4001."""
        pass

    def test_ws_with_expired_token_rejects(self):
        """Unhappy: WS met verlopen token → close 4001."""
        pass
```

**Taak-afronding integratie test**:
```python
async def test_integration_2_1_auth0_end_to_end():
    """
    Integratie: Auth0 login flow → JWT → API call → tenant isolation.
    Test op productie Auth0 tenant (staging environment).
    """
    # 1. Simuleer Auth0 M2M token via client_credentials
    # 2. Call /api/health met token
    # 3. Verify tenant_id in response context
    # 4. Call zonder token → 401
```

---

### TAAK 2.2: Multi-Tenant Row-Level Security

**Doel**: PostgreSQL RLS policies zodat tenant A nooit data van tenant B kan zien.

**Bestanden te wijzigen**:
- `backend/data/models.py` (39 regels — tenant_id kolom toevoegen)
- `backend/data/repository.py` (121 regels — tenant filter)

**Bestanden te creëren**:
- `backend/migrations/add_rls_policies.py`
- `backend/tests/unit/test_rls_policies.py`

**Bestaande referenties**:
- `backend/data/models.py:1-39` (SQLAlchemy modellen)
- `backend/data/repository.py:1-121` (Repository patroon)
- `diagnose_rls.py` (root — bestaand RLS diagnose script)

---

#### Microtaak 2.2.1: RLS Alembic Migration

**Masterprompt**:
```
Maak Alembic migration die:
1. tenant_id UUID kolom toevoegt aan alle relevante tabellen
2. RLS inschakelt: ALTER TABLE ... ENABLE ROW LEVEL SECURITY
3. Policy: USING (tenant_id = current_setting('app.tenant_id')::uuid)
4. App user (non-superuser) in PostgreSQL aanmaken
Bestaand: alembic.ini in root, backend/migrations/ directory met versions/
```

**Test FIRST**:
```python
class TestRLSPolicies:

    def test_tenant_a_cannot_see_tenant_b_data(self):
        """Happy: Tenant A ziet alleen eigen data."""
        pass

    def test_superuser_sees_all_data(self):
        """Happy: Superuser bypassed RLS."""
        pass

    def test_insert_without_tenant_id_fails(self):
        """Unhappy: Insert zonder tenant_id → violation."""
        pass

    def test_rls_applies_to_all_tables(self):
        """Happy: Alle tabellen hebben RLS policy."""
        pass

    def test_cross_tenant_update_blocked(self):
        """Unhappy: Update van andere tenant's data → 0 rows affected."""
        pass
```

---

### TAAK 2.3: HashiCorp Vault Secret Rotation

**Doel**: Dynamische secrets voor API keys en database credentials.

**Bestanden te wijzigen**:
- `backend/core/config/settings.py` (Vault-aware properties op L50-90)

**Bestanden te creëren**:
- `backend/core/vault_client.py`
- `backend/tests/unit/test_vault_client.py`

**Bestaande code settings.py:50-70**:
```python
@cached_property
def JWT_SECRET_KEY(self) -> str:
    if self.VAULT_ENABLED:
        return self._read_vault_secret("jwt/secret")
    return self.JWT_SECRET_KEY_ENV or "dev-secret"
```

---

#### Microtaak 2.3.1: VaultClient implementatie

**Masterprompt**:
```
Bouw VaultClient met hvac library. Features:
- Token/AppRole auth
- KV v2 secret engine read/write
- Dynamic database credentials (PostgreSQL secret engine)
- Automatic lease renewal
- Graceful fallback naar env vars als Vault onbereikbaar
Bestaand: settings.py heeft al VAULT_ENABLED, VAULT_ADDR, VAULT_TOKEN.
K8s: cronjob-key-rotation.yaml bestaat al in infrastructure/k8s/.
```

**Test FIRST**:
```python
class TestVaultClient:

    def test_read_secret_returns_value(self):
        """Happy: KV v2 secret lezen."""
        pass

    def test_dynamic_db_credential_valid(self):
        """Happy: Dynamic PostgreSQL cred werkt."""
        pass

    def test_lease_renewal(self):
        """Happy: Lease wordt automatisch vernieuwd."""
        pass

    def test_vault_unreachable_fallback_to_env(self):
        """Unhappy: Vault down → fallback naar env vars."""
        pass

    def test_expired_token_re_authenticates(self):
        """Unhappy: Verlopen token → re-auth via AppRole."""
        pass

    def test_rotation_does_not_interrupt_active_connections(self):
        """Happy: Key rotation gracefully — geen connection drops."""
        pass
```

**Taak-afronding integratie test**:
```python
async def test_integration_2_3_vault_rotation_e2e():
    """
    Integratie: Vault secret rotation → settings reload → active connections ok.
    """
    pass
```

---

## Fase 2 Productie Test

```python
@pytest.mark.e2e
async def test_production_phase2_security_complete():
    """
    PRODUCTIE TEST: Volledige security stack.
    1. Auth0 JWT validatie op alle endpoints
    2. RLS isolatie tussen tenants
    3. Vault secret beschikbaar
    4. WebSocket JWT validatie
    5. Rate limiting werkt
    """
    pass
```

---

## Kruisverwijzingen

- **← Fase 1**: NavagrahaState moet per-tenant geïsoleerd worden (Taak 2.2)
- **→ Fase 3**: Vault moet in K8s als init container draaien (Taak 3.1)
- **→ Fase 3**: Prometheus moet Auth0 metrics scrapen (Taak 3.3)
- **→ Fase 5**: Frontend Auth0 React SDK integratie (Taak 5.3)
- **→ Fase 7**: MiFID II audit trails per tenant (Taak 7.1)
