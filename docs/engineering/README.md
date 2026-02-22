# Engineering Documentation

> Technical resources for the engineering team

---

## Documentation Index

### Getting Started

| Document | Purpose |
|----------|---------|
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Complete onboarding guide for new engineers |
| [TECHNICAL_DUE_DILIGENCE.md](./TECHNICAL_DUE_DILIGENCE.md) | Acquisition/exit documentation |

### Architecture

See [Architecture Documentation](../architecture/)

- [C4 Model](../architecture/c4/) - System architecture at 4 levels
- [ADRs](../adr/) - Architecture Decision Records

### Infrastructure

See [Infrastructure Documentation](../infrastructure/)

- [HTTPS/SSL Setup](../infrastructure/HTTPS_SSL_SETUP.md)
- [WebSocket Implementation](../websockets/)

---

## Quick Reference

### Start Development

```bash
# 1. Clone and setup
git clone <repo>
cp .env.example .env
cp frontend/.env.example frontend/.env

# 2. Start infrastructure
docker-compose up -d postgres redis clickhouse chromadb

# 3. Install dependencies
pip install -r requirements/dev.txt
cd frontend && npm install

# 4. Start servers
uvicorn backend.api.main:app --reload --port 8000
npm run dev  # (in frontend/)
```

### Key Commands

| Task | Command |
|------|---------|
| Run tests | `pytest backend/tests/ -v` |
| Database migration | `alembic revision --autogenerate -m "desc"` |
| Format code | `black backend/ && ruff check backend/` |
| Frontend lint | `cd frontend && npm run lint` |
| API docs | `http://localhost:8000/docs` |

---

## For New Engineers

1. **Read** [DEVELOPMENT.md](./DEVELOPMENT.md) - Complete setup guide
2. **Review** [C4 Architecture](../architecture/c4/) - Understand the system
3. **Check** [ADRs](../adr/) - Know why decisions were made
4. **Start** with a "good first issue"

---

## For Due Diligence / Acquisition

See [TECHNICAL_DUE_DILIGENCE.md](./TECHNICAL_DUE_DILIGENCE.md) for:
- System overview and IP assessment
- Code quality metrics
- Scalability analysis
- Security posture
- Team knowledge transfer plan

---

## Contributing

To add engineering documentation:
1. Create `.md` file in appropriate `docs/` subdirectory
2. Update this README with link
3. Submit PR for review
