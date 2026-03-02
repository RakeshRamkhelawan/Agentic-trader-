# Redis Fix Summary

## Problem
**Error:** `unknown command 'XADD'`
**Root Cause:** Python was connecting to native Windows Redis v3.0.504 (too old) instead of Docker Redis v7.4.7

## Diagnosis Steps

1. **Checked Redis version in Docker:** ✅ 7.4.7 (supports Streams)
2. **Checked Redis version from Python:** ❌ 3.0.504 (too old)
3. **Found native Redis process:** Running on Windows, using port 6379
4. **Port conflict:** Native Redis blocked Docker Redis on port 6379

## Solution

Instead of fighting the native Redis service, configured the app to use **Docker Redis on port 6380**.

### Files Created/Modified:

1. **`backend/core/config/redis_config.py`** (NEW)
   - Automatic Redis URL detection
   - Priority: Env var → Docker (6380) → Local (6379)
   - Port 6380 is Docker Redis with Streams support

2. **`backend/events/triad_event_bus.py`** (MODIFIED)
   - Uses `REDIS_URL` from config
   - Now connects to correct Redis instance

## Verification

```bash
# Before fix
Redis version: 3.0.504
XADD: FAILED - unknown command

# After fix
Redis URL: redis://localhost:6380
Redis version: 7.4.7
XADD: SUCCESS - id: 1772233133369-0
```

## Test Results

| Component | Before Fix | After Fix |
|-----------|-----------|-----------|
| Guna Council | PASS | PASS |
| Mind Council | PASS | PASS |
| Calibrated Thresholds | PASS | PASS |
| Orchestrator | FAIL (XADD) | **PASS** |

**Final Score: 4/4 PASS (100%)** ✅

## Configuration

### Environment Variable (optional)
```bash
export REDIS_URL="redis://localhost:6380"
```

### Default Behavior
- Automatically detects port 6380 (Docker Redis)
- Falls back to port 6379 if 6380 unavailable
- No code changes needed

## Docker Redis Details

```yaml
Container: sanskritisetuorg-redis-test-1
Port: 6380 → 6379 (host → container)
Version: 7.4.7
Streams: ✅ Supported
```

## Next Steps

✅ Infrastructure fixed
✅ All tests passing
🚀 Ready for Phase 4 (Buddhi + Body Council)
