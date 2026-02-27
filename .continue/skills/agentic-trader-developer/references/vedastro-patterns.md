# VedAstro Patterns - Agentic Trader

Guide for working with Vedic astrology (VedAstro) in the Agentic Trader platform.

## Overview

VedAstro provides astrological signals for trading decisions based on planetary positions.

**Location:** `backend/vedastro/`  
**Key Components:**
- `EnhancedAstroOrchestrator` - Main entry point
- `TradingSignalGenerator` - Signal generation
- `connector.py` - C# VedAstro bridge

## Quick Start

### Generate Trading Signal

```python
from backend.vedastro import EnhancedAstroOrchestrator

# Initialize
orchestrator = EnhancedAstroOrchestrator()

# Get signal
signal = await orchestrator.analyze_asset(
    symbol="BTC",
    current_price=45000.0
)

# Use signal
print(signal.trading_signal.signal)      # "buy" | "sell" | "hold"
print(signal.trading_signal.confidence)  # 0.0 - 1.0
```

### Access Signal Details

```python
signal_data = {
    "signal": signal.trading_signal.signal,
    "confidence": signal.trading_signal.confidence,
    "strength_score": signal.trading_signal.strength_score,
    "risk_level": signal.trading_signal.risk_level,
    "primary_factors": signal.trading_signal.primary_factors,
    "supporting_factors": signal.trading_signal.supporting_factors,
}
```

## Signal Interpretation

### Signal Values

| Signal | Meaning | Action |
|--------|---------|--------|
| `buy` | Strong bullish | Consider long position |
| `sell` | Strong bearish | Consider short position |
| `hold` | Neutral/unclear | No action |

### Confidence Levels

| Confidence | Interpretation |
|------------|----------------|
| > 0.8 | Very high confidence |
| 0.6 - 0.8 | High confidence |
| 0.4 - 0.6 | Medium confidence |
| < 0.4 | Low confidence, avoid |

### Risk Levels

| Risk | Interpretation |
|------|----------------|
| `low` | Favorable conditions |
| `medium` | Caution advised |
| `high` | Avoid trading |

## MCP Tool Integration

VedAstro tools are exposed via MCP:

```python
# In AgentWithTools subclass
async def get_vedastro_signal(self, symbol: str, price: float):
    """Get VedAstro signal via MCP."""
    return await self.call_tool(
        "vedastro__generate_signal",
        {"symbol": symbol, "current_price": price}
    )
```

## Dasha Analysis

Get planetary period information:

```python
from backend.vedastro import get_dasha_info

dasha = await get_dasha_info(
    symbol="BTC",
    birth_chart_data={...}
)

print(dasha.current_mahadasha)   # Current major period
print(dasha.current_antardasha)  # Current sub-period
```

## Transit Analysis

Get current planetary transits:

```python
from backend.vedastro import get_transit_analysis

transits = await get_transit_analysis(
    symbol="BTC",
    date=datetime.now()
)

for transit in transits:
    print(f"{transit.planet} in {transit.sign}")
    print(f"Aspect: {transit.aspect}")
    print(f"Strength: {transit.strength}")
```

## Trading Strategies

### Conservative Strategy

```python
async def conservative_signal(symbol, price):
    signal = await get_vedastro_signal(symbol, price)
    
    # Only trade high confidence + low risk
    if signal["confidence"] > 0.7 and signal["risk_level"] == "low":
        return signal["signal"]
    
    return "hold"
```

### Aggressive Strategy

```python
async def aggressive_signal(symbol, price):
    signal = await get_vedastro_signal(symbol, price)
    
    # Trade on medium confidence
    if signal["confidence"] > 0.5:
        return signal["signal"]
    
    return "hold"
```

### Combined Strategy

```python
async def combined_signal(symbol, price, technical_signal):
    vedastro = await get_vedastro_signal(symbol, price)
    
    # Only trade when both agree
    if vedastro["signal"] == technical_signal and vedastro["confidence"] > 0.6:
        return vedastro["signal"]
    
    return "hold"
```

## Error Handling

VedAstro can fail if:
- Ephemeris data unavailable
- Invalid symbol
- Network issues (if using HTTP bridge)

Always handle errors:

```python
try:
    signal = await orchestrator.analyze_asset(symbol, price)
except Exception as e:
    logger.error(f"VedAstro failed: {e}")
    # Fallback to technical analysis
    return {"signal": "hold", "error": str(e)}
```

## Testing

```python
@pytest.mark.asyncio
async def test_vedastro_signal():
    orchestrator = EnhancedAstroOrchestrator()
    
    signal = await orchestrator.analyze_asset("BTC", 45000.0)
    
    assert signal.trading_signal.signal in ["buy", "sell", "hold"]
    assert 0.0 <= signal.trading_signal.confidence <= 1.0
```

## Performance Considerations

- VedAstro calculations are CPU intensive
- Results can be cached for 1-5 minutes
- Use circuit breaker for HTTP bridge calls

```python
@circuit_breaker(failure_threshold=3)
async def cached_vedastro_signal(symbol, price):
    cache_key = f"vedastro:{symbol}:{int(price/100)}"
    
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    signal = await orchestrator.analyze_asset(symbol, price)
    await cache.set(cache_key, signal, ttl=300)  # 5 min cache
    
    return signal
```

## SOC2 Data Handling

VedAstro signals are used for trading decisions. Ensure:
- Signals are logged for audit trail
- Decisions can be traced back to signal data
- No PII in astrological calculations

```python
async def audited_vedastro_signal(symbol, price):
    """Get signal with audit logging for SOC2."""
    signal = await orchestrator.analyze_asset(symbol, price)
    
    # Audit log for compliance
    logger.info(f"VEDASTRO_SIGNAL: {symbol}, signal={signal.signal}, confidence={signal.confidence}")
    
    return signal
```

## References

- Swiss Ephemeris documentation
- Vedic astrology texts
- Platform backtest results: `BACKTEST_RESULTS.md`
