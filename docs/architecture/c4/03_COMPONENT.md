# C4 Architecture - Level 3: Component Diagram

> Component-level view showing internal structure of key containers

---

## Overview

This diagram drills into the Backend API Gateway container, showing its internal components and their responsibilities.

---

## API Gateway Component Diagram

```mermaid
flowchart TB
    subgraph External["External"]
        WebApp["Web Application"]
        AdminPanel["Admin Panel"]
        Workers["Background Workers"]
    end

    subgraph APIGateway["API Gateway Container<br/>FastAPI Application"]
        subgraph API["API Layer"]
            Router["Router<br/>FastAPI APIRouter<br/>Endpoint definitions"]
            Middleware["Middleware Stack<br/>CORS, Auth, Rate Limit, Logging"]
            Validator["Pydantic Validators<br/>Request/Response models"]
        end

        subgraph Services["Service Layer"]
            AuthService["AuthService<br/>JWT, Auth0 integration"]
            TradingService["TradingService<br/>Order management, execution"]
            BacktestService["BacktestService<br/>Strategy simulation"]
            MarketDataService["MarketDataService<br/>Price feeds, orderbook"]
            RiskService["RiskService<br/>VaR, position limits"]
            VedAstroService["VedAstroService<br/>Astrological analysis"]
            ElementalService["ElementalService<br/>Elemental consensus"]
        end

        subgraph Core["Core Layer"]
            Config["Config<br/>Pydantic Settings<br/>Environment management"]
            Database["Database<br/>SQLAlchemy + asyncpg<br/>Connection pooling"]
            Cache["Cache<br/>Redis client<br/>Session & data cache"]
            EventBus["EventBus<br/>Redis Streams<br/>Pub/Sub events"]
            Logger["Telemetry<br/>OpenTelemetry + Prometheus<br/>Metrics & tracing"]
        end

        subgraph Adapters["Adapter Layer"]
            BitvavoClient["BitvavoClient<br/>Exchange adapter"]
            RevolutClient["RevolutClient<br/>Banking adapter"]
            DeepSeekClient["DeepSeekClient<br/>LLM adapter"]
            MCPClient["MCPClient<br/>MCP tool caller"]
        end

        subgraph Security["Security Layer"]
            JWTHandler["JWTHandler<br/>Token validation"]
            RLS["RLS Enforcer<br/>Row-level security"]
            AuditLogger["AuditLogger<br/>Compliance logging"]
        end
    end

    subgraph DataStores["Data Stores"]
        PostgreSQL[(PostgreSQL)]
        Redis[(Redis)]
        ClickHouse[(ClickHouse)]
    end

    subgraph ExternalAPIs["External APIs"]
        Bitvavo["Bitvavo"]
        Revolut["Revolut"]
        DeepSeek["DeepSeek"]
    end

    %% External to API
    WebApp -->|"HTTP/WSS<br/>Authenticated"| Middleware
    AdminPanel -->|"HTTP<br/>Admin JWT"| Middleware
    Workers -->|"HTTP<br/>Service token"| Middleware

    %% API to Services
    Middleware -->|"Validate + Route"| Router
    Router -->|"Dispatch"| AuthService
    Router -->|"Dispatch"| TradingService
    Router -->|"Dispatch"| BacktestService
    Router -->|"Dispatch"| MarketDataService
    Router -->|"Dispatch"| RiskService
    Router -->|"Dispatch"| VedAstroService
    Router -->|"Dispatch"| ElementalService

    %% Services to Core
    AuthService -->|"Uses"| JWTHandler
    AuthService -->|"Uses"| Config

    TradingService -->|"Uses"| Database
    TradingService -->|"Uses"| Cache
    TradingService -->|"Uses"| BitvavoClient
    TradingService -->|"Uses"| RiskService
    TradingService -->|"Uses"| RLS
    TradingService -->|"Emits"| EventBus

    BacktestService -->|"Uses"| Database
    BacktestService -->|"Uses"| Cache
    BacktestService -->|"Uses"| MarketDataService

    MarketDataService -->|"Uses"| Cache
    MarketDataService -->|"Uses"| BitvavoClient

    RiskService -->|"Uses"| Database
    RiskService -->|"Uses"| Cache

    VedAstroService -->|"Uses"| Cache
    VedAstroService -->|"Uses"| DeepSeekClient

    ElementalService -->|"Uses"| VedAstroService
    ElementalService -->|"Uses"| MarketDataService

    %% Core to Data Stores
    Database -->|"SQL<br/>Async"| PostgreSQL
    Cache -->|"Redis Protocol<br/>Async"| Redis
    EventBus -->|"Redis Streams"| Redis
    Logger -->|"HTTP"| ClickHouse

    %% Adapters to External
    BitvavoClient -->|"REST + WS"| Bitvavo
    RevolutClient -->|"REST<br/>OAuth"| Revolut
    DeepSeekClient -->|"HTTP<br/>API Key"| DeepSeek

    %% Security
    JWTHandler -->|"Token decode"| Config
    RLS -->|"Policy check"| Database
    TradingService -->|"Log"| AuditLogger
    AuditLogger -->|"Write"| ClickHouse
```

---

## Component Responsibilities

### API Layer

| Component | Responsibility | Key Technologies |
|-----------|----------------|------------------|
| Router | Route HTTP requests to appropriate handlers | FastAPI APIRouter |
| Middleware | Cross-cutting concerns (auth, CORS, rate limiting) | FastAPI Middleware |
| Validator | Request validation, serialization | Pydantic v2 |

### Service Layer

| Component | Responsibility | Dependencies |
|-----------|----------------|--------------|
| AuthService | User authentication, token management | JWTHandler, Config |
| TradingService | Order lifecycle management, execution | BitvavoClient, RiskService, RLS |
| BacktestService | Historical simulation, strategy testing | MarketDataService, Database |
| MarketDataService | Real-time price feeds, orderbook | BitvavoClient, Cache |
| RiskService | Risk calculations, limits enforcement | Database, Cache |
| VedAstroService | Astrological analysis, timing | DeepSeekClient, Cache |
| ElementalService | Multi-factor consensus scoring | VedAstroService, MarketDataService |

### Core Layer

| Component | Responsibility | Key Technologies |
|-----------|----------------|------------------|
| Config | Environment variables, settings | Pydantic Settings |
| Database | Database connections, ORM | SQLAlchemy 2.0, asyncpg |
| Cache | Caching layer, session store | redis-py |
| EventBus | Event streaming, pub/sub | Redis Streams |
| Logger | Observability, metrics | OpenTelemetry, Prometheus |

### Adapter Layer

| Component | Responsibility | Protocol |
|-----------|----------------|----------|
| BitvavoClient | Exchange integration | REST + WebSocket |
| RevolutClient | Banking integration | REST API |
| DeepSeekClient | AI/LLM integration | HTTP API |
| MCPClient | MCP tool execution | stdio |

### Security Layer

| Component | Responsibility | Standards |
|-----------|----------------|-----------|
| JWTHandler | Token validation, claims extraction | RS256, JWKS |
| RLS | Row-level security enforcement | PostgreSQL RLS |
| AuditLogger | Compliance audit trails | MiFID II, GDPR |

---

## Component Interactions

### Trade Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant Middleware
    participant TradingService
    participant RiskService
    participant BitvavoClient
    participant Database
    participant EventBus

    Client->>Middleware: POST /api/v1/orders
    Middleware->>Middleware: Validate JWT
    Middleware->>Router: Route to handler
    Router->>TradingService: create_order(order_data)

    TradingService->>RiskService: check_risk_limits(order)
    RiskService-->>TradingService: approved / rejected

    alt Risk check passed
        TradingService->>BitvavoClient: place_order(order)
        BitvavoClient-->>TradingService: order confirmation
        TradingService->>Database: save_order(order)
        TradingService->>EventBus: publish(order_executed)
        TradingService-->>Router: order_response
        Router-->>Middleware: response
        Middleware-->>Client: 201 Created
    else Risk check failed
        TradingService-->>Router: risk_error
        Router-->>Middleware: error_response
        Middleware-->>Client: 400 Bad Request
    end
```

### Backtest Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant BacktestService
    participant MarketDataService
    participant ElementalService
    participant VedAstroService
    participant Cache
    participant Database

    Client->>Router: POST /api/v1/backtest/run
    Router->>BacktestService: run_backtest(config)

    BacktestService->>MarketDataService: get_historical_data(symbol, range)
    MarketDataService->>Cache: check_cache(key)

    alt Cache miss
        MarketDataService-->>BacktestService: fetch_from_exchange()
        MarketDataService->>Cache: store_data()
    else Cache hit
        Cache-->>MarketDataService: cached_data
    end

    MarketDataService-->>BacktestService: historical_data

    BacktestService->>ElementalService: calculate_signals(data)
    ElementalService->>VedAstroService: get_astrological_context(date)
    VedAstroService-->>ElementalService: astro_data
    ElementalService-->>BacktestService: consensus_signals

    BacktestService->>BacktestService: simulate_trades()
    BacktestService->>Database: save_results()
    BacktestService-->>Router: backtest_results
    Router-->>Client: 200 OK + results
```

---

## MCP Server Component Diagram

```mermaid
flowchart TB
    subgraph Claude["Claude Desktop"]
        MCPClient["MCP Client"]
    end

    subgraph MCPServerContainer["MCP Server Container"]
        Transport["Transport Layer<br/>stdio/stdout"]

        subgraph Tools["Tool Registry"]
            BacktestTool["Backtest Tool<br/>Run backtests"]
            VedAstroTool["VedAstro Tool<br/>Astrological analysis"]
            ElementalTool["Elemental Tool<br/>Elemental consensus"]
            MarketDataTool["MarketData Tool<br/>Price queries"]
            TradingTool["Trading Tool<br/>Order management"]
        end

        subgraph Execution["Execution Layer"]
            ToolExecutor["Tool Executor<br/>Async execution"]
            ErrorHandler["Error Handler<br/>Graceful degradation"]
            Logger["Logger<br/>Structured logging"]
        end

        subgraph InternalAPI["Internal API"]
            ServiceBridge["Service Bridge<br/>Import backend.services"]
        end
    end

    subgraph BackendServices["Backend Services"]
        BacktestService["BacktestService"]
        VedAstroService["VedAstroService"]
        MarketDataService["MarketDataService"]
        TradingService["TradingService"]
    end

    %% Flow
    MCPClient -->|"JSON-RPC<br/>stdio"| Transport
    Transport -->|"Parse requests"| ToolExecutor

    ToolExecutor -->|"Dispatch"| BacktestTool
    ToolExecutor -->|"Dispatch"| VedAstroTool
    ToolExecutor -->|"Dispatch"| ElementalTool
    ToolExecutor -->|"Dispatch"| MarketDataTool
    ToolExecutor -->|"Dispatch"| TradingTool

    BacktestTool -->|"Calls"| ServiceBridge
    VedAstroTool -->|"Calls"| ServiceBridge
    ElementalTool -->|"Calls"| ServiceBridge
    MarketDataTool -->|"Calls"| ServiceBridge
    TradingTool -->|"Calls"| ServiceBridge

    ServiceBridge -->|"Direct import"| BacktestService
    ServiceBridge -->|"Direct import"| VedAstroService
    ServiceBridge -->|"Direct import"| MarketDataService
    ServiceBridge -->|"Direct import"| TradingService

    ToolExecutor -->|"On error"| ErrorHandler
    ToolExecutor -->|"Log"| Logger
```

---

## File Structure Mapping

```
backend/
├── api/
│   ├── routers/              # Router components
│   │   ├── backtest.py
│   │   ├── trading.py
│   │   └── health.py
│   ├── middleware/           # Middleware components
│   │   ├── auth.py
│   │   ├── rate_limit.py
│   │   └── logging.py
│   ├── websocket_endpoints.py
│   └── main.py               # FastAPI app factory
│
├── services/                 # Service layer
│   ├── auth_service.py
│   ├── trading_service.py
│   ├── backtest_service.py
│   ├── market_data_service.py
│   ├── risk_service.py
│   └── consensus/
│       ├── vedastro_service.py
│       └── elemental_service.py
│
├── core/                     # Core layer
│   ├── config/
│   │   └── settings.py       # Config component
│   ├── database/
│   │   └── session.py        # Database component
│   ├── cache/
│   │   └── redis_client.py   # Cache component
│   ├── events/
│   │   └── event_bus.py      # EventBus component
│   └── telemetry/
│       ├── metrics.py        # Logger component
│       └── tracing.py
│
├── adapters/                 # Adapter layer
│   ├── bitvavo_client.py
│   ├── revolut_client.py
│   └── deepseek_client.py
│
├── security/                 # Security layer
│   ├── jwt_handler.py
│   ├── rls.py
│   └── audit.py
│
└── mcp_server/               # MCP Server
    ├── server.py             # Transport layer
    ├── tools/                # Tool registry
    │   ├── backtest_tool.py
    │   ├── vedastro_tool.py
    │   └── ...
    └── bridge.py             # ServiceBridge
```

---

## Related Documentation

- [Level 2: Container](./02_CONTAINER.md)
- [Level 4: Code](./04_CODE.md)
- [Architecture Decision Records](../../adr/)
- [API Documentation](../../api/)
