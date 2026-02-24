# Agentic Trader Platform - TDD System Documentation

## Overview
This platform is a multi-exchange crypto trading system designed with Test-Driven Development (TDD) principles. It supports canonical symbol normalization, smart routing across multiple exchanges, and real-time monitoring.

## System Components
- **API Gateway**: FastAPI-based gateway for routing and trading.
- **Router Engine**: Finds the best prices across Bitvavo, Binance, Kraken, and Revolut.
- **Symbol Normalizer**: Handles conversion between "BTC/EUR", "BTC-EUR", and concatenated formats.
- **Observability**: Prometheus metrics and real-time performance dashboard.

## Adding a New Exchange
To add a new exchange to the platform:
1. **Normalizer Rules**: Update `backend/core/symbol_normalizer.py` if the exchange uses a unique symbol format.
2. **Adapter**: Create a new broker adapter class in `backend/core/adapters/` (or use the mock pattern in `routing.py`).
3. **Router Integration**: Register the new exchange in `backend/api/routers/routing.py` within the `get_router_engine` dependency.
4. **Tests**: Add integration tests in `backend/tests/integration/` to verify price fetching and normalization.

## Running the Test Suite
The project follows TDD. Run all tests using:
```bash
python -m pytest backend/tests/ -v
```
Specifically for routing and normalization:
```bash
python -m pytest backend/tests/test_symbol_normalizer.py backend/tests/router_engine_tests.py -v
```

## Monitoring & Performance
Metrics are exposed at `/metrics` in Prometheus format.
Use the built-in dashboard for real-time visualization:
```bash
python backend/tools/monitor_performance.py
```

## Deployment
The platform is containerized using Docker.
```bash
docker-compose up --build
```
This starts the API, a PostgreSQL database, and a Redis cache.
Exchange API keys can be mapped via environment variables in `docker-compose.yml`.
