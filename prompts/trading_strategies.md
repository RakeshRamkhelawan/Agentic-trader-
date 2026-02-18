# Trading Strategy Knowledge Base

Structured prompt library voor LLM-agents die trading decisions ondersteunen.

---

## 1. Trend Following (MA Crossover + RSI)

### Entry Conditions
- **BULLISH**: Short MA (50) kruist boven Long MA (200)
  - Bevestiging: RSI > 50 (momentum intact)
  - Volume: Huidige volume > 1.5x gemiddelde van 50 bars
- **BEARISH**: Short MA (50) kruist onder Long MA (200)
  - Bevestiging: RSI < 50

### Exit Rules
- Omgekeerde crossover (Death Cross na Golden Cross)
- RSI < 30 bij long positie (oversold maar momentum weg)
- Trailing stop op 2x ATR

### Risk Parameters
- Stop-loss: 2x ATR onder entry (long) / boven entry (short)
- Max risk per trade: 1% van equity
- Geen entry in sideways markt (ADX < 20)

### Regime Aanpassingen
- **Bull market**: Verruim RSI drempel naar 40 (meer long trades)
- **Bear market**: Verscherp RSI naar 60 (conservatiever)
- **Hoge volatiliteit**: Verklein position size met 50%

---

## 2. Mean Reversion (Bollinger Bands)

### Entry Conditions
- **BULLISH**: Prijs raakt of breekt door lower Bollinger Band
  - Bevestiging: RSI < 30 (oversold)
- **BEARISH**: Prijs raakt of breekt door upper Bollinger Band
  - Bevestiging: RSI > 70 (overbought)

### Exit Rules
- Prijs keert terug naar SMA (middelste band)
- Max holding period: 10 bars (voorkom vastzittende trades)

### Risk Parameters
- Stop-loss: 1% onder lower band (long) / boven upper band (short)
- Max risk: 1% van equity
- Vermijd: trending markten (BB width > 4x normaal)

---

## 3. Breakout Trading (Consolidation Range)

### Entry Conditions
- **BULLISH_BREAKOUT**: Prijs breekt boven N-bar range_high
  - Consolidatie: range < 3% van midpoint gedurende 20+ bars
  - Volume: 2x gemiddelde op breakout bar
- **BEARISH_BREAKOUT**: Prijs breekt onder N-bar range_low

### Exit Rules
- Trailing stop op 50% van range hoogte
- Take profit: 1.5x range hoogte
- Timeout: als breakout niet bevestigd binnen 3 bars -> exit

### Risk Parameters
- Stop-loss: Terug in de range (range_high bij short, range_low bij long)
- Max risk: 0.5% per trade (breakouts falen vaak)
- Volume verificatie is VERPLICHT

---

## 4. LLM Decision Template

Gebruik dit template wanneer de LLM een trade-beslissing moet nemen:

```
CONTEXT:
- Symbool: {symbol}
- Huidige prijs: {price}
- Strategie signaal: {signal_type}
- Signal confidence: {confidence}%

TECHNISCHE INDICATOREN:
- RSI: {rsi}
- MACD: {macd_line} / Signal: {signal_line}
- Bollinger Band positie: {bb_position}
- Volume ratio: {volume_ratio}x gemiddelde

RISK STATUS:
- Portfolio drawdown: {drawdown}%
- Drawdown status: {drawdown_status}
- Dagelijks PnL: {daily_pnl}
- Open posities: {open_positions}/{max_positions}

OPDRACHT:
Analyseer de bovenstaande data en geef:
1. Trade richting (LONG/SHORT/GEEN)
2. Confidence score (0-100)
3. Aanbevolen entry prijs
4. Stop-loss niveau
5. Take-profit niveau
6. Maximale position grootte als % van equity
7. Belangrijkste risico's bij deze trade
```

---

## 5. Risk Decision Hierarchy

Bij elke trade-beslissing gelden de volgende prioriteiten (van hoog naar laag):

1. **Kill Switch actief?** -> GEEN TRADE
2. **Drawdown > hard limit (20%)?** -> GEEN TRADE
3. **Dagelijkse loss > limiet?** -> GEEN TRADE
4. **Max posities bereikt?** -> GEEN TRADE
5. **Confidence < 30%?** -> GEEN TRADE
6. **Drawdown > soft limit (10%)?** -> HALVEER positie
7. **VaR limiet overschreden?** -> VERKLEIN positie
8. **Alle checks geslaagd** -> TRADE met berekende grootte
