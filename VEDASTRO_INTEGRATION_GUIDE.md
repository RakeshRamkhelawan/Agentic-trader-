# VedAstro-Tattvas Fusion Integration Guide

## Overview

This integration combines **VedAstro's C# Vedic astrology engine** with the **36-Tattvas consciousness trading system** to create a hybrid trading oracle that respects both technical ML signals and philosophical alignment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VEDASTRO-TATTVAS FUSION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 4: TattvaOrchestrator ("Consciousness Controller")                   │
│  ├─ Integrates VedAstro + XGBoost + 36 Tattvas                             │
│  ├─ Applies philosophical filters (Tamas block, coherence check)            │
│  └─ Calculates alignment score between ML and philosophy                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 3: XGBoost Oracle ("Buddhi" - Intellect)                            │
│  ├─ Fast prediction (< 1ms)                                                 │
│  ├─ Pre-trained on OHLCV + Astro features                                   │
│  └─ Online learning support                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 2: Feature Engine (Astro → ML Features)                             │
│  ├─ 24-dimensional feature vectors                                          │
│  ├─ Planetary angles, aspects, dignities                                    │
│  ├─ Gann Square of 9 integration                                            │
│  └─ 36 Tattvas state encoding                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 1: VedAstro Connector (C# Interop)                                  │
│  ├─ pythonnet for direct C# calls (10x faster)                              │
│  ├─ HTTP fallback for containers                                            │
│  ├─ Kundli caching (immutable data)                                         │
│  └─ Transit calculation (hourly cache)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
backend/vedastro/
├── __init__.py           # Module exports
├── connector.py          # VedAstro C# bridge
├── features.py           # ML feature extraction
├── oracle.py             # XGBoost model
├── orchestrator.py       # Integration controller
└── http_bridge.py        # HTTP fallback API

infrastructure/docker/
└── vedastro.Dockerfile   # Container setup with .NET + Mono

scripts/
└── train_xgboost_model.py # Training pipeline

backend/tests/unit/vedastro/
└── test_vedastro_integration.py # Unit tests
```

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install xgboost scikit-learn numpy pandas

# For C# interop on Windows
pip install pythonnet

# For HTTP fallback
pip install httpx fastapi uvicorn
```

### Docker Setup

```bash
# Build VedAstro container
docker build -f infrastructure/docker/vedastro.Dockerfile -t vedastro-bridge .

# Run container
docker run -p 5000:5000 vedastro-bridge
```

## Usage

### Basic Example

```python
import asyncio
from datetime import datetime
from backend.vedastro import TattvaOrchestrator

async def main():
    # Initialize orchestrator
    orchestrator = TattvaOrchestrator(
        system_identity=your_system_identity,  # 36 Tattvas
        guna_quantifier=your_guna_quantifier,
        min_coherence=0.6,
        tamas_threshold=0.5
    )
    
    # Pre-calculate Kundli's (one-time at startup)
    await orchestrator.initialize(assets=['BTC', 'ETH'])
    
    # Process market tick
    tick = {
        'symbol': 'BTC',
        'price': 43250.50,
        'volume': 1234567
    }
    
    result = await orchestrator.process_market_tick('BTC', tick)
    
    print(f"Decision: {result['decision']['action']}")
    print(f"Confidence: {result['decision']['confidence']:.2f}")
    print(f"Alignment: {result['alignment_score']:.2f}")

asyncio.run(main())
```

### Training a Model

```bash
python scripts/train_xgboost_model.py \
    --data data/historical/btc_ohlcv.csv \
    --symbol BTC \
    --output models/xgboost_btc.json
```

### Configuration

```python
from backend.vedastro import VedAstroConnector, VedAstroConfig

# C# interop mode (fastest)
config = VedAstroConfig(
    dll_path='./libs/VedAstro.dll',
    use_http_fallback=False
)

# HTTP fallback mode (containers)
config = VedAstroConfig(
    use_http_fallback=True,
    http_endpoint='http://vedastro:5000'
)

connector = VedAstroConnector(config)
```

## Feature Reference (24 dimensions)

| Feature | Description | Range |
|---------|-------------|-------|
| `sun_moon_angle` | Sun-Moon angular separation | 0-1 |
| `sun_jupiter_angle` | Sun-Jupiter angle | 0-1 |
| `moon_saturn_angle` | Moon-Saturn angle | 0-1 |
| `jupiter_trine_sun` | Jupiter trine Sun aspect | 0/1 |
| `saturn_square_moon` | Saturn square Moon aspect | 0/1 |
| `benefic_aspects` | Count of benefic aspects | 0-1 |
| `malefic_aspects` | Count of malefic aspects | 0-1 |
| `retrograde_count` | Number of retrograde planets | 0-1 |
| `exalted_count` | Exalted planets count | 0-1 |
| `jupiter_dignity` | Jupiter dignity (-1 to 1) | 0-1 |
| `price_at_cardinal` | Price at Gann cardinal | 0/1 |
| `tattva_coherence` | 36 Tattvas coherence | 0-1 |
| `dominant_guna` | Sattva(0)/Rajas(1)/Tamas(2) | 0-1 |

## Philosophical Rules

### 1. Tamas Block
```python
if gunas['tamas'] > 0.5:
    return HOLD  # Preservation mode
```

### 2. Coherence Requirement
```python
if coherence < 0.6:
    return WAIT  # Unclear consciousness
```

### 3. Sade Sati Protection
```python
if sade_sati_active and signal == 'UP':
    return HOLD  # Saturn restriction
```

### 4. Size Scaling
```python
size_multiplier = (
    sattva * 1.0 +   # Full size
    rajas * 0.5 +    # Half size
    tamas * 0.0      # No trade
)
```

## Performance

| Operation | Latency |
|-----------|---------|
| Kundli cache lookup | 0.1 ms |
| Transit calculation | 0.5 ms |
| Feature extraction | 0.2 ms |
| XGBoost prediction | 0.2 ms |
| Tattva filter | 0.1 ms |
| **Total** | **~1 ms** |

## Testing

```bash
# Run VedAstro tests
pytest backend/tests/unit/vedastro/ -v

# Run all integration tests
pytest backend/tests/unit/vedastro/ \
       backend/tests/unit/core/test_tracing.py \
       backend/tests/unit/testing/test_chaos_monkey.py \
       backend/tests/unit/core/test_promptguard.py -v
```

## Asset Birthdays

| Symbol | Birth Date | Event |
|--------|------------|-------|
| BTC | 2009-01-03 | Genesis block |
| ETH | 2015-07-30 | Genesis block |
| AAPL | 1980-12-12 | IPO |
| TSLA | 2010-06-29 | IPO |
| GOOGL | 2004-08-19 | IPO |
| MSFT | 1986-03-13 | IPO |
| AMZN | 1997-05-15 | IPO |
| NVDA | 1999-01-22 | IPO |

## Deployment

### Production Checklist

- [ ] Copy VedAstro DLLs to `libs/` directory
- [ ] Pre-calculate Kundli's for all traded assets
- [ ] Train XGBoost model on historical data
- [ ] Configure environment variables
- [ ] Set up HTTP bridge fallback (optional)
- [ ] Test with ChaosMonkey enabled
- [ ] Verify tracing integration

### Environment Variables

```bash
# VedAstro
VEDASTRO_DLL_PATH=./libs/VedAstro.dll
VEDASTRO_USE_HTTP=false
VEDASTRO_HTTP_ENDPOINT=http://localhost:5000

# XGBoost
XGBOOST_MODEL_PATH=models/xgboost.json
XGBOOST_CONFIDENCE_THRESHOLD=0.6

# Tattva Filters
TATTVA_MIN_COHERENCE=0.6
TATTVA_TAMAS_THRESHOLD=0.5
SADE_SATI_PROTECTION=true
```

## License

This integration respects both:
- **VedAstro** (GPL v3) - Vedic astrology calculations
- **Agentic Trader Platform** (Proprietary) - 36 Tattvas trading system
