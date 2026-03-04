# Deployment Checklist - Prediction Market Intelligence Service

**Project:** Agentic Trader Platform
**Service:** Prediction Market Intelligence
**Target Environment:** Staging
**Date:** February 13, 2026
**Prepared By:** Implementation Agent

---

## 📋 Pre-Deployment Verification

### Code Quality Gates

- [x] All unit tests passing (33/33)
- [x] Code review completed (Grade: A)
- [x] Security review passed
  - [x] No hardcoded secrets
  - [x] Non-root user in Docker
  - [x] Minimal privilege principle applied
- [x] Linting passed (no warnings in Dockerfile after fixes)
- [x] Type hints present in Python code
- [x] Docstrings on public functions

### Docker Build Verification

- [x] Docker image builds without errors
- [x] Docker image builds without warnings (after casing fix)
- [x] Image size reasonable: 1.18 GB (< 2GB acceptable for staging)
- [x] Multi-stage build verified
- [x] Non-root user verified (appuser:1000)
- [x] Health check endpoint configured
- [x] All required ports exposed (8002)

### Docker Compose Validation

- [x] docker-compose.yml is valid YAML
- [x] All services defined
- [x] Service dependencies correct
- [x] Health checks configured
- [x] Volumes properly defined
- [x] Environment variables exported
- [x] Networks configuration correct

### Environment Configuration

- [x] .env file exists
- [x] All required variables defined
- [x] No secrets checked into version control
- [x] Default values reasonable
- [x] API keys set to placeholders (not actual keys)

---

## 🚀 Deployment Steps (Staging)

### Phase 1: Pre-Deployment (0.5 hours)

#### Step 1.1: Verify Infrastructure
```bash
# Check Docker version
docker --version
# Expected: Docker version 24.0+

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version 2.0+

# Check available disk space
df -h /
# Required: > 10 GB free space
```

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 1.2: Prepare Staging Environment
```bash
# Create staging directory
mkdir -p /opt/staging/prediction-intelligence
cd /opt/staging/prediction-intelligence

# Copy deployment configuration
cp docker-compose.yml /opt/staging/prediction-intelligence/
cp .env /opt/staging/prediction-intelligence/.env.staging
cp infrastructure/docker/Dockerfile /opt/staging/prediction-intelligence/
```

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 1.3: Configure Environment for Staging
```bash
# Edit .env.staging with staging values
vim /opt/staging/prediction-intelligence/.env.staging

# Required changes:
# - DATABASE_URL: point to staging database
# - REDIS_URL: point to staging Redis
# - LOG_LEVEL: DEBUG (for better troubleshooting)
# - PREDICTION_SERVICE_ENABLED: true
# - External API keys: empty or test keys only
```

**Configuration Checklist:**
- [ ] DATABASE_URL correct (staging postgres)
- [ ] REDIS_URL correct (staging redis)
- [ ] LOG_LEVEL set to DEBUG
- [ ] No production API keys present
- [ ] KALSHI_API_KEY is empty or test key
- [ ] POLYGON_RPC is public endpoint or test RPC

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

### Phase 2: Image Building (1-2 hours)

#### Step 2.1: Build Docker Image
```bash
cd /opt/staging/prediction-intelligence

# Build image
docker build \
  -f Dockerfile \
  -t prediction-intelligence:staging-v1.0.0 \
  -t prediction-intelligence:staging-latest \
  .

# Verify build
docker images prediction-intelligence:staging-*
```

**Expected Output:**
```
REPOSITORY                  TAG                    SIZE
prediction-intelligence     staging-v1.0.0         1.18GB
prediction-intelligence     staging-latest         1.18GB
```

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 2.2: Security Scan Docker Image
```bash
# Scan with Trivy (if installed)
trivy image prediction-intelligence:staging-latest

# Or pull Trivy in Docker
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --severity HIGH,CRITICAL \
  prediction-intelligence:staging-latest
```

**Acceptance Criteria:**
- [ ] No CRITICAL vulnerabilities
- [ ] HIGH vulnerabilities documented and accepted
- [ ] All findings logged in vulnerability report

**Vulnerability Report:** `[ ] Attached`
**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 2.3: Push Image to Registry (Optional)
```bash
# Tag for registry
docker tag prediction-intelligence:staging-latest \
  registry.staging.agentic-trader.com/prediction-intelligence:staging-v1.0.0

# Push to registry
docker push registry.staging.agentic-trader.com/prediction-intelligence:staging-v1.0.0
```

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

### Phase 3: Deployment (1-2 hours)

#### Step 3.1: Start Supporting Services
```bash
cd /opt/staging/prediction-intelligence

# Start only required dependencies first
docker-compose up -d postgres redis

# Wait for services to be healthy
sleep 30
docker-compose ps

# Verify health
docker-compose exec postgres pg_isready
docker-compose exec redis redis-cli ping
```

**Expected Output:**
```
postgres accepts connections
PONG
```

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 3.2: Deploy Prediction Intelligence Service
```bash
# Update docker-compose.yml with staging image
sed -i 's|prediction-intelligence:dev|prediction-intelligence:staging-v1.0.0|g' \
  docker-compose.yml

# Start the prediction service
docker-compose up -d prediction-intelligence

# Wait for service startup (15-30 seconds)
sleep 30

# Check service status
docker-compose ps prediction-intelligence
```

**Expected Output:**
```
NAME                        STATUS
prediction_intelligence     Up (healthy)
```

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 3.3: Verify Service Health
```bash
# Check health endpoint
curl -v http://localhost:8002/health

# Expected response:
# HTTP/1.1 200 OK
# {"status":"healthy","service":"prediction-intelligence","version":"1.0.0",...}

# Check readiness
curl http://localhost:8002/health/ready

# Expected response:
# {"ready":true,"message":"Service is ready"}

# Check API documentation
curl http://localhost:8002/docs
```

**Health Checks:**
- [ ] GET /health returns 200
- [ ] GET /health/ready returns ready=true
- [ ] GET /docs returns 200
- [ ] Service logs show no errors

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 3.4: Monitor Service Startup
```bash
# Watch service logs
docker-compose logs -f prediction-intelligence

# Expected log output during startup:
# 2026-02-13T12:00:00+01:00 INFO 🚀 Starting Prediction Market Intelligence Service...
# 2026-02-13T12:00:00+01:00 INFO 📊 Initializing DuckDB connection...
# 2026-02-13T12:00:02+01:00 INFO Uvicorn running on http://0.0.0.0:8002

# Exit logs with Ctrl+C after 30 seconds
```

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

### Phase 4: Integration Testing (1 hour)

#### Step 4.1: Test Service Connectivity
```bash
# Test from host machine
curl http://localhost:8002/health

# Test from within Docker network
docker-compose exec api-server curl http://prediction-intelligence:8002/health

# Test database connectivity (if applicable)
docker-compose exec prediction-intelligence \
  python -c "import duckdb; print('DuckDB OK')"
```

**Connectivity Tests:**
- [ ] Host → Service (localhost:8002) works
- [ ] Network → Service (docker network) works
- [ ] Database connections initialized
- [ ] Redis connections (if used) work

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 4.2: Run Integration Tests
```bash
# Navigate to test directory
cd /path/to/prediction-market-analysis/tests

# Run all tests
pytest . -v --tb=short

# Expected output: All tests should PASS
```

**Test Results:**
- [ ] All unit tests passing
- [ ] Health endpoint tests passing
- [ ] Docker compose tests passing
- [ ] No test failures or timeouts

**Test Report:** `[ ] Attached`
**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 4.3: Performance Baseline
```bash
# Run simple load test
ab -n 100 -c 10 http://localhost:8002/health

# Expected results:
# Requests per second: > 50
# Mean response time: < 100ms
# Failed requests: 0
```

**Performance Metrics:**
- [ ] > 50 req/sec
- [ ] < 100ms latency
- [ ] 0 errors
- [ ] No memory leaks detected

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

### Phase 5: Post-Deployment (1 hour)

#### Step 5.1: Document Deployment
```bash
# Create deployment log
cat > /opt/staging/deployment.log << EOF
Deployment Date: $(date)
Image Tag: prediction-intelligence:staging-v1.0.0
Services Started:
EOF

docker-compose ps >> /opt/staging/deployment.log
```

**Documentation Checklist:**
- [ ] Deployment date recorded
- [ ] Image tag documented
- [ ] Service versions recorded
- [ ] Configuration backed up
- [ ] Logs archived

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 5.2: Set Up Monitoring
```bash
# Configure application monitoring
# - Check service logs regularly
# - Monitor CPU/Memory usage
# - Monitor network I/O
# - Set up alerts for health check failures

# Example: Monitor logs
docker-compose logs --tail=100 --follow prediction-intelligence &
```

**Monitoring Setup:**
- [ ] Log aggregation configured
- [ ] Metrics collection enabled
- [ ] Alerts configured for failures
- [ ] Dashboard created (if applicable)
- [ ] Runbook prepared for on-call team

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

#### Step 5.3: Backup & Rollback Plan
```bash
# Save current state for rollback
docker save prediction-intelligence:staging-v1.0.0 | gzip > \
  /opt/backup/prediction-intelligence-staging-v1.0.0.tar.gz

# Document rollback procedure
cat > /opt/staging/ROLLBACK_PROCEDURE.md << 'EOF'
## Rollback Procedure

If deployment fails:

1. Stop current service:
   docker-compose down prediction-intelligence

2. Restore previous image:
   docker load < /opt/backup/prediction-intelligence-staging-previous.tar.gz

3. Update docker-compose.yml with previous tag

4. Restart service:
   docker-compose up -d prediction-intelligence

5. Verify health:
   curl http://localhost:8002/health
EOF
```

**Backup & Recovery:**
- [ ] Images backed up
- [ ] Images archived with timestamps
- [ ] Rollback procedure documented
- [ ] Rollback tested (at least conceptually)
- [ ] Emergency contacts on call

**Status:** `[ ] Done`
**Completed By:** ___________ | **Date:** ___________

---

## ✅ Sign-Off & Approval

### Deployment Verification Summary

| Phase | Status | Comments |
|-------|--------|----------|
| Pre-Deployment | `[ ]` | ____ |
| Building | `[ ]` | ____ |
| Deployment | `[ ]` | ____ |
| Testing | `[ ]` | ____ |
| Post-Deployment | `[ ]` | ____ |

### Quality Gates

| Gate | Pass/Fail | Notes |
|------|-----------|-------|
| Code Review | ✅ PASS | Grade A |
| Security Scan | `[ ]` | |
| All Tests | ✅ PASS | 33/33 |
| Performance | `[ ]` | `____ms latency` |
| Integration | `[ ]` | |

### Sign-Off

**Technical Lead Approval:**
- Name: _____________________
- Date: _____________________
- Signature: _____________________

**QA Approval:**
- Name: _____________________
- Date: _____________________
- Signature: _____________________

**Deployment Manager Approval:**
- Name: _____________________
- Date: _____________________
- Signature: _____________________

---

## 📞 Deployment Support

### Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Service Owner | _____ | _____ | _____ |
| Technical Lead | _____ | _____ | _____ |
| DevOps Engineer | _____ | _____ | _____ |
| On-Call Support | _____ | _____ | _____ |

### Support Hours

- **Business Hours:** 9 AM - 6 PM CET
- **Emergency:** 24/7 on-call roster

### Incident Response

If deployment fails:
1. Contact Service Owner immediately
2. Check logs: `docker-compose logs prediction-intelligence`
3. Verify dependencies: `docker-compose ps`
4. Execute rollback if needed (see Rollback Plan above)
5. Post-mortem within 24 hours

---

## 📚 Reference Documentation

- [Code Review Report](EPIC_01_CODE_REVIEW.md)
- [Dockerfile Reference](../prediction-market-analysis/Dockerfile)
- [Docker Compose Config](../docker-compose.yml)
- [Environment Variables](../.env)
- [API Documentation](http://localhost:8002/docs) *after deployment*

---

**Deployment Status:** Ready for Staging Deployment
**Estimated Duration:** 4-6 hours (including all verification)
**Next Steps:** Monitor for 48 hours, then promote to production (requires separate approval)
