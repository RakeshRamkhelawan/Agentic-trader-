# C4 Architecture Documentation

> Complete architectural overview using the C4 model

---

## What is the C4 Model?

The C4 model provides a structured approach to visualizing software architecture through four levels of abstraction:

| Level | Name | Description | Audience |
|-------|------|-------------|----------|
| 1 | Context | System interactions with users and external systems | Non-technical stakeholders |
| 2 | Container | Applications, databases, and their interactions | Technical stakeholders |
| 3 | Component | Internal structure of key containers | Development team |
| 4 | Code | Implementation details, patterns, and examples | Engineers |

---

## Diagrams

### [Level 1: System Context](./01_CONTEXT.md)
Shows the Agentic Trader Platform in context of users and external systems.

**Key Elements:**
- Retail Trader (end user)
- Platform Admin (administrator)
- Claude Desktop User (AI assistant user)
- External systems: Auth0, Bitvavo, Revolut, DeepSeek, Redis, ClickHouse

### [Level 2: Container Diagram](./02_CONTAINER.md)
Shows the deployable units (containers) that make up the system.

**Key Elements:**
- Single Page Application (React)
- API Gateway (FastAPI)
- MCP Server (FastMCP)
- Background Workers (Celery)
- Data stores: PostgreSQL, ClickHouse, Redis, ChromaDB

### [Level 3: Component Diagram](./03_COMPONENT.md)
Shows internal components of the API Gateway container.

**Key Elements:**
- API Layer: Router, Middleware, Validators
- Service Layer: Trading, Backtest, Risk, VedAstro services
- Core Layer: Config, Database, Cache, EventBus
- Adapter Layer: External API clients

### [Level 4: Code](./04_CODE.md)
Shows implementation details of critical components.

**Key Elements:**
- JWT Token validation
- Row-Level Security (RLS)
- Trading service workflow
- Backtest engine
- WebSocket manager
- MCP tool implementation

---

## Quick Navigation

| If you want to understand... | Go to |
|------------------------------|-------|
| Who uses the system | [Level 1: Context](./01_CONTEXT.md) |
| What technologies we use | [Level 2: Container](./02_CONTAINER.md) |
| How components interact | [Level 3: Component](./03_COMPONENT.md) |
| Implementation patterns | [Level 4: Code](./04_CODE.md) |

---

## Architecture Principles

1. **Security First**: All data access through RLS, JWT authentication
2. **Async Throughout**: Python asyncio, FastAPI async endpoints
3. **Multi-tenant**: Complete tenant isolation at database level
4. **Dual Interface**: REST API for web, MCP for AI assistants
5. **Event-Driven**: Real-time updates via WebSocket and Redis pub/sub

---

## For Engineers

**New to the codebase?** Start here:
1. Read [Level 1: Context](./01_CONTEXT.md) - Understand the system
2. Read [Level 2: Container](./02_CONTAINER.md) - Learn the tech stack
3. Read [Level 3: Component](./03_COMPONENT.md) - Understand the architecture
4. Set up local environment: [DEVELOPMENT.md](../../engineering/DEVELOPMENT.md)

---

## For Due Diligence / Acquisition

This documentation package provides:
- Complete system architecture overview
- Technology stack inventory
- Security implementation details
- Code organization and patterns
- Integration points and dependencies

See also:
- [Architecture Decision Records](../../adr/)
- [Engineering Handbook](../../engineering/)
