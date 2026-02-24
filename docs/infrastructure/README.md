# Infrastructure Documentation

> Deployment, SSL, and infrastructure guides

---

## Documentation Files

| File | Description |
|------|-------------|
| [HTTPS_SSL_SETUP.md](./HTTPS_SSL_SETUP.md) | Complete SSL/TLS setup guide with Let's Encrypt |
| [SSL_CHEATSHEET.md](./SSL_CHEATSHEET.md) | Quick reference commands for SSL management |

---

## Quick Links

### SSL/HTTPS

- **Let's Encrypt Setup** → [HTTPS_SSL_SETUP.md#lets-encrypt-setup-recommended](./HTTPS_SSL_SETUP.md#lets-encrypt-setup-recommended)
- **Nginx SSL Config** → [HTTPS_SSL_SETUP.md#nginx-ssl-configuration](./HTTPS_SSL_SETUP.md#nginx-ssl-configuration)
- **Kubernetes SSL** → [HTTPS_SSL_SETUP.md#kubernetes-ssl-setup](./HTTPS_SSL_SETUP.md#kubernetes-ssl-setup)
- **Quick Commands** → [SSL_CHEATSHEET.md](./SSL_CHEATSHEET.md)

---

## Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                            │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS (443)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      NGINX/LOAD BALANCER                    │
│  - SSL termination (Let's Encrypt)                          │
│  - Reverse proxy to services                                │
│  - WebSocket upgrade support                                │
└───────┬───────────────────────────────┬─────────────────────┘
        │                               │
        ▼                               ▼
┌───────────────┐              ┌─────────────────┐
│   FRONTEND    │              │     BACKEND     │
│  (React/Vite) │              │   (FastAPI)     │
│  - Static     │              │  - REST API     │
│    files      │              │  - WebSocket    │
│  Port: 80/443 │              │  - MCP Server   │
│               │              │  Port: 8000     │
└───────────────┘              └─────────────────┘
```

---

## Environment Setup

### Development (Local HTTP)

```bash
# .env (frontend)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# No SSL needed for local development
```

### Production (HTTPS)

```bash
# .env (frontend)
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws

# SSL certificate required
```

---

## Common Tasks

### Obtain SSL Certificate

```bash
# Using Let's Encrypt + Certbot
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Using Docker
./scripts/init-ssl.sh yourdomain.com
```

### Renew Certificate

```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal
```

### Test SSL Configuration

```bash
# SSL Labs test
curl -I https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

# Command line check
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

## Related Documentation

- [WebSocket Implementation](../websockets/WEBSOCKET_IMPLEMENTATION.md)
- [Docker Deployment](../DOCKER_DEPLOYMENT.md)
- [CI/CD Setup](../CI_CD_SETUP.md)
