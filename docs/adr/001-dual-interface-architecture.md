# ADR 001: Dual Interface Architecture (REST + MCP)

## Status
Accepted

## Context

The Agentic Trader Platform needs to serve two distinct user personas:

1. **Web Dashboard Users**: Human traders using a React frontend
2. **AI Assistant Users**: Claude Desktop users leveraging AI for trading analysis

Additionally, internal backtests and batch processes need direct Python access without HTTP overhead.

## Decision

We will implement a **Dual Interface Architecture** with three access patterns:

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTIC TRADER PLATFORM                  │
├─────────────────┬──────────────────┬────────────────────────┤
│   LLM/AI Users  │  SaaS Dashboard  │   Internal/Batch       │
│   (Claude MCP)  │   (REST API)     │   (Direct Import)      │
├─────────────────┼──────────────────┼────────────────────────┤
│  MCP stdio      │  HTTP/REST       │  Python import         │
│  AI tools       │  JWT auth        │  Direct function call  │
│  Natural lang   │  WebSocket       │  No serialization      │
└─────────────────┴──────────────────┴────────────────────────┘
```

### REST API (FastAPI)
- **Use case**: Web dashboard, mobile apps, third-party integrations
- **Protocol**: HTTP/REST with OpenAPI docs
- **Auth**: JWT tokens (Auth0)
- **Transport**: HTTPS/WSS

### MCP Server (FastMCP)
- **Use case**: Claude Desktop, AI assistants
- **Protocol**: Model Context Protocol (stdio)
- **Auth**: Implicit (runs locally)
- **Transport**: Standard input/output

### Direct Import
- **Use case**: Internal backtests, batch jobs, unit tests
- **Protocol**: Python module import
- **Auth**: N/A (same process)
- **Transport**: Direct function calls

## Consequences

### Positive
- **Optimized for each use case**: REST for browser, MCP for AI, direct for performance
- **No overhead for backtests**: Direct imports avoid HTTP serialization
- **Clean separation**: Each interface has its own auth and validation
- **AI-native**: MCP provides structured tools for LLM agents

### Negative
- **Duplicated routing logic**: Endpoints defined in both FastAPI and MCP
- **Multiple auth mechanisms**: JWT (REST), implicit (MCP), none (direct)
- **Documentation overhead**: Must document all three interfaces
- **Testing complexity**: Need to test each interface separately

### Mitigation
- Shared service layer implements business logic once
- Service layer is interface-agnostic
- Automated testing covers all three interfaces

## Related Decisions
- ADR 003: Python 3.13 with asyncio
- ADR 004: Auth0 for Authentication

## References
- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
