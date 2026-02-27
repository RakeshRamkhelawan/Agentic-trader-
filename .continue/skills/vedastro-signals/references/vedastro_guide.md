# VedAstro Integration Guide

Complete guide for VedAstro integration in the Agentic Trader Platform.

## What is VedAstro?

VedAstro is a C# Vedic astrology engine that calculates:
- Planetary positions (Swiss Ephemeris accuracy)
- Dasha periods (Vimshottari)
- Yogas (planetary combinations)
- Sahams (sensitive points)
- Transit analysis

## Architecture Layers

```
Layer 4: TattvaOrchestrator (Consciousness Controller)
├── Integrates VedAstro + XGBoost + 36 Tattvas
├── Applies philosophical filters (Tamas block, coherence check)
└── Calculates alignment score between ML and philosophy

Layer 3: XGBoost Oracle ("Buddhi" - Intellect)
├── Fast prediction (< 1ms)
├── Pre-trained on OHLCV + Astro features
└── Online learning support

Layer 2: Feature Engine
├── 24-dimensional feature vectors
├── Planetary angles, aspects, dignities
├── Gann Square of 9 integration
└── 36 Tattvas state encoding

Layer 1: VedAstro Connector
├── pythonnet for direct C# calls (10x faster)
├── HTTP fallback for containers
├── Kundli caching (immutable data)
└── Transit calculation (hourly cache)
```

## Key Concepts

### Dasha Periods

Vimshottari Dasha system - planetary periods that influence life/trading:

```python
# Major period (Mahadasha) - Years
# Minor period (Antardasha) - Months
# Sub-period (Pratyantardasha) - Days

from backend.vedastro import get_current_dasha

dasha = get_current_dasha(birth_chart, datetime.now())
print(f"Mahadasha: {dasha.lord} ({dasha.years} years)")
print(f"Antardasha: {dasha.sub_lord}")
```

### Yogas

Auspicious/inauspicious planetary combinations:

| Yoga | Effect | Trading Signal |
|------|--------|----------------|
| Gaja Kesari | Wisdom, success | Bullish |
| Dhana Yoga | Wealth | Bullish |
| Papa Kartari | Obstacles | Bearish/Caution |
| Kemadruma | Isolation | Neutral/Hold |

### Sahams

Sensitive points in the chart for specific events:

```python
# Trading Sahams
paisa_saham = calculate_saham(chart, 'Paisa')  # Money
labha_saham = calculate_saham(chart, 'Labha')  # Profit
```

## Configuration

### C# Interop Mode (Fastest)

```python
from backend.vedastro import VedAstroConfig, VedAstroConnector

config = VedAstroConfig(
    dll_path='./libs/VedAstro.dll',
    use_http_fallback=False
)
connector = VedAstroConnector(config)
```

### HTTP Fallback Mode

```python
config = VedAstroConfig(
    use_http_fallback=True,
    http_endpoint='http://vedastro:5000',
    timeout=30
)
```

## Trading Signal Flow

```python
async def generate_signal(symbol: str, tick: dict):
    # 1. Get or create Kundli for asset
    kundli = await connector.get_kundli(symbol)

    # 2. Calculate current transits
    transits = await connector.get_transits(datetime.now())

    # 3. Extract 24-dim features
    features = extract_features(kundli, transits)

    # 4. XGBoost prediction
    ml_signal = oracle.predict(features)

    # 5. Elemental filter
    alignment = orchestrator.check_alignment(ml_signal, tattva_state)

    # 6. Risk check
    if alignment < 0.6:
        return {'action': 'hold', 'reason': 'Low alignment'}

    return {
        'action': ml_signal.action,
        'confidence': ml_signal.confidence,
        'alignment': alignment
    }
```

## Performance

- VedAstro calculation: ~0.02s per asset
- XGBoost prediction: <1ms
- Cache hit rate: High for same-day calls
- Async overhead: <5%

## File Locations

```
backend/vedastro/
├── __init__.py
├── connector.py      # C# bridge
├── features.py       # ML features
├── oracle.py         # XGBoost
├── orchestrator.py   # Integration
└── http_bridge.py    # HTTP fallback

libs/
├── VedAstro.dll      # C# library
└── swisseph.dll      # Swiss Ephemeris
```
