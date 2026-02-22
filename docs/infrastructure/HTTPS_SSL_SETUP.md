# HTTPS/SSL Setup Guide

> Complete guide for securing Agentic Trader Platform with HTTPS/SSL certificates

---

## Table of Contents

1. [Overview](#overview)
2. [Certificate Options](#certificate-options)
3. [Let's Encrypt Setup (Recommended)](#lets-encrypt-setup-recommended)
4. [Cloud Provider SSL](#cloud-provider-ssl)
5. [Self-Signed Certificates (Dev Only)](#self-signed-certificates-dev-only)
6. [Nginx SSL Configuration](#nginx-ssl-configuration)
7. [Kubernetes SSL Setup](#kubernetes-ssl-setup)
8. [Certificate Renewal](#certificate-renewal)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Agentic Trader Platform requires HTTPS for:
- **Production security** (TLS 1.3)
- **WebSocket connections** (WSS)
- **Auth0 authentication** callbacks
- **API security** (JWT over HTTPS)

### SSL/TLS Requirements

| Component | Protocol | Certificate Type |
|-----------|----------|------------------|
| Web Frontend | TLS 1.3 | Let's Encrypt / Commercial |
| REST API | TLS 1.3 | Let's Encrypt / Commercial |
| WebSocket | WSS | Same as API |
| MCP Server | stdio (local) | N/A |

---

## Certificate Options

### 1. Let's Encrypt (FREE - Recommended)
- **Cost**: Free
- **Validity**: 90 days (auto-renewal)
- **Validation**: HTTP-01 or DNS-01
- **Wildcard**: Supported with DNS-01
- **Best for**: Production, staging

### 2. Commercial Certificate
- **Cost**: $50-500/year
- **Validity**: 1-2 years
- **Validation**: Domain/Organization/Extended
- **Wildcard**: Yes
- **Best for**: Enterprise, compliance requirements

### 3. Cloud Provider (AWS/GCP/Azure)
- **AWS**: ACM (free with load balancer)
- **GCP**: Google-managed SSL (free)
- **Azure**: Key Vault certificates
- **Best for**: Cloud-native deployments

---

## Let's Encrypt Setup (Recommended)

### Method 1: Certbot (Bare Metal/VM)

```bash
# Install Certbot
# Ubuntu/Debian
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx

# macOS
brew install certbot
```

#### Obtain Certificate (Standalone)

```bash
# Stop nginx temporarily (port 80 needed)
sudo systemctl stop nginx

# Obtain certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  -d api.yourdomain.com

# Certificate location:
# /etc/letsencrypt/live/yourdomain.com/
# - fullchain.pem (certificate + intermediates)
# - privkey.pem (private key)
```

#### Obtain Certificate (Nginx plugin)

```bash
# Automatic nginx configuration
sudo certbot --nginx \
  -d yourdomain.com \
  -d www.yourdomain.com \
  -d api.yourdomain.com

# Certbot automatically updates nginx config
```

### Method 2: Docker (Recommended for our stack)

```yaml
# docker-compose.ssl.yml
version: '3.8'

services:
  certbot:
    image: certbot/certbot
    container_name: certbot
    volumes:
      - ./ssl/certbot/conf:/etc/letsencrypt
      - ./ssl/certbot/www:/var/www/certbot
      - ./ssl/certbot/log:/var/log/letsencrypt
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h; done'"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl/certbot/conf:/etc/letsencrypt:ro
      - ./ssl/certbot/www:/var/www/certbot:ro
      - ./infrastructure/docker/nginx.ssl.conf:/etc/nginx/nginx.conf:ro
```

```bash
# Initial certificate request
docker-compose -f docker-compose.ssl.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email \
  -d yourdomain.com \
  -d api.yourdomain.com

# Start services
docker-compose -f docker-compose.ssl.yml up -d
```

---

## Nginx SSL Configuration

### Complete SSL Nginx Config

```nginx
# infrastructure/docker/nginx.ssl.conf

# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com api.yourdomain.com;
    
    # Certbot challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Configuration (A+ Rating)
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Frontend
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript;
    
    # Static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # React Router
    location / {
        try_files $uri $uri/ /index.html;
    }
}

# HTTPS - API server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Certificates (same as main)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # API proxy
    location / {
        proxy_pass http://api-server:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket proxy (WSS)
    location /ws {
        proxy_pass http://api-server:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## Kubernetes SSL Setup

### Using cert-manager + Let's Encrypt

```yaml
# infrastructure/k8s/cert-manager/issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

```yaml
# infrastructure/k8s/ingress-ssl.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agentic-trader-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "86400"
spec:
  tls:
  - hosts:
    - yourdomain.com
    - api.yourdomain.com
    secretName: agentic-trader-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-server
            port:
              number: 8000
```

### Install cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager

# Apply issuer
kubectl apply -f infrastructure/k8s/cert-manager/issuer.yaml

# Apply ingress
kubectl apply -f infrastructure/k8s/ingress-ssl.yaml
```

---

## Self-Signed Certificates (Dev Only)

```bash
# Create certificates directory
mkdir -p ssl/local

# Generate private key
openssl genrsa -out ssl/local/server.key 2048

# Generate self-signed certificate
openssl req -new -x509 -sha256 -key ssl/local/server.key \
  -out ssl/local/server.crt -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Trust certificate (macOS)
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ssl/local/server.crt

# Trust certificate (Ubuntu)
sudo cp ssl/local/server.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

```yaml
# docker-compose.local-ssl.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./ssl/local/server.crt:/etc/nginx/ssl/server.crt:ro
      - ./ssl/local/server.key:/etc/nginx/ssl/server.key:ro
      - ./infrastructure/docker/nginx.local-ssl.conf:/etc/nginx/conf.d/default.conf:ro
```

---

## Certificate Renewal

### Automatic Renewal

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# View renewal logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Systemd Timer (Linux)

```bash
# Check certbot timer
sudo systemctl status certbot.timer
sudo systemctl list-timers | grep certbot

# Manual trigger
sudo systemctl start certbot.service
```

### Docker Renewal

```bash
# Manual renewal
docker-compose -f docker-compose.ssl.yml run --rm certbot renew

# Or restart certbot container (auto-renewal loop)
docker-compose -f docker-compose.ssl.yml restart certbot
```

---

## Troubleshooting

### Certificate Not Found

```bash
# Check certificate status
sudo certbot certificates

# Verify paths
ls -la /etc/letsencrypt/live/yourdomain.com/
```

### Nginx SSL Errors

```bash
# Test nginx config
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Verify SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### Port 80/443 Already in Use

```bash
# Find process using port 80
sudo lsof -i :80
sudo lsof -i :443

# Kill process or change nginx config
sudo kill -9 <PID>
```

### Rate Limiting

Let's Encrypt has rate limits:
- **Duplicate certificates**: 5 per week
- **New orders**: 300 per 3 hours
- **Failed validations**: 5 per hour

```bash
# Check if rate limited
curl -I https://acme-v02.api.letsencrypt.org/directory

# Use staging server for testing
sudo certbot --staging certonly --standalone -d yourdomain.com
```

### Mixed Content Warnings

If you see "Mixed Content" errors after enabling HTTPS:

```javascript
// frontend/src/services/api.ts
const API_URL = window.location.protocol === 'https:' 
  ? 'https://api.yourdomain.com' 
  : 'http://localhost:8000';

const WS_URL = window.location.protocol === 'https:'
  ? 'wss://api.yourdomain.com/ws'
  : 'ws://localhost:8000/ws';
```

---

## SSL Testing

### Online Tools

```bash
# SSL Labs Test
https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

# Security Headers Check
https://securityheaders.com/?q=yourdomain.com

# SSL Checker
https://www.sslchecker.com/sslchecker
```

### Command Line

```bash
# Check certificate expiry
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Full certificate info
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -text

# Check TLS version
curl -I -v --tlsv1.3 https://yourdomain.com 2>&1 | grep "TLS"
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Obtain cert | `sudo certbot certonly --standalone -d domain.com` |
| Renew certs | `sudo certbot renew` |
| Test config | `sudo nginx -t` |
| Reload nginx | `sudo systemctl reload nginx` |
| View certs | `sudo certbot certificates` |
| Revoke cert | `sudo certbot revoke --cert-name domain.com` |
| Delete cert | `sudo certbot delete --cert-name domain.com` |

---

## Summary

| Environment | SSL Method | Auto-Renewal |
|-------------|------------|--------------|
| Development | Self-signed | Manual |
| Staging | Let's Encrypt Staging | Yes |
| Production | Let's Encrypt | Yes |
| Enterprise | Commercial cert | Manual |

**Next Steps**:
1. Choose your SSL method
2. Configure DNS A records
3. Obtain certificate
4. Configure nginx
5. Test with SSL Labs
