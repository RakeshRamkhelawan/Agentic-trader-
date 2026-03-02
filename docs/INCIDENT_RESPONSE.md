# Incident Response Plan - Agentic Trader Platform

> **Status:** ACTIVE  
> **Classification:** CONFIDENTIAL  
> **Owner:** Incident Response Team

## Overview

This document defines the incident response procedures for the Agentic Trader Platform. Given the financial nature of the platform, rapid response is critical to prevent financial loss and maintain regulatory compliance.

## Incident Classification

### Financial Incidents (P0)

| Type | Description | Example |
|------|-------------|---------|
| **F1** | Unauthorized Trading | Account takeover with trading activity |
| **F2** | Trading System Failure | Circuit breaker fails to trip |
| **F3** | Price Manipulation | Oracle/circuit breaker bypass |
| **F4** | Fund Loss | Direct theft from accounts |

### Security Incidents (P1)

| Type | Description | Example |
|------|-------------|---------|
| **S1** | Authentication Bypass | JWT validation failure |
| **S2** | Data Breach | Unauthorized data access |
| **S3** | Injection Attack | SQL/command injection |
| **S4** | DoS Attack | Service unavailability |

### Operational Incidents (P2)

| Type | Description | Example |
|------|-------------|---------|
| **O1** | Performance Degradation | API latency > 1s |
| **O2** | Data Loss | Corrupted trade records |
| **O3** | Compliance Violation | Missing audit logs |

## Response Team

### Roles

| Role | Responsibilities | Primary |
|------|------------------|---------|
| **Incident Commander** | Overall coordination, decision making | On-call Engineer |
| **Security Lead** | Security assessment, forensics | Security Team |
| **Technical Lead** | System recovery, fixes | Senior Developer |
| **Communications** | Stakeholder updates | Product Manager |
| **Compliance** | Regulatory notifications | Compliance Officer |

### Contact Tree

```
Incident Detected
    |
    v
On-Call Engineer (5 min)
    |
    +---> P0 (Financial) ----> CISO + Legal (15 min)
    |
    +---> P1 (Security) ----> Security Team (30 min)
    |
    +---> P2 (Operational) --> Engineering Manager (1 hour)
```

## Response Procedures

### P0 - Unauthorized Trading

#### Detection
- Alert: `CIRCUIT_BREAKER_TRIP` or `UNUSUAL_TRADING_PATTERN`
- Metric: Trading volume > 300% of average

#### Immediate Response (0-15 min)

1. **STOP TRADING IMMEDIATELY**
   ```python
   # Emergency kill switch
   from backend.governance.circuit_breaker import CircuitBreaker
   
   breaker = CircuitBreaker(db_session=session)
   await breaker.emergency_shutdown()
   ```

2. **ISOLATE AFFECTED ACCOUNTS**
   ```sql
   -- Disable trading for affected account
   UPDATE users 
   SET trading_enabled = false, 
       account_locked = true 
   WHERE id = 'SUSPECT_ACCOUNT_ID';
   
   -- Force logout all sessions
   DELETE FROM user_sessions 
   WHERE user_id = 'SUSPECT_ACCOUNT_ID';
   ```

3. **PRESERVE EVIDENCE**
   ```bash
   # Capture current state
   kubectl logs deployment/api --since=1h > /tmp/incident_logs_$(date +%s).txt
   
   # Export recent trades
   clickhouse-client --query="
     SELECT * FROM trades 
     WHERE timestamp > now() - INTERVAL 1 HOUR
     FORMAT CSV
   " > /tmp/recent_trades_$(date +%s).csv
   
   # Database snapshot
   pg_dump $DATABASE_URL > /tmp/db_snapshot_$(date +%s).sql
   ```

#### Assessment (15-60 min)

1. **Determine Scope**
   - Affected accounts
   - Financial impact (realized/unrealized)
   - Attack vector (credentials, session hijacking, etc.)

2. **Analyze Logs**
   ```bash
   # Check authentication patterns
   grep "auth" /tmp/incident_logs_*.txt | grep "SUSPECT_ACCOUNT_ID"
   
   # Check IP addresses
   grep "SUSPECT_ACCOUNT_ID" /tmp/incident_logs_*.txt | awk '{print $5}' | sort | uniq -c
   
   # Check trade history
   grep "EXECUTE" /tmp/incident_logs_*.txt | tail -100
   ```

#### Recovery (1-4 hours)

1. **Block Attack Vector**
   - If IP-based: Block at firewall
   - If credential-based: Force password reset
   - If session-based: Revoke all tokens

2. **Verify System Integrity**
   ```bash
   # Run security checks
   bandit -r backend/
   
   # Check for persistence
   ps aux | grep -i "suspicious"
   netstat -tulpn | grep -v "expected"
   ```

3. **Gradual Restart**
   - Enable trading in paper mode first
   - Monitor for 1 hour
   - Enable live trading with increased monitoring

#### Post-Incident (24-48 hours)

1. **Financial Reconciliation**
   - Calculate exact losses
   - Identify affected counterparties
   - Prepare compensation if applicable

2. **Regulatory Reporting**
   - File incident report with regulator
   - Notify affected customers
   - Update compliance records

### P1 - Authentication Bypass

#### Detection
- Alert: `JWT_VALIDATION_FAILURE` or `UNAUTHORIZED_ACCESS_ATTEMPT`

#### Response

1. **Immediate Actions**
   ```bash
   # Rotate JWT secret immediately
   kubectl patch secret jwt-secret -p='{"data":{"JWT_SECRET_KEY":"'$(openssl rand -base64 32 | tr -d '\n')'"}}'
   
   # Revoke all existing sessions
   redis-cli FLUSHDB  # Or selectively delete auth tokens
   
   # Force re-authentication
   kubectl rollout restart deployment/api
   ```

2. **Verify Fix**
   ```bash
   # Test authentication
   curl -H "Authorization: Bearer $OLD_TOKEN" http://api/health
   # Should return 401
   
   curl -H "Authorization: Bearer $NEW_TOKEN" http://api/health
   # Should return 200
   ```

### P1 - SQL Injection

#### Detection
- Alert: `SQL_INJECTION_ATTEMPT` or `UNUSUAL_QUERY_PATTERN`

#### Response

1. **Immediate Actions**
   ```sql
   -- Check for successful injection
   SELECT * FROM pg_stat_activity 
   WHERE query LIKE '%drop%' OR query LIKE '%delete%';
   
   -- Check audit log for data access
   SELECT * FROM audit_log 
   WHERE timestamp > NOW() - INTERVAL '1 hour'
   AND action = 'DATA_ACCESS'
   ORDER BY timestamp DESC;
   ```

2. **If Data Access Confirmed**
   - Identify accessed records
   - Notify affected tenants (GDPR requirement)
   - Rotate database credentials
   - Enable query logging (if not already)

## Communication Templates

### Internal Notification (Slack)

```
🚨 INCIDENT ALERT 🚨

Severity: P0 - Critical
Type: Unauthorized Trading
Status: Investigating

Impact: Account XYZ123 - $50,000 in unauthorized trades
Actions Taken: Trading halted, account locked
Next Update: 30 minutes

Incident Commander: @oncall-engineer
```

### Customer Notification (Email)

```
Subject: Security Incident Notification - Account Temporary Suspension

Dear [Customer Name],

We are writing to inform you of a security incident affecting your account 
([Account ID]).

What Happened:
At [Time], we detected unauthorized trading activity on your account. 
As a precautionary measure, we have:
- Suspended all trading on your account
- Locked your account pending investigation
- Reset your authentication credentials

Impact:
[X] trades were executed without your authorization.
We are conducting a full investigation and will provide updates within 24 hours.

What We're Doing:
- Investigating the root cause
- Reversing unauthorized trades where possible
- Enhancing security measures

What You Should Do:
- Review your account statement
- Contact us immediately if you notice any other suspicious activity
- Enable two-factor authentication when your account is restored

We sincerely apologize for this incident and any inconvenience caused.

Contact: security@agentictrader.com
Reference: INC-2026-XXXX
```

### Regulatory Notification

```
To: [Regulator]
Subject: Incident Report - Reference: INC-2026-XXXX

Date of Incident: [Date]
Time of Detection: [Time]
Nature of Incident: [Unauthorized Access / System Failure / etc.]

Description:
[Detailed description of the incident]

Impact:
- Number of affected customers: [X]
- Financial impact: $[Amount]
- Data compromised: [Yes/No, details]

Root Cause:
[Initial assessment of root cause]

Remediation:
[Steps taken to resolve the incident]

Prevention:
[Measures to prevent recurrence]

Contact: compliance@agentictrader.com
```

## Recovery Checklists

### System Recovery

- [ ] Kill switch deactivated
- [ ] All services healthy
- [ ] Database connections stable
- [ ] Redis/cache operational
- [ ] External APIs responding
- [ ] Circuit breaker in CLOSED state
- [ ] Risk limits verified
- [ ] Audit logging active

### Security Verification

- [ ] All credentials rotated
- [ ] No unauthorized accounts
- [ ] Network policies active
- [ ] WAF rules updated
- [ ] Security scans passing
- [ ] Monitoring alerts functional
- [ ] Incident response team notified

### Business Verification

- [ ] All trades reconciled
- [ ] Customer balances correct
- [ ] Regulatory notifications sent
- [ ] Customer communications sent
- [ ] Insurance claims filed (if applicable)
- [ ] Post-mortem scheduled

## Lessons Learned Process

1. **Timeline Creation**
   - Exact sequence of events
   - Detection to resolution times
   - Communication delays

2. **Root Cause Analysis**
   - 5 Whys technique
   - Contributing factors
   - Missed opportunities

3. **Improvement Actions**
   - Technical fixes
   - Process improvements
   - Training needs

4. **Documentation**
   - Update runbooks
   - Revise procedures
   - Share learnings

## Testing

### Tabletop Exercises

Conduct quarterly exercises simulating:
- Unauthorized trading
- Data breach
- Ransomware attack
- Insider threat

### Chaos Engineering

Monthly chaos tests:
```bash
# Simulate pod failure
kubectl delete pod -l app=api --force

# Simulate database latency
# (using chaos mesh or similar)

# Simulate network partition
# (using istio fault injection)
```

## Appendix

### A. Useful Commands

```bash
# Check system health
kubectl get pods -n agentic-trader
kubectl top nodes
kubectl top pods

# View logs
stern -n agentic-trader api

# Database queries
psql $DATABASE_URL -c "SELECT count(*) FROM users WHERE last_login > NOW() - INTERVAL '1 day';"

# Redis inspection
redis-cli INFO
redis-cli MONITOR  # Careful in production!

# Network diagnostics
kubectl exec -it deployment/api -- netstat -tulpn
kubectl exec -it deployment/api -- ss -tulpn
```

### B. External Resources

- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [SANS Incident Handler's Handbook](https://www.sans.org)
- [ISO 27035 Incident Management](https://www.iso.org)

---

**Document Owner:** Security Team  
**Review Cycle:** Quarterly  
**Next Review:** 2026-06-01
