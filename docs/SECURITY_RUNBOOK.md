# Security Runbook - Agentic Trader Platform

> **Classification:** INTERNAL USE ONLY  
> **Last Updated:** March 2026  
> **Owner:** Security Team

## Table of Contents

1. [Incident Response](#incident-response)
2. [Security Monitoring](#security-monitoring)
3. [Vulnerability Management](#vulnerability-management)
4. [Access Control](#access-control)
5. [Compliance Checks](#compliance-checks)

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **P0 - Critical** | Active exploitation or data breach | 15 minutes | Unauthorized trading, data exfiltration |
| **P1 - High** | Vulnerability with high impact | 1 hour | Auth bypass, injection attack |
| **P2 - Medium** | Security misconfiguration | 24 hours | Weak TLS, missing headers |
| **P3 - Low** | Informational findings | 7 days | Outdated dependencies |

### Incident Response Playbook

#### 1. Unauthorized Trading Detected (P0)

**Immediate Actions (0-15 min):**
1. **Kill Switch:** Activate emergency circuit breaker
   ```bash
   kubectl exec -it deployment/api -- python -c "
   from backend.governance.circuit_breaker import CircuitBreaker
   # Trigger emergency shutdown
   "
   ```

2. **Isolate:** Disable trading for affected account(s)
   ```sql
   UPDATE users SET trading_enabled = false WHERE id = 'affected_user_id';
   ```

3. **Preserve Evidence:**
   - Capture logs: `kubectl logs deployment/api > incident_logs_$(date +%Y%m%d_%H%M%S).txt`
   - Screenshot Grafana dashboards
   - Export audit logs from ClickHouse

**Short-term Actions (15-60 min):**
1. Notify security team and compliance
2. Analyze attack vector
3. Block malicious IPs at firewall
4. Force logout all sessions for affected user

**Post-Incident:**
1. Document timeline
2. Conduct root cause analysis
3. Implement preventive measures

#### 2. SQL Injection Attempt (P1)

**Detection:**
- Alert: `SQL_INJECTION_ATTEMPT_DETECTED`
- Logs contain: `SELECT set_config('app.current_tenant', ...)`

**Response:**
1. Check if attempt succeeded:
   ```bash
   grep "set_config" /var/log/app/app.log | grep -v "system_admin"
   ```

2. Review tenant isolation:
   ```sql
   -- Check for cross-tenant data access
   SELECT * FROM audit_log 
   WHERE action = 'DATA_ACCESS' 
   AND tenant_id != user_tenant_id;
   ```

3. If successful:
   - Rotate all database credentials
   - Revoke all active sessions
   - Notify affected tenants

#### 3. JWT Token Compromise (P1)

**Detection:**
- Unusual token patterns in logs
- Multiple failed validation attempts

**Response:**
1. **Immediate:** Rotate JWT signing key
   ```bash
   # Generate new key
   openssl rand -hex 32
   
   # Update secret in Vault/Kubernetes
   kubectl create secret generic jwt-secret \
     --from-literal=JWT_SECRET_KEY="$(openssl rand -hex 32)" \
     --namespace=agentic-trader \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

2. Invalidate all existing tokens
3. Force re-authentication for all users
4. Review audit logs for unauthorized access

---

## Security Monitoring

### Key Metrics to Monitor

| Metric | Threshold | Alert Channel |
|--------|-----------|---------------|
| Failed auth attempts | > 10/min | PagerDuty |
| SQL injection attempts | Any | PagerDuty |
| Circuit breaker trips | > 3/hour | Slack |
| Unusual trading volume | > 3σ from mean | Slack |
| API error rate | > 5% | PagerDuty |
| JWT validation failures | > 5/min | Slack |

### Daily Security Checks

```bash
#!/bin/bash
# daily_security_check.sh

echo "=== Daily Security Check ==="

# 1. Check for new vulnerabilities
echo "Checking for CVEs..."
trivy image agentic-trader:latest --severity HIGH,CRITICAL

# 2. Verify no hardcoded secrets
echo "Checking for secrets..."
gitleaks detect --source . --verbose

# 3. Check authentication logs
echo "Checking auth logs..."
kubectl logs deployment/api | grep -i "unauthorized\|forbidden" | tail -20

# 4. Database audit
echo "Checking database access..."
psql $DATABASE_URL -c "
SELECT tenant_id, COUNT(*) 
FROM audit_log 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY tenant_id;
"

echo "=== Check Complete ==="
```

---

## Vulnerability Management

### Scanning Schedule

| Tool | Frequency | Scope |
|------|-----------|-------|
| Bandit | Every commit | Python code |
| Trivy | Daily | Container images |
| OWASP ZAP | Weekly | Running application |
| npm audit | Every commit | Frontend dependencies |
| Dependabot | Real-time | GitHub dependencies |

### Patching SLA

| Severity | Patch Timeline |
|----------|----------------|
| Critical (CVSS 9.0-10.0) | 24 hours |
| High (CVSS 7.0-8.9) | 7 days |
| Medium (CVSS 4.0-6.9) | 30 days |
| Low (CVSS 0.1-3.9) | 90 days |

### Vulnerability Response Workflow

1. **Detection:** Automated scan or manual report
2. **Triage:** Assign severity and owner
3. **Assessment:** Determine exploitability
4. **Remediation:** Patch or implement mitigation
5. **Verification:** Confirm fix with rescan
6. **Documentation:** Update vulnerability register

---

## Access Control

### Privilege Levels

| Role | Permissions | MFA Required |
|------|-------------|--------------|
| **System Admin** | Full system access | Yes (Hardware token) |
| **Security Admin** | Security config, audit logs | Yes (App-based) |
| **Trader** | Trading, view own data | Yes (App-based) |
| **Viewer** | Read-only access | No |
| **Support** | View logs, user management | Yes (App-based) |

### Access Review

- **Quarterly:** Review all admin access
- **Monthly:** Review dormant accounts (>30 days inactive)
- **On-demand:** Immediate review upon team changes

### Emergency Access

**Break-glass procedure:**
1. Request approval from CISO
2. Use emergency admin account (monitored)
3. Document all actions
4. Revoke access within 24 hours
5. Conduct post-access review

---

## Compliance Checks

### OWASP Top 10 Verification

| # | Control | Verification Method | Frequency |
|---|---------|---------------------|-----------|
| A01 | Access Control | Penetration test | Quarterly |
| A02 | Cryptographic Failures | Code review | Monthly |
| A03 | Injection | Automated scan (Bandit) | Every commit |
| A04 | Insecure Design | Architecture review | Quarterly |
| A05 | Security Misconfiguration | CIS benchmark scan | Monthly |
| A06 | Vulnerable Components | Dependency scan | Daily |
| A07 | Auth Failures | Brute-force testing | Quarterly |
| A08 | Data Integrity | Audit log review | Monthly |
| A09 | Logging Failures | Log analysis | Continuous |
| A10 | SSRF | Network policy review | Quarterly |

### GDPR Compliance

- **Data Retention:** 7 years (MiFID II requirement)
- **Right to Erasure:** Manual process - contact DPO
- **Data Portability:** Export via `/api/v1/user/export`
- **Breach Notification:** Within 72 hours to regulator

### Audit Requirements

**What we log:**
- All authentication attempts (success/failure)
- All trading decisions
- All admin actions
- All risk limit changes
- All circuit breaker events

**Log retention:** 7 years (immutable storage)

---

## Emergency Contacts

| Role | Contact | Phone |
|------|---------|-------|
| Security Team Lead | security@agentictrader.com | +1-XXX-XXX-XXXX |
| On-Call Engineer | oncall@agentictrader.com | PagerDuty |
| Compliance Officer | compliance@agentictrader.com | +1-XXX-XXX-XXXX |
| CISO | ciso@agentictrader.com | +1-XXX-XXX-XXXX |

---

## Tools & Resources

### Security Tools

- **SIEM:** ELK Stack / Splunk
- **Vulnerability Scanner:** Trivy, Bandit
- **Penetration Testing:** OWASP ZAP, Burp Suite
- **Secret Detection:** Gitleaks
- **Container Security:** Falco

### Documentation

- [Security Architecture](ARCHITECTURE.md)
- [Incident Response Plan](INCIDENT_RESPONSE.md)
- [Disaster Recovery Plan](DISASTER_RECOVERY.md)
- [Compliance Reports](COMPLIANCE/)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-03-01 | 1.0 | Initial version |

---

**Next Review Date:** 2026-06-01
