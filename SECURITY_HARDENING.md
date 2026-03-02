# Security Hardening Guide

> **Document Version:** 1.0  
> **Date:** March 2026  
> **Status:** IMPLEMENTED

This document describes the security hardening measures implemented in the Agentic Trader Platform.

---

## 🔒 Implemented Security Measures

### 1. Production-Safe Defaults (HIGH)

#### DEBUG Mode
- **Before:** `DEBUG: bool = True` (default)
- **After:** `DEBUG: bool = False` (default)
- **Impact:** Prevents information leakage in production
- **File:** `backend/core/config/settings.py`

#### Environment Mode
- **Before:** `ENV: str = "development"` (default)
- **After:** `ENV: str = "production"` (default)
- **Impact:** Ensures production settings by default
- **File:** `backend/core/config/settings.py`

### 2. Mandatory JWT Secret (HIGH)

- **Before:** Fallback to `"dev-secret-key"` if not set
- **After:** **REQUIRED** - No fallback, application fails to start without it
- **Validation:** Minimum 32 characters
- **Files:**
  - `backend/core/config/settings.py`
  - `backend/api/auth_api.py`

**Error if not set:**
```
pydantic.error_wrappers.ValidationError: JWT_SECRET_KEY is required
```

### 3. Secure Password Hashing (HIGH)

- **Before:** SHA256 fallback when bcrypt unavailable
- **After:** **bcrypt ONLY** - Application raises RuntimeError if passlib unavailable
- **Impact:** Prevents weak password storage
- **File:** `backend/api/auth_api.py`

**Migration required for existing SHA256 passwords:**
Users with SHA256 hashed passwords must reset their password.

### 4. Security Headers Middleware (MEDIUM)

New middleware adds the following headers to all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS protection (legacy) |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HSTS |
| `Content-Security-Policy` | `default-src 'self'` | CSP |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Privacy |
| `Permissions-Policy` | `geolocation=(), ...` | Feature restrictions |

- **File:** `backend/api/security_middleware.py`

### 5. CORS Configuration Hardening (MEDIUM)

- **Before:** `allow_origins=["*"]` (wildcard)
- **After:** Specific origins only, no wildcard
- **Before:** `allow_methods=["*"]` (all methods)
- **After:** Specific methods only: `GET, POST, PUT, DELETE, OPTIONS`
- **Before:** `allow_headers=["*"]` (all headers)
- **After:** Specific headers only
- **File:** `backend/api/main.py`

### 6. Deprecated API Fixes (MEDIUM)

- **Before:** `Query(..., regex="...")` (deprecated)
- **After:** `Query(..., pattern="...")` (current)
- **File:** `backend/api/routers/routing.py`

### 7. Legacy Code Archive (LOW)

- Added deprecation notice to archive directory
- Marked as NOT FOR PRODUCTION USE
- Planned removal: Q2 2026
- **File:** `backend/agents/archive/README.md`

---

## 🚀 Migration Guide

### For Developers

1. **Update your .env file:**
   ```bash
   # Add this (generate with: openssl rand -hex 32)
   JWT_SECRET_KEY=your-secure-random-key-here-min-32-chars
   
   # For development
   DEBUG=true
   ENV=development
   ```

2. **Install passlib (REQUIRED):**
   ```bash
   pip install passlib[bcrypt]
   ```

3. **Update CORS origins (if needed):**
   ```bash
   BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
   ```

### For Production

1. **Required Environment Variables:**
   ```bash
   # These MUST be set - no defaults
   JWT_SECRET_KEY=<generate-secure-key>
   DEBUG=false
   ENV=production
   
   # Optional but recommended
   BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
   ```

2. **Verify Security Headers:**
   ```bash
   curl -I https://your-api.com/health
   # Check for X-Content-Type-Options, X-Frame-Options, etc.
   ```

---

## 📋 Security Checklist

Before deploying to production:

- [ ] `JWT_SECRET_KEY` is set (min 32 chars)
- [ ] `DEBUG=false`
- [ ] `ENV=production`
- [ ] `passlib[bcrypt]` is installed
- [ ] CORS origins are restricted to production domains
- [ ] Security headers are present in responses
- [ ] No wildcard `*` in CORS origins
- [ ] `.env` file is not committed to git
- [ ] Redis protected-mode is configured correctly
- [ ] SSL/TLS certificates are installed

---

## 🔍 Verification

### Test Security Headers
```bash
curl -I http://localhost:8000/api/v1/health
```

Expected headers:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Test JWT Secret Required
```bash
# Unset the secret
unset JWT_SECRET_KEY

# Try to start the app
python -m backend.api.main

# Should fail with validation error
```

### Test Password Hashing
```python
from backend.api.auth_api import hash_password

# This should work (bcrypt)
hash_password("test-password")

# If passlib not installed, should raise RuntimeError
```

---

## 📝 Related Documents

- [PORT_ALLOCATION_SSOT.md](PORT_ALLOCATION_SSOT.md) - Port configuration
- [CODE_REVIEW_AUDIT_REPORT.md](CODE_REVIEW_AUDIT_REPORT.md) - Full audit report
- `.env.example` - Environment variable template

---

## 🆘 Troubleshooting

### "JWT_SECRET_KEY is required"
**Solution:** Set the environment variable:
```bash
export JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### "Passlib/bcrypt is required"
**Solution:** Install the package:
```bash
pip install passlib[bcrypt]
```

### "CORS errors in development"
**Solution:** Set explicit origins:
```bash
export BACKEND_CORS_ORIGINS='["http://localhost:3000"]'
```

---

*Document maintained by: Development Team*  
*Last updated: March 2026*
