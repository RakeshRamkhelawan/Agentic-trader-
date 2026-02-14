# Prediction Market Intelligence API Documentation

## Service Overview

The Prediction Market Intelligence Service is a FastAPI-based platform that analyzes prediction market data from Kalshi and Polymarket, generating actionable trading signals through advanced data analysis and statistical frameworks.

**Base URL**: `http://localhost:8000`  
**API Version**: 1.0.0  
**Status**: Production-Ready

---

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
3. [Data Models](#data-models)
4. [Examples](#examples)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)

---

## Authentication

Currently, the API operates without authentication (open access). Future versions will implement:
- JWT token-based authentication
- API key validation
- Role-based access control

---

## API Endpoints

### Health Check Endpoints

#### GET /health
Full health check with all system status.

**Response**: 200 OK
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-13T15:30:45.123Z",
  "database": "connected",
  "services": {
    "analysis": "ready",
    "ingestion": "ready",
    "signals": "ready"
  }
}
```

#### GET /health/ready
Readiness probe (Kubernetes compatible).

**Response**: 200 OK

#### GET /health/live
Liveness probe (Kubernetes compatible).

**Response**: 200 OK

---

### Analysis Endpoints

#### POST /api/v1/analysis/run
Submit an analysis job to the queue.

**Request**:
```json
{
  "market": "kalshi",
  "category": "politics",
  "analysis_type": "maker_taker",
  "parameters": {
    "symbol": "TRUMP25",
    "limit": 100
  }
}
```

**Parameters**:
- `market` (string, required): `kalshi` or `polymarket`
- `category` (string, optional): Filter by category (crypto, politics, economics, finance, sports, entertainment)
- `analysis_type` (string, required): `maker_taker`, `volume_trends`, or `statistical_tests`
- `parameters` (object, optional): Additional analysis parameters

**Response**: 202 Accepted
```json
{
  "analysis_id": "analysis_a1b2c3d4",
  "analysis_type": "maker_taker",
  "status": "queued",
  "created_at": "2026-02-13T15:30:45.123Z",
  "completed_at": null,
  "result": null,
  "error": null,
  "metadata": {
    "market": "kalshi",
    "category": "politics",
    "parameters": {
      "symbol": "TRUMP25",
      "limit": 100
    }
  }
}
```

---

#### GET /api/v1/analysis/{analysis_id}
Retrieve analysis status and results.

**Parameters**:
- `analysis_id` (string, path, required): Analysis ID from submission

**Response**: 200 OK
```json
{
  "analysis_id": "analysis_a1b2c3d4",
  "analysis_type": "maker_taker",
  "status": "completed",
  "created_at": "2026-02-13T15:30:45.123Z",
  "completed_at": "2026-02-13T15:31:02.456Z",
  "result": {
    "analysis_type": "maker_taker",
    "market": "kalshi",
    "category": "politics",
    "status": "completed",
    "timestamp": "2026-02-13T15:31:02.456Z",
    "spread_metrics": {
      "liquidity_score": 75.5,
      "efficiency_score": 82.3
    },
    "volume_metrics": {
      "volume_trend": "increasing",
      "activity_score": 68.9
    },
    "signals": [
      {
        "signal_id": "sig_xyz789",
        "market": "kalshi",
        "signal_type": "SPREAD_OPPORTUNITY",
        "confidence": 0.85,
        "indicators": {
          "spread_width": 0.02,
          "liquidity": 0.75
        }
      }
    ],
    "signal_count": 3,
    "high_confidence_signals": 2
  },
  "error": null,
  "metadata": {...}
}
```

**Status Values**:
- `queued`: Analysis waiting to be processed
- `running`: Analysis currently executing
- `completed`: Analysis finished successfully
- `failed`: Analysis failed with error

---

#### GET /api/v1/analysis
List recent analyses.

**Query Parameters**:
- `status` (string, optional): Filter by status (queued, running, completed, failed)
- `limit` (integer, optional, default: 10, max: 50): Number of results

**Response**: 200 OK
```json
{
  "analyses": [
    {
      "analysis_id": "analysis_a1b2c3d4",
      "analysis_type": "maker_taker",
      "status": "completed",
      "created_at": "2026-02-13T15:30:45.123Z",
      "completed_at": "2026-02-13T15:31:02.456Z",
      "result": {...},
      "error": null,
      "metadata": {...}
    }
  ],
  "total": 42
}
```

---

### Market Information Endpoints

#### GET /api/v1/markets/summary
Get summary statistics for a prediction market.

**Query Parameters**:
- `market` (string, optional, default: kalshi): Market name

**Response**: 200 OK
```json
{
  "market": "kalshi",
  "total_markets": 1250,
  "active_markets": 487,
  "total_volume_24h": 15420000.50,
  "categories": [
    "crypto",
    "politics",
    "economics",
    "finance",
    "sports"
  ],
  "last_updated": "2026-02-13T15:30:45.123Z"
}
```

---

### Signal Endpoints

#### GET /api/v1/signals
List recent signals.

**Query Parameters**:
- `market` (string, optional): Filter by market
- `signal_type` (string, optional): Filter by signal type
- `min_confidence` (float, optional, default: 0.5): Minimum confidence (0-1)
- `limit` (integer, optional, default: 10, max: 100): Number of results

**Response**: 200 OK
```json
{
  "signals": [
    {
      "signal_id": "sig_xyz789",
      "market": "kalshi",
      "category": "politics",
      "signal_type": "SPREAD_OPPORTUNITY",
      "confidence": 0.85,
      "symbol": "TRUMP25",
      "timestamp": "2026-02-13T15:30:45.123Z",
      "indicators": {...}
    }
  ],
  "total": 156
}
```

**Signal Types**:
- `SPREAD_OPPORTUNITY`: Favorable spread conditions detected
- `VOLUME_SPIKE`: Unusual trading volume detected
- `TREND_REVERSAL`: Potential trend reversal signal
- `ARBITRAGE`: Cross-market arbitrage opportunity
- `ANOMALY`: Statistical anomaly detected
- `LIQUIDITY_WARNING`: Low liquidity warning
- `CORRELATION_SHIFT`: Correlation change detected

---

## Data Models

### AnalysisRequest
```python
{
  "market": str,              # "kalshi" or "polymarket"
  "category": str | None,     # Market category
  "analysis_type": str,       # Analysis type enum
  "parameters": dict          # Additional parameters
}
```

### AnalysisResult
```python
{
  "analysis_id": str,         # Unique ID
  "analysis_type": str,       # Analysis type
  "status": str,              # Status enum
  "created_at": datetime,     # Creation timestamp
  "completed_at": datetime | None,  # Completion timestamp
  "result": dict | None,      # Analysis results
  "error": str | None,        # Error message if failed
  "metadata": dict            # Additional metadata
}
```

### MarketSignal
```python
{
  "signal_id": str,           # Unique signal ID
  "market": str,              # Source market
  "category": str,            # Market category
  "signal_type": str,         # Signal type enum
  "confidence": float,        # Confidence 0-1
  "symbol": str,              # Trading symbol
  "timestamp": datetime,      # Signal generation time
  "indicators": dict          # Analysis indicators
}
```

---

## Examples

### Example 1: Maker/Taker Analysis for Kalshi Politics

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
    "market": "kalshi",
    "category": "politics",
    "analysis_type": "maker_taker",
    "parameters": {
      "symbol": "TRUMP25",
      "limit": 200
    }
  }'
```

**Response**:
```json
{
  "analysis_id": "analysis_abc123",
  "status": "queued",
  "analysis_type": "maker_taker",
  ...
}
```

**Poll for Results**:
```bash
curl http://localhost:8000/api/v1/analysis/analysis_abc123
```

---

### Example 2: Volume Trends Analysis

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
    "market": "polymarket",
    "analysis_type": "volume_trends",
    "parameters": {
      "window_hours": 24
    }
  }'
```

---

### Example 3: List High-Confidence Signals

**Request**:
```bash
curl "http://localhost:8000/api/v1/signals?min_confidence=0.80&limit=20"
```

---

### Example 4: Concurrent Analysis Requests

```python
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

endpoint = "http://localhost:8000/api/v1/analysis/run"

requests_data = [
    {
        "market": "kalshi",
        "category": "politics",
        "analysis_type": "maker_taker",
        "parameters": {"symbol": f"SYM{i}"}
    }
    for i in range(5)
]

# Submit all requests
analysis_ids = []
for req in requests_data:
    resp = requests.post(endpoint, json=req)
    analysis_ids.append(resp.json()["analysis_id"])

# Poll for results
for aid in analysis_ids:
    result = requests.get(f"http://localhost:8000/api/v1/analysis/{aid}").json()
    print(f"{aid}: {result['status']}")
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "detail": "Additional technical details"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET request |
| 202 | Accepted | Analysis job queued |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Analysis ID doesn't exist |
| 422 | Unprocessable Entity | Invalid request schema |
| 500 | Internal Server Error | Server error |

### Error Examples

**Invalid Market**:
```json
{
  "error": "invalid_market",
  "message": "Unknown market: 'invalid'",
  "detail": "Supported markets: kalshi, polymarket"
}
```

**Missing Analysis**:
```json
{
  "error": "not_found",
  "message": "Analysis analysis_xyz not found",
  "detail": "Use /api/v1/analysis to list available analyses"
}
```

**Invalid Request Schema**:
```json
{
  "error": "validation_error",
  "message": "Invalid request schema",
  "detail": "Field 'analysis_type' is required"
}
```

---

## Rate Limiting

Currently, the service has no rate limiting. Future versions will implement:

**X-RateLimit Headers**:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

**Per-Client Limits**:
- Analysis submission: 100 requests/minute
- Results polling: 1000 requests/minute
- Market data: 500 requests/minute

---

## Deployment & Operations

### Health Checks

**Kubernetes Readiness**:
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Kubernetes Liveness**:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20
```

### Environment Variables

```bash
# Database
DB_PATH=/app/data/prediction_market.duckdb
DATA_DIR=/app/data

# API
API_PORT=8000
API_WORKERS=4

# Logging
LOG_LEVEL=INFO
```

### Database

The service uses DuckDB for persistence with these tables:
- `kalshi_trades`: Kalshi market trade data
- `polymarket_trades`: Polymarket market trade data
- `generated_signals`: Generated trading signals
- `analysis_results`: Complete analysis results

---

## Performance Characteristics

### Benchmarks (on sample data)

| Operation | Time | Throughput |
|-----------|------|-----------|
| Analysis submission | <50ms | 200 req/s |
| Results retrieval | <10ms | 1000 req/s |
| Market summary | <20ms | 500 req/s |
| Signal generation | 50-100ms | 10-20 signals/s |

### Resource Requirements

- **Memory**: 256MB (minimal), 1GB (recommended)
- **Disk**: 100MB data directory
- **CPU**: 1 core (minimal), 2 cores (recommended)

---

## Support & Documentation

- **Full API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **GitHub Repository**: [Link to repo]
- **Issue Tracker**: [Link to issues]

---

## Version History

### v1.0.0 (2026-02-13)
- Initial release with DuckDB integration
- Maker/Taker, Volume Trends, Statistical Tests analysis
- Signal generation engine
- Full API documentation

---

**Last Updated**: 2026-02-13  
**Maintained By**: Data Science Team  
**Status**: Production Ready ✅
