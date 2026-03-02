# Contributing to Agentic Trader Platform

Thank you for your interest in contributing to the Agentic Trader Platform! We welcome contributions from the community and are pleased to have you join us.

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- Docker 24.0+
- Git

### Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/RakeshRamkhelawan/Agentic-trader-.git
   cd Agentic-trader-
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start infrastructure**
   ```bash
   docker-compose up -d postgres redis clickhouse chromadb redpanda
   ```

4. **Install Python dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements/base.txt
   pip install -r requirements/dev.txt
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Setup pre-commit hooks**
   ```bash
   pre-commit install
   ```

## 📋 Contribution Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements
- `security/` - Security fixes

### 2. Make Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all pre-commit hooks pass

### 3. Run Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/unit/test_your_module.py -v
```

### 4. Run Pre-commit Hooks

```bash
pre-commit run --all-files
```

### 5. Commit Changes

```bash
git add .
git commit -m "type(scope): description

Detailed description of changes

- Bullet point 1
- Bullet point 2"
```

**Commit message format:**
```
type(scope): subject

body

footer
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, semicolons, etc)
- `refactor` - Code refactoring
- `test` - Test additions/fixes
- `chore` - Build process or auxiliary tool changes
- `security` - Security fixes

**Examples:**
```
feat(risk): add portfolio VaR limit check

- Implement pre-trade VaR validation
- Add configurable max_daily_var_pct parameter
- Update risk orchestrator tests

Closes #123
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots/GIFs for UI changes
- Test results

## 📝 Code Style Guidelines

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black formatter)
- Use docstrings for all public modules, classes, and functions

```python
from typing import Optional, Dict, List, Any

async def process_order(
    symbol: str,
    quantity: float,
    side: OrderSide,
    order_type: OrderType = OrderType.MARKET
) -> OrderResult:
    """
    Process a trading order.

    Args:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        quantity: Order quantity
        side: Buy or sell
        order_type: Market, limit, etc.

    Returns:
        OrderResult with order details and status

    Raises:
        ValidationError: If order parameters are invalid
        InsufficientFundsError: If account balance is insufficient
    """
    # Implementation
```

### TypeScript/React

- Use functional components with hooks
- Use TypeScript strict mode
- Follow ESLint configuration
- Use meaningful component and variable names

## 🧪 Testing Requirements

- Write unit tests for all new functionality
- Maintain minimum 85% code coverage
- Write integration tests for API endpoints
- Test both happy path and error scenarios

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_process_order_success():
    """Test successful order processing."""
    # Arrange
    mock_service = Mock()
    mock_service.execute = AsyncMock(return_value={"status": "filled"})

    # Act
    result = await process_order(mock_service, "BTC-USD", 1.0, "buy")

    # Assert
    assert result.status == "filled"
    mock_service.execute.assert_called_once()
```

## 📚 Documentation

- Update README.md if adding new features
- Update CHANGELOG.md under `## [Unreleased]`
- Add/update docstrings for public APIs
- Update AGENTS.md if changing development patterns

## 🔒 Security

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Follow OWASP guidelines
- Run security scans before submitting PR

```bash
# Run security scan
bandit -r backend/ -f json -o bandit-report.json
```

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description** - Clear description of the bug
2. **Steps to Reproduce** - Detailed steps to reproduce
3. **Expected Behavior** - What should happen
4. **Actual Behavior** - What actually happens
5. **Environment** - OS, Python version, dependencies
6. **Logs/Tracebacks** - Relevant error messages

Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)

## 💡 Feature Requests

When requesting features:

1. **Use Case** - Describe the problem you're trying to solve
2. **Proposed Solution** - Your idea for implementation
3. **Alternatives** - Other approaches you've considered
4. **Additional Context** - Screenshots, examples, etc.

Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)

## 🏗️ Architecture Decisions

For significant architectural changes:

1. Create an Architecture Decision Record (ADR) in `docs/adr/`
2. Follow the format: `ADR-XXX-short-description.md`
3. Include: Context, Decision, Consequences
4. Get approval from maintainers before implementation

## 📞 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and ideas
- **Email**: support@agentictrader.com for private inquiries

## 🙏 Recognition

Contributors will be recognized in our README.md and release notes.

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Agentic Trader Platform! 🚀
