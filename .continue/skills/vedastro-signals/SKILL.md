---
name: vedastro-signals
description: Generate and analyze Vedic astrological trading signals using VedAstro integration with the 36-Tattvas consciousness system. Use when calculating planetary positions for trading, generating Tattva alignment signals, creating Kundli charts for assets, or analyzing Navagraha asset affinities. Triggers include "VedAstro", "Vedic astrology", "planetary signal", "Tattva", "Kundli", "Navagraha", "Jupiter transit", "Dasha period", "Yoga formation", "elemental filter", "fire element", "crypto astrology".
---

# VedAstro Signals Skill

Generate and analyze Vedic astrological trading signals using VedAstro integration.

## Overview

This skill combines **VedAstro's C# Vedic astrology engine** with the **36-Tattvas consciousness system** to create trading signals based on planetary positions, Dasha periods, and Yogas.

## Architecture

```
VedAstro Connector (C#) → Feature Engine → TattvaOrchestrator → Trading Signal
     ↓                         ↓                  ↓
  Kundli Cache           24-dim features    Elemental Filter
  Transit Calc           ML Features        Risk Check
```

## Quick Start

### Generate a Signal

```python
from backend.vedastro import TattvaOrchestrator

orchestrator = TattvaOrchestrator()
await orchestrator.initialize(assets=['BTC', 'ETH'])

result = await orchestrator.process_market_tick('BTC', {
    'symbol': 'BTC',
    'price': 45000,
    'volume': 1000000
})

# Result contains:
# - decision: BUY/SELL/HOLD
# - confidence: 0.0-1.0
# - alignment_score: Tattva alignment
# - vedastro_data: Planetary positions
```

### Use the CLI

```bash
# Generate signal for BTC today
python .continue/skills/vedastro-signals/scripts/vedastro_signal.py --symbol BTC --date today

# Check Jupiter transit for Gold
python .continue/skills/vedastro-signals/scripts/vedastro_signal.py --symbol XAU --planet JUPITER --aspect

# Generate elemental filter report
python .continue/skills/vedastro-signals/scripts/vedastro_signal.py --element fire --assets BTC,SOL,NVDA
```

## Capabilities

### 1. Planetary Signal Generation

Calculate trading signals based on:
- **Dasha periods** - Major/minor planetary periods
- **Yogas** - Auspicious/inauspicious combinations
- **Sahams** - Sensitive points in the chart
- **Transits** - Current planetary positions

### 2. Elemental Filtering

Filter signals by Tattva (element):
- **Fire (Agni)** - Trend following, high confidence
- **Water (Apas)** - Sentiment, adaptability
- **Earth (Prithvi)** - Stability, value
- **Air (Vayu)** - Volatility, speed
- **Ether (Akasha)** - Growth, expansion

### 3. Navagraha Asset Affinity

Match assets to planetary energies:

| Planet | Style | Assets |
|--------|-------|--------|
| SUN | Trend | BTC, SPX500, XAU |
| MOON | Sentiment | ETH, EUR/USD, XAG |
| MARS | Momentum | SOL, NVDA, OIL |
| MERCURY | Scalping | LINK, EUR/GBP |
| JUPITER | Growth | SPX500, MSFT, DOT |
| VENUS | Value | ETH, JNJ, EUR/GBP |
| SATURN | Discipline | ADA, GBP/USD, JPM |

## CLI Reference

```bash
# Generate signal
python scripts/vedastro_signal.py --symbol BTC --date 2026-02-25

# Check planetary aspect
python scripts/vedastro_signal.py --symbol BTC --planet JUPITER --aspect conjunction

# Elemental filter
python scripts/vedastro_signal.py --element fire --min-score 0.6

# Batch analysis
python scripts/vedastro_signal.py --batch --assets BTC,ETH,SOL,XAU --output report.json
```

## Integration Patterns

### In an Agent

```python
class VedAstroAgent(BaseAgent):
    async def analyze(self, features, context):
        symbol = features['symbol']
        
        # Get VedAstro signal
        signal = await self.orchestrator.process_market_tick(symbol, features)
        
        # Check elemental alignment
        if signal['alignment_score'] < 0.6:
            return {'signal': 'hold', 'reason': 'Low alignment'}
        
        return {
            'signal': signal['decision']['action'],
            'confidence': signal['decision']['confidence'],
            'vedastro': signal['vedastro_data']
        }
```

### Backtest Integration

```python
# Add VedAstro features to backtest
from backend.vedastro.features import generate_astro_features

features = generate_astro_features(
    symbol='BTC',
    date='2026-02-25',
    include_dasha=True,
    include_yogas=True
)
```

## Configuration

```python
from backend.vedastro import VedAstroConfig

# C# interop (fastest, local)
config = VedAstroConfig(
    dll_path='./libs/VedAstro.dll',
    use_http_fallback=False
)

# HTTP fallback (containers)
config = VedAstroConfig(
    use_http_fallback=True,
    http_endpoint='http://vedastro:5000'
)
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/vedastro/connector.py` | C# bridge |
| `backend/vedastro/features.py` | ML feature extraction |
| `backend/vedastro/oracle.py` | XGBoost model |
| `backend/vedastro/orchestrator.py` | Integration controller |
| `prompts/elemental/` | Elemental agent prompts |

## References

- `references/vedastro_guide.md` - Complete VedAstro integration guide
- `references/tattva_system.md` - 36-Tattvas system details
- `references/navagraha_assets.md` - Asset-planet mappings

## Swiss Ephemeris

The platform uses Swiss Ephemeris for precise planetary calculations:
- Location: `libs/` folder
- Accuracy: 0.001 arcseconds
- Range: 3000 BCE to 3000 CE
