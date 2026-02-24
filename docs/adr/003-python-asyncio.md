# ADR 003: Python 3.13 with Asyncio Throughout

## Status
Accepted

## Context

The trading platform requires:
- High concurrency for WebSocket connections (real-time data)
- Concurrent API requests to external exchanges
- Non-blocking database operations
- Efficient handling of I/O-bound workloads

## Decision

We will use **Python 3.13+ with asyncio** for all I/O-bound operations.

### Key Technologies

```python
# FastAPI with native async
from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI()

# Async database with SQLAlchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
engine = create_async_engine("postgresql+asyncpg://...")

# Async Redis
import redis.asyncio as redis
redis_client = redis.Redis(host='localhost', port=6379)

# Async HTTP client
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.exchange.com/ticker")
```

### Concurrency Model

```
┌─────────────────────────────────────────────┐
│           Python Event Loop                 │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Request 1│  │ Request 2│  │ WebSocket│  │
│  │ (async)  │  │ (async)  │  │ (async)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │         │
│       └─────────────┼─────────────┘         │
│                     │                       │
│  ┌──────────────────┴──────────────────┐   │
│  │   Async I/O (Non-blocking)          │   │
│  │   - DB queries                      │   │
│  │   - HTTP requests                   │   │
│  │   - WebSocket messages              │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Asyncio (Chosen)** | Native Python, FastAPI support, scalable | Learning curve, callback complexity |
| Sync + Threading | Simpler code | Thread overhead, GIL limitations |
| Celery for everything | Distributed | Adds latency, complexity |
| Node.js | Natural async | Different language, ecosystem mismatch |

## Consequences

### Positive
- **High concurrency**: Single thread handles many connections
- **FastAPI integration**: Native async support
- **Resource efficient**: Less memory than threading
- **Modern Python**: Industry standard for I/O-bound apps

### Negative
- **Learning curve**: Team must understand async/await
- **Debugging harder**: Stack traces more complex
- **Library support**: Some libraries not async
- **CPU-bound tasks**: Need thread/process pool

### Patterns We Use

```python
# 1. Async context managers
async def get_db_session():
    async with AsyncSession(engine) as session:
        yield session

# 2. Concurrent execution
async def fetch_all_prices(symbols):
    tasks = [fetch_price(s) for s in symbols]
    return await asyncio.gather(*tasks)

# 3. Background tasks
@app.post("/long-task")
async def long_task(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_data)
    return {"status": "started"}

# 4. WebSocket handling
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        await process_message(data)
```

## Migration Path

For CPU-intensive tasks (backtests, ML), we use:
```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

async def run_cpu_intensive_task(data):
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_bound_function, data)
    return result
```

## Related Decisions
- ADR 001: Dual Interface Architecture
- ADR 004: FastAPI as Web Framework

## References
- [Python Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Async](https://fastapi.tiangolo.com/async/)
