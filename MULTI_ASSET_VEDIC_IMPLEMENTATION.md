# Multi-Asset Vedic Implementation

Complete implementation of multi-asset universe with elemental agent prompts.

---

## Overview

This implementation expands the Agentic Trader Platform from crypto-only to a **full multi-asset trading system** aligned with Vedic principles.

---

## Part 1: Asset Universe (57 Assets)

### File: `backend/config/asset_universe.py`

**Asset Classes:**
| Class | Count | Examples |
|-------|-------|----------|
| CRYPTO | 7 | BTC/EUR, ETH/EUR, SOL/EUR, ADA/EUR, XRP/EUR, LINK/EUR, DOT/EUR |
| FOREX | 5 | EUR/USD, GBP/USD, USD/JPY, EUR/GBP, USD/CHF |
| COMMODITIES | 3 | XAU/USD (Gold), XAG/USD (Silver), OIL/USD (WTI) |
| INDICES | 3 | SPX500, NAS100, GER40 (DAX) |
| EQUITIES | 39 | AAPL, MSFT, GOOGL, TSLA, NVDA, ASML, SAP, etc. |

### Vedic Attributes per Asset

Each asset has:
- `vedic_element`: fire, water, earth, air, ether
- `navagraha_affinity`: SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN

### Example Asset Definition

```python
TradableAsset(
    symbol="BTC/EUR",
    asset_class=AssetClass.CRYPTO,
    exchange="bitvavo",
    min_qty=0.0001,
    tick_size=0.01,
    vedic_element="fire",      # BTC = Fire (aggressive, dominant)
    navagraha_affinity="SUN"   # SUN = Authority, core trend
)
```

---

## Part 2: Navagraha Asset Affinity

### File: `backend/core/navagraha/asset_affinity.py`

**Planet → Asset Mapping:**

| Planet | Trading Style | Primary Assets | Element |
|--------|--------------|----------------|---------|
| **SUN** | Trend following | BTC/EUR, SPX500, XAU/USD, AAPL | Fire |
| **MOON** | Sentiment | ETH/EUR, EUR/USD, XAG/USD, NFLX | Water |
| **MARS** | Momentum | BTC/EUR, SOL/EUR, OIL/USD, NVDA | Fire |
| **MERCURY** | Scalping | EUR/USD, LINK/EUR, NAS100, CRM | Air |
| **JUPITER** | Value/Growth | SPX500, GER40, DOT/EUR, MSFT | Ether |
| **VENUS** | Value | ETH/EUR, EUR/GBP, XAG/USD, JNJ | Water |
| **SATURN** | Disciplined | ADA/EUR, GBP/USD, GER40, JPM | Earth |
| **RAHU** | Speculative | SOL, DOT, NVDA, TSLA, COIN | - (Blocks) |
| **KETU** | Exit-focused | BTC, ETH, SPX500, XAU | - (Closes) |

### Key Functions

```python
# Get assets for current planetary configuration
get_favored_assets_for_planet("JUPITER")
# Returns: ["SPX500", "GER40", "DOT/EUR", "XAU/USD", ...]

# Check if asset aligns with dominant planet
should_trade_asset("JUPITER", "DOT/EUR")  # True

# Get position size adjustment
get_position_size_multiplier("SATURN")  # 0.5 (conservative)
get_position_size_multiplier("MARS")    # 1.5 (aggressive)

# Get full priority list for trading
get_asset_priority_list("JUPITER", "MERCURY")
```

---

## Part 3: Elemental Agent Prompts

### Location: `prompts/elemental/`

### 🔥 Fire Agent (Agni) — Risk Guardian

**File:** `fire_agent_system.txt`

**Role:** Final risk check before trade execution
**Element:** Fire (discrimination, protection)
**Guna:** Sattva 0.4 | Rajas 0.5 | Tamas 0.1

**Key Responsibilities:**
- Block trades during Rahu Kala
- Enforce position limits per asset class
- Calculate risk scores
- Veto power over all trades

**Decision Rules:**
1. Rahu Kala active → BLOCK
2. Prana < 10 → BLOCK
3. Harmony < 0.25 → BLOCK
4. Position too large → REDUCE
5. High volatility → Increase risk score

---

### 💧 Water Agent (Apas) — Macro Research

**File:** `water_agent_system.txt`

**Role:** Market regime analysis and context
**Element:** Water (adaptation, memory)
**Guna:** Sattva 0.4 | Rajas 0.3 | Tamas 0.3

**Key Responsibilities:**
- Determine market regime (expansion/contraction/neutral/recovery)
- Analyze per-asset-class outlook
- Provide macro narrative
- Access memory episodes from ChromaDB

**Regime Definitions:**
- **expansion**: BTC >20% above 200MA, SPX uptrend, VIX < 20
- **contraction**: Crypto >-30% from ATH, SPX < 200MA, VIX > 25
- **neutral**: Sideways, VIX 20-25
- **recovery**: After contraction, first recovery signs

---

### 🌬️ Air Agent (Vayu) — Technical Signals

**File:** `air_agent_system.txt`

**Role:** Generate concrete trading signals
**Element:** Air (movement, speed)
**Guna:** Sattva 0.3 | Rajas 0.6 | Tamas 0.1

**Key Responsibilities:**
- Technical analysis for all asset classes
- Generate BUY/SELL/HOLD signals
- Set stop-loss and take-profit levels
- Determine time horizon

**Technical Toolkit:**
- Momentum: RSI, MACD, ROC
- Trend: EMA 20/50/200 alignment
- Volatility: ATR, Bollinger Bands
- Volume: VWAP, volume profile
- Patterns: breakout, mean reversion

---

### 🌍 Earth Agent (Prithvi) — Valuation

**File:** `earth_agent_system.txt`

**Role:** Calculate fair value and detect mispricings
**Element:** Earth (stability, value)
**Guna:** Sattva 0.1 | Rajas 0.1 | Tamas 0.8

**Key Responsibilities:**
- Calculate fair value per asset
- Detect over/under-valuation
- Suggest position sizing based on value
- Grounded, fundamental analysis

**Valuation Methods by Asset Class:**
- **CRYPTO**: Stock-to-Flow, NVT ratio, Metcalfe's Law
- **FOREX**: Purchasing Power Parity (PPP), interest rate differential
- **COMMODITIES**: Cost of carry, seasonality, supply/demand
- **INDICES**: P/E trend, earnings growth, yield gap

---

### 🌌 Ether Agent (Akasha) — Orchestrator

**File:** `ether_agent_system.txt`

**Role:** Meta-intelligence, synthesizes all agent outputs
**Element:** Ether (space, consciousness)
**Guna:** Sattva 0.8 | Rajas 0.1 | Tamas 0.1

**Key Responsibilities:**
- Synthesize outputs from Fire, Water, Air, Earth
- Calculate Harmony Score
- Make final EXECUTE/BLOCK/PARTIAL decision
- Broadcast WebSocket decision to frontend

**Synthesis Rules:**
1. Harmony Score < 0.3 → cosmic_block
2. Fire blocks → Always BLOCK (safety first)
3. All 4 agree → confidence × 1.3 (consensus bonus)
4. Earth OVERVALUED + Air BUY → reduce 40%
5. Navagraha determines asset class priority

---

## Part 4: Usage Example

### Loading Prompts

```python
from prompts.elemental import fire_prompt, water_prompt, air_prompt, earth_prompt, ether_prompt

# Load Fire Agent prompt
system_prompt = fire_prompt()

# Use with LLM
response = await llm.complete(
    system=system_prompt,
    user=json.dumps(trade_data),
    response_format="json_object",
    temperature=0.2
)
```

### Getting Assets for Current Planet

```python
from backend.core.navagraha.asset_affinity import (
    get_favored_assets_for_planet,
    get_asset_priority_list,
    get_position_size_multiplier
)

# Get current navagraha state
navagraha_state = await navagraha_service.get_current_state()
dominant = navagraha_state.dominant_planet  # e.g., "JUPITER"

# Get favored assets
favored = get_favored_assets_for_planet(dominant)
# Returns: ["SPX500", "GER40", "DOT/EUR", "XAU/USD", ...]

# Get full priority list
priority_list = get_asset_priority_list(dominant, secondary="MERCURY")

# Adjust position size
multiplier = get_position_size_multiplier(dominant)  # 1.2 for Jupiter
```

### Creating Multi-Asset Order

```python
from backend.config.asset_universe import get_asset_by_symbol

# Get asset definition
asset = get_asset_by_symbol("XAU/USD")
# Returns: TradableAsset with vedic_element="earth", navagraha="SUN"

# Create order respecting Vedic attributes
order = {
    "symbol": asset.symbol,
    "asset_class": asset.asset_class.value,
    "quantity": calculate_position_size(asset, portfolio_value),
    "vedic_element": asset.vedic_element,
    "navagraha_affinity": asset.navagraha_affinity
}
```

---

## Statistics

### Asset Universe Breakdown

```
Total Assets: 57

By Asset Class:
  crypto: 7
  forex: 5
  commodities: 3
  indices: 3
  equities: 39

By Vedic Element:
  fire: 12
  water: 11
  earth: 18
  air: 10
  ether: 6

By Navagraha:
  SUN: 8
  MOON: 7
  MARS: 10
  MERCURY: 11
  JUPITER: 9
  VENUS: 7
  SATURN: 10
```

---

## Integration with Existing System

### Paper Trading Integration

The elemental agents replace `random.random()` in the trading loop:

```python
# OLD (random)
if random.random() > 0.5:
    execute_buy()

# NEW (Vedic agents)
fire_output = await fire_agent.evaluate(trade_data)
water_output = await water_agent.analyze(market_data)
air_output = await air_agent.generate_signal(technical_data)
earth_output = await earth_agent.calculate_value(fundamental_data)

# Ether synthesizes
final_decision = await ether_agent.synthesize(
    fire_output, water_output, air_output, earth_output
)

if final_decision.final_decision == "EXECUTE":
    execute_buy()
```

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/config/asset_universe.py` | 57-asset registry with Vedic attributes |
| `backend/core/navagraha/asset_affinity.py` | Planet → asset mapping |
| `prompts/elemental/fire_agent_system.txt` | Fire Agent (Risk) prompt |
| `prompts/elemental/water_agent_system.txt` | Water Agent (Macro) prompt |
| `prompts/elemental/air_agent_system.txt` | Air Agent (Technical) prompt |
| `prompts/elemental/earth_agent_system.txt` | Earth Agent (Valuation) prompt |
| `prompts/elemental/ether_agent_system.txt` | Ether Agent (Orchestrator) prompt |
| `prompts/elemental/__init__.py` | Prompt loader utility |

---

## Next Steps

1. **Implement Agent Classes** using these prompts
2. **Integrate with LLM** (DeepSeek/GPT-4)
3. **Connect to Trading Loop** replacing random decisions
4. **Test with Paper Trading** on all 57 assets
5. **Monitor Vedic Metrics** (harmony, prana, navagraha)

---

*This implementation transforms the crypto-only system into a true multi-asset Vedic trading platform with 57 assets across 6 classes, all aligned with Vedic astrology principles.*
