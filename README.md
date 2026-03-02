<div align="center">

# 🤖 Agentic Trader Platform

**AI-Powered Multi-Agent Trading System with Vedic Intelligence**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg?logo=react)](https://react.dev)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-734+-success.svg)](docs/TESTING.md)
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen.svg)](docs/TESTING.md)
[![Security](https://img.shields.io/badge/security-88%2F100-brightgreen.svg)](docs/SECURITY_RUNBOOK.md)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg?logo=docker)](DOCKER.md)

[🚀 Quick Start](#quick-start) • [📚 Documentation](#documentation) • [🧪 Testing](#testing) • [🔒 Security](#security) • [🤝 Contributing](#contributing)

</div>

---

## 🌟 Overview

**Agentic Trader Platform** is a production-grade, AI-powered trading system that combines modern financial technology with ancient Vedic intelligence principles. Built with enterprise-grade architecture, it features a multi-agent cognitive system with ReAct reasoning patterns, advanced risk management, and real-time trade execution.

### ✨ Key Features

- 🤖 **Multi-Agent AI System** - ReAct reasoning with specialized agents (Research, Risk, Portfolio, Execution)
- 🧠 **Vedic Intelligence** - Unique consciousness-inspired architecture (Samkhya philosophy)
- 📊 **Advanced Risk Management** - VaR calculations, stress testing, Kelly criterion optimization
- ⚡ **Real-time Execution** - Smart order routing with <10ms latency
- 🔒 **Enterprise Security** - JWT RS256, multi-tenant RLS, Vault integration
- 📈 **Paper Trading** - Risk-free testing environment with real market data
- 🏗️ **Microservices Architecture** - Docker, Kubernetes, Redis, ClickHouse, PostgreSQL

### 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  AI AGENTS (ReAct Pattern)                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Research │ │   Risk   │ │Portfolio │ │ Execution│           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       └─────────────┴─────────────┴─────────────┘               │
├─────────────────────────────────────────────────────────────────┤
│  CONSCIOUSNESS LAYERS (Samkhya-Inspired)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Eternal Soul │ │Cognitive Mind│ │ Reflex Body  │            │
│  │  (Cosmic)    │ │ (Decisions)  │ │ (Execution)  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE                                                 │
│  PostgreSQL • Redis • ClickHouse • ChromaDB • Redpanda • Docker │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.13+
- **Node.js**: 18+ (for frontend)
- **Docker**: 24.0+ & Docker Compose 2.0+
- **Git**: For version control

### Installation

```bash
# Clone repository
git clone https://github.com/RakeshRamkhelawan/Agentic-trader-.git
cd Agentic-trader-

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start infrastructure
docker-compose up -d postgres redis clickhouse chromadb redpanda

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# Run migrations
alembic upgrade head

# Start backend
uvicorn backend.api.main:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

📖 **Detailed Setup**: [QUICK_START.md](QUICK_START.md) | [DOCKER.md](DOCKER.md)

---

## 📚 Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [QUICK_START.md](QUICK_START.md) | Quick start guide for developers |
| [DOCKER.md](DOCKER.md) | Docker setup and configuration |
| [docs/SECURITY_RUNBOOK.md](docs/SECURITY_RUNBOOK.md) | Security practices and incident response |
| [docs/TESTING.md](docs/TESTING.md) | Testing strategy and coverage |
| [docs/INCIDENT_RESPONSE.md](docs/INCIDENT_RESPONSE.md) | Incident handling procedures |
| [PORT_ALLOCATION_SSOT.md](PORT_ALLOCATION_SSOT.md) | Port allocation guide |

### Architecture Documentation

| Document | Description |
|----------|-------------|
| [FEDERATED_TRIAD_ARCHITECTURE.md](FEDERATED_TRIAD_ARCHITECTURE.md) | Core architecture overview |
| [FEDERATED_TRIAD_GEBRUIKERSHANDLEIDING.md](FEDERATED_TRIAD_GEBRUIKERSHANDLEIDING.md) | User guide (Dutch) |
| [FEDERATED_TRIAD_IMPLEMENTATIE_DOCUMENTATIE.md](FEDERATED_TRIAD_IMPLEMENTATIE_DOCUMENTATIE.md) | Implementation docs |

### Trading Documentation

| Document | Description |
|----------|-------------|
| [PAPER_TRADING_GUIDE.md](PAPER_TRADING_GUIDE.md) | Paper trading setup |
| [ULTIMATE_PAPER_TRADING.md](ULTIMATE_PAPER_TRADING.md) | Advanced paper trading |
| [BACKTEST_RESULTS.md](BACKTEST_RESULTS.md) | Performance reports |

### Development Documentation

| Document | Description |
|----------|-------------|
| [AGENTS.md](AGENTS.md) | Guide for AI coding agents |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [WEEK13_PRODUCTION_SUMMARY.md](WEEK13_PRODUCTION_SUMMARY.md) | Production readiness |

---

## 🧪 Testing

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test suite
pytest backend/tests/unit/ -v
pytest backend/tests/integration/ -v
```

**Coverage**: 88% overall, 95%+ on critical modules
**Total Tests**: 734+ tests passing

📖 [Testing Guide](docs/TESTING.md)

---

## 🔒 Security

- **OWASP 2024 Score**: 95/100
- **Security Grade**: 88/100 (Production Ready)
- **Zero Critical Vulnerabilities**

### Security Features

- ✅ JWT RS256 token-based authentication
- ✅ Multi-tenant row-level security (RLS)
- ✅ Parameterized queries (SQL injection prevention)
- ✅ Input sanitization (LLM prompt injection protection)
- ✅ Non-root Docker containers
- ✅ Automated security scanning (Bandit, Trivy)

📖 [Security Runbook](docs/SECURITY_RUNBOOK.md) | [Incident Response](docs/INCIDENT_RESPONSE.md)

---

## 🏗️ Project Structure

```
agentic-trader/
├── backend/                    # Python backend (549+ modules)
│   ├── agents/                 # AI agents (ReAct pattern)
│   ├── api/                    # FastAPI endpoints
│   ├── core/                   # Core cognitive system
│   ├── execution/              # Trading execution
│   ├── risk/                   # Risk management
│   └── tests/                  # Test suite
├── frontend/                   # React frontend
│   ├── src/                    # Source code
│   └── package.json            # NPM dependencies
├── docs/                       # Documentation
├── infrastructure/             # IaC (K8s, Docker, Terraform)
├── requirements/               # Python dependencies
└── docker-compose.yml          # Full stack orchestration
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contributing Guide

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Security Score** | 88/100 |
| **Reliability Score** | 85/100 |
| **Test Coverage** | 88% |
| **Tests Passing** | 734+ |
| **API Response Time** | <50ms (p95) |
| **Order Execution** | <10ms |

---

## 🛣️ Roadmap

See [NEXT_STEPS.md](NEXT_STEPS.md) and [VERSIONING.md](VERSIONING.md) for upcoming features and version plans.

### Current Status

- ✅ Phase A: Foundation & Data Infrastructure
- ✅ Phase B: Execution & Risk Management
- ✅ Phase C: Cognition & AI
- ✅ Phase D: Enterprise Operations & Monitoring
- ✅ Phase E: Analytics & Business Layer
- 🔄 Phase F: Multi-Asset & Advanced ML (In Progress)

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

The Apache 2.0 license allows you to:
- ✅ Use the software commercially
- ✅ Modify the software
- ✅ Distribute the software
- ✅ Use patent claims
- ✅ Place warranty

With the conditions:
- Include copyright notice
- State changes made
- Include license text

---

## 🙏 Acknowledgments

- Vedic philosophy inspiration from Samkhya tradition
- ReAct pattern research from Princeton & Google
- FastAPI community for excellent framework
- All contributors who have helped shape this project

---

<div align="center">

**[⬆ Back to Top](#agentic-trader-platform)**

Built with ❤️ by the Agentic Trader Team

</div>
