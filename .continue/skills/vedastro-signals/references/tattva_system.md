# 36-Tattvas System

The consciousness trading system based on Samkhya philosophy.

## Overview

The 36 Tattvas (principles) form a hierarchy from pure consciousness (Purusha) to material elements (Earth).

## Five Elements (Pancha Mahabhuta)

### Fire (Agni/Tejas)
- **Quality**: Transformation, discrimination
- **Trading Style**: Aggressive, trend-following
- **Guna**: Sattva 0.4 | Rajas 0.5 | Tamas 0.1
- **Assets**: BTC, SOL, NVDA, MSTR
- **Use**: Entry decisions, momentum trades

### Water (Apas)
- **Quality**: Adaptation, memory, flow
- **Trading Style**: Sentiment-based, adaptive
- **Guna**: Sattva 0.4 | Rajas 0.3 | Tamas 0.3
- **Assets**: ETH, EUR/USD, XAG, TLT
- **Use**: Market regime analysis

### Earth (Prithvi)
- **Quality**: Stability, grounding
- **Trading Style**: Conservative, value
- **Guna**: Sattva 0.5 | Rajas 0.2 | Tamas 0.3
- **Assets**: ADA, JPM, PG, XLU
- **Use**: Risk management, stops

### Air (Vayu)
- **Quality**: Movement, change, volatility
- **Trading Style**: Scalping, quick trades
- **Guna**: Sattva 0.3 | Rajas 0.6 | Tamas 0.1
- **Assets**: LINK, EUR/GBP, CRM, XLK
- **Use**: Technical signals, exits

### Ether (Akasha)
- **Quality**: Space, growth, expansion
- **Trading Style**: Long-term growth
- **Guna**: Sattva 0.6 | Rajas 0.2 | Tamas 0.2
- **Assets**: DOT, MSFT, SPX500, QQQ
- **Use**: Portfolio allocation

## Elemental Agents

### Fire Agent (Risk Guardian)
```
Role: Final risk check
Powers: Veto trades, enforce limits
Blocks: Rahu Kala, Prana < 10, Harmony < 0.25
```

### Water Agent (Macro Research)
```
Role: Market regime analysis
Regimes: expansion, contraction, neutral, recovery
Memory: ChromaDB episodes
```

### Air Agent (Technical)
```
Role: Signal generation
Tools: RSI, MACD, ROC
Outputs: BUY/SELL/HOLD with stops
```

### Earth Agent (Valuation)
```
Role: Position sizing
Limits: €2k cap, trailing stops
Logic: Kelly criterion variant
```

## Coherence Score

Measures alignment between ML signal and elemental state:

```python
coherence = calculate_coherence(
    ml_signal=signal,
    tattva_state=current_state,
    min_threshold=0.6
)

if coherence < 0.6:
    # Block trade - misalignment
    return 'hold'
```

## Gunas (Qualities)

### Sattva (Harmony)
- Clear thinking, wisdom
- Good for analysis

### Rajas (Activity)
- Action, desire
- Good for execution

### Tamas (Inertia)
- Confusion, obstruction
- **Block trades when > 0.5**

## Implementation

```python
from backend.core.samkhya import TattvaState

state = TattvaState()
state.fire = 0.7    # High fire energy
state.water = 0.4
state.earth = 0.5
state.air = 0.6
state.ether = 0.5

# Check if safe to trade
if state.tamas > 0.5:
    return False, "High tamas - avoid trading"

# Calculate elemental balance
balance = state.get_balance_score()
```
