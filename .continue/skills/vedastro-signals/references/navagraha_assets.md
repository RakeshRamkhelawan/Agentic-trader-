# Navagraha Asset Affinity

Mapping of the 9 planets (Navagraha) to trading assets and styles.

## Planet Reference

| Planet | Sanskrit | Energy | Direction |
|--------|----------|--------|-----------|
| Sun | Surya | Masculine, hot | East |
| Moon | Chandra | Feminine, moist | North-West |
| Mars | Mangala | Masculine, hot | South |
| Mercury | Budha | Neutral, moist | North |
| Jupiter | Guru | Masculine, warm | North-East |
| Venus | Shukra | Feminine, moist | South-East |
| Saturn | Shani | Neutral, cold | West |
| Rahu | - | Tamasic, chaotic | South-West |
| Ketu | - | Detached, spiritual | - |

## Asset Affinities

### ☉ SUN (Surya)
**Trading Style**: Trend following, authority, core positions
**Element**: Fire
**Best For**: Major trend identification

**Primary Assets**:
- BTC/EUR - Digital gold, authority
- SPX500 - Core market indicator
- XAU/USD - Physical gold, Sun metal
- AAPL - Dominant tech

**Signal**: Strong when SUN is well-placed (own sign, exalted)
**Avoid**: When SUN is combust or debilitated

### ☽ MOON (Chandra)
**Trading Style**: Sentiment, emotional analysis, quick moves
**Element**: Water
**Best For**: Short-term sentiment shifts

**Primary Assets**:
- ETH/EUR - Silver to BTC's gold
- EUR/USD - Most liquid pair
- XAG/USD - Silver, Moon metal
- NFLX - Entertainment, emotions

**Signal**: Follow Moon's speed (fast changes)
**Avoid**: During Moon's nodes (Rahu/Ketu)

### ♂ MARS (Mangala)
**Trading Style**: Momentum, breakout, aggression
**Element**: Fire
**Best For**: High-volatility entries

**Primary Assets**:
- BTC/EUR - Volatile, aggressive
- SOL/EUR - Fast, momentum
- OIL/USD - Energy, conflict-driven
- NVDA - High-beta tech

**Signal**: Entry on momentum confirmation
**Caution**: Can cause over-trading

### ☿ MERCURY (Budha)
**Trading Style**: Scalping, quick trades, arbitrage
**Element**: Air
**Best For**: Short-term technical plays

**Primary Assets**:
- EUR/USD - Liquid, tight spreads
- LINK/EUR - Oracle network, communication
- NAS100 - Tech-heavy, quick moves
- CRM - Business/communication

**Signal**: Quick in-and-out trades
**Avoid**: During Mercury retrograde

### ♃ JUPITER (Guru)
**Trading Style**: Value, growth, expansion
**Element**: Ether
**Best For**: Long-term positions

**Primary Assets**:
- SPX500 - Broad market growth
- GER40 - European growth
- DOT/EUR - Web3 expansion
- MSFT - Steady growth

**Signal**: Accumulate on dips
**Best**: When Jupiter is strong (Sagittarius, Pisces, Cancer)

### ♀ VENUS (Shukra)
**Trading Style**: Value, income, stability
**Element**: Water
**Best For**: Dividend/value plays

**Primary Assets**:
- ETH/EUR - Utility value
- EUR/GBP - Stable pair
- XAG/USD - Industrial value
- JNJ - Defensive, dividend

**Signal**: Quality over quantity
**Best**: In Taurus, Libra, Pisces

### ♄ SATURN (Shani)
**Trading Style**: Discipline, patience, long-term
**Element**: Earth
**Best For**: Risk management, stops

**Primary Assets**:
- ADA/EUR - Methodical development
- GBP/USD - Conservative
- GER40 - Structured market
- JPM - Banking discipline

**Signal**: Strict position sizing
**Caution**: Can cause missed opportunities

### ☊ RAHU (North Node)
**Trading Style**: Speculative, unconventional
**Element**: - (Shadow planet)
**Best For**: Avoiding

**Associated With**:
- SOL, DOT, NVDA, TSLA, COIN
- Meme stocks, crypto

**Warning**: **BLOCK trading during Rahu Kala**
```python
if is_rahu_kala(current_time):
    return {'action': 'block', 'reason': 'Rahu Kala'}
```

### ☋ KETU (South Node)
**Trading Style**: Exit-focused, detachment
**Element**: - (Shadow planet)
**Best For**: Profit taking

**Associated With**:
- BTC, ETH, SPX500, XAU
- Exiting positions

**Signal**: Consider taking profits when Ketu aspects position

## Position Sizing by Planet

```python
position_multipliers = {
    'SUN': 1.0,      # Standard size
    'MOON': 0.8,     # Reduce (emotional)
    'MARS': 1.5,     # Increase (aggressive)
    'MERCURY': 0.5,  # Small (scalping)
    'JUPITER': 1.2,  # Slight increase
    'VENUS': 1.0,    # Standard
    'SATURN': 0.5,   # Conservative
    'RAHU': 0.0,     # BLOCK
    'KETU': 0.0,     # Exit only
}
```

## Usage in Code

```python
from backend.core.navagraha import get_favored_assets, get_position_multiplier

# Get assets for current planet
dominant_planet = 'JUPITER'
assets = get_favored_assets(dominant_planet)
# Returns: ['SPX500', 'GER40', 'DOT/EUR', ...]

# Adjust position size
multiplier = get_position_multiplier(dominant_planet)
size = base_size * multiplier
```
