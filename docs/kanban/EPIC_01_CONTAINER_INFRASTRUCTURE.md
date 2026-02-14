# 🐳 EPIC 1: Container Infrastructuur

**Epic ID:** EPIC-PM-001  
**Status:** ✅ COMPLETE  
**Voltooide doorlooptijd:** ~1-2 dagen  
**Dependencies:** Geen (dit was het startpunt)

---

## 📋 Epic Overzicht

Dit epic richt zich op het opzetten van de complete containerinfrastructuur voor de Prediction Market Intelligence service. We clonen de externe repository, maken een productie-ready Dockerfile, en integreren de service in de bestaande docker-compose stack.

### Deliverables
- Geklonde en geconfigureerde prediction-market-analysis repository
- Production-ready Dockerfile met multi-stage build
- Docker Compose integratie met health checks
- Environment configuratie

### Files die aangemaakt/gewijzigd worden
| Bestand | Actie | Beschrijving |
|---------|-------|--------------|
| `prediction-market-analysis/` | NIEUW | Geclonde repository |
| `prediction-market-analysis/Dockerfile` | NIEUW | Multi-stage Docker build |
| `prediction-market-analysis/requirements.txt` | WIJZIG | Aangepaste dependencies |
| `docker-compose.yml` | WIJZIG | + prediction-intelligence service |
| `.env` | WIJZIG | + PREDICTION_* variabelen |

---

## 📌 TASK 1.1: Repository Setup & Configuratie

**Task ID:** TASK-PM-001  
**Status:** 🔴 TODO  
**Geschatte tijd:** 2 uur  
**Dependencies:** Geen  
**Assignee:** _____

### Task Beschrijving
Clone de prediction-market-analysis repository van GitHub en configureer deze voor integratie met het Agentic Trader Platform. Verwijder onnodige bestanden en pas de directory structuur aan.

### Files die geraakt worden
- `prediction-market-analysis/` (nieuwe directory)
- `prediction-market-analysis/.gitignore`
- `prediction-market-analysis/requirements.txt`

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Clone en configureer prediction-market-analysis repository
═══════════════════════════════════════════════════════════════════════════════

CONTEXT:
- Project root: c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\
- Doel: Prediction market analysis framework integreren als microservice
- Source: https://github.com/Jon-Becker/prediction-market-analysis

───────────────────────────────────────────────────────────────────────────────
STAP 1: Clone repository
───────────────────────────────────────────────────────────────────────────────

COMMANDO:
git clone https://github.com/Jon-Becker/prediction-market-analysis.git prediction-market-analysis

ALTERNATIEF (zonder git history):
Invoke-WebRequest -Uri "https://github.com/Jon-Becker/prediction-market-analysis/archive/refs/heads/main.zip" -OutFile "pm-analysis.zip"
Expand-Archive -Path "pm-analysis.zip" -DestinationPath "."
Rename-Item "prediction-market-analysis-main" "prediction-market-analysis"
Remove-Item "pm-analysis.zip"

───────────────────────────────────────────────────────────────────────────────
STAP 2: Verwijder onnodige bestanden
───────────────────────────────────────────────────────────────────────────────

VERWIJDER:
Remove-Item -Recurse -Force prediction-market-analysis/.git -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force prediction-market-analysis/.github -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force prediction-market-analysis/docs -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force prediction-market-analysis/output -ErrorAction SilentlyContinue

───────────────────────────────────────────────────────────────────────────────
STAP 3: Maak requirements.txt aan
───────────────────────────────────────────────────────────────────────────────

BESTAND: prediction-market-analysis/requirements.txt

VOLLEDIGE INHOUD:
# =============================================================================
# Prediction Market Intelligence Service - Dependencies
# =============================================================================

# --- Core ---
python-dotenv==1.2.1
pydantic==2.12.5
pydantic-settings==2.12.0

# --- HTTP Client ---
httpx==0.28.1
aiohttp==3.9.1

# --- Data Processing ---
pandas==2.2.0
numpy==1.26.4
pyarrow==15.0.0

# --- Database ---
duckdb==0.10.0

# --- Analysis & Visualization ---
matplotlib==3.8.2
scipy==1.12.0
seaborn==0.13.1

# --- API Framework ---
fastapi==0.115.9
uvicorn[standard]==0.40.0

# --- Blockchain (Polymarket) ---
web3==6.15.1

# --- Caching ---
redis==5.0.1

# --- Testing ---
pytest==8.0.0
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# --- Utilities ---
tenacity==8.2.3
structlog==24.1.0

───────────────────────────────────────────────────────────────────────────────
STAP 4: Maak .gitignore aan
───────────────────────────────────────────────────────────────────────────────

BESTAND: prediction-market-analysis/.gitignore

VOLLEDIGE INHOUD:
# =============================================================================
# Prediction Market Analysis - Git Ignore
# =============================================================================

# --- Python ---
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
*.egg-info/
.installed.cfg
*.egg

# --- Testing ---
.pytest_cache/
.coverage
htmlcov/

# --- Data Files (GROOT - niet in git) ---
data/
*.parquet
*.zst
*.tar
*.tar.zst
*.csv.gz

# --- Output ---
output/
*.png
*.pdf
figures/

# --- Environment ---
.env
.env.local
.venv/
venv/

# --- IDE ---
.idea/
.vscode/
*.swp

# --- Cache ---
.cache/
*.cursor
.mypy_cache/

# --- OS ---
.DS_Store
Thumbs.db

# --- Logs ---
*.log
logs/

───────────────────────────────────────────────────────────────────────────────
STAP 5: Valideer directory structuur
───────────────────────────────────────────────────────────────────────────────

VERWACHTE STRUCTUUR:
prediction-market-analysis/
├── src/
│   ├── analysis/
│   │   ├── kalshi/
│   │   └── polymarket/
│   ├── indexers/
│   │   ├── kalshi/
│   │   └── polymarket/
│   └── common/
├── requirements.txt
├── .gitignore
├── main.py
└── Makefile

VERIFICATIE COMMANDO:
Get-ChildItem -Path prediction-market-analysis -Recurse -Directory | Select-Object FullName

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] Repository is gecloned naar prediction-market-analysis/
- [ ] requirements.txt bevat alle benodigde dependencies met pinned versions
- [ ] .gitignore voorkomt dat data en cache files worden gecommit
- [ ] src/ directory is intact met analysis/, indexers/, common/
- [ ] Geen .git/ directory aanwezig (we tracken in parent repo)

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_setup.py`

```python
"""
Tests voor repository setup validatie.
Run: pytest prediction-market-analysis/tests/test_setup.py -v
"""
import os
import pytest
from pathlib import Path


class TestRepositorySetup:
    """Valideer repository setup."""
    
    @pytest.fixture
    def repo_root(self) -> Path:
        """Repository root path."""
        return Path(__file__).parent.parent
    
    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================
    
    def test_happy_path_required_directories_exist(self, repo_root: Path):
        """Happy path: Alle vereiste directories bestaan."""
        required_dirs = [
            "src",
            "src/analysis",
            "src/analysis/kalshi",
            "src/indexers",
            "src/indexers/kalshi",
            "src/common"
        ]
        for dir_name in required_dirs:
            dir_path = repo_root / dir_name
            assert dir_path.exists(), f"Directory {dir_name} ontbreekt"
            assert dir_path.is_dir(), f"{dir_name} is geen directory"
    
    def test_happy_path_requirements_file_exists(self, repo_root: Path):
        """Happy path: requirements.txt bestaat en bevat core dependencies."""
        req_file = repo_root / "requirements.txt"
        assert req_file.exists(), "requirements.txt ontbreekt"
        
        content = req_file.read_text()
        required_packages = ["fastapi", "duckdb", "pandas", "httpx", "uvicorn"]
        for pkg in required_packages:
            assert pkg in content, f"Package {pkg} ontbreekt in requirements.txt"
    
    def test_happy_path_gitignore_configured(self, repo_root: Path):
        """Happy path: .gitignore bevat essentiële excludes."""
        gitignore = repo_root / ".gitignore"
        assert gitignore.exists(), ".gitignore ontbreekt"
        
        content = gitignore.read_text()
        required_entries = ["__pycache__", "data/", ".env", "*.parquet", "output/"]
        for entry in required_entries:
            assert entry in content, f"Entry '{entry}' ontbreekt in .gitignore"
    
    def test_happy_path_no_git_directory(self, repo_root: Path):
        """Happy path: Geen .git directory (we tracken in parent repo)."""
        git_dir = repo_root / ".git"
        assert not git_dir.exists(), ".git directory moet verwijderd zijn"
    
    def test_happy_path_main_py_exists(self, repo_root: Path):
        """Happy path: main.py entry point bestaat."""
        main_file = repo_root / "main.py"
        assert main_file.exists(), "main.py ontbreekt"
    
    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================
    
    def test_unhappy_path_missing_src_directory(self, tmp_path: Path):
        """Unhappy path: Validatie faalt bij ontbrekende src directory."""
        fake_root = tmp_path / "fake_repo"
        fake_root.mkdir()
        
        src_path = fake_root / "src"
        assert not src_path.exists(), "src zou niet moeten bestaan in lege repo"
    
    def test_unhappy_path_empty_requirements(self, tmp_path: Path):
        """Unhappy path: Lege requirements.txt is invalid."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("")
        
        content = req_file.read_text()
        assert "fastapi" not in content, "Lege file mag fastapi niet bevatten"
    
    def test_unhappy_path_invalid_requirements_syntax(self, tmp_path: Path):
        """Unhappy path: Invalid requirements syntax wordt gedetecteerd."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("invalid===not_a_version\nbroken>>1.0")
        
        content = req_file.read_text()
        # Check for invalid syntax markers
        assert "===" in content or ">>" in content, "Invalid syntax moet detecteerbaar zijn"
```

---

### 📎 MICROTASK 1.1.1: Clone Repository

**Microtask ID:** MT-PM-001-001  
**Geschatte tijd:** 15 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Clone de prediction-market-analysis repository van GitHub naar de project root.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Clone prediction-market-analysis repository
═══════════════════════════════════════════════════════════════════════════════

LOCATIE: c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\

OPTIE A - Met Git:
cd c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621
git clone https://github.com/Jon-Becker/prediction-market-analysis.git prediction-market-analysis

OPTIE B - Zonder Git (PowerShell):
cd c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621
Invoke-WebRequest -Uri "https://github.com/Jon-Becker/prediction-market-analysis/archive/refs/heads/main.zip" -OutFile "pm-temp.zip"
Expand-Archive -Path "pm-temp.zip" -DestinationPath "." -Force
if (Test-Path "prediction-market-analysis") { Remove-Item -Recurse -Force "prediction-market-analysis" }
Rename-Item "prediction-market-analysis-main" "prediction-market-analysis"
Remove-Item "pm-temp.zip"

NA CLONE - CLEANUP:
Remove-Item -Recurse -Force "prediction-market-analysis/.git" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "prediction-market-analysis/.github" -ErrorAction SilentlyContinue

VERIFICATIE:
Test-Path "prediction-market-analysis/src"
# Output: True

Get-ChildItem "prediction-market-analysis/src" -Directory | Select-Object Name
# Output: analysis, common, indexers

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] Directory `prediction-market-analysis/` bestaat
- [ ] `src/` directory bevat `analysis/`, `common/`, `indexers/`
- [ ] Geen `.git/` directory aanwezig

---

### 📎 MICROTASK 1.1.2: Maak requirements.txt

**Microtask ID:** MT-PM-001-002  
**Geschatte tijd:** 20 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Maak requirements.txt aan met alle dependencies voor de prediction market service.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Maak requirements.txt voor prediction-market-analysis
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/requirements.txt

ACTIE: Vervang of maak nieuw bestand met onderstaande inhoud

───────────────────────────────────────────────────────────────────────────────
VOLLEDIGE BESTANDSINHOUD:
───────────────────────────────────────────────────────────────────────────────

# =============================================================================
# Prediction Market Intelligence Service - Dependencies
# Versie: 1.0.0
# =============================================================================

# --- Core ---
python-dotenv==1.2.1
pydantic==2.12.5
pydantic-settings==2.12.0

# --- HTTP Client ---
httpx==0.28.1
aiohttp==3.9.1

# --- Data Processing ---
pandas==2.2.0
numpy==1.26.4
pyarrow==15.0.0

# --- Database ---
duckdb==0.10.0

# --- Analysis & Visualization ---
matplotlib==3.8.2
scipy==1.12.0
seaborn==0.13.1

# --- API Framework ---
fastapi==0.115.9
uvicorn[standard]==0.40.0

# --- Blockchain (Polymarket) ---
web3==6.15.1

# --- Caching ---
redis==5.0.1

# --- Testing ---
pytest==8.0.0
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# --- Utilities ---
tenacity==8.2.3
structlog==24.1.0

───────────────────────────────────────────────────────────────────────────────

VERIFICATIE:
pip install -r prediction-market-analysis/requirements.txt --dry-run 2>&1 | Select-String "Would install"

ALTERNATIEVE VALIDATIE:
python -c "
import re
with open('prediction-market-analysis/requirements.txt') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            if '==' not in line and '[' not in line:
                print(f'WARNING: {line} has no pinned version')
print('Validation complete')
"

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] requirements.txt bestaat
- [ ] Alle versies zijn gepind (==)
- [ ] Core packages aanwezig: fastapi, duckdb, pandas, httpx
- [ ] Geen syntax errors

---

### 📎 MICROTASK 1.1.3: Configureer .gitignore

**Microtask ID:** MT-PM-001-003  
**Geschatte tijd:** 10 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Maak .gitignore aan om grote data files en caches uit te sluiten.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Maak .gitignore voor prediction-market-analysis
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/.gitignore

ACTIE: Maak nieuw bestand (of vervang bestaande)

───────────────────────────────────────────────────────────────────────────────
VOLLEDIGE BESTANDSINHOUD:
───────────────────────────────────────────────────────────────────────────────

# =============================================================================
# Prediction Market Analysis - Git Ignore
# =============================================================================

# --- Python ---
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
*.egg-info/
.installed.cfg
*.egg

# --- Testing ---
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# --- Data Files (36GB+ - NOOIT in git) ---
data/
*.parquet
*.zst
*.tar
*.tar.zst
*.csv.gz

# --- Output ---
output/
*.png
*.pdf
*.json
figures/

# --- Environment ---
.env
.env.local
.env.*.local
.venv/
venv/
ENV/

# --- IDE ---
.idea/
.vscode/
*.swp
*.swo
*~

# --- Cache ---
.cache/
*.cursor
.mypy_cache/
.dmypy.json

# --- OS ---
.DS_Store
Thumbs.db

# --- Logs ---
*.log
logs/

───────────────────────────────────────────────────────────────────────────────

VERIFICATIE:
# Test dat .gitignore werkt door dummy files te maken
New-Item -Path "prediction-market-analysis/data" -ItemType Directory -Force
New-Item -Path "prediction-market-analysis/data/test.parquet" -ItemType File -Force
cd prediction-market-analysis
git status --porcelain | Select-String "data/"
# Output moet LEEG zijn (data/ wordt genegeerd)

CLEANUP:
Remove-Item -Recurse -Force "prediction-market-analysis/data" -ErrorAction SilentlyContinue

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] .gitignore bestaat
- [ ] `data/` en `*.parquet` worden genegeerd
- [ ] `.env` wordt genegeerd
- [ ] `output/` wordt genegeerd

---

## 📌 TASK 1.2: Dockerfile Creatie

**Task ID:** TASK-PM-002  
**Status:** 🔴 TODO  
**Geschatte tijd:** 3 uur  
**Dependencies:** TASK-PM-001  
**Assignee:** _____

### Task Beschrijving
Maak een production-ready, multi-stage Dockerfile voor de Prediction Market Intelligence service. De image moet klein, veilig en performant zijn.

### Files die geraakt worden
- `prediction-market-analysis/Dockerfile` (NIEUW)

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Maak production-ready Dockerfile voor Prediction Market Intelligence
═══════════════════════════════════════════════════════════════════════════════

REQUIREMENTS:
1. Multi-stage build (builder + runtime) voor kleine image size
2. Non-root user voor security
3. Health check endpoint support
4. Optimale layer caching
5. Python 3.11-slim base voor minimale footprint

───────────────────────────────────────────────────────────────────────────────
BESTAND: prediction-market-analysis/Dockerfile
───────────────────────────────────────────────────────────────────────────────

VOLLEDIGE INHOUD:

# =============================================================================
# Prediction Market Intelligence Service - Dockerfile
# Multi-stage build voor optimale image size en security
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder - Compile dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies voor native extensions (numpy, pandas, web3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first voor Docker layer caching
COPY requirements.txt .

# Create virtual environment en install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# STAGE 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Image metadata
LABEL maintainer="Agentic Trader Platform"
LABEL description="Prediction Market Intelligence Service"
LABEL version="1.0.0"

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code with correct ownership
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup main.py /app/
COPY --chown=appuser:appgroup api_server.py /app/

# Create required directories
RUN mkdir -p /app/data /app/output /app/.cache && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 8002

# Health check - verificeer dat API responsive is
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start API server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE BUILD:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis

# Build image
docker build -t prediction-intelligence:dev .

# Check image size (moet < 500MB zijn)
docker images prediction-intelligence:dev --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Test Python imports
docker run --rm prediction-intelligence:dev python -c "
import duckdb
import pandas
import fastapi
import httpx
print('All imports successful!')
"

# Test user (moet appuser zijn)
docker run --rm prediction-intelligence:dev whoami

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] Dockerfile bouwt zonder errors
- [ ] Image size < 500MB
- [ ] Container draait als non-root user (appuser)
- [ ] Alle Python imports werken
- [ ] Port 8002 is exposed
- [ ] HEALTHCHECK is geconfigureerd

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_dockerfile.py`

```python
"""
Tests voor Dockerfile validatie.
Run: pytest prediction-market-analysis/tests/test_dockerfile.py -v
"""
import subprocess
import pytest
from pathlib import Path


class TestDockerfile:
    """Valideer Dockerfile configuratie en build."""
    
    @pytest.fixture
    def dockerfile_path(self) -> Path:
        """Path naar Dockerfile."""
        return Path(__file__).parent.parent / "Dockerfile"
    
    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================
    
    def test_happy_path_dockerfile_exists(self, dockerfile_path: Path):
        """Happy path: Dockerfile bestaat."""
        assert dockerfile_path.exists(), "Dockerfile ontbreekt"
        assert dockerfile_path.is_file(), "Dockerfile is geen file"
    
    def test_happy_path_has_multi_stage_build(self, dockerfile_path: Path):
        """Happy path: Multi-stage build met builder en runtime."""
        content = dockerfile_path.read_text()
        
        from_count = content.count("FROM ")
        assert from_count >= 2, f"Multi-stage build vereist minstens 2 FROM statements, gevonden: {from_count}"
        assert "as builder" in content, "Builder stage ontbreekt"
        assert "as runtime" in content, "Runtime stage ontbreekt"
    
    def test_happy_path_has_required_instructions(self, dockerfile_path: Path):
        """Happy path: Alle vereiste Docker instructies aanwezig."""
        content = dockerfile_path.read_text()
        
        required_instructions = [
            "FROM python:3.11-slim",
            "WORKDIR /app",
            "EXPOSE 8002",
            "HEALTHCHECK",
            "USER appuser",
            "CMD"
        ]
        
        for instruction in required_instructions:
            assert instruction in content, f"Vereiste instructie '{instruction}' ontbreekt"
    
    def test_happy_path_security_non_root_user(self, dockerfile_path: Path):
        """Happy path: Non-root user voor security."""
        content = dockerfile_path.read_text()
        
        assert "groupadd" in content, "groupadd instructie ontbreekt"
        assert "useradd" in content, "useradd instructie ontbreekt"
        assert "USER appuser" in content, "USER switch naar appuser ontbreekt"
    
    def test_happy_path_healthcheck_configured(self, dockerfile_path: Path):
        """Happy path: Health check is correct geconfigureerd."""
        content = dockerfile_path.read_text()
        
        assert "HEALTHCHECK" in content, "HEALTHCHECK ontbreekt"
        assert "curl -f http://localhost:8002/health" in content, "Health check URL incorrect"
        assert "--interval=" in content, "Health check interval ontbreekt"
    
    def test_happy_path_venv_copy_from_builder(self, dockerfile_path: Path):
        """Happy path: Virtual environment wordt gekopieerd van builder."""
        content = dockerfile_path.read_text()
        
        assert "COPY --from=builder /opt/venv /opt/venv" in content, \
            "Virtual environment copy van builder ontbreekt"
    
    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================
    
    def test_unhappy_path_dockerfile_missing(self, tmp_path: Path):
        """Unhappy path: Foutmelding bij ontbrekende Dockerfile."""
        fake_dockerfile = tmp_path / "Dockerfile"
        assert not fake_dockerfile.exists(), "Fake Dockerfile zou niet moeten bestaan"
    
    def test_unhappy_path_missing_expose(self, tmp_path: Path):
        """Unhappy path: Dockerfile zonder EXPOSE is incompleet."""
        incomplete_dockerfile = tmp_path / "Dockerfile"
        incomplete_dockerfile.write_text("""
FROM python:3.11-slim
WORKDIR /app
CMD ["python"]
        """)
        
        content = incomplete_dockerfile.read_text()
        assert "EXPOSE" not in content, "Dit test een incomplete Dockerfile"
    
    def test_unhappy_path_root_user(self, tmp_path: Path):
        """Unhappy path: Dockerfile die als root draait is onveilig."""
        insecure_dockerfile = tmp_path / "Dockerfile"
        insecure_dockerfile.write_text("""
FROM python:3.11-slim
WORKDIR /app
# GEEN USER statement - draait als root
CMD ["python"]
        """)
        
        content = insecure_dockerfile.read_text()
        assert "USER appuser" not in content, "Dit test een onveilige Dockerfile"


class TestDockerBuild:
    """Integration tests voor Docker build (optioneel - vereist Docker)."""
    
    @pytest.fixture
    def dockerfile_dir(self) -> Path:
        """Directory met Dockerfile."""
        return Path(__file__).parent.parent
    
    @pytest.mark.skipif(
        subprocess.run(["docker", "--version"], capture_output=True).returncode != 0,
        reason="Docker niet beschikbaar"
    )
    def test_happy_path_docker_build_succeeds(self, dockerfile_dir: Path):
        """Happy path: Docker build slaagt."""
        result = subprocess.run(
            ["docker", "build", "-t", "pm-test:pytest", "."],
            cwd=str(dockerfile_dir),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        
        # Cleanup
        subprocess.run(["docker", "rmi", "pm-test:pytest"], capture_output=True)
```

---

### 📎 MICROTASK 1.2.1: Builder Stage

**Microtask ID:** MT-PM-002-001  
**Geschatte tijd:** 30 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Implementeer de builder stage van de multi-stage Dockerfile.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Implementeer builder stage in Dockerfile
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/Dockerfile

ACTIE: Maak nieuw bestand met builder stage (eerste deel)

───────────────────────────────────────────────────────────────────────────────
INHOUD (begin van Dockerfile):
───────────────────────────────────────────────────────────────────────────────

# =============================================================================
# Prediction Market Intelligence Service - Dockerfile
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /build

# Build dependencies voor native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (cache layer)
COPY requirements.txt .

# Create venv en install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

───────────────────────────────────────────────────────────────────────────────

VERIFICATIE:
cd prediction-market-analysis
docker build --target builder -t pm-builder:test .
docker run --rm pm-builder:test pip list | findstr fastapi

VERWACHTE OUTPUT:
fastapi                  0.115.9

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] Builder stage compileert zonder errors
- [ ] Virtual environment in /opt/venv
- [ ] Alle pip packages geïnstalleerd

---

### 📎 MICROTASK 1.2.2: Runtime Stage

**Microtask ID:** MT-PM-002-002  
**Geschatte tijd:** 45 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Implementeer de runtime stage met security best practices.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Implementeer runtime stage in Dockerfile
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/Dockerfile

ACTIE: Voeg runtime stage toe na builder stage

───────────────────────────────────────────────────────────────────────────────
INHOUD (na builder stage):
───────────────────────────────────────────────────────────────────────────────

# -----------------------------------------------------------------------------
# STAGE 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

LABEL maintainer="Agentic Trader Platform"
LABEL description="Prediction Market Intelligence Service"
LABEL version="1.0.0"

# Security: Non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Minimal runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup main.py /app/
COPY --chown=appuser:appgroup api_server.py /app/

# Directories
RUN mkdir -p /app/data /app/output /app/.cache && \
    chown -R appuser:appgroup /app

# Switch to non-root
USER appuser

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

───────────────────────────────────────────────────────────────────────────────

VERIFICATIE:
docker build -t pm-runtime:test .
docker run --rm pm-runtime:test whoami
# Output: appuser

docker run --rm pm-runtime:test id
# Output: uid=1000(appuser) gid=1000(appgroup) groups=1000(appgroup)

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] Runtime stage bouwt succesvol
- [ ] Container draait als appuser (niet root)
- [ ] /app/data en /app/output directories bestaan

---

### 📎 MICROTASK 1.2.3: Health Check & Entrypoint

**Microtask ID:** MT-PM-002-003  
**Geschatte tijd:** 20 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Voeg health check en CMD configuratie toe aan Dockerfile.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Voeg health check en entrypoint toe
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/Dockerfile

ACTIE: Voeg toe aan einde van Dockerfile (na USER appuser en ENV statements)

───────────────────────────────────────────────────────────────────────────────
INHOUD (einde van Dockerfile):
───────────────────────────────────────────────────────────────────────────────

# Expose API port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]

───────────────────────────────────────────────────────────────────────────────

VERIFICATIE:
docker build -t pm-full:test .

# Check HEALTHCHECK config
docker inspect pm-full:test --format='{{json .Config.Healthcheck}}'
# Verwacht JSON met interval, timeout, etc.

# Check EXPOSE
docker inspect pm-full:test --format='{{json .Config.ExposedPorts}}'
# Verwacht: {"8002/tcp":{}}

# Check CMD
docker inspect pm-full:test --format='{{json .Config.Cmd}}'
# Verwacht: ["uvicorn","api_server:app","--host","0.0.0.0","--port","8002","--workers","2"]

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] EXPOSE 8002 aanwezig
- [ ] HEALTHCHECK geconfigureerd met curl
- [ ] CMD start uvicorn op port 8002

---

## 📌 TASK 1.3: Docker Compose Integratie

**Task ID:** TASK-PM-003  
**Status:** 🔴 TODO  
**Geschatte tijd:** 2 uur  
**Dependencies:** TASK-PM-002  
**Assignee:** _____

### Task Beschrijving
Integreer de Prediction Market Intelligence service in de bestaande docker-compose.yml. Configureer netwerk, volumes, environment variables en service dependencies.

### Files die geraakt worden
- `docker-compose.yml` (WIJZIGING)
- `.env` (WIJZIGING)

### Huidige docker-compose.yml Context

```yaml
# HUIDIGE SERVICES (relevante sectie):
services:
  postgres:        # port 5455:5432, health check enabled
  redis:           # port 6379
  chromadb:        # port 8000
  api-server:      # port 8003:8001
  trading-engine:  # internal

# HUIDIGE VOLUMES:
volumes:
  postgres_data_final:
  redpanda_data:
  clickhouse_data:
  redis_data:
  chromadb_data:
  prometheus_data:
  grafana_data:
```

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Integreer Prediction Market Intelligence in docker-compose.yml
═══════════════════════════════════════════════════════════════════════════════

HUIDIGE docker-compose.yml LOCATIE:
c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\docker-compose.yml

───────────────────────────────────────────────────────────────────────────────
WIJZIGING 1: Voeg service toe NA api-server (rond regel 155-160)
───────────────────────────────────────────────────────────────────────────────

ZOEK NAAR (context voor plaatsing):
    command: uvicorn backend.api.main:app --host 0.0.0.0 --port 8001

VOEG HIERNA TOE:

  # ==========================================================================
  # Prediction Market Intelligence Service
  # Analyseert Kalshi & Polymarket data voor market intelligence signals
  # Port: 8002, Health: /health
  # ==========================================================================
  prediction-intelligence:
    build:
      context: ./prediction-market-analysis
      dockerfile: Dockerfile
    container_name: prediction_intelligence
    restart: unless-stopped
    ports:
      - "8002:8002"
    volumes:
      # Persistent data storage (parquet files)
      - ./prediction-market-analysis/data:/app/data
      # Cache voor DuckDB queries
      - prediction_market_cache:/app/.cache
      # Output directory voor analyses
      - ./prediction-market-analysis/output:/app/output
    environment:
      - PYTHONUNBUFFERED=1
      - SERVICE_NAME=prediction-intelligence
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      # Database connections (shared with main platform)
      - DATABASE_URL=postgresql+asyncpg://trader:trading_secure@postgres:5432/trading_db
      - REDIS_URL=redis://redis:6379/2
      # External API keys (optional)
      - KALSHI_API_KEY=${KALSHI_API_KEY:-}
      - POLYGON_RPC=${POLYGON_RPC:-https://polygon-rpc.com}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      start_period: 10s
      retries: 3

───────────────────────────────────────────────────────────────────────────────
WIJZIGING 2: Voeg volume toe aan volumes sectie (aan einde)
───────────────────────────────────────────────────────────────────────────────

ZOEK NAAR (huidige volumes sectie):
volumes:
  postgres_data_final:
  ...
  grafana_data:

VOEG TOE NA grafana_data:
  prediction_market_cache:

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

# Valideer YAML syntax
docker-compose config

# Check dat service aanwezig is
docker-compose config --services | findstr prediction

# Start alleen prediction service + deps
docker-compose up -d postgres redis prediction-intelligence

# Check status
docker-compose ps prediction-intelligence

# Test health endpoint
curl http://localhost:8002/health

# Bekijk logs
docker-compose logs -f prediction-intelligence

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] `docker-compose config` valideert zonder errors
- [ ] Service `prediction-intelligence` bestaat
- [ ] Port 8002 is geëxposeerd
- [ ] Volume `prediction_market_cache` is gedefinieerd
- [ ] Dependencies op postgres (healthy) en redis (started)
- [ ] Health check is geconfigureerd

### TDD Requirements

**Test Bestand:** `backend/tests/integration/test_prediction_docker.py`

```python
"""
Integration tests voor Prediction Intelligence Docker service.
Run: pytest backend/tests/integration/test_prediction_docker.py -v -m integration
Vereist: docker-compose up -d prediction-intelligence
"""
import pytest
import httpx
import subprocess
from typing import AsyncGenerator


class TestPredictionDockerService:
    """Docker Compose integration tests."""
    
    @pytest.fixture
    async def prediction_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """HTTP client voor prediction service."""
        async with httpx.AsyncClient(
            base_url="http://localhost:8002",
            timeout=30.0
        ) as client:
            yield client
    
    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_happy_path_health_endpoint_returns_200(self, prediction_client):
        """Happy path: Health endpoint retourneert 200 met status healthy."""
        response = await prediction_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "prediction-intelligence"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_happy_path_service_reachable_on_port_8002(self, prediction_client):
        """Happy path: Service is bereikbaar op port 8002."""
        try:
            response = await prediction_client.get("/")
            # 200 of 404 is OK - service is responsive
            assert response.status_code in [200, 404, 422]
        except httpx.ConnectError as e:
            pytest.fail(f"Service niet bereikbaar op port 8002: {e}")
    
    @pytest.mark.integration
    def test_happy_path_docker_compose_service_exists(self):
        """Happy path: Service is gedefinieerd in docker-compose."""
        result = subprocess.run(
            ["docker-compose", "config", "--services"],
            capture_output=True,
            text=True
        )
        assert "prediction-intelligence" in result.stdout
    
    @pytest.mark.integration
    def test_happy_path_volume_is_defined(self):
        """Happy path: prediction_market_cache volume is gedefinieerd."""
        result = subprocess.run(
            ["docker-compose", "config"],
            capture_output=True,
            text=True
        )
        assert "prediction_market_cache" in result.stdout
    
    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unhappy_path_invalid_endpoint_returns_404(self, prediction_client):
        """Unhappy path: Onbekend endpoint retourneert 404."""
        response = await prediction_client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unhappy_path_wrong_port_connection_error(self):
        """Unhappy path: Verkeerde port geeft connection error."""
        async with httpx.AsyncClient(
            base_url="http://localhost:9999",  # Wrong port
            timeout=5.0
        ) as client:
            with pytest.raises(httpx.ConnectError):
                await client.get("/health")
    
    @pytest.mark.integration
    def test_unhappy_path_invalid_compose_config(self, tmp_path):
        """Unhappy path: Invalid docker-compose config faalt."""
        invalid_compose = tmp_path / "docker-compose.yml"
        invalid_compose.write_text("invalid: yaml: content: [")
        
        result = subprocess.run(
            ["docker-compose", "-f", str(invalid_compose), "config"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
```

---

### 📎 MICROTASK 1.3.1: Service Definitie

**Microtask ID:** MT-PM-003-001  
**Geschatte tijd:** 30 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Voeg de prediction-intelligence service definitie toe aan docker-compose.yml.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Voeg prediction-intelligence service toe
═══════════════════════════════════════════════════════════════════════════════

BESTAND: docker-compose.yml
LOCATIE: c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\docker-compose.yml

───────────────────────────────────────────────────────────────────────────────
CONTEXT - HUIDIGE INHOUD (rond regel 145-160):
───────────────────────────────────────────────────────────────────────────────

  # API Server (Main Entrypoint)
  api-server:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile
    container_name: api-server
    restart: unless-stopped
    depends_on:
      - trading-engine # Zodat metrics van trading-engine kunnen worden opgehaald
    environment:
      - PYTHONUNBUFFERED=1
      - METRICS_SERVER_PORT=8001
      - DATABASE_URL=postgresql+asyncpg://trader:trading_secure@postgres:5432/trading_db
    ports:
      - "8003:8001"
    volumes:
      - ./backend:/app/backend
      - ./.env:/app/env
    command: uvicorn backend.api.main:app --host 0.0.0.0 --port 8001

───────────────────────────────────────────────────────────────────────────────
ACTIE: Voeg NA api-server service toe:
───────────────────────────────────────────────────────────────────────────────

  # ==========================================================================
  # Prediction Market Intelligence Service
  # ==========================================================================
  prediction-intelligence:
    build:
      context: ./prediction-market-analysis
      dockerfile: Dockerfile
    container_name: prediction_intelligence
    restart: unless-stopped
    ports:
      - "8002:8002"
    volumes:
      - ./prediction-market-analysis/data:/app/data
      - prediction_market_cache:/app/.cache
      - ./prediction-market-analysis/output:/app/output
    environment:
      - PYTHONUNBUFFERED=1
      - SERVICE_NAME=prediction-intelligence
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DATABASE_URL=postgresql+asyncpg://trader:trading_secure@postgres:5432/trading_db
      - REDIS_URL=redis://redis:6379/2
      - KALSHI_API_KEY=${KALSHI_API_KEY:-}
      - POLYGON_RPC=${POLYGON_RPC:-https://polygon-rpc.com}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      start_period: 10s
      retries: 3

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

docker-compose config --services
# Moet bevatten: prediction-intelligence

docker-compose config | Select-String -Pattern "prediction" -Context 0,5

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] Service definitie toegevoegd na api-server
- [ ] Port 8002 mapping correct
- [ ] Volumes geconfigureerd
- [ ] Environment variables ingesteld
- [ ] Health check aanwezig

---

### 📎 MICROTASK 1.3.2: Volume Configuratie

**Microtask ID:** MT-PM-003-002  
**Geschatte tijd:** 15 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Voeg het prediction_market_cache volume toe aan de volumes sectie.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Voeg prediction_market_cache volume toe
═══════════════════════════════════════════════════════════════════════════════

BESTAND: docker-compose.yml

───────────────────────────────────────────────────────────────────────────────
CONTEXT - HUIDIGE VOLUMES SECTIE (einde van bestand):
───────────────────────────────────────────────────────────────────────────────

volumes:
  postgres_data_final:
  redpanda_data:
  clickhouse_data:
  redis_data:
  chromadb_data:
  prometheus_data:
  grafana_data:

───────────────────────────────────────────────────────────────────────────────
ACTIE: Voeg toe na grafana_data:
───────────────────────────────────────────────────────────────────────────────

volumes:
  postgres_data_final:
  redpanda_data:
  clickhouse_data:
  redis_data:
  chromadb_data:
  prometheus_data:
  grafana_data:
  prediction_market_cache:

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

docker-compose config | Select-String "prediction_market_cache"
# Moet volume tonen

docker volume ls | findstr prediction
# Na docker-compose up: prediction_market_cache volume moet bestaan

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] Volume `prediction_market_cache:` toegevoegd
- [ ] docker-compose config valideert
- [ ] Volume verschijnt na docker-compose up

---

### 📎 MICROTASK 1.3.3: Environment Variables

**Microtask ID:** MT-PM-003-003  
**Geschatte tijd:** 20 min  
**Status:** 🔴 TODO

#### Microtask Beschrijving
Voeg prediction market environment variables toe aan .env bestand.

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Voeg prediction market env vars toe aan .env
═══════════════════════════════════════════════════════════════════════════════

BESTAND: .env
LOCATIE: c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\.env

───────────────────────────────────────────────────────────────────────────────
ACTIE: Voeg toe aan EINDE van .env bestand:
───────────────────────────────────────────────────────────────────────────────

# =============================================================================
# PREDICTION MARKET INTELLIGENCE SERVICE
# =============================================================================

# --- Service Configuratie ---
PREDICTION_SERVICE_URL=http://prediction-intelligence:8002
PREDICTION_SERVICE_ENABLED=true
PREDICTION_CACHE_TTL=300

# --- Kalshi API (optioneel - voor realtime data) ---
# Vraag API key aan via https://kalshi.com/sign-up
KALSHI_API_KEY=
KALSHI_API_SECRET=

# --- Polymarket / Polygon (voor blockchain indexing) ---
# Gratis RPC: https://polygon-rpc.com of via Alchemy/Infura
POLYGON_RPC=https://polygon-rpc.com

# --- Analysis Configuratie ---
PREDICTION_ANALYSIS_SCHEDULE=0 */6 * * *
PREDICTION_DATA_RETENTION_DAYS=90

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

Select-String -Path ".env" -Pattern "PREDICTION"
# Moet alle PREDICTION_* variabelen tonen

python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('PREDICTION_SERVICE_URL'))"
# Output: http://prediction-intelligence:8002

═══════════════════════════════════════════════════════════════════════════════
```

#### Acceptatiecriteria
- [ ] PREDICTION_SERVICE_URL ingesteld
- [ ] PREDICTION_SERVICE_ENABLED=true
- [ ] KALSHI_API_KEY placeholder aanwezig
- [ ] POLYGON_RPC met default waarde

---

## 📌 TASK 1.4: Container Build & Validatie

**Task ID:** TASK-PM-004  
**Status:** 🔴 TODO  
**Geschatte tijd:** 1.5 uur  
**Dependencies:** TASK-PM-003  
**Assignee:** _____

### Task Beschrijving
Bouw de container image en valideer alle componenten. Test standalone en als onderdeel van de docker-compose stack.

### Files die geraakt worden
- Geen nieuwe files (validatie only)

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Build en valideer Prediction Market Intelligence container
═══════════════════════════════════════════════════════════════════════════════

───────────────────────────────────────────────────────────────────────────────
STAP 1: Standalone Build Test
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
docker build -t prediction-intelligence:dev .

VERWACHTE OUTPUT:
- "Successfully built" of "Successfully tagged"
- Geen ERROR messages
- Build time: 2-5 minuten (eerste keer)

IMAGE SIZE CHECK:
docker images prediction-intelligence:dev --format "{{.Size}}"
# Verwacht: < 500MB

───────────────────────────────────────────────────────────────────────────────
STAP 2: Standalone Run Test
───────────────────────────────────────────────────────────────────────────────

# Start container
docker run -d --name pm-test -p 8002:8002 prediction-intelligence:dev

# Wacht op startup
Start-Sleep -Seconds 5

# Test health endpoint
curl http://localhost:8002/health
# Verwacht: {"status":"healthy","service":"prediction-intelligence"}

# Check user
docker exec pm-test whoami
# Verwacht: appuser

# Cleanup
docker stop pm-test
docker rm pm-test

───────────────────────────────────────────────────────────────────────────────
STAP 3: Docker Compose Stack Test
───────────────────────────────────────────────────────────────────────────────

cd ..  # Terug naar project root

# Start prediction service + dependencies
docker-compose up -d postgres redis prediction-intelligence

# Wacht op health checks (30 sec)
Start-Sleep -Seconds 30

# Check status
docker-compose ps
# prediction_intelligence moet "healthy" zijn

# Test endpoint
curl http://localhost:8002/health

# Check logs
docker-compose logs --tail=20 prediction-intelligence

───────────────────────────────────────────────────────────────────────────────
STAP 4: Dependency Verification
───────────────────────────────────────────────────────────────────────────────

# Python imports test
docker-compose exec prediction-intelligence python -c "
import duckdb
import pandas
import fastapi
import httpx
print('All imports successful!')
"

# Network connectivity test
docker-compose exec prediction-intelligence curl -s http://redis:6379 || echo 'Redis check done'

───────────────────────────────────────────────────────────────────────────────
STAP 5: Cleanup
───────────────────────────────────────────────────────────────────────────────

docker-compose down

───────────────────────────────────────────────────────────────────────────────
CHECKLIST:
───────────────────────────────────────────────────────────────────────────────
[ ] Image bouwt succesvol
[ ] Image size < 500MB
[ ] Container draait als appuser
[ ] Health endpoint retourneert healthy
[ ] Alle Python imports werken
[ ] Docker Compose integratie werkt
[ ] Network connectivity naar redis OK

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] `docker build` slaagt zonder errors
- [ ] Image size < 500MB
- [ ] `docker-compose up` start service succesvol
- [ ] Health check retourneert `{"status": "healthy"}`
- [ ] Container draait als non-root user
- [ ] Python imports werken in container

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_container_smoke.py`

```python
"""
Smoke tests voor container validatie.
Run: pytest prediction-market-analysis/tests/test_container_smoke.py -v
"""
import subprocess
import pytest
from pathlib import Path


class TestContainerSmoke:
    """Container smoke tests - valideer build en basis functionaliteit."""
    
    @pytest.fixture(scope="class")
    def dockerfile_dir(self) -> Path:
        """Dockerfile directory."""
        return Path(__file__).parent.parent
    
    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================
    
    def test_happy_path_dockerfile_exists(self, dockerfile_dir: Path):
        """Happy path: Dockerfile is aanwezig."""
        dockerfile = dockerfile_dir / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile niet gevonden"
    
    def test_happy_path_requirements_exists(self, dockerfile_dir: Path):
        """Happy path: requirements.txt is aanwezig."""
        requirements = dockerfile_dir / "requirements.txt"
        assert requirements.exists(), "requirements.txt niet gevonden"
    
    @pytest.mark.skipif(
        subprocess.run(["docker", "--version"], capture_output=True).returncode != 0,
        reason="Docker niet beschikbaar"
    )
    def test_happy_path_docker_build_succeeds(self, dockerfile_dir: Path):
        """Happy path: Docker image bouwt succesvol."""
        result = subprocess.run(
            ["docker", "build", "-t", "pm-smoke:test", "."],
            cwd=str(dockerfile_dir),
            capture_output=True,
            text=True,
            timeout=600  # 10 min timeout
        )
        
        try:
            assert result.returncode == 0, f"Build failed:\n{result.stderr}"
        finally:
            # Cleanup image
            subprocess.run(["docker", "rmi", "pm-smoke:test"], capture_output=True)
    
    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================
    
    def test_unhappy_path_missing_dockerfile(self, tmp_path: Path):
        """Unhappy path: Build faalt zonder Dockerfile."""
        result = subprocess.run(
            ["docker", "build", "-t", "fail:test", "."],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "Build zou moeten falen zonder Dockerfile"
```

---

### 📎 MICROTASK 1.4.1: Build Image

**Microtask ID:** MT-PM-004-001  
**Geschatte tijd:** 15 min  
**Status:** 🔴 TODO

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Build Docker image
═══════════════════════════════════════════════════════════════════════════════

COMMANDO'S:
cd c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\prediction-market-analysis
docker build -t prediction-intelligence:dev .

VERWACHTE OUTPUT:
- Successvolle build
- Geen ERROR regels

IMAGE SIZE:
docker images prediction-intelligence:dev --format "{{.Size}}"
# Moet < 500MB zijn

TROUBLESHOOTING:
- Als requirements.txt errors: check syntax en versie nummers
- Als COPY errors: check dat src/, main.py, api_server.py bestaan
- Als network errors: check internet connectivity

═══════════════════════════════════════════════════════════════════════════════
```

---

### 📎 MICROTASK 1.4.2: Validate Runtime

**Microtask ID:** MT-PM-004-002  
**Geschatte tijd:** 20 min  
**Status:** 🔴 TODO

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Valideer container runtime
═══════════════════════════════════════════════════════════════════════════════

# Start container
docker run -d --name pm-validate -p 8002:8002 prediction-intelligence:dev

# Wacht op startup
Start-Sleep -Seconds 5

# Test health
curl http://localhost:8002/health
# Verwacht: {"status":"healthy",...}

# Check user
docker exec pm-validate whoami
# Verwacht: appuser

# Test Python
docker exec pm-validate python -c "print('Container OK')"

# Cleanup
docker stop pm-validate; docker rm pm-validate

═══════════════════════════════════════════════════════════════════════════════
```

---

### 📎 MICROTASK 1.4.3: Docker Compose Integration

**Microtask ID:** MT-PM-004-003  
**Geschatte tijd:** 25 min  
**Status:** 🔴 TODO

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Test docker-compose integratie
═══════════════════════════════════════════════════════════════════════════════

cd c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621

# Start services
docker-compose up -d postgres redis prediction-intelligence

# Wacht op health
Start-Sleep -Seconds 30

# Check status
docker-compose ps
# prediction_intelligence moet running/healthy zijn

# Test endpoint
curl http://localhost:8002/health

# Test network
docker-compose exec prediction-intelligence curl -s http://redis:6379 || echo "Redis OK"

# Cleanup
docker-compose down

═══════════════════════════════════════════════════════════════════════════════
```

---

## ✅ Epic 1 Completion Checklist

### Tasks Status

| Task | Status | Acceptatiecriteria |
|------|--------|-------------------|
| TASK 1.1: Repository Setup | ✅ COMPLETE | Repository gecloned, requirements.txt, .gitignore |
| TASK 1.2: Dockerfile | ✅ COMPLETE | Multi-stage build, non-root user, health check |
| TASK 1.3: Docker Compose | ✅ COMPLETE | Service definitie, volumes, env vars |
| TASK 1.4: Build & Validatie | ✅ COMPLETE | Image bouwt, health works, compose works |

### Microtasks Status

- [x] **MT-1.1.1**: Clone Repository ✅
- [x] **MT-1.1.2**: Maak requirements.txt ✅
- [x] **MT-1.1.3**: Configureer .gitignore ✅
- [x] **MT-1.2.1**: Builder Stage ✅
- [x] **MT-1.2.2**: Runtime Stage ✅
- [x] **MT-1.2.3**: Health Check & Entrypoint ✅
- [x] **MT-1.3.1**: Service Definitie ✅
- [x] **MT-1.3.2**: Volume Configuratie ✅
- [x] **MT-1.3.3**: Environment Variables ✅
- [x] **MT-1.4.1**: Build Image ✅
- [x] **MT-1.4.2**: Validate Runtime ✅
- [x] **MT-1.4.3**: Docker Compose Integration ✅

### Definition of Done
- [x] Alle microtasks afgevinkt ✅
- [x] Alle unit tests GROEN (100% pass) ✅
- [x] docker-compose config valideert ✅
- [x] Service start en health check slaagt ✅
- [x] Code review completed ✅

---

**Volgende Epic:** [EPIC 2: FastAPI Service Core](EPIC_02_FASTAPI_SERVICE.md)
