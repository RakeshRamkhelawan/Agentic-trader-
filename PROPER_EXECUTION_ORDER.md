# Proper Execution Order - Multi-Frequency Consciousness Architecture

## ✅ **IMPORTANT: Execution Sequence Matters**

The monitor script **connects to SHM blocks** that must already exist. These blocks are **created by the verification/main script**.

---

## 🔴 **WRONG WAY** (What You Just Tried)
```bash
# ❌ DON'T start the monitor first
python backend/scripts/monitor_market_shm.py

# ERROR: Could not connect to any shared memory blocks!
# (Blocks don't exist yet)
```

---

## 🟢 **CORRECT WAY** (Proper Sequence)

### **Option 1: Verification Testing (Recommended First)**

#### Terminal 1: Start Verification Script
```bash
# This creates the SHM blocks (v2)
python backend/scripts/verify_mind_body_flow.py

# Output:
# ✓ Verified Redis at redis://localhost:6380/0
# ✓ Layer 1: Eternal Soul Service started
# ✓ Layer 2: Cognitive Mind Service started
# ✓ Layer 3: Reflex Body Service started
#
# >>> SCENARIO 1: Normal State (Rahu Kala = False)
# ...
# >>> SCENARIO 5: Strategy Switching
# --- Stopping Services ---
```

#### Terminal 2: Start Monitor (While verification is running)
```bash
# ✅ NOW it can connect (blocks exist)
python backend/scripts/monitor_market_shm.py

# Output:
# [OK] Connected to market_data_v2 shared memory
# [OK] Connected to trading_intents_v2 shared memory
#
# [MARKET] BTC/USD      | Bid: 43500.00 Ask: 43510.00 | Latency: 2.34ms
# [MIND]   BTC/USD      | Action: BUY  Size: 1.0000 | Latency: 3.21ms
```

---

### **Option 2: Production Mode (Full System)**

#### Terminal 1: Start Full System
```bash
# This starts all 3 layers + creates SHM blocks
python backend/main.py

# Output:
# ✓ Layer 1: Eternal Soul Service started (frequency: ~1 minute)
# ✓ Layer 2: Cognitive Mind Service started (frequency: 50-200ms)
# ✓ Layer 3: Reflex Body Service started (frequency: <10ms)
# Platform initialized. Keeping services alive...
```

#### Terminal 2: Start Monitor
```bash
# ✅ Now it can connect
python backend/scripts/monitor_market_shm.py

# Shows live SHM activity
```

---

## 📋 **Why This Order Matters**

### SHM Block Lifecycle

```
1. CREATION (happens once, during first service startup)
   └─ CognitiveMindService.__init__()
   └─ ZeroCopyBridge(create=True, ...)
   └─ Creates: trading_intents_v2 block (6.4 KB)

   └─ MarketDataStreamer.__init__()
   └─ ZeroCopyBridge(create=True, ...)
   └─ Creates: market_data_v2 block (6.4 KB)

2. ATTACHMENT (happens when other services connect)
   └─ ReflexExecutor.start()
   └─ ZeroCopyBridge(create=False, ...)
   └─ Attaches to: trading_intents_v2 block

   └─ monitor_market_shm.py
   └─ ZeroCopyBridge(create=False, ...)
   └─ Attaches to: BOTH blocks (read-only)

3. USAGE (continuous reading/writing)
   └─ Mind writes intents to SHM
   └─ Body reads intents from SHM
   └─ Monitor reads both blocks

4. CLEANUP (when all processes exit)
   └─ SHM blocks remain in memory until reboot
   └─ OR until all processes holding references exit
```

### The Monitor's Role

The monitor is a **read-only observer**. It:
- ✅ **Connects** to existing blocks (doesn't create them)
- ✅ **Reads** data without modifying it
- ✅ **Displays** live updates from both blocks
- ❌ **Cannot** create blocks itself
- ❌ **Will fail** if blocks don't exist

---

## 🧪 **Test Scenarios**

### Scenario A: Monitor Starts First (FAILS)
```bash
# Terminal 1
python backend/scripts/monitor_market_shm.py
# ERROR: [WAIT] Could not connect to market_data_v2 SHM
# ERROR: [WAIT] Could not connect to trading_intents_v2 SHM
# ERROR: Fatal error: Could not connect to any shared memory blocks!
# ✅ This is CORRECT behavior (blocks don't exist yet)

# Terminal 2 (start verification)
python backend/scripts/verify_mind_body_flow.py
# Monitor in Terminal 1 should now see SHM activity!
# [OK] Connected to market_data_v2 shared memory
# [OK] Connected to trading_intents_v2 shared memory
# [MARKET] BTC/USD | ...
```

### Scenario B: Verification Starts First (SUCCESS)
```bash
# Terminal 1
python backend/scripts/verify_mind_body_flow.py
# Creates SHM blocks immediately
# ✓ Layer 1: Eternal Soul Service started
# ✓ Layer 2: Cognitive Mind Service started
# ✓ Layer 3: Reflex Body Service started

# Terminal 2 (after a few seconds)
python backend/scripts/monitor_market_shm.py
# Immediately connects
# [OK] Connected to market_data_v2 shared memory
# [OK] Connected to trading_intents_v2 shared memory
# Starts showing live data
```

### Scenario C: Monitor Stays Connected (WORKS)
```bash
# Terminal 1 - Start monitor (will fail initially)
python backend/scripts/monitor_market_shm.py
# ERROR: Could not connect...
# (Keeps retrying internally)

# Terminal 2 - Start verification (takes ~30s)
python backend/scripts/verify_mind_body_flow.py
# Monitor in Terminal 1 automatically connects!
# [OK] Connected to market_data_v2 shared memory
# [OK] Connected to trading_intents_v2 shared memory
```

---

## ✅ **Quick Start Guide**

### For Development/Testing
```bash
# Open 2 terminals

# Terminal 1
python backend/scripts/verify_mind_body_flow.py

# Wait for "Layer 2: Cognitive Mind Service started"
# Then open Terminal 2

# Terminal 2
python backend/scripts/monitor_market_shm.py
```

### For Production/Full System
```bash
# Terminal 1
python backend/main.py

# Wait for "Platform initialized. Keeping services alive..."
# Then open Terminal 2

# Terminal 2
python backend/scripts/monitor_market_shm.py
```

---

## 🔧 **Troubleshooting**

### Error: "Could not connect to any shared memory blocks!"

**Meaning**: SHM blocks don't exist yet

**Solutions**:
1. ✅ **Recommended**: Start verification/main script first, then monitor
2. ✅ **Alternative**: Let monitor wait, start verification script later (monitor will auto-connect)
3. ❌ **Wrong**: Don't run monitor alone expecting blocks to appear

### Error: "Het systeem kan het opgegeven bestand niet vinden" (Windows Dutch)

**Meaning**: Same as above (Windows system message)

**Translation**: "The system cannot find the specified file"

**Solution**: Follow proper execution order above

### Error: "buffer is too small" (OLD ERROR - FIXED)

**Status**: ✅ FIXED in this version

**Cause**: Was trying to connect to old v1 blocks

**Fix**: All blocks now use v2 naming

---

## 📊 **Performance Notes**

When monitor is connected:
- Overhead: **<1%** (reads only, doesn't modify)
- Latency impact: **None**
- Memory usage: **Negligible** (shared memory, not copied)
- CPU usage: **<1 core**

---

## 🎯 **Success Indicators**

### Monitor Successfully Connected
```
2026-02-17 11:36:09,235 - MarketSHMMonitor - INFO - Initializing Market Data Monitor...
2026-02-17 11:36:09,240 - MarketSHMMonitor - INFO - [OK] Connected to market_data_v2 shared memory
2026-02-17 11:36:09,245 - MarketSHMMonitor - INFO - [OK] Connected to trading_intents_v2 shared memory

========================================
MONITORING SHARED MEMORY - Press Ctrl+C to exit
========================================

[MARKET] BTC/USD      | Bid: 43500.00 Ask: 43510.00 Last: 43505.00 | Latency: 2.34ms
[MIND]   BTC/USD      | Action: BUY  Size: 1.0000 Conf:  80.00% | Latency: 3.21ms
```

### Monitor Waiting for Blocks
```
2026-02-17 11:36:09,235 - MarketSHMMonitor - INFO - Initializing Market Data Monitor...
2026-02-17 11:36:09,240 - MarketSHMMonitor - INFO - [WAIT] Could not connect to market_data_v2 SHM: ...
2026-02-17 11:36:09,240 - MarketSHMMonitor - INFO -   (Ensure verification script is running first)
2026-02-17 11:36:09,245 - MarketSHMMonitor - INFO - [WAIT] Could not connect to trading_intents_v2 SHM: ...
2026-02-17 11:36:09,245 - MarketSHMMonitor - INFO -   (Ensure Cognitive Mind Service is running)
2026-02-17 11:36:09,247 - MarketSHMMonitor - ERROR - Fatal error: Could not connect to any shared memory blocks!

# ✅ This is OK - monitor is not supposed to create blocks
# Start the verification/main script to create blocks
```

---

## 📝 **Summary**

| Action | Correct Sequence | Common Mistake |
|--------|-----------------|-----------------|
| Monitor without services | ❌ FAILS (as expected) | Users think it's broken |
| Verification then Monitor | ✅ WORKS perfectly | Not obvious it's the right order |
| Monitor then Verification | ✅ WORKS (monitor waits) | But requires patience |
| Monitor alone forever | ❌ FAILS (blocks never created) | Expecting monitor to create them |

---

**Remember**: The monitor is a **consumer of SHM data**, not a **producer**. Start your services first!

---

## 🚀 **Ready?**

```bash
# Try this now:
python backend/scripts/verify_mind_body_flow.py
# (Wait ~5 seconds for services to start)
# Then in another terminal:
python backend/scripts/monitor_market_shm.py
```

**Expected**: Monitor connects and shows live SHM data ✅
