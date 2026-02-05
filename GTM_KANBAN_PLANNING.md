# GTM Kanban Task Planning: Agentic Trader Platform

This document breaks down the [GTM_GAPS_PRD.md](GTM_GAPS_PRD.md) into actionable microtasks for implementation.

---

## 🟦 BACKLOG: Infrastructure & DevOps (P0)

### Task 1: Kubernetes & Orchestration Setup
**Status**: 🔴 Not Started | **Priority**: P0 | **Estimated Effort**: 5 days

**Context**: Current deployment via `docker-compose.yml` with 7 services (Redpanda, ClickHouse, Redis, ChromaDB, Prometheus, Grafana, Metrics-Server). No K8s infrastructure exists.

**Dependencies**: 
- Existing `infrastructure/docker/Dockerfile` (python:3.13-slim)
- `backend/api/gateway.py` (FastAPI with JWT skeleton)
- `backend/core/config/settings.py` (env-based config)

**Subtasks**:
- [ ] **1.1 Docker Optimization** (4h)
  - **Goal**: Reduce image from ~800MB to <200MB using multi-stage Alpine build
  - **Current Issues**: Debian base, dev tools in final image, no layer caching
  - **Deliverables**: 
    - Multi-stage Dockerfile with builder + runtime stages
    - `.dockerignore` file to exclude tests/docs
    - Health check endpoint on port 8000
  - **Validation**: `docker images` shows <250MB, container starts in <5s
  - **Files**: `infrastructure/docker/Dockerfile`, `infrastructure/docker/.dockerignore`

- [ ] **1.2 Base Helm Charts** (8h)
  - **Goal**: Create umbrella chart structure with dependency management
  - **Architecture**: Parent chart + subcharts (agent-orchestrator, dashboard-api)
  - **Deliverables**:
    - `Chart.yaml` with dependencies (ClickHouse Altinity, Redis Bitnami, Strimzi Kafka)
    - `values.yaml` with global config (namespace, domain, imageRegistry)
    - `_helpers.tpl` for common labels and selectors
  - **Validation**: `helm lint` passes, `helm template` generates valid YAML
  - **Files**: `infrastructure/k8s/charts/agentic-platform/`

- [ ] **1.3 Service Deployments** (12h)
  - **Goal**: Deploy agent orchestrator as StatefulSet with persistent state
  - **Key Features**:
    - Prometheus scraping on port 8001
    - Non-root user (UID 1000)
    - PersistentVolumeClaim for agent state
    - Service discovery via headless ClusterIP
  - **Environment Variables**:
    - `CLICKHOUSE_HOST`: `clickhouse-service.agentic-platform-prod.svc.cluster.local`
    - `REDIS_URL`: `redis://redis-master:6379/0`
    - `KAFKA_BOOTSTRAP_SERVERS`: `kafka-bootstrap:9092`
  - **Validation**: StatefulSet running, readiness probe passes in <30s
  - **Files**: `charts/agent-orchestrator/templates/statefulset.yaml`, `service.yaml`

- [ ] **1.4 Ingress & TLS** (6h)
  - **Goal**: HTTPS termination with automatic Let's Encrypt certificates
  - **Prerequisites**: Install NGINX Ingress Controller v1.9.5, Cert-Manager v1.13.3
  - **Hosts**: 
    - `api.yourdomain.com` → dashboard-api:8000
    - `yourdomain.com/metrics` → agent-orchestrator:8001
  - **Rate Limiting**: 100 req/min, 10 RPS per IP
  - **Validation**: `kubectl get certificate` shows READY=True, curl returns 200 OK with valid TLS
  - **Files**: `templates/ingress.yaml`, `cluster-issuer.yaml`

- [ ] **1.5 Resource Quotas** (4h)
  - **Goal**: Prevent resource starvation via namespace-level quotas
  - **Hard Limits**:
    - CPU: 20 cores (requests), 40 cores (limits with burst)
    - Memory: 64Gi (requests), 128Gi (limits)
    - PVCs: Max 10 per namespace
  - **Container Defaults**: 200m CPU / 256Mi RAM (requests), 500m CPU / 512Mi RAM (defaults)
  - **Network Policies**: Agent orchestrator can only reach ClickHouse:8123, Redis:6379
  - **Validation**: Pod creation fails when quota exceeded
  - **Files**: `templates/resource-quota.yaml`, `network-policy.yaml`

### Task 2: Secrets Hardening
**Status**: 🔴 Not Started | **Priority**: P0 | **Estimated Effort**: 3 days

**Context**: Currently using `.env` files and local `revolut_private.pem` for credentials. Non-compliant with SOC2/ISO27001.

**Current Security Issues**:
- API keys in plain text in `backend/core/config/settings.py`
- Ed25519 private key on filesystem (`REVOLUT_PRIVATE_KEY_PATH`)
- No audit trail for secret access
- No automatic rotation

**Target Architecture**: HashiCorp Vault with Kubernetes CSI driver for runtime injection

**Subtasks**:
- [ ] **2.1 Vault Client** (6h)
  - **Goal**: Create Python wrapper for HashiCorp Vault KV v2 secrets
  - **Implementation**:
    - Use `hvac` library for Vault API client
    - Support AppRole authentication for K8s service accounts
    - Implement connection pooling and retry logic (tenacity)
  - **Methods**:
    - `get_secret(path: str, key: str) -> str`
    - `list_secrets(path: str) -> List[str]`
    - `rotate_key(path: str, new_value: bytes) -> bool`
  - **Error Handling**: Fallback to `.env` if Vault unreachable (dev mode only)
  - **Validation**: `vault_manager.get_secret('revolut/api_key')` returns valid key
  - **Files**: `backend/core/security/vault_manager.py`
  - **Dependencies**: Add `hvac==2.1.0` to `requirements/base.txt`

- [ ] **2.2 Settings Integration** (4h)
  - **Goal**: Refactor Pydantic Settings to prioritize Vault over environment variables
  - **Current State**: `settings.py` reads from `.env` via `pydantic_settings`
  - **Changes**:
    - Add `VAULT_ENABLED: bool = False` flag
    - Implement `@property` decorators for sensitive fields
    - Override `__init__` to fetch from Vault when enabled
  - **Priority Order**: Vault → K8s Secrets → Environment Variables → Defaults
  - **Example**:
    ```python
    @property
    def REVOLUT_API_KEY(self) -> str:
        if self.VAULT_ENABLED:
            return vault_manager.get_secret('revolut', 'api_key')
        return os.getenv('REVOLUT_API_KEY', '')
    ```
  - **Validation**: Start app with `VAULT_ENABLED=true`, verify no `.env` reads in logs
  - **Files**: `backend/core/config/settings.py`

- [ ] **2.3 Key Rotation Service** (6h)
  - **Goal**: Automate Ed25519 key pair rotation for exchange authentication
  - **Current State**: Static key in `revolut_private.pem`, no rotation mechanism
  - **Implementation**:
    - Generate new Ed25519 key pair using `cryptography.hazmat`
    - Upload public key to Revolut API (`POST /api/1.0/keys`)
    - Store private key in Vault with versioning
    - Update `ExchangeAdapter` to fetch latest key from Vault
  - **Rotation Schedule**: Every 90 days (configurable)
  - **Deployment**: K8s CronJob running daily (checks if rotation due)
  - **Validation**: After rotation, new orders succeed, old orders fail gracefully
  - **Files**: `backend/core/security/key_rotator.py`, `infrastructure/k8s/charts/agentic-platform/templates/cronjob-key-rotation.yaml`
  - **Rollback Strategy**: Keep last 3 key versions in Vault

---

## 🟨 BACKLOG: Platform Core & Multi-tenancy (P0)

### Task 3: Identity & Access Management (IAM)
**Status**: 🔴 Not Started | **Priority**: P0 | **Estimated Effort**: 4 days

**Context**: Current `backend/api/gateway.py` has JWT skeleton but no enforcement. No multi-tenant isolation exists.

**Business Impact**: Without IAM, Tenant A can access Tenant B's metrics/trades via API.

**Current State Analysis**:
- `RateLimiter` class exists in `gateway.py` (in-memory, not production-ready)
- `HTTPBearer` imported but not used
- `python-jose[cryptography]==3.3.0` already in dependencies

**Target Architecture**:
```
User Request → Ingress → AuthMiddleware (JWT validation) → 
Extract tenant_id → ContextVar injection → Route to handler → 
ClickHouse query (auto-filtered by tenant_id)
```

**Subtasks**:
- [ ] **3.1 Identity Provider Setup** (4h)
  - **Goal**: Configure Auth0 tenant for OAuth2/OIDC flow
  - **Decision**: Auth0 vs Keycloak
    - **Auth0**: Faster setup, $25/month for 1000 users, managed service
    - **Keycloak**: Self-hosted, free, requires maintenance
    - **Recommendation**: Auth0 for MVP, migrate to Keycloak if cost becomes issue
  - **Configuration**:
    - Create Auth0 tenant: `agentic-trader.auth0.com`
    - Enable RS256 signing algorithm (not HS256)
    - Configure callback URL: `https://api.yourdomain.com/auth/callback`
    - Add custom claim: `tenant_id` in JWT payload
  - **Roles**:
    - `viewer`: Read-only dashboard access
    - `trader`: Can submit orders manually
    - `admin`: Can modify API keys and config
  - **Validation**: Generate test JWT with `tenant_id=test-tenant-001`, decode successfully
  - **Files**: Auth0 dashboard configuration (document in `docs/auth0-setup.md`)

- [ ] **3.2 JWT Validator** (6h)
  - **Goal**: Verify RS256 JWTs using Auth0's public JWKS endpoint
  - **Current State**: `python-jose` already installed
  - **Implementation**:
    - Fetch JWKS from `https://agentic-trader.auth0.com/.well-known/jwks.json`
    - Cache public keys in memory (refresh every 1 hour)
    - Verify signature, expiration (exp), and issuer (iss)
    - Extract claims: `sub` (user_id), `tenant_id`, `roles`
  - **Error Handling**:
    - Expired token → HTTP 401 with `WWW-Authenticate` header
    - Invalid signature → HTTP 401 + log security event
    - Missing tenant_id → HTTP 403 (malformed token)
  - **Class Structure**:
    ```python
    class JWTValidator:
        def __init__(self, jwks_url: str, issuer: str, audience: str)
        async def validate_token(self, token: str) -> TokenPayload
        async def refresh_jwks(self) -> None
    ```
  - **Validation**: Unit test with valid/expired/tampered tokens
  - **Files**: `backend/core/auth/jwt_validator.py`, `backend/core/auth/models.py` (TokenPayload dataclass)

- [ ] **3.3 Tenant Context Management** (4h)
  - **Goal**: Store `tenant_id` per-request without passing through every function
  - **Python Feature**: `contextvars.ContextVar` (thread-safe, async-safe)
  - **Current State**: No context management exists
  - **Implementation**:
    ```python
    from contextvars import ContextVar
    
    _tenant_context: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
    
    def set_current_tenant(tenant_id: str) -> None:
        _tenant_context.set(tenant_id)
    
    def get_current_tenant() -> str:
        tenant_id = _tenant_context.get()
        if not tenant_id:
            raise UnauthorizedError("No tenant context")
        return tenant_id
    ```
  - **Integration Points**:
    - Set in `AuthMiddleware` after JWT validation
    - Read in `ClickHouseClient.query()` to inject `WHERE tenant_id = :tid`
    - Read in `CognitiveOrchestrator` for agent message routing
  - **Validation**: Concurrent requests from different tenants don't leak context
  - **Files**: `backend/core/auth/tenant_context.py`

- [ ] **3.4 Authentication Middleware** (6h)
  - **Goal**: Enforce JWT validation on all `/api/*` routes
  - **Current State**: FastAPI app in `gateway.py` has no middleware
  - **Implementation**:
    ```python
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class AuthMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, jwt_validator: JWTValidator):
            super().__init__(app)
            self.validator = jwt_validator
        
        async def dispatch(self, request: Request, call_next):
            # Skip auth for /health and /docs
            if request.url.path in ["/health", "/docs", "/openapi.json"]:
                return await call_next(request)
            
            # Extract Bearer token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse({"error": "Missing token"}, status_code=401)
            
            token = auth_header.split(" ")[1]
            try:
                payload = await self.validator.validate_token(token)
                set_current_tenant(payload.tenant_id)
                response = await call_next(request)
                return response
            except JWTError as e:
                return JSONResponse({"error": str(e)}, status_code=401)
    ```
  - **Registration**:
    ```python
    app = FastAPI()
    app.add_middleware(AuthMiddleware, jwt_validator=jwt_validator)
    ```
  - **Validation**: 
    - Request without token → 401
    - Request with expired token → 401
    - Request with valid token → 200 + correct tenant isolation
  - **Files**: `backend/core/auth/middleware.py`, update `backend/api/gateway.py`
  - **Performance**: Middleware adds <5ms latency (JWKS cached)

### Task 4: Multi-tenant Runtime Enforcement
**Status**: 🔴 Not Started | **Priority**: P0 | **Estimated Effort**: 3 days

**Context**: Schema has `tenant_id` columns, but Python code doesn't enforce isolation. Risk of data leakage.

**Current Issues**:
- `ClickHouseClient.query()` accepts raw SQL without tenant filtering
- `ChromaDB` collections are global (e.g., `memories` shared across all tenants)
- `AgentMessage` dataclass has no `tenant_id` field

**Target State**: Zero-trust architecture where tenant context is enforced at every layer.

**Subtasks**:
- [ ] **4.1 ClickHouse Query Wrapper** (8h)
  - **Goal**: Automatically inject `WHERE tenant_id = :tid` into all queries
  - **Current State**: `clickhouse_client.py` has basic `query()` and `query_np()` methods
  - **Implementation Strategy**:
    1. Create `TenantAwareQuery` class that wraps SQL AST
    2. Parse SQL using `sqlparse` library
    3. Inject tenant filter before `ORDER BY` / `LIMIT`
    4. Prevent raw queries in production (require prepared statements)
  - **Code Example**:
    ```python
    class TenantAwareClickHouseClient:
        async def query(self, sql: str, params: Dict = None) -> List[Dict]:
            tenant_id = get_current_tenant()  # From Task 3.3
            
            # Parse and inject tenant filter
            parsed = sqlparse.parse(sql)[0]
            if 'WHERE' in sql.upper():
                sql = sql.replace('WHERE', f"WHERE tenant_id = '{tenant_id}' AND")
            else:
                # Find position before ORDER BY / LIMIT
                sql = self._inject_where_clause(sql, tenant_id)
            
            return await super().query(sql, params)
    ```
  - **Edge Cases**:
    - Subqueries: Apply filter recursively
    - JOINs: Apply to all joined tables
    - Aggregations: Filter before `GROUP BY`
  - **Validation**: 
    - Query for tenant A returns 0 rows from tenant B's data
    - Benchmark: <2ms overhead for filter injection
  - **Files**: `backend/storage/clickhouse_client.py`, add `sqlparse==0.4.4` to requirements

- [ ] **4.2 ChromaDB Collection Isolation** (4h)
  - **Goal**: Namespace ChromaDB collections by tenant to prevent cross-tenant reads
  - **Current State**: `backend/core/memory_agent.py` uses global collection names
  - **Implementation**:
    - Prefix all collection names: `f"{tenant_id}_memories"`
    - Update `BaseAgent` to accept `tenant_id` in constructor
    - Modify `MemoryAgent.store()` and `MemoryAgent.search()` to use prefixed collections
  - **Code Changes**:
    ```python
    class MemoryAgent:
        def __init__(self, tenant_id: str):
            self.tenant_id = tenant_id
            self.collection_name = f"{tenant_id}_memories"
            self.collection = chroma_client.get_or_create_collection(self.collection_name)
        
        async def store(self, text: str, metadata: Dict):
            # ChromaDB automatically isolates by collection
            self.collection.add(documents=[text], metadatas=[metadata])
    ```
  - **Migration**: Create script to rename existing collections (one-time)
  - **Validation**: 
    - Tenant A cannot search tenant B's memories
    - `chroma_client.list_collections()` shows tenant prefixes
  - **Files**: `backend/core/memory_agent.py`, `backend/agents/base_agent.py`

- [ ] **4.3 AgentMessage Schema Update** (4h)
  - **Goal**: Make `tenant_id` a mandatory field in all inter-agent messages
  - **Current State**: `backend/schemas/agent_messages.py` has no tenant awareness
  - **Implementation**:
    ```python
    @dataclass
    class AgentMessage:
        source: str
        target: str
        type: str
        payload: Dict[str, Any]
        tenant_id: str  # NEW: Mandatory field
        id: str = field(default_factory=lambda: str(uuid.uuid4()))
        timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
        
        def __post_init__(self):
            if not self.tenant_id:
                raise ValueError("tenant_id is required for all messages")
            # Existing validation...
    ```
  - **Propagation**: Update all `handle_message()` methods in agents
  - **Orchestrator Changes**: `CognitiveOrchestrator` must validate tenant_id matches request context
  - **Backward Compatibility**: Support optional tenant_id for 1 release cycle (log warning)
  - **Validation**:
    - Message without tenant_id raises `ValueError`
    - Orchestrator rejects messages with mismatched tenant_id
  - **Files**: `backend/schemas/agent_messages.py`, `backend/services/cognitive_orchestrator.py`
  - **Breaking Change**: Requires coordinated deployment of all agents

---

## 🟧 BACKLOG: Trading & Execution (P1)

### Task 5: Broker Expansion & WebSocket Upgrade
**Status**: 🔴 Not Started | **Priority**: P1 | **Estimated Effort**: 5 days

**Context**: Current `ExchangeAdapter` only supports Revolut X via REST polling (high latency). Need sub-100ms data for HFT strategies.

**Current Limitations**:
- REST polling: 500-1000ms latency per request
- No order book depth visibility
- Single exchange = single point of failure
- Slippage not calculated in real-time

**Target Performance**:
- Market data latency: <50ms (via WebSocket)
- Order execution: <100ms (placement to ack)
- Order book updates: Real-time streaming

**Subtasks**:
- [ ] **5.1 WebSocket Interface Design** (6h)
  - **Goal**: Extend `ExecutionInterface` to support streaming data
  - **Current State**: `broker_interface.py` only has synchronous REST methods
  - **New Abstract Methods**:
    ```python
    class ExecutionInterface(ABC):
        # Existing methods...
        
        @abstractmethod
        async def subscribe_ticker(self, symbol: str) -> AsyncGenerator[TickerUpdate, None]:
            """Stream real-time price updates."""
            pass
        
        @abstractmethod
        async def subscribe_orders(self) -> AsyncGenerator[OrderUpdate, None]:
            """Stream order status changes."""
            pass
        
        @abstractmethod
        async def subscribe_orderbook(self, symbol: str, depth: int = 10) -> AsyncGenerator[OrderBook, None]:
            """Stream order book snapshots."""
            pass
    ```
  - **Data Models** (new file: `backend/schemas/market_data.py`):
    ```python
    @dataclass
    class TickerUpdate:
        symbol: str
        bid: float
        ask: float
        last: float
        volume_24h: float
        timestamp: datetime
    
    @dataclass
    class OrderUpdate:
        order_id: str
        status: OrderStatus
        filled_qty: float
        avg_price: float
        timestamp: datetime
    
    @dataclass
    class OrderBook:
        symbol: str
        bids: List[Tuple[float, float]]  # [(price, size), ...]
        asks: List[Tuple[float, float]]
        timestamp: datetime
    ```
  - **Validation**: Interface passes type checking with `mypy --strict`
  - **Files**: `backend/execution/broker_interface.py`, `backend/schemas/market_data.py`

- [ ] **5.2 Binance WebSocket Adapter** (12h)
  - **Goal**: Implement production-ready Binance integration via `ccxt.pro`
  - **Current State**: No Binance adapter exists
  - **Implementation**:
    ```python
    import ccxt.pro as ccxtpro
    
    class BinanceAdapter(ExecutionInterface):
        def __init__(self, api_key: str, secret: str, testnet: bool = False):
            self.exchange = ccxtpro.binance({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'future' if not testnet else 'future'},
            })
            if testnet:
                self.exchange.set_sandbox_mode(True)
        
        async def subscribe_ticker(self, symbol: str) -> AsyncGenerator[TickerUpdate, None]:
            while True:
                ticker = await self.exchange.watch_ticker(symbol)
                yield TickerUpdate(
                    symbol=ticker['symbol'],
                    bid=ticker['bid'],
                    ask=ticker['ask'],
                    last=ticker['last'],
                    volume_24h=ticker['quoteVolume'],
                    timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000)
                )
        
        async def subscribe_orderbook(self, symbol: str, depth: int = 10):
            while True:
                orderbook = await self.exchange.watch_order_book(symbol, limit=depth)
                yield OrderBook(
                    symbol=symbol,
                    bids=orderbook['bids'][:depth],
                    asks=orderbook['asks'][:depth],
                    timestamp=datetime.fromtimestamp(orderbook['timestamp'] / 1000)
                )
    ```
  - **Error Handling**:
    - Reconnect on WebSocket disconnect (exponential backoff)
    - Handle rate limits (429) gracefully
    - Validate symbol exists before subscribing
  - **Performance**: Benchmark latency with `pytest-benchmark`
  - **Validation**:
    - Subscribe to BTC/USDT, verify <50ms updates
    - Simulate disconnect, verify auto-reconnect
  - **Files**: `backend/execution/binance_adapter.py`
  - **Dependencies**: Add `ccxt==4.2.25` to requirements (not ccxt.pro, it's included)

- [ ] **5.3 Smart Order Router Enhancement** (10h)
  - **Goal**: Split large orders across exchanges to minimize slippage
  - **Current State**: `smart_order_router.py` exists but only routes to single exchange
  - **Algorithm** (VWAP-based routing):
    1. Fetch order books from all connected exchanges
    2. Calculate available liquidity at each price level
    3. Allocate order chunks to maximize VWAP (minimize slippage)
    4. Submit child orders in parallel
    5. Monitor fills and re-route unfilled quantity
  - **Implementation**:
    ```python
    class SmartOrderRouter:
        def __init__(self, adapters: Dict[str, ExecutionInterface]):
            self.adapters = adapters  # {'binance': adapter, 'revolut': adapter}
        
        async def route_order(self, order: OrderRequest) -> List[OrderResult]:
            # Fetch order books from all exchanges
            orderbooks = await self._fetch_orderbooks(order.symbol)
            
            # Calculate optimal allocation
            allocations = self._calculate_vwap_routing(orderbooks, order.qty, order.side)
            # Example: [('binance', 0.5 BTC), ('revolut', 0.3 BTC)]
            
            # Execute in parallel
            tasks = [
                self.adapters[exchange].submit_order(
                    OrderRequest(symbol=order.symbol, side=order.side, qty=qty, ...)
                )
                for exchange, qty in allocations
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return [r for r in results if not isinstance(r, Exception)]
    ```
  - **Edge Cases**:
    - Exchange offline: Route 100% to remaining exchanges
    - Partial fill: Re-route unfilled quantity
    - Price moved: Recalculate routing mid-execution
  - **Validation**:
    - 1 BTC order split 60/40 Binance/Revolut based on liquidity
    - One exchange fails: Order completes on other
    - Average slippage <0.1% vs single-exchange execution
  - **Files**: `backend/execution/smart_order_router.py`
  - **Performance**: <200ms for routing decision

### Task 6: Backtesting & Simulation Suite
**Status**: 🔴 Not Started | **Priority**: P1 | **Estimated Effort**: 6 days

**Context**: No way to validate agent performance before live deployment. Need high-fidelity simulation.

**Current Gap**: Agents can only be tested in production (risk of capital loss).

**Target Capabilities**:
- Replay historical data at configurable speed (1x, 10x, 100x)
- Simulate market impact (large orders move price)
- Generate performance reports (Sharpe, Win Rate, Max DD)

**Subtasks**:
- [ ] **6.1 Historical Data Replay Engine** (12h)
  - **Goal**: Stream historical tick data from ClickHouse to agents as if real-time
  - **Current State**: No backtesting infrastructure
  - **Data Source**: `execution_logs` table + external historical data (if available)
  - **Implementation**:
    ```python
    class BacktestEngine:
        def __init__(self, clickhouse: ClickHouseClient, start_date: datetime, end_date: datetime):
            self.clickhouse = clickhouse
            self.start_date = start_date
            self.end_date = end_date
            self.clock = SimulatedClock(start_date)
        
        async def stream_ticks(self, symbol: str, interval: str = '1m') -> AsyncGenerator[TickerUpdate, None]:
            query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM historical_ohlcv
                WHERE symbol = '{symbol}'
                  AND timestamp BETWEEN '{self.start_date}' AND '{self.end_date}'
                ORDER BY timestamp ASC
            """
            async for row in self.clickhouse.stream_query(query):
                # Simulate real-time by advancing clock
                await self.clock.sleep_until(row['timestamp'])
                
                yield TickerUpdate(
                    symbol=symbol,
                    bid=row['low'],  # Pessimistic for realism
                    ask=row['high'],
                    last=row['close'],
                    volume_24h=row['volume'],
                    timestamp=row['timestamp']
                )
    ```
  - **Clock Control**:
    ```python
    class SimulatedClock:
        def __init__(self, start_time: datetime, speed: float = 1.0):
            self.current_time = start_time
            self.speed = speed  # 1.0 = real-time, 100.0 = 100x faster
        
        async def sleep_until(self, target_time: datetime):
            delta = (target_time - self.current_time).total_seconds()
            await asyncio.sleep(delta / self.speed)
            self.current_time = target_time
    ```
  - **Validation**:
    - Backtest 1 month of data completes in <5 minutes at 100x speed
    - Clock advances correctly (no time travel bugs)
  - **Files**: `backend/execution/backtest_engine.py`, `backend/execution/simulated_clock.py`

- [ ] **6.2 Paper Exchange with Slippage Model** (10h)
  - **Goal**: Simulate realistic order execution without real trades
  - **Current State**: No mock exchange exists
  - **Slippage Model** (based on volatility):
    ```python
    class PaperExchange(ExecutionInterface):
        def __init__(self, historical_data: BacktestEngine):
            self.historical_data = historical_data
            self.open_orders: Dict[str, OrderRequest] = {}
            self.fills: List[OrderResult] = []
        
        async def submit_order(self, order: OrderRequest) -> OrderResult:
            current_tick = await self.historical_data.get_current_tick(order.symbol)
            
            # Calculate slippage based on order size and volatility
            volatility = self._calculate_recent_volatility(order.symbol)
            market_impact = (order.qty / current_tick.volume_24h) * volatility
            
            if order.side == OrderSide.BUY:
                fill_price = current_tick.ask * (1 + market_impact)
            else:
                fill_price = current_tick.bid * (1 - market_impact)
            
            # Simulate latency (50-200ms)
            await asyncio.sleep(random.uniform(0.05, 0.2))
            
            # Partial fill simulation (90% filled immediately, 10% remains)
            filled_qty = order.qty * 0.9
            
            return OrderResult(
                order_id=str(uuid.uuid4()),
                client_order_id=str(order.client_order_id),
                status=OrderStatus.PARTIALLY_FILLED,
                filled_qty=filled_qty,
                avg_price=fill_price,
            )
    ```
  - **Realism Enhancements**:
    - Order rejections (insufficient balance, invalid symbol)
    - Partial fills over time (not instant)
    - Price improvement (fill better than limit price)
  - **Validation**:
    - Large order (>1% daily volume) shows >0.5% slippage
    - Small order (<0.01% volume) shows <0.05% slippage
  - **Files**: `backend/execution/paper_exchange.py`

- [ ] **6.3 Performance Analytics Service** (8h)
  - **Goal**: Automated calculation of trading performance metrics
  - **Current State**: Manual analysis via SQL queries
  - **Metrics to Calculate**:
    - **Sharpe Ratio**: `(mean_return - risk_free_rate) / std_deviation`
    - **Sortino Ratio**: Like Sharpe but only penalizes downside volatility
    - **Max Drawdown**: Largest peak-to-trough decline
    - **Win Rate**: % of profitable trades
    - **Profit Factor**: Gross profit / Gross loss
    - **Calmar Ratio**: Annual return / Max drawdown
  - **Implementation**:
    ```python
    class PerformanceAnalytics:
        def __init__(self, clickhouse: ClickHouseClient):
            self.clickhouse = clickhouse
        
        async def calculate_sharpe_ratio(self, tenant_id: str, period_days: int = 30) -> float:
            # Fetch daily returns from execution_logs
            query = f"""
                SELECT 
                    toDate(timestamp) as date,
                    sum(quantity * price) as daily_pnl
                FROM execution_logs
                WHERE tenant_id = '{tenant_id}'
                  AND timestamp >= today() - INTERVAL {period_days} DAY
                GROUP BY date
                ORDER BY date
            """
            returns = await self.clickhouse.query(query)
            
            mean_return = statistics.mean([r['daily_pnl'] for r in returns])
            std_dev = statistics.stdev([r['daily_pnl'] for r in returns])
            
            # Assume 2% annual risk-free rate (daily = 2% / 252)
            risk_free_daily = 0.02 / 252
            
            sharpe = (mean_return - risk_free_daily) / std_dev if std_dev > 0 else 0
            return sharpe * (252 ** 0.5)  # Annualized
        
        async def calculate_max_drawdown(self, tenant_id: str) -> float:
            # Fetch cumulative equity curve
            query = f"""
                SELECT 
                    timestamp,
                    sum(quantity * price) OVER (ORDER BY timestamp) as cumulative_pnl
                FROM execution_logs
                WHERE tenant_id = '{tenant_id}'
                ORDER BY timestamp
            """
            equity_curve = await self.clickhouse.query(query)
            
            peak = equity_curve[0]['cumulative_pnl']
            max_dd = 0.0
            
            for point in equity_curve:
                if point['cumulative_pnl'] > peak:
                    peak = point['cumulative_pnl']
                drawdown = (peak - point['cumulative_pnl']) / peak
                max_dd = max(max_dd, drawdown)
            
            return max_dd
    ```
  - **API Endpoint**: `GET /api/analytics/performance?period=30d`
  - **Validation**:
    - Known portfolio returns Sharpe of 1.5 (verified manually)
    - Max drawdown calculated matches visual inspection of equity curve
  - **Files**: `backend/services/performance_analytics.py`
  - **Dependencies**: Add `scipy==1.11.4` for advanced statistics

---

## 🟩 BACKLOG: UI/UX & Dashboard (P1)

### Task 7: Frontend Dashboard (MVP)
**Status**: 🔴 Not Started | **Priority**: P1 | **Estimated Effort**: 8 days

**Context**: Backend Phase 16 API is production-ready, but no UI exists for non-technical users.

**Current State**: Users must use `curl` or Postman to interact with the platform.

**Target User Experience**:
- Real-time Mahabhutas coherence visualization ("AI health meter")
- Portfolio overview with P&L charts
- One-click emergency stop (cancel all orders)

**Subtasks**:
- [ ] **7.1 Next.js Project Initialization** (4h)
  - **Goal**: Bootstrap modern React framework with TypeScript and TailwindCSS
  - **Current State**: No `frontend/` directory exists
  - **Technology Choices**:
    - **Framework**: Next.js 14 (App Router for RSC)
    - **Styling**: TailwindCSS + Shadcn/UI components
    - **State Management**: Zustand (lightweight, no boilerplate)
    - **Data Fetching**: TanStack Query (React Query v5)
  - **Commands**:
    ```bash
    npx create-next-app@latest frontend --typescript --tailwind --app --src-dir
    cd frontend
    npx shadcn-ui@latest init
    npm install zustand @tanstack/react-query
    npm install recharts d3 @types/d3  # For charts
    ```
  - **Project Structure**:
    ```
    frontend/
    ├── src/
    │   ├── app/              # Next.js App Router
    │   │   ├── layout.tsx
    │   │   ├── page.tsx      # Dashboard home
    │   │   └── api/          # API routes (proxies to backend)
    │   ├── components/       # Reusable UI components
    │   │   ├── ui/           # Shadcn components
    │   │   └── dashboard/    # Dashboard-specific
    │   ├── lib/              # Utilities
    │   │   ├── api-client.ts
    │   │   └── stores.ts     # Zustand stores
    │   └── types/            # TypeScript definitions
    ├── public/
    └── package.json
    ```
  - **Environment Variables** (`.env.local`):
    ```
    NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com/ws
    ```
  - **Validation**: `npm run dev` starts on localhost:3000
  - **Files**: Entire `frontend/` directory

- [ ] **7.2 TypeScript API Client Generation** (6h)
  - **Goal**: Auto-generate type-safe client from backend OpenAPI spec
  - **Current State**: Backend exports OpenAPI at `/openapi.json`
  - **Tool**: `openapi-typescript-codegen` or `orval`
  - **Process**:
    ```bash
    # Install codegen
    npm install --save-dev openapi-typescript-codegen
    
    # Generate client
    npx openapi-typescript-codegen \
      --input https://api.yourdomain.com/openapi.json \
      --output src/lib/api-client \
      --client fetch
    ```
  - **Wrapper with Authentication**:
    ```typescript
    // src/lib/api-client.ts
    import { DefaultApi, Configuration } from './api-client/generated';
    
    const getAuthToken = () => localStorage.getItem('auth_token');
    
    const config = new Configuration({
      basePath: process.env.NEXT_PUBLIC_API_URL,
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    
    export const apiClient = new DefaultApi(config);
    ```
  - **React Query Integration**:
    ```typescript
    // src/hooks/useMetrics.ts
    import { useQuery } from '@tanstack/react-query';
    import { apiClient } from '@/lib/api-client';
    
    export const useMetrics = () => {
      return useQuery({
        queryKey: ['metrics'],
        queryFn: () => apiClient.getMetrics(),
        refetchInterval: 2000, // Poll every 2 seconds
      });
    };
    ```
  - **Validation**: TypeScript autocomplete works for all API methods
  - **Files**: `src/lib/api-client/`, `src/hooks/`

- [ ] **7.3 Mahabhutas Coherence Visualization** (12h)
  - **Goal**: Radial chart showing L32-L36 coherence in real-time
  - **Design Concept**: 5 concentric rings, color-coded by coherence level
    - Green (>0.8): Stable
    - Yellow (0.6-0.8): Moderate
    - Red (<0.6): Critical
  - **Implementation** (D3.js):
    ```typescript
    // src/components/dashboard/CoherenceAura.tsx
    import * as d3 from 'd3';
    import { useEffect, useRef } from 'react';
    import { useMetrics } from '@/hooks/useMetrics';
    
    export const CoherenceAura = () => {
      const svgRef = useRef<SVGSVGElement>(null);
      const { data: metrics } = useMetrics();
      
      useEffect(() => {
        if (!metrics || !svgRef.current) return;
        
        const svg = d3.select(svgRef.current);
        const width = 400, height = 400;
        const centerX = width / 2, centerY = height / 2;
        
        // Clear previous render
        svg.selectAll('*').remove();
        
        // Draw concentric circles for each layer
        const layers = ['L32', 'L33', 'L34', 'L35', 'L36'];
        layers.forEach((layer, i) => {
          const coherence = metrics.mahabhutas_coherence[layer];
          const radius = 50 + (i * 40);
          const color = coherence > 0.8 ? '#10b981' : coherence > 0.6 ? '#fbbf24' : '#ef4444';
          
          svg.append('circle')
            .attr('cx', centerX)
            .attr('cy', centerY)
            .attr('r', radius)
            .attr('fill', 'none')
            .attr('stroke', color)
            .attr('stroke-width', 8)
            .attr('opacity', coherence);
          
          // Add label
          svg.append('text')
            .attr('x', centerX)
            .attr('y', centerY - radius - 10)
            .attr('text-anchor', 'middle')
            .attr('fill', 'white')
            .text(`${layer}: ${(coherence * 100).toFixed(0)}%`);
        });
      }, [metrics]);
      
      return <svg ref={svgRef} width={400} height={400} />;
    };
    ```
  - **Animation**: Smooth transitions when coherence changes (d3.transition)
  - **Validation**: Chart updates at 2Hz (500ms), no flickering
  - **Files**: `src/components/dashboard/CoherenceAura.tsx`

- [ ] **7.4 Trading Console with Emergency Controls** (10h)
  - **Goal**: View active orders + one-click cancel all
  - **Features**:
    - Real-time order table (Symbol, Side, Qty, Filled, Status)
    - "Panic Sell" button (red, requires confirmation)
    - Portfolio summary (Total Value, P&L, Max DD)
  - **Implementation**:
    ```typescript
    // src/components/dashboard/TradingConsole.tsx
    import { useState } from 'react';
    import { Button } from '@/components/ui/button';
    import { apiClient } from '@/lib/api-client';
    import { useOrders } from '@/hooks/useOrders';
    
    export const TradingConsole = () => {
      const { data: orders } = useOrders();
      const [cancelling, setCancelling] = useState(false);
      
      const handlePanicSell = async () => {
        if (!confirm('Cancel ALL orders? This cannot be undone.')) return;
        
        setCancelling(true);
        try {
          await apiClient.cancelAllOrders();
          alert('All orders cancelled successfully');
        } catch (error) {
          alert(`Failed: ${error.message}`);
        } finally {
          setCancelling(false);
        }
      };
      
      return (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Active Orders</h2>
            <Button 
              variant="destructive" 
              onClick={handlePanicSell}
              disabled={cancelling}
            >
              {cancelling ? 'Cancelling...' : '🚨 Panic Sell'}
            </Button>
          </div>
          
          <table className="w-full">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Filled</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders?.map(order => (
                <tr key={order.order_id}>
                  <td>{order.symbol}</td>
                  <td className={order.side === 'BUY' ? 'text-green-500' : 'text-red-500'}>
                    {order.side}
                  </td>
                  <td>{order.quantity}</td>
                  <td>{order.filled_qty}</td>
                  <td>{order.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    };
    ```
  - **WebSocket for Real-Time Updates**:
    ```typescript
    // src/hooks/useOrderStream.ts
    import { useEffect, useState } from 'react';
    
    export const useOrderStream = () => {
      const [orders, setOrders] = useState([]);
      
      useEffect(() => {
        const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL);
        
        ws.onmessage = (event) => {
          const update = JSON.parse(event.data);
          setOrders(prev => {
            const index = prev.findIndex(o => o.order_id === update.order_id);
            if (index >= 0) {
              return [...prev.slice(0, index), update, ...prev.slice(index + 1)];
            }
            return [...prev, update];
          });
        };
        
        return () => ws.close();
      }, []);
      
      return orders;
    };
    ```
  - **Validation**:
    - Order appears in table <1s after submission
    - Panic button cancels all orders within 2 seconds
  - **Files**: `src/components/dashboard/TradingConsole.tsx`, `src/hooks/useOrderStream.ts`

---

## 🟪 BACKLOG: AIOps & Sustainability (P1)

### Task 8: Token Tracking & Billing
**Status**: 🔴 Not Started | **Priority**: P1 | **Estimated Effort**: 4 days

**Context**: LLM API calls are unmetered, creating risk of bill shock and negative margins.

**Current Issue**: A single tenant could exhaust monthly API budget in hours.

**Target State**: Real-time usage tracking with hard limits per tenant.

**Subtasks**:
- [ ] **8.1 Token Counter with Tiktoken** (6h)
  - **Goal**: Accurately count tokens for all LLM providers (OpenAI, Gemini, Ollama)
  - **Current State**: No token tracking in `backend/llm/providers/`
  - **Implementation**:
    ```python
    # backend/llm/usage_tracker.py
    import tiktoken
    from typing import Dict, Optional
    
    class TokenCounter:
        def __init__(self):
            self.encoders = {
                'gpt-4': tiktoken.encoding_for_model('gpt-4'),
                'gpt-3.5-turbo': tiktoken.encoding_for_model('gpt-3.5-turbo'),
                'gemini-pro': tiktoken.get_encoding('cl100k_base'),  # Approximate
            }
        
        def count_tokens(self, text: str, model: str) -> int:
            encoder = self.encoders.get(model)
            if not encoder:
                # Fallback: estimate 1 token = 4 characters
                return len(text) // 4
            return len(encoder.encode(text))
        
        def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
            # Pricing as of Feb 2026 (update periodically)
            pricing = {
                'gpt-4': {'prompt': 0.03 / 1000, 'completion': 0.06 / 1000},
                'gpt-3.5-turbo': {'prompt': 0.0015 / 1000, 'completion': 0.002 / 1000},
                'gemini-1.5-pro': {'prompt': 0.00125 / 1000, 'completion': 0.005 / 1000},
            }
            
            if model not in pricing:
                return 0.0  # Free models (Ollama)
            
            return (
                prompt_tokens * pricing[model]['prompt'] +
                completion_tokens * pricing[model]['completion']
            )
    ```
  - **Integration**: Wrap all `provider.generate()` calls
    ```python
    # backend/llm/service.py
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        token_counter = TokenCounter()
        prompt_tokens = token_counter.count_tokens(prompt, model)
        
        response = await self.provider.generate(prompt, model)
        completion_tokens = token_counter.count_tokens(response.text, model)
        
        cost = token_counter.calculate_cost(prompt_tokens, completion_tokens, model)
        
        # Log usage (Task 8.2)
        await self.usage_tracker.log_usage(
            tenant_id=get_current_tenant(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost
        )
        
        return response
    ```
  - **Validation**: 
    - GPT-4 100-token prompt = $0.003 (manual calculation matches)
    - Gemini tokens counted within 5% of official API count
  - **Files**: `backend/llm/usage_tracker.py`
  - **Dependencies**: Add `tiktoken==0.5.2` to requirements

- [ ] **8.2 Async Buffer for Usage Logging** (6h)
  - **Goal**: Batch write token usage to ClickHouse to avoid query overhead
  - **Current State**: No usage logging table
  - **Database Schema** (add to migrations):
    ```sql
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
    ```
  - **Buffer Implementation**:
    ```python
    # backend/llm/usage_tracker.py
    from collections import deque
    import asyncio
    
    class UsageTracker:
        def __init__(self, clickhouse: ClickHouseClient, batch_size: int = 100, flush_interval: int = 5):
            self.clickhouse = clickhouse
            self.buffer = deque(maxlen=1000)
            self.batch_size = batch_size
            self.flush_interval = flush_interval
            self._flush_task = None
        
        async def start(self):
            self._flush_task = asyncio.create_task(self._periodic_flush())
        
        async def log_usage(self, tenant_id: str, model: str, prompt_tokens: int, 
                           completion_tokens: int, cost_usd: float):
            self.buffer.append({
                'tenant_id': tenant_id,
                'timestamp': datetime.now(timezone.utc),
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'cost_usd': cost_usd,
                'agent_name': 'unknown',  # TODO: extract from context
                'request_id': str(uuid.uuid4()),
            })
            
            if len(self.buffer) >= self.batch_size:
                await self._flush()
        
        async def _periodic_flush(self):
            while True:
                await asyncio.sleep(self.flush_interval)
                await self._flush()
        
        async def _flush(self):
            if not self.buffer:
                return
            
            batch = [self.buffer.popleft() for _ in range(min(len(self.buffer), self.batch_size))]
            await self.clickhouse.insert('llm_usage_logs', batch)
    ```
  - **Validation**:
    - 100 log calls result in 1 database insert (check query logs)
    - No data loss on graceful shutdown (flush on SIGTERM)
  - **Files**: `backend/llm/usage_tracker.py`, `backend/storage/migrations/003_llm_usage.sql`

- [ ] **8.3 Quota Enforcement in Orchestrator** (6h)
  - **Goal**: Block agent execution when tenant exceeds daily budget
  - **Current State**: `CognitiveOrchestrator` has no budget checks
  - **Implementation**:
    ```python
    # backend/services/cognitive_orchestrator.py
    class CognitiveOrchestrator:
        async def handle_message(self, message: AgentMessage):
            tenant_id = message.tenant_id
            
            # Check quota before processing
            usage_today = await self._get_daily_usage(tenant_id)
            quota = await self._get_tenant_quota(tenant_id)
            
            if usage_today >= quota:
                logger.warning(f"Tenant {tenant_id} exceeded quota: {usage_today:.2f}/{quota:.2f} USD")
                raise QuotaExceededError(
                    f"Daily LLM budget exceeded. Used ${usage_today:.2f} of ${quota:.2f}"
                )
            
            # Continue with normal processing
            await self._route_message(message)
        
        async def _get_daily_usage(self, tenant_id: str) -> float:
            query = f"""
                SELECT sum(cost_usd) as total_cost
                FROM llm_usage_logs
                WHERE tenant_id = '{tenant_id}'
                  AND timestamp >= today()
            """
            result = await self.clickhouse.query(query)
            return result[0]['total_cost'] if result else 0.0
        
        async def _get_tenant_quota(self, tenant_id: str) -> float:
            # Fetch from tenant configuration (hardcoded for MVP)
            tier_quotas = {
                'free': 1.0,      # $1/day
                'starter': 10.0,  # $10/day
                'pro': 100.0,     # $100/day
            }
            # TODO: Query tenant tier from database
            return tier_quotas.get('starter', 10.0)
    ```
  - **User Experience**: Return HTTP 429 with `Retry-After` header
  - **Dashboard Integration**: Show usage meter in frontend (75% → yellow, 90% → red)
  - **Validation**:
    - Tenant with $9.95 usage can make 1 more $0.05 request
    - Next request after exceeding quota returns 429
  - **Files**: `backend/services/cognitive_orchestrator.py`

---

## 🟥 BACKLOG: Governance (P2)

### Task 9: Audit & Explainability
**Status**: 🔴 Not Started | **Priority**: P2 | **Estimated Effort**: 5 days

**Context**: Regulatory requirement (MiFID II) to explain every algorithmic trading decision.

**Business Impact**: Cannot operate in EU markets without audit trail.

**Current Gap**: Agent decisions are not logged with reasoning.

**Target Compliance**: Full "Explainable AI" audit trail for all trades.

**Subtasks**:
- [ ] **9.1 Audit Logger Service** (8h)
  - **Goal**: Immutable logging of all system actions to `audit_trail` table
  - **Current State**: Schema exists in `multi_tenant_schema.sql` but unused
  - **Schema Reminder**:
    ```sql
    CREATE TABLE IF NOT EXISTS audit_trail (
        tenant_id UUID,
        audit_id UUID,
        timestamp DateTime,
        user_id String,
        action String,
        resource_type String,
        resource_id String,
        old_value String,
        new_value String,
        ip_address String,
        user_agent String
    ) ENGINE = ReplacingMergeTree()
    ORDER BY (tenant_id, timestamp);
    ```
  - **Implementation**:
    ```python
    # backend/core/compliance/audit_logger.py
    from typing import Optional, Dict, Any
    import json
    
    class AuditLogger:
        def __init__(self, clickhouse: ClickHouseClient):
            self.clickhouse = clickhouse
        
        async def log_action(
            self,
            tenant_id: str,
            user_id: str,
            action: str,
            resource_type: str,
            resource_id: str,
            old_value: Optional[Dict] = None,
            new_value: Optional[Dict] = None,
            metadata: Optional[Dict] = None
        ):
            await self.clickhouse.insert('audit_trail', [{
                'tenant_id': tenant_id,
                'audit_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc),
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'old_value': json.dumps(old_value) if old_value else '',
                'new_value': json.dumps(new_value) if new_value else '',
                'ip_address': metadata.get('ip') if metadata else '',
                'user_agent': metadata.get('user_agent') if metadata else '',
            }])
    ```
  - **Usage Decorator**:
    ```python
    def audit_decision(action: str, resource_type: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                tenant_id = get_current_tenant()
                result = await func(*args, **kwargs)
                
                await audit_logger.log_action(
                    tenant_id=tenant_id,
                    user_id='system',  # Or extract from context
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(result.get('order_id', 'unknown')),
                    new_value=result
                )
                
                return result
            return wrapper
        return decorator
    
    # Usage
    @audit_decision('ORDER_SUBMITTED', 'trading_order')
    async def submit_order(order: OrderRequest):
        return await exchange.submit_order(order)
    ```
  - **Validation**:
    - Every order submission creates audit log
    - Audit logs are immutable (ReplacingMergeTree prevents updates)
  - **Files**: `backend/core/compliance/audit_logger.py`

- [ ] **9.2 Agent Reasoning Capture** (10h)
  - **Goal**: Store full chain-of-thought for LLM-based decisions
  - **Current State**: Agents return decisions but not reasoning
  - **Schema Addition**:
    ```sql
    CREATE TABLE IF NOT EXISTS agent_decision_logs (
        tenant_id UUID,
        decision_id UUID,
        timestamp DateTime,
        agent_name String,
        decision_type String,  -- 'TRADE', 'RISK_BLOCK', 'SENTIMENT_SHIFT'
        input_context String,  -- Full prompt sent to LLM
        llm_response String,   -- Raw LLM output
        final_decision String, -- Structured decision JSON
        confidence Float64,
        execution_time_ms UInt32
    ) ENGINE = MergeTree()
    ORDER BY (tenant_id, timestamp)
    PARTITION BY toYYYYMM(timestamp);
    ```
  - **Implementation in SentimentAgent**:
    ```python
    # backend/agents/sentiment_agent.py
    class SentimentAgent:
        async def analyze_sentiment(self, news_articles: List[str]) -> SentimentDecision:
            tenant_id = get_current_tenant()
            start_time = time.time()
            
            # Build LLM prompt
            prompt = self._build_prompt(news_articles)
            
            # Call LLM
            llm_response = await self.llm_service.generate(prompt, model='gemini-1.5-pro')
            
            # Parse decision
            decision = self._parse_response(llm_response.text)
            
            # Log reasoning
            await self.clickhouse.insert('agent_decision_logs', [{
                'tenant_id': tenant_id,
                'decision_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc),
                'agent_name': 'SentimentAgent',
                'decision_type': 'SENTIMENT_SHIFT',
                'input_context': prompt,
                'llm_response': llm_response.text,
                'final_decision': json.dumps(decision.__dict__),
                'confidence': decision.confidence,
                'execution_time_ms': int((time.time() - start_time) * 1000),
            }])
            
            return decision
    ```
  - **Privacy Consideration**: Truncate PII from logs (mask account numbers)
  - **Validation**:
    - Every agent decision has corresponding log entry
    - Logs include full prompt + response (audit-ready)
  - **Files**: `backend/agents/sentiment_agent.py`, `backend/agents/base_agent.py`, migration file

- [ ] **9.3 MiFID II Compliance Export** (8h)
  - **Goal**: API endpoint to generate regulatory reports
  - **Current State**: No export functionality
  - **Report Contents**:
    - All trades in date range
    - Agent decisions leading to each trade
    - Risk checks applied
    - User actions (manual overrides)
  - **Implementation**:
    ```python
    # backend/api/gateway.py
    from fastapi.responses import StreamingResponse
    import zipfile
    import io
    
    @app.get('/api/compliance/report')
    async def export_compliance_report(
        start_date: date,
        end_date: date,
        tenant_id: str = Depends(get_current_tenant)
    ) -> StreamingResponse:
        # Fetch data from multiple tables
        trades = await clickhouse.query(f"""
            SELECT * FROM execution_logs
            WHERE tenant_id = '{tenant_id}'
              AND timestamp BETWEEN '{start_date}' AND '{end_date}'
        """)
        
        decisions = await clickhouse.query(f"""
            SELECT * FROM agent_decision_logs
            WHERE tenant_id = '{tenant_id}'
              AND timestamp BETWEEN '{start_date}' AND '{end_date}'
        """)
        
        audits = await clickhouse.query(f"""
            SELECT * FROM audit_trail
            WHERE tenant_id = '{tenant_id}'
              AND timestamp BETWEEN '{start_date}' AND '{end_date}'
        """)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add CSV files
            zip_file.writestr('trades.csv', _to_csv(trades))
            zip_file.writestr('agent_decisions.csv', _to_csv(decisions))
            zip_file.writestr('audit_trail.csv', _to_csv(audits))
            
            # Add metadata
            metadata = {
                'report_generated': datetime.now(timezone.utc).isoformat(),
                'tenant_id': tenant_id,
                'date_range': f'{start_date} to {end_date}',
                'total_trades': len(trades),
            }
            zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
        
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type='application/zip',
            headers={'Content-Disposition': f'attachment; filename=compliance_{start_date}_{end_date}.zip'}
        )
    ```
  - **Access Control**: Only users with 'admin' role can export
  - **Rate Limiting**: Max 1 export per 10 minutes (expensive query)
  - **Validation**:
    - ZIP contains 4 files (3 CSVs + metadata)
    - Trade CSV matches manual SQL query
  - **Files**: `backend/api/gateway.py`

---

## 📅 Suggested Sprint Cycles

| Sprint | Goal | Tasks |
| :--- | :--- | :--- |
| **Sprint 1** | Security & Auth Foundations | 3, 4 |
| **Sprint 2** | Production Infrastructure | 1, 2 |
| **Sprint 3** | Trading & Simulation | 5, 6 |
| **Sprint 4** | Dashboard & UI MVP | 7 |
| **Sprint 5** | Billing & Audit | 8, 9 |
