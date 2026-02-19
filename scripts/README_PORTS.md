# Port Configuration Guide

## Overview

The Agentic Trader Platform uses Docker Compose for orchestration. When default ports are occupied by other projects, you can easily switch to alternative ports.

## Quick Start

### Windows (PowerShell)

```powershell
# Check port availability
.\scripts\switch-ports.ps1 -Mode check

# Switch to alternative ports (if defaults are occupied)
.\scripts\switch-ports.ps1 -Mode alt

# Restore default ports
.\scripts\switch-ports.ps1 -Mode default
```

### macOS/Linux (Bash)

```bash
# Check port availability
make check-ports
# or
bash scripts/docker-dev.sh check-ports

# Switch to alternative ports
make alt-ports
# or
bash scripts/docker-dev.sh alt-ports

# Restore default ports
make default-ports
# or
bash scripts/docker-dev.sh default-ports
```

## Default vs Alternative Ports

| Service | Default Port | Alternative Port |
|---------|-------------|------------------|
| API Server | 8000 | 9000 |
| Frontend | 5173 | 6173 |
| PostgreSQL | 5456 | 6456 |
| Redis | 6380 | 7380 |
| ClickHouse HTTP | 8124 | 9124 |
| ChromaDB | 8005 | 9005 |
| Redpanda Kafka | 9094 | 10094 |
| Redpanda Console | 8081 | 9081 |
| Prometheus | 9091 | 10091 |
| Grafana | 3100 | 4100 |
| Federated Triad | 8001 | 10001 |

## Access URLs

### Default Ports
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Alternative Ports
- Frontend: http://localhost:6173
- API: http://localhost:9000
- API Docs: http://localhost:9000/docs

## How It Works

1. **Port Detection**: The system checks if default ports (8000, 5173, etc.) are available
2. **Automatic Suggestion**: If ports are occupied, suggests alternative configuration
3. **Override File**: Uses `docker-compose.override.yml` to customize port mappings
4. **Backup**: Original configuration is saved to `docker-compose.override.yml.backup`

## Troubleshooting

### "Port already in use" errors
```powershell
# Check which process is using the port
netstat -ano | findstr :8000

# Switch to alternative ports
.\scripts\switch-ports.ps1 -Mode alt
```

### Restore after switching
```powershell
# Restore original ports
.\scripts\switch-ports.ps1 -Mode default
```

### Manual override
You can manually edit `docker-compose.override.yml` to use any ports you prefer.

## Files

- `docker-compose.override.yml` - Active port configuration
- `docker-compose.override.yml.backup` - Original configuration (auto-created)
- `scripts/switch-ports.ps1` - Windows port switcher
- `scripts/use-alt-ports.sh` - Linux/Mac alternative ports script
- `scripts/use-default-ports.sh` - Linux/Mac default ports script
