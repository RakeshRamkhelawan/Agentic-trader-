# Security Guide - Agentic Trader

Comprehensive security guide for the Agentic Trader platform.

## Security Scan Results

**Current Status:** Grade A (Production Ready)
- HIGH: 0 issues [PASS]
- MEDIUM: 25 issues (test files + false positives) [PASS]
- LOW: 4131 issues (mostly test asserts) [PASS]

## Critical Rules

### B324: Weak Hash Algorithms

**NEVER use MD5, SHA1 for any purpose.**

```python
# BAD
import hashlib
hashlib.md5(data).hexdigest()

# GOOD
import hashlib
hashlib.blake2b(data, digest_size=16).hexdigest()
```

**Fixed in:**
- `backend/agents/news_agent.py`
- `backend/agents/sentiment_agent_v2.py`
- `backend/core/memory_system.py`
- `backend/mcp_broker/backtest_engine_v18.py`
- `backend/mcp_broker/performance/cache.py`
- `backend/mcp_broker/tools/external_tools.py`

### B608: SQL Injection

**ALWAYS use parameterized queries.**

```python
# BAD - Never do this
query = f"SELECT * FROM users WHERE id = '{user_id}'"

# GOOD - Parameterized
query = "SELECT * FROM users WHERE id = %(id)s"
result = await client.execute(query, {"id": user_id})

# GOOD - Table name internally controlled
query = f"SELECT * FROM {table} WHERE id = %(id)s"  # table is internal
result = await client.execute(query, {"id": user_id})
```

**Key Principle:** f-strings are ONLY acceptable for table/column names that are internally controlled. User input MUST be parameterized.

### B113: Request Timeouts

**ALWAYS specify timeouts.**

```python
# BAD
requests.get(url)

# GOOD
requests.get(url, timeout=30)
```

### B105/B106: Hardcoded Passwords

**Use environment variables for secrets.**

```python
# BAD
SECRET_KEY = "my-secret-key"

# GOOD
SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback")
```

**False positives:** OAuth2 token types (`"bearer"`), test values, enum values. Mark with `# nosec`.

### B104: Binding to All Interfaces

**Required for Docker, mark with nosec.**

```python
# GOOD - Required for containerized deployment
uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
```

### B301: Pickle Usage

**Internal cache only, mark with nosec.**

```python
# GOOD - Internal cache, not user-facing
return pickle.loads(data)  # nosec B301
```

## SOC2 Compliance

### Access Control (CC6.1)
- JWT tokens with 24h expiration
- Role-based permissions
- Principle of least privilege

### Encryption (CC6.6)
- TLS 1.3 for data in transit
- AES-256 for data at rest
- BLAKE2b for hashing (not MD5/SHA1)

### Monitoring (CC7.2)
- All security events logged
- Failed authentication tracked
- Audit trail for all trades

### Change Management (CC8.1)
- Pull request required
- Security scan in CI/CD
- Two approvers for production

## Security Checklist

Before every commit, run:

```bash
# 1. Security scan
python -m bandit -r backend/ --severity-level high --exclude backend/tests

# 2. Should show: "No issues identified."

# 3. Test critical integrations
python scripts/test_real_gaps.py
```

### Pre-commit Checklist

- [ ] No MD5/SHA1 usage
- [ ] SQL queries parameterized
- [ ] All requests have timeouts
- [ ] No hardcoded secrets in code
- [ ] Bandit HIGH scan passes
- [ ] No PII in logs
- [ ] Audit logging added

## Bandit Configuration

Create `.bandit.yml`:

```yaml
# Bandit configuration
skips:
  # Acceptable false positives
  - B101  # Assert statements in tests
  - B311  # Random for simulation
  
exclude_dirs:
  - backend/tests
  - backend/**/test_*.py
```

## Incident Response

If a security issue is found:

1. **Assess severity** (HIGH/MEDIUM/LOW)
2. **Fix immediately** for HIGH
3. **Add to nosec** with justification if false positive
4. **Update tests** to prevent regression
5. **Document** in this guide
6. **Report** to security team per SOC2 requirements

## Compliance

| Standard | Status |
|----------|--------|
| OWASP ASVS L1 | [PASS] |
| CWE-327 (Broken Crypto) | [FIXED] |
| CWE-89 (SQL Injection) | [PASS] Parameterized |
| CWE-400 (Resource Consumption) | [PASS] Timeouts added |
| SOC2 CC6.1 | [PASS] Access controls |
| SOC2 CC6.6 | [PASS] Encryption |

## Security Contacts

- Security issues: Report immediately
- False positives: Document with # nosec
- Questions: Check this guide first
