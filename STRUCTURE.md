# Repository Structure

This document describes the professional organization of the Agentic Trader Platform repository.

## Directory Overview

```
agentic-trader/
├── .github/              # GitHub configuration (CI/CD, templates)
├── .gitignore            # Git ignore rules
├── backend/              # Core Python application
├── config/               # Configuration files
├── data/                 # Data assets and schemas
├── docker/               # Docker deployment files
├── docs/                 # Documentation
├── frontend/             # React frontend application
├── infrastructure/       # Infrastructure as Code (K8s, Terraform)
├── libs/                 # External libraries (VedAstro)
├── models/               # ML model files (Git LFS tracked)
├── requirements/         # Python dependencies
├── scripts/              # Utility scripts
│   ├── admin/            # Administrative utilities
│   ├── debug/            # Debugging tools
│   ├── deployment/       # Deployment scripts
│   ├── ml_training/      # ML model training scripts
│   └── setup/            # Setup and installation
├── LICENSE               # Apache 2.0 License
├── Makefile              # Build automation
└── README.md             # Main documentation
```

## Directory Details

### `/backend/` - Core Application
Contains the main Python application with 549+ modules:
- `agents/` - AI agents (ReAct pattern)
- `api/` - FastAPI REST endpoints
- `core/` - Core cognitive system
- `execution/` - Trading execution layer
- `risk/` - Risk management (VaR, Kelly)
- `tests/` - Comprehensive test suite

### `/config/` - Configuration
Centralized configuration management:
- `alembic.ini` - Database migrations
- `prometheus.prod.yml` - Monitoring
- `pytest.ini` - Test configuration
- `pyproject.toml` - Project metadata
- `redis.conf` - Redis configuration

### `/docker/` - Deployment
Docker and containerization:
- `Dockerfile` - Main container image
- `docker-compose.yml` - Development stack
- `docker-compose.prod.yml` - Production stack
- `.dockerignore` - Docker exclusions

### `/scripts/` - Utilities
Organized utility scripts:
- `admin/` - Admin utilities (check_admin.py, etc.)
- `debug/` - Debug tools (check_*.py)
- `deployment/` - Deployment automation
- `ml_training/` - ML model training (data_prep.py, train.py, eval.py)
- `setup/` - Setup scripts (setup_ollama.sh, setup_ssl.sh)

### `/models/` - ML Models
Machine learning model files (Git LFS tracked):
- `chitta_lstm_best.pt` - LSTM model
- `chitta_quick_test.pt` - Quick test model
- `chitta_transformer_ultimate.pt` - Transformer model

### `/data/` - Data Assets
Essential data files:
- Asset lists (bitvavo_assets.json, revolutx_assets.json)
- Database schemas
- Migration files

### `/docs/` - Documentation
Project documentation:
- Architecture guides
- API documentation
- User guides

### `/infrastructure/` - IaC
Infrastructure as Code:
- Kubernetes manifests
- Terraform configurations
- Nginx configurations
- Grafana dashboards

### `/libs/` - External Libraries
Third-party dependencies:
- `VedAstro.Library.dll` - VedAstro integration

## Git LFS

Large binary files are tracked with Git LFS:
- `*.pt` - PyTorch models
- `*.pkl` - Pickle files
- `*.joblib` - Joblib serialized files

## Excluded from Git

The following are excluded via `.gitignore`:
- Virtual environments (`venv/`, `.venv/`)
- IDE files (`.vscode/`, `.idea/`)
- Logs (`*.log`, `logs/`)
- Cache directories (`__pycache__/`, `.cache/`)
- Secrets (`secrets/`, `*.pem`)
- Temp data (`backtest_results/`, `paper_trading_analytics/`)
- Node modules (`node_modules/`)
- Build outputs (`dist/`, `build/`)

## Best Practices

1. **Keep it minimal** - Only essential files in root
2. **Organize by purpose** - Group related files together
3. **Use Git LFS** - Track large binaries properly
4. **Document everything** - Clear structure for new developers
5. **Separate concerns** - Config, code, and data in different locations
