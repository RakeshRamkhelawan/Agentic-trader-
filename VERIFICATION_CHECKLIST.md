# SHM Fix Verification Checklist

## 🎯 Quick Status Check

### ✅ What Was Done
All SHM block names upgraded from `v1` to `v2` to resolve Windows zombie process locks.

**Files Changed**:
- ✅ `backend/core/zero_copy_bridge.py` (default param)
- ✅ `backend/core/cognitive_mind_service.py` (default param)
- ✅ `backend/execution/reflex_executor.py` (default params)
- ✅ `backend/main.py` (service initialization)
- ✅ `backend/scripts/verify_mind_body_flow.py` (service init)
- ✅ `backend/scripts/monitor_market_shm.py` (SHM names)
- ✅ `backend/services/market_data_streamer.py` (SHM name)

### ✅ SHM Block Naming
| Block | Old | New |
|-------|-----|-----|
| Trading Intents | `trading_intents` | `trading_intents_v2` |
| Market Data | `market_data` | `market_data_v2` |
| Verify Test | `verify_intents` | `verify_intents_v2` |

---

## 📋 Pre-Verification Checklist

- [ ] **Backup your work** (if you modified anything)
  ```bash
  git add -A
  git commit -m "Backup before SHM verification"
  ```

- [ ] **Check Redis is running**
  ```bash
  redis-cli ping
  # Expected: PONG
  ```

- [ ] **Close all Python terminals/processes**
  - All IDE instances should be closed
  - All Python scripts should be stopped
  - This releases any zombie SHM locks

---

## 🧪 VERIFICATION SEQUENCE

### Test 1: Quick Syntax Check (1 minute)
```bash
python -m py_compile backend/core/zero_copy_bridge.py
python -m py_compile backend/core/cognitive_mind_service.py
python -m py_compile backend/execution/reflex_executor.py
python -m py_compile backend/scripts/verify_mind_body_flow.py
python -m py_compile backend/scripts/monitor_market_shm.py
python -m py_compile backend/services/market_data_streamer.py

# Expected: No output (all files syntactically correct)
```

### Test 2: Reference Check (2 minutes)
```bash
# Verify all old references are gone
grep -r "shm_name.*'trading_intents'" backend/ --include="*.py" | grep -v "_v2"
grep -r "shm_name.*'market_data'" backend/ --include="*.py" | grep -v "_v2"

# Expected: NO OUTPUT (all upgraded to v2)
```

### Test 3: Run Verification Script (5-10 minutes)
```bash
# Make sure Redis is running
redis-cli ping  # Should return PONG

# Run verification
python backend/scripts/verify_mind_body_flow.py
```

**Expected Behavior**:
- ✅ Redis connection verified
- ✅ All 3 layers start successfully
- ✅ Scenarios 1-5 run without errors
- ✅ No "buffer is too small" errors
- ✅ No "SharedMemory already exists" errors
- ✅ Clean shutdown

**Expected Output Examples**:
```
2026-02-17 00:27:07,353 - VerificationScript - INFO - Verified Redis at redis://localhost:6380/0
2026-02-17 00:27:07,387 - backend.core.eternal_soul_service - INFO - Awakening the Eternal Soul...
2026-02-17 00:27:07,390 - backend.core.eternal_soul_service - INFO - Eternal Soul connected to Redis.
2026-02-17 00:27:07,391 - backend.core.cognitive_mind_service - INFO - Starting Cognitive Mind Service...
2026-02-17 00:27:07,393 - backend.execution.reflex_executor - INFO - Starting Reflex Executor...

>>> SCENARIO 1: Normal State (Rahu Kala = False)
Mind: Written Intent to SHM (Action=1, Size=1.0000, Reason=OK)
[REFLEX] EXECUTE BUY BTC/USD Size=1.0 (Latency=X.XXms)

>>> SCENARIO 2: Rahu Kala Active (Rahu Kala = True)
Mind: Written Intent to SHM (Action=0, Conf=0.0) [RAHU KALA]

>>> SCENARIO 3: High Risk Trade (Size > Limit)
Risk Reject: MiFID Compliance Block
Mind: Written Intent to SHM (Action=0, Size=0.0)

>>> SCENARIO 4: Volatile Regime Detection
[TEST] Injected 200 volatile price points into Soul.

>>> SCENARIO 5: Strategy Switching (BULL vs SIDEWAYS)
[TEST] Injecting BULL Trend...
[TEST] Injecting SIDEWAYS Trend...

--- Stopping Services ---
Stopping Reflex Executor...
Stopping Cognitive Mind Service...
The Eternal Soul has withdrawn.
```

### Test 4: Real-Time Monitoring (Parallel, 5 minutes)
```bash
# In ANOTHER terminal (keep verification running in first)
python backend/scripts/monitor_market_shm.py
```

**Expected Output**:
```
✓ Connected to market_data_v2 shared memory
✓ Connected to trading_intents_v2 shared memory
MONITORING SHARED MEMORY - Press Ctrl+C to exit

[MARKET] BTC/USD      | Bid: 43500.00 Ask: 43510.00 Last: 43505.00 | Latency: 2.34ms
[MIND]   BTC/USD      | Action: BUY  Size: 1.0000 Conf:  80.00% | Latency: 3.21ms
```

**No Error Expected**:
- ✅ No "buffer is too small"
- ✅ No "unlink failed"
- ✅ No "cannot create file"

### Test 5: Full Integration (10 minutes)
```bash
# Stop previous tests first
# Then run main app with all layers
python backend/main.py
```

**Expected Output**:
```
✓ Layer 1: Eternal Soul Service started (frequency: ~1 minute)
✓ Layer 2: Cognitive Mind Service started (frequency: 50-200ms)
✓ Layer 3: Reflex Body Service started (frequency: <10ms)
Platform initialized. Keeping services alive...
```

**Let it run for 30 seconds**, then:
- Stop with `Ctrl+C`
- Expect clean shutdown with no errors

---

## ✅ SUCCESS CRITERIA

All tests pass if:
- [ ] No syntax errors on compile check
- [ ] No old `v1` references found
- [ ] verify_mind_body_flow.py runs all 5 scenarios without crashes
- [ ] monitor_market_shm.py connects to both v2 blocks without "buffer too small"
- [ ] backend/main.py starts all 3 layers successfully
- [ ] No errors mentioning old block names

---

## ❌ TROUBLESHOOTING

### Error: "ValueError: buffer is too small"
**Meaning**: Still connected to old block
**Solution**:
1. Close ALL Python processes
2. Wait 5 seconds
3. Restart verification: `python backend/scripts/verify_mind_body_flow.py`

### Error: "FileExistsError: [Errno 17] File exists"
**Meaning**: SHM block already exists from prior run
**Solution**:
1. Normal if first run - it just attaches to existing block
2. Should not cause errors, only a warning
3. If persistent, close all Python and try again

### Error: "ConnectionRefusedError: Redis not running"
**Meaning**: Redis not started
**Solution**:
```bash
redis-cli ping  # Check if running
redis-server    # Start if not running
```

### Error: Import errors
**Meaning**: Python path issue
**Solution**:
```bash
# Run from project root
cd /path/to/agentic_trader_platform
python backend/scripts/verify_mind_body_flow.py
```

---

## 📊 Test Summary Table

| Test | Duration | Status | Notes |
|------|----------|--------|-------|
| Syntax Check | 1 min | ✅ | Verify all files compile |
| Reference Check | 2 min | ✅ | Verify all v1→v2 upgraded |
| Verification Script | 5-10 min | ✅ | Run all 5 scenarios |
| Monitor Script | 5 min | ✅ | Live SHM observation |
| Full Integration | 10 min | ✅ | Main app startup |
| **TOTAL** | **~30 min** | ✅ | Complete verification |

---

## 🎯 Next Steps After Verification

1. **If all tests pass**:
   ```bash
   git add -A
   git commit -m "SHM upgrade: v1 → v2 blocks (Windows compatibility)"
   git push
   ```

2. **Start using the system**:
   ```bash
   python backend/main.py
   ```

3. **Monitor in production**:
   ```bash
   python backend/scripts/monitor_market_shm.py
   ```

---

## 📝 Notes for Future Upgrades

If you need to upgrade SHM blocks again in future:
- `v2` → `v3`: Update defaults in 7 files
- `v3` → `v4`: Same pattern
- No code changes needed, just naming

```bash
# Quick upgrade script template
sed -i 's/trading_intents_v2/trading_intents_v3/g' backend/**/*.py
sed -i 's/market_data_v2/market_data_v3/g' backend/**/*.py
```

---

**Status**: ✅ **READY FOR VERIFICATION**

Start with Test 1 and work through all tests in sequence.

**Estimated time**: 30 minutes for full verification
**Expected outcome**: All green ✅
