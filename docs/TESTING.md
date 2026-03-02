# Testing Guide - Agentic Trader Platform

> **Purpose:** Comprehensive testing procedures and best practices  
> **Audience:** Developers, QA Engineers, DevOps  
> **Last Updated:** March 2026

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Suite Overview](#test-suite-overview)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Categories](#test-categories)
6. [Coverage Requirements](#coverage-requirements)
7. [CI/CD Integration](#cicd-integration)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [Troubleshooting](#troubleshooting)

---

## Testing Philosophy

### Principles

1. **Test Early, Test Often** - Tests run on every commit
2. **Fail Fast** - Fast feedback loop (< 5 minutes for unit tests)
3. **Comprehensive Coverage** - 85% overall, 100% critical paths
4. **Deterministic** - Tests produce same results every run
5. **Independent** - Tests don't depend on external services

### Test Pyramid

```
        /\
       /  \
      /E2E \      <- Few tests, full system (10%)
     /______\
    /        \
   /Integration\   <- Service integration (20%)
  /____________\
 /              \
/     Unit       \ <- Many tests, isolated (70%)
/________________\
```

---

## Test Suite Overview

### Test Structure

```
backend/tests/
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_circuit_breaker.py
│   ├── test_sentiment_agent.py
│   ├── test_event_bus.py
│   └── ...
├── integration/                # Integration tests
│   ├── test_complete_trading_flow.py
│   ├── test_full_samkhya_flow.py
│   └── ...
├── e2e/                        # End-to-end tests
│   ├── test_full_system.py
│   └── test_unified_consciousness_e2e.py
├── security/                   # Security tests
│   ├── test_security_regression.py
│   └── test_prompt_guard.py
└── load/                       # Performance tests
    └── locustfile.py
```

### Test Counts

| Category | Count | Target Time |
|----------|-------|-------------|
| Unit Tests | 250+ | < 2 minutes |
| Integration Tests | 50+ | < 5 minutes |
| E2E Tests | 10+ | < 10 minutes |
| Security Tests | 30+ | < 2 minutes |
| **Total** | **340+** | **~15 minutes** |

---

## Running Tests

### Quick Start

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/unit/test_circuit_breaker.py -v

# Run specific test class
pytest backend/tests/unit/test_circuit_breaker.py::TestCircuitBreakerBasic -v

# Run specific test method
pytest backend/tests/unit/test_circuit_breaker.py::TestCircuitBreakerBasic::test_initial_state_closed -v
```

### Running by Category

```bash
# Unit tests only
pytest backend/tests/unit/ -v --tb=short

# Integration tests (requires services)
docker-compose up -d postgres redis
pytest backend/tests/integration/ -v

# Security tests
pytest backend/tests/security/ -v

# E2E tests (requires full stack)
docker-compose up -d
pytest backend/tests/e2e/ -v
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest backend/tests/ -n auto

# Run with specific number of workers
pytest backend/tests/ -n 4
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Exclude slow tests
pytest -m "not slow"
```

---

## Writing Tests

### Test Structure

```python
# test_example.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestComponentName:
    """Test suite for ComponentName."""
    
    @pytest.fixture
    def component(self):
        """Create test fixture."""
        return ComponentName()
    
    @pytest.mark.asyncio
    async def test_success_case(self, component):
        """Test the happy path."""
        # Arrange
        input_data = "test_input"
        
        # Act
        result = await component.process(input_data)
        
        # Assert
        assert result.status == "success"
        assert result.value == expected_value
    
    @pytest.mark.asyncio
    async def test_error_case(self, component):
        """Test error handling."""
        # Arrange
        invalid_input = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="invalid input"):
            await component.process(invalid_input)
    
    @pytest.mark.asyncio
    async def test_mocked_dependency(self, component):
        """Test with mocked external dependency."""
        with patch("backend.module.external_service") as mock:
            mock.fetch = AsyncMock(return_value={"data": "mocked"})
            
            result = await component.call_external()
            
            assert result == {"data": "mocked"}
            mock.fetch.assert_called_once()
```

### Best Practices

#### 1. Use Descriptive Names
```python
# Good
def test_calculate_var_with_high_volatility_returns_higher_risk():
    pass

# Bad
def test_var_1():
    pass
```

#### 2. One Assertion Per Test (Usually)
```python
# Good - focused test
def test_kelly_formula_returns_zero_for_invalid_probability():
    result = kelly_calculator.calculate(win_prob=-0.1)
    assert result == 0.0

# Also good - grouping related assertions
def test_risk_decision_includes_all_fields():
    decision = risk_orchestrator.check(signal)
    assert decision.approved is True
    assert decision.quantity > 0
    assert decision.reason is not None
```

#### 3. Use Fixtures for Common Setup
```python
@pytest.fixture
def mock_db_session():
    """Provide mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def sample_order():
    """Provide sample order for testing."""
    return OrderRequest(
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=1.0,
        price=50000.0
    )
```

#### 4. Test Edge Cases
```python
@pytest.mark.parametrize("win_prob", [
    0.0,   # Edge: zero probability
    0.001, # Edge: very small
    0.5,   # Normal case
    0.999, # Edge: very high
    1.0,   # Edge: certainty
])
def test_position_sizer_handles_all_probabilities(win_prob):
    result = sizer.calculate(win_probability=win_prob)
    assert 0 <= result.quantity <= max_position
```

#### 5. Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation():
    """Always use pytest.mark.asyncio for async tests."""
    result = await async_function()
    assert result is not None
```

---

## Test Categories

### Unit Tests

**Purpose:** Test individual components in isolation  
**Speed:** Fast (< 100ms per test)  
**Dependencies:** Mocked  
**Coverage Target:** 90%

```python
# Example: Testing a calculation function
def test_calculate_kelly_fraction():
    """Test Kelly criterion calculation."""
    result = calculate_kelly(
        win_prob=0.55,
        win_ratio=2.0,
        loss_ratio=1.0
    )
    
    # f* = (0.55 * 2 - 0.45) / 2 = 0.325
    assert abs(result - 0.325) < 0.001
```

### Integration Tests

**Purpose:** Test component interactions  
**Speed:** Medium (< 1s per test)  
**Dependencies:** Real services (DB, Redis)  
**Coverage Target:** 80%

```python
@pytest.mark.asyncio
async def test_order_flow_with_database():
    """Test complete order flow with real database."""
    # Uses real DB session
    async with get_db_session() as session:
        order = await create_order(session, order_data)
        assert order.id is not None
        
        fetched = await get_order(session, order.id)
        assert fetched.symbol == order_data.symbol
```

### E2E Tests

**Purpose:** Test complete user workflows  
**Speed:** Slow (< 10s per test)  
**Dependencies:** Full stack  
**Coverage Target:** 70%

```python
@pytest.mark.asyncio
async def test_complete_buy_workflow():
    """Test complete buy workflow from API to execution."""
    # 1. Authenticate
    token = await login("test_user", "test_pass")
    
    # 2. Place order
    order = await place_order(token, buy_order_data)
    
    # 3. Verify execution
    assert order.status == "FILLED"
    
    # 4. Check portfolio update
    portfolio = await get_portfolio(token)
    assert portfolio.positions[order.symbol] == order.quantity
```

### Security Tests

**Purpose:** Verify security controls  
**Speed:** Fast  
**Dependencies:** None (mostly)  
**Coverage Target:** 100%

```python
def test_sql_injection_blocked():
    """Verify SQL injection attempts are blocked."""
    malicious_input = "'; DROP TABLE users; --"
    
    # Should not raise exception, should sanitize
    result = sanitize_input(malicious_input)
    assert "DROP" not in result
```

---

## Coverage Requirements

### Minimum Coverage by Module

| Module | Minimum | Target |
|--------|---------|--------|
| Security | 95% | 100% |
| Risk Management | 95% | 100% |
| Execution | 90% | 95% |
| Event Bus | 90% | 95% |
| API | 85% | 90% |
| Agents | 80% | 85% |
| **Overall** | **85%** | **90%** |

### Generating Coverage Reports

```bash
# HTML report
pytest backend/tests/ --cov=backend --cov-report=html
# Open: htmlcov/index.html

# Terminal report
pytest backend/tests/ --cov=backend --cov-report=term-missing

# XML report (for CI)
pytest backend/tests/ --cov=backend --cov-report=xml

# Fail if coverage below threshold
pytest backend/tests/ --cov=backend --cov-fail-under=85
```

### Coverage Exclusions

```ini
# .coveragerc
[run]
omit =
    */tests/*
    */migrations/*
    */venv/*
    */__pycache__/*
    backend/api/main.py  # App entry point

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run unit tests
        run: pytest backend/tests/unit/ -v --cov=backend --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest backend/tests/unit/ -v --tb=short
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

---

## Performance Testing

### Load Testing with Locust

```python
# backend/tests/load/locustfile.py
from locust import HttpUser, task, between

class TradingUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Login before starting."""
        response = self.client.post("/auth/token", json={
            "username": "test_user",
            "password": "test_pass"
        })
        self.token = response.json()["access_token"]
    
    @task(10)
    def get_portfolio(self):
        """Simulate portfolio checks."""
        self.client.get(
            "/portfolio",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(5)
    def place_order(self):
        """Simulate order placement."""
        self.client.post(
            "/orders",
            json={
                "symbol": "BTC-EUR",
                "side": "buy",
                "quantity": 0.1
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

### Running Load Tests

```bash
# Install locust
pip install locust

# Run load test
locust -f backend/tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=5m
```

### Performance Benchmarks

```python
# test_performance.py
import pytest
import time

@pytest.mark.benchmark
class TestPerformance:
    def test_var_calculation_under_100ms(self):
        """VaR calculation should complete in < 100ms."""
        start = time.time()
        calculate_var(historical_returns)
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # 100ms
    
    def test_api_response_under_200ms(self, client):
        """API health check should respond in < 200ms."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.2  # 200ms
```

---

## Security Testing

### Running Security Tests

```bash
# All security tests
pytest backend/tests/security/ -v

# Specific security category
pytest backend/tests/security/test_sql_injection.py -v
```

### Security Test Categories

1. **Input Validation**
   - SQL injection
   - XSS
   - Command injection
   - Path traversal

2. **Authentication**
   - JWT validation
   - Session management
   - Password policies
   - MFA

3. **Authorization**
   - Role-based access
   - Resource permissions
   - Tenant isolation

4. **Cryptography**
   - Key management
   - Encryption
   - Hashing

---

## Troubleshooting

### Common Issues

#### 1. Tests Fail Due to Missing Environment Variables

```bash
# Create test environment file
cp .env.example .env.test
# Edit .env.test with test values
source .env.test
pytest backend/tests/
```

#### 2. Database Connection Errors

```bash
# Start test database
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Run tests
pytest backend/tests/
```

#### 3. Async Test Failures

```python
# Make sure to use pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

#### 4. Flaky Tests

```python
# Add retry for flaky tests
@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_occasionally_fails():
    pass

# Or mark as expected to fail
@pytest.mark.xfail(reason="Race condition, fixing in next release")
def test_known_issue():
    pass
```

### Debug Mode

```bash
# Run with verbose output
pytest -vvv --tb=long

# Run with PDB on failure
pytest --pdb

# Run specific test with max verbosity
pytest backend/tests/unit/test_circuit_breaker.py::TestCircuitBreakerBasic::test_initial_state_closed -vvv --tb=long
```

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Locust documentation](https://docs.locust.io/)

---

**Questions?** Contact the QA team at qa@agentictrader.com
