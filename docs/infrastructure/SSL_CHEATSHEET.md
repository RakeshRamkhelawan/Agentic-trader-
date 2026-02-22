# SSL/TLS Cheatsheet

Quick commands for HTTPS setup and management.

---

## Let's Encrypt (Recommended)

### Initial Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (standalone - stops nginx temporarily)
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Or with nginx plugin (automatic config)
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

### Certificate Paths

| File | Path |
|------|------|
| Certificate | `/etc/letsencrypt/live/yourdomain.com/fullchain.pem` |
| Private Key | `/etc/letsencrypt/live/yourdomain.com/privkey.pem` |
| Chain | `/etc/letsencrypt/live/yourdomain.com/chain.pem` |
| Cert only | `/etc/letsencrypt/live/yourdomain.com/cert.pem` |

### Renewal

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# View renewal timer
sudo systemctl list-timers | grep certbot
```

---

## Self-Signed (Dev Only)

```bash
# Generate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/CN=localhost"

# Trust on macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain server.crt

# Trust on Ubuntu
sudo cp server.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

---

## Nginx Config

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.3;

    # WebSocket support
    location /ws {
        proxy_pass http://backend:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Testing

```bash
# Check certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check expiry
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# SSL Labs test
# https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

# Test HTTPS
curl -I https://yourdomain.com

# Test WebSocket (secure)
wscat -c wss://api.yourdomain.com/ws
```

---

## Docker Compose

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl/certbot/conf:/etc/letsencrypt:ro
      - ./ssl/certbot/www:/var/www/certbot:ro

  certbot:
    image: certbot/certbot
    volumes:
      - ./ssl/certbot/conf:/etc/letsencrypt
      - ./ssl/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h; done'"
```

---

## Common Issues

| Error | Fix |
|-------|-----|
| `Failed to connect to port 80` | Stop nginx temporarily: `sudo systemctl stop nginx` |
| `Rate limited` | Wait 1 hour or use staging: `--staging` |
| `Permission denied` | Run with sudo |
| `Certificate not found` | Check path: `sudo certbot certificates` |

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `sudo certbot certificates` | List all certs |
| `sudo certbot delete --cert-name domain.com` | Remove cert |
| `sudo certbot revoke --cert-name domain.com` | Revoke cert |
| `sudo nginx -t` | Test nginx config |
| `sudo systemctl reload nginx` | Reload nginx |
