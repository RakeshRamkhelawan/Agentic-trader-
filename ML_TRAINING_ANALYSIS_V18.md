# ML Training Analysis: Waarom V18 Data Niet Werkt

## 🎯 De Kern van het Probleem

V18 is een **goede trading strategie**, maar **NIET geschikt voor ML training**.

## 📊 Data Analyse Resultaten

### 1. Harmony Features (Het Belangrijkste Probleem)

| Metric | Waarde | Interpretatie |
|--------|--------|---------------|
| Mean | 0.517 | Redelijk gecentreerd |
| **Std Dev** | **0.031** | **❌ EXTREEM LAAG** |
| Range | 0.364 - 0.623 | Klein bereik |

**Probleem:** Harmony varieert amper (±3% rond het gemiddelde). ML heeft **variance nodig** om patronen te leren.

**Analogie:** Probeer kleuren te leren terwijl alles "lichtblauw" is. Onmogelijk.

### 2. Feature-Target Correlatie

```
Harmony Score -> P&L Correlatie: 0.0799
```

| Correlatie | Betekenis |
|------------|-----------|
| > 0.5 | Sterk, ML kan leren ✅ |
| 0.3 - 0.5 | Matig, bruikbaar ⚠️ |
| **0.0 - 0.1** | **Geen relatie, ML faalt ❌** |

**Probleem:** Harmony voorspelt de outcome (P&L) NIET.

### 3. Strategie Performance

| Metric | Waarde | Doel voor ML |
|--------|--------|--------------|
| Total Return | 5.73% | Positief ✅ |
| **Win Rate** | **47.1%** | **❌ < 50%** |
| Sharpe | Laag | Onvoldoende |

**Probleem:** Win rate is LAGER dan gokken (50%). ML kan geen "winnende" pattern leren als er geen winnaars zijn.

## 🔍 Waarom Werkt V18 Wél als Trading Strategie?

V18 gebruikt harmony als **RISK MANAGEMENT** tool, niet als predictive feature:

```
V18 Logica:
IF harmony < 0.4 THEN BLOCK (te gevaarlijk)
IF harmony > 0.6 THEN TRADE (veilig genoeg)
```

Dit is een **heuristiek** (regel-gebaseerd), niet een **predictive model**.

Het werkt omdat het:
1. Risico reduceert (survivorship bias)
2. Trades filtert (kwaliteit over kwantiteit)
3. Maar GEEN return voorspelt

## ✅ Wat is WEL Nodig voor ML Training?

### Optie 1: Verbeterde Features

In plaats van harmony, gebruik features die WEL varieren:

```python
features = {
    'rsi': 0-100,           # WEL variance ✅
    'macd': -inf to +inf,   # WEL variance ✅
    'volatility': 0-1,      # WEL variance ✅
    'trend': -1, 0, 1,      # WEL variance ✅
    'harmony': 0.5-0.6,     # GEEN variance ❌
}
```

### Optie 2: Beter Target

In plaats van 5-step return (te ruisachtig):

```python
target = {
    'return_5d': -0.1 to +0.1,  # Te noisy ❌
    'direction': -1, 0, 1,       # Beter ✅
    'win': 0, 1,                 # Binary ✅
}
```

### Optie 3: Winnende Strategie

Train ML alleen op data van een strategie die WEL wint:

| Strategie | Win Rate | Geschikt voor ML? |
|-----------|----------|-------------------|
| V18 Elemental | 47% | ❌ Nee |
| Random | 50% | ❌ Nee |
| **Winning (>55%)** | **>55%** | **✅ Ja** |

## 🛠️ Aanbevelingen

### Korte Termijn (Nu)

1. **Gebruik V18 als heuristic**, niet als ML training data
2. **Focus op productie pipeline** zonder ML
3. **Verzamel live data** voor echte ML training

### Middellange Termijn (Weeks)

1. **Draai nieuwe backtests** met:
   - Echte technical indicators (RSI, MACD, etc)
   - Beter strategie (>55% win rate)
   - Duidelijke feature-target relatie

2. **Gebruik winnende strategie** (`backtest_20260220_142832.json` met 488% return)
   - Analyseer waarom deze wint
   - Pas toe op elemental framework
   - Genereer nieuwe ML-ready data

### Lange Termijn (Maanden)

1. **Online learning**: Start met heuristic, switch naar ML na 1000+ live trades
2. **Ensemble**: Combineer V18 + ML + andere strategieën
3. **Transfer learning**: Gebruik backtest data als pre-training, fine-tune op live data

## 📋 Conclusie

| Aspect | V18 Status | Vereist voor ML |
|--------|------------|-----------------|
| Feature Variance | ❌ 0.03 std | ✅ >0.3 std |
| Feature-Target Corr | ❌ 0.08 | ✅ >0.3 |
| Win Rate | ❌ 47% | ✅ >55% |
| Data Size | ✅ 67K samples | ✅ >10K samples |

**V18 is goed voor trading, niet voor ML training.**

---

*Gegenereerd op: 2026-02-27*
*Dataset: Elemental backtest (representatief voor V18)*
