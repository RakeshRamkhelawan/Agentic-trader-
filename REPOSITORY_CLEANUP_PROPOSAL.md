# Repository Cleanup Proposal

## Current State
The repository contains many development artifacts, old documentation, and temporary files that clutter the structure.

## Proposed Production-Ready Structure

```
agentic-trader/
├── 📁 backend/                    # Core Python application (KEEP)
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── execution/
│   ├── risk/
│   └── tests/                     # Keep essential tests
├── 📁 frontend/                   # React UI (KEEP)
│   ├── src/
│   ├── public/
│   └── package.json
├── 📁 docs/                       # Essential documentation only
│   ├── README.md                  # Main documentation
│   ├── QUICK_START.md             # Getting started
│   ├── DEPLOYMENT.md              # Deployment guide
│   ├── ARCHITECTURE.md            # System architecture
│   └── API.md                     # API documentation
├── 📁 infrastructure/             # IaC for deployment (KEEP)
│   ├── docker/
│   ├── k8s/
│   └── terraform/
├── 📁 requirements/               # Python dependencies (KEEP)
│   ├── base.txt
│   └── dev.txt
├── 📁 .github/                    # GitHub Actions (KEEP)
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── FUNDING.yml
├── 📄 docker-compose.yml          # Production orchestration (KEEP)
├── 📄 Dockerfile                  # Main image (KEEP)
├── 📄 .env.example                # Environment template (KEEP)
├── 📄 README.md                   # Main entry point (KEEP)
├── 📄 LICENSE                     # Apache 2.0 (KEEP)
├── 📄 CHANGELOG.md                # Version history (KEEP)
├── 📄 CONTRIBUTING.md             # Contribution guide (KEEP)
└── 📄 CODE_OF_CONDUCT.md          # Community standards (KEEP)

## Files/Directories to REMOVE or MOVE to archive

### ❌ Delete (temporary/cache)
- .benchmarks/
- .cache/
- .mypy_cache/
- .pytest_cache/
- .ruff_cache/
- .tmp/
- __pycache__/
- *.log files
- .DS_Store
- *.pyc

### 📦 Move to docs/archive/ (historical docs)
- WEEK*_IMPLEMENTATION_SUMMARY.md
- FASE_*_IMPLEMENTATION_SUMMARY.md
- *_RESULTS_SUMMARY.md
- *_AUDIT_REPORT.md (keep latest only)
- *_FIXES_SUMMARY.md
- CORRECTED_IMPLEMENTATION_PLAN.md
- MASTERPROMPT*.md
- PRD_V18_Realiteit.md
- All Dutch documentation (unless needed)

### 🔬 Move to tests/ or docs/examples/ (test artifacts)
- backtest_logs/
- backtest_results/ (keep only latest in docs/examples/)
- paper_trading_analytics/ (keep only essential)

### 🗑️ Delete (development artifacts)
- .claude/
- .continue/
- .gemini/
- .mcp-debug-tools/
- .qoder/
- .serena/
- analysis/
- cache/
- data/backtest_archive/ (old data)
- downloads/
- frontend_old/ (deprecated)
- libs/ (if not used)
- logs/
- model/ (old models)
- models/production/history_*.json (logs)
- prediction-market-analysis/ (separate project?)
- prompts/ (dev only)
- reports/ (move to docs/reports/)
- scripts/ (keep only production scripts)
- secrets/ (should never be in repo!)
- ssl/ (user provides their own)
- tests/ (consolidate under backend/tests/)
- venv/ (should be in .gitignore)

### 📄 Delete (temporary files)
- *.txt files (logs, temp)
- *.json files (session data, temp)
- *.csv files (temp data)
- check_*.py scripts
- test_*.py in root (move to tests/)
- verify_*.py scripts
- diagnose_*.py scripts
- All *.log files
- epic*_full.txt
- fase*_full.txt
- handover_full.txt
- generator.log
- monitor.log
- verification*.log

### 🔒 SECURITY CRITICAL - Delete immediately
- Any files with API keys
- Any files with passwords
- Any files with private keys
- secrets/ directory
- backend/tests/inject_revolut_key.py
- Any .env files with real credentials

## Implementation Steps

1. Create backup branch
2. Remove cache/temp directories from git history
3. Move historical docs to docs/archive/
4. Consolidate test files
5. Update .gitignore
6. Clean root directory
7. Verify Docker build still works
8. Test production deployment

## Size Reduction Estimate

Current: ~2-3 GB (estimated)
After cleanup: ~200-500 MB (estimated)

## Benefits

- ✅ Faster clones
- ✅ Clearer structure
- ✅ Easier onboarding
- ✅ Professional appearance
- ✅ Faster CI/CD
- ✅ Less confusion for users
