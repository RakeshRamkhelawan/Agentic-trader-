# Multi-Frequency Consciousness Architecture - Setup Guide

## System Components

### Layer 1: Eternal Soul (Atman)
- **Service**: `backend/core/eternal_soul_service.py`
- **Frequency**: ~1 minute (slow, strategic)
- **Responsibility**:
  - Cosmic time (Vedic calculations via Navagraha)
  - Market regime detection
  - Publishing soul context to Redis
- **Dependencies**: Redis, Navagraha service

### Layer 2: Cognitive Mind (Buddhi)
- **Service**: `backend/core/cognitive_mind_service.py`
- **Frequency**: 50-200ms (mid-frequency)
- **Responsibility**:
  - Read soul context from Redis
  - Generate trading intents (decisions)
  - Write intents to shared memory
- **Dependencies**: Redis, Shared Memory

### Layer 3: Reflex Body (Physical Action)
- **Service**: `backend/execution/reflex_executor.py`
- **Frequency**: <10ms (high-frequency)
- **Responsibility**:
  - Read trading intents from shared memory
  - Validate against current market data
  - Execute orders
- **Dependencies**: Shared Memory

### Zero-Copy Bridge
- **Service**: `backend/core/zero_copy_bridge.py`
- **Communication**: Shared Memory (inter-process, zero-copy)
- **Blocks**:
  - `trading_intents`: Trading intent structures
  - `market_data`: Market data (BBO, last price, timestamp)

## Prerequisites

### Required Services
1. **Redis** (for inter-service messaging)
   - Default: `localhost:6379`
   - Docker: Configured in `docker-compose.yml` (port 6380)
   - Optional fallback: Ports 6379, 6380, 6381 auto-detected

2. **Shared Memory** (for zero-copy communication)
   - Platform: Linux/macOS/Windows (Python multiprocessing)
   - No external service required
   - Auto-created on first initialization

## Quick Start

### Option 1: Using Docker Compose (Recommended)
```bash
# Start all infrastructure services
docker-compose up redis

# In another terminal, run the application
python backend/scripts/verify_mind_body_flow.py
```

### Option 2: Local Development (Redis only)
```bash
# Install and run Redis locally
# macOS with Homebrew:
brew install redis
brew services start redis

# Linux (Ubuntu/Debian):
sudo apt-get install redis-server
sudo service redis-server start

# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Or use WSL with Linux commands

# Then run:
python backend/scripts/verify_mind_body_flow.py
```

### Option 3: Manual Integration
See `Integration` section below to add to your existing application.

## Verification Scripts

### 1. Test Mind-Body Flow
```bash
python backend/scripts/verify_mind_body_flow.py
```
Tests:
- Soul Context generation and Redis publishing
- Mind reading soul context and writing intents to shared memory
- Body reading intents from shared memory
- Staleness checking and validation

Expected output:
```
SCENARIO 1: Normal State (Rahu Kala = False)
Mind: Written Intent to SHM (Action=0, Conf=0.5)
[REFLEX] EXECUTE BUY BTC/USD Size=0.0 (Latency=2.34ms)

SCENARIO 2: Rahu Kala Active (Rahu Kala = True)
Mind: Written Intent to SHM (Action=0, Conf=0.0) [RAHU KALA]
[No execution - defensive mode]
```

### 2. Monitor Shared Memory
```bash
python backend/scripts/monitor_market_shm.py
```
Real-time monitoring of:
- Market data updates from streamer
- Trading intent updates from mind
- Reflex body reads

### 3. Test Market Data Streaming
```bash
python -c "
from backend.services.market_data_streamer import MarketDataStreamer
import asyncio

async def test():
    streamer = MarketDataStreamer()
    await streamer.start_stream('BTC/USD')
    await asyncio.sleep(10)
    await streamer.stop_stream('BTC/USD')

asyncio.run(test())
"
```

## Integration into Existing Application

### In your FastAPI app or main startup:

```python
from backend.core.eternal_soul_service import EternalSoulService
from backend.core.cognitive_mind_service import CognitiveMindService
from backend.execution.reflex_executor import ReflexExecutor

async def startup():
    # Initialize services
    soul = EternalSoulService()
    mind = CognitiveMindService(shm_name="trading_intents")
    body = ReflexExecutor(shm_name="trading_intents", market_shm_name="market_data")

    # Start them (non-blocking)
    await soul.start()
    await mind.start()
    await body.start()

    # Store for cleanup on shutdown
    app.state.soul = soul
    app.state.mind = mind
    app.state.body = body

async def shutdown():
    # Graceful cleanup
    if hasattr(app.state, 'body'):
        await app.state.body.stop()
    if hasattr(app.state, 'mind'):
        await app.state.mind.stop()
    if hasattr(app.state, 'soul'):
        await app.state.soul.stop()

app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ETERNAL SOUL (Layer 1)                   │
│              (Vedic Time + Market Regime)                   │
│                   Frequency: ~1 minute                      │
└─────────────┬───────────────────────────────────────────────┘
              │ [Redis: soul:context]
              │ (Cosmic constraints)
              ▼
┌─────────────────────────────────────────────────────────────┐
│              COGNITIVE MIND (Layer 2)                        │
│          (Decision Making - Buddhi/Intellect)               │
│               Frequency: 50-200ms                           │
└─────────────┬───────────────────────────────────────────────┘
              │ [Shared Memory: trading_intents]
              │ (TradingIntent struct)
              ▼
┌─────────────────────────────────────────────────────────────┐
│              REFLEX BODY (Layer 3)                           │
│          (Order Execution - Physical Action)                │
│                Frequency: <10ms                             │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │
                    [Shared Memory: market_data]
                    (Real-time BBO + prices)
                          │
              ┌───────────┴──────────┐
              │                      │
    ┌─────────▼────────┐   ┌────────▼──────┐
    │ Market Streamer  │   │ MonitorScript  │
    └──────────────────┘   └────────────────┘
```

## Troubleshooting

### Redis Connection Error
```
redis.exceptions.ConnectionError: Error 22 connecting to localhost:6379
```

**Solution**:
1. Check if Redis is running: `redis-cli ping`
2. If not running, start it: `redis-server` or `brew services start redis`
3. Verify port: Default 6379, Docker mapped to 6380
4. Check REDIS_URL in `backend/core/config/settings.py`

### Shared Memory Error
```
FileExistsError: Shared memory 'trading_intents' already exists
```

**Solution**:
1. A previous instance left shared memory blocks
2. Clean up manually (Python):
   ```python
   from multiprocessing import shared_memory
   try:
       shm = shared_memory.SharedMemory(name='trading_intents')
       shm.close()
       shm.unlink()
   except:
       pass
   ```
3. Or restart your system

### Services Not Starting
```
ERROR - Failed to connect to Redis
```

**Solutions**:
1. Services attempt automatic fallback to available ports (6379, 6380, 6381)
2. If none available, services log warning but continue (SHM-only mode)
3. Run without Redis: Use direct SHM communication (see `verify_mind_body_flow.py`)

### Latency Too High
- Verify no other heavy processes running
- Check Python GIL: Consider C++ extension for Reflex Body in production
- Profile with: `python -m cProfile backend/scripts/verify_mind_body_flow.py`

## Performance Targets

| Layer | Frequency | Target Latency | Notes |
|-------|-----------|-----------------|-------|
| Soul (L1) | 1/minute | N/A | Strategic decisions |
| Mind (L2) | 50-200ms | <50ms | Can afford some compute |
| Body (L3) | <10ms polling | <1ms | Must be sub-millisecond |
| Body→Execute | Event-based | <100µs | Critical path |

## Development Workflow

1. **Edit Code**: Modify service implementations
2. **Test Locally**: `python backend/scripts/verify_mind_body_flow.py`
3. **Monitor**: `python backend/scripts/monitor_market_shm.py` (in another terminal)
4. **Integrate**: Add to `backend/main.py` as shown above
5. **Deploy**: Use Docker Compose for production

## Files Modified/Created

- ✅ `backend/core/eternal_soul_service.py` - Layer 1 (Existing, enhanced)
- ✅ `backend/core/cognitive_mind_service.py` - Layer 2 (New)
- ✅ `backend/execution/reflex_executor.py` - Layer 3 (New)
- ✅ `backend/core/zero_copy_bridge.py` - Zero-Copy Bridge (New)
- ✅ `backend/scripts/verify_mind_body_flow.py` - Verification (New, fixed)
- ⏳ `backend/scripts/monitor_market_shm.py` - Monitor (TODO)
- ✅ `backend/services/market_data_streamer.py` - Writer to market_data SHM (Existing, enhanced)

## Next Steps

1. **Verify Setup**: Run `python backend/scripts/verify_mind_body_flow.py`
2. **Monitor**: Run `python backend/scripts/monitor_market_shm.py`
3. **Integrate**: Add to `backend/main.py` using the code snippet above
4. **Test**: Run full application and check logs
5. **Optimize**: Measure latencies and identify bottlenecks

## Support

For issues:
1. Check logs: All services log to stdout with timestamps
2. Enable debug logging: Set `settings.DEBUG = True`
3. Monitor shared memory: Use `monitor_market_shm.py`
4. Verify Redis: `redis-cli INFO`
5. Check disk space: Shared memory uses /dev/shm (Linux) or temp (Windows)
