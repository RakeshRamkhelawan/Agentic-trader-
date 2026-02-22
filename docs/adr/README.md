# Architecture Decision Records (ADRs)

> Documenting significant architectural decisions and their rationale

---

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help teams understand:

- **Why** a decision was made
- **What** alternatives were considered
- **What** the consequences are

---

## ADR Index

| # | Title | Status | Date |
|---|-------|--------|------|
| [001](001-dual-interface-architecture.md) | Dual Interface Architecture (REST + MCP) | Accepted | 2026-02 |
| [002](002-multi-tenancy-with-rls.md) | Multi-Tenancy with PostgreSQL RLS | Accepted | 2026-02 |
| [003](003-python-asyncio.md) | Python 3.13 with Asyncio Throughout | Accepted | 2026-02 |
| [004](004-websocket-realtime.md) | WebSocket for Real-Time Data | Accepted | 2026-02 |
| [005](005-ai-llm-integration.md) | AI/LLM Integration Strategy | Accepted | 2026-02 |

---

## ADR Template

When creating a new ADR, use this template:

```markdown
# ADR XXX: Title

## Status
- Proposed
- Accepted
- Deprecated
- Superseded by ADR YYY

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing or have agreed to implement?

## Consequences
What becomes easier or more difficult to do because of this change?

### Positive
- Benefit 1
- Benefit 2

### Negative
- Trade-off 1
- Trade-off 2

## Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| Option A | ... | ... |
| Option B | ... | ... |

## Related Decisions
- Links to related ADRs

## References
- External documentation
```

---

## Decision Categories

### Architectural Patterns
- [ADR 001: Dual Interface](001-dual-interface-architecture.md)
- [ADR 004: WebSocket](004-websocket-realtime.md)

### Data & Security
- [ADR 002: Multi-Tenancy](002-multi-tenancy-with-rls.md)

### Technology Stack
- [ADR 003: Python Asyncio](003-python-asyncio.md)
- [ADR 005: AI/LLM](005-ai-llm-integration.md)

---

## For Due Diligence

These ADRs provide insight into:

1. **Technical Maturity**: Documented decision-making process
2. **Architecture Rationale**: Understanding why certain choices were made
3. **Trade-offs**: Awareness of limitations and compromises
4. **Evolution Path**: How the architecture can adapt

---

## Contributing

To propose a new ADR:

1. Copy the template above
2. Create `docs/adr/XXX-title.md`
3. Submit PR for team review
4. Update this index

---

## References
- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
