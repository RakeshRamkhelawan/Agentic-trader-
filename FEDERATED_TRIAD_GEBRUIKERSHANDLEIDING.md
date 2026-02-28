# Federated Triad - Gebruikershandleiding

> **Doelgroep:** Eindgebruikers, Traders, Portfolio Managers
> **Vereiste kennis:** Basis trading begrippen
> **Technische kennis:** Niet vereist

---

## Inhoudsopgave

1. [Wat is Federated Triad?](#1-wat-is-federated-triad)
2. [Snelstart](#2-snelstart)
3. [De Vier Councils](#3-de-vier-councils)
4. [Het Dashboard](#4-het-dashboard)
5. [Trading Werkwijze](#5-trading-werkwijze)
6. [A/B Testing](#6-ab-testing)
7. [Prestaties Monitoren](#7-prestaties-monitoren)
8. [Troubleshooting](#8-troubleshooting)
9. [Veelgestelde Vragen](#9-veelgestelde-vragen)

---

## 1. Wat is Federated Triad?

### 1.1 Overzicht

Federated Triad is een **AI-gedreven trading systeem** dat meerdere "intelligenties" combineert om betere trading beslissingen te nemen. In plaats van één algoritme, gebruikt het drie gespecialiseerde "councils" die samenwerken:

```
┌─────────────────────────────────────────┐
│         FEDERATED TRIAD                 │
│                                         │
│   🧘 Guna    🧠 Mind     💪 Body       │
│   Council    Council     Council       │
│                                         │
│        ↓         ↓         ↓           │
│              🎯 BUDDHI                  │
│            (Decision Maker)            │
│                                         │
└─────────────────────────────────────────┘
```

### 1.2 Waarom "Triad"?

Het systeem is geïnspireerd op **Samkhya filosofie** (een oude Indiase wijsbegeerte):

- **Drie Gunas** (kwaliteiten): Sattva (harmonie), Rajas (activiteit), Tamas (inertie)
- **Buddhi** (intellect): Het vermogen om te onderscheiden en beslissingen te nemen

Dit betekent in trading:
- Verschillende "perspectieven" op de markt
- Eén centrale beslisser die alles weegt
- Meer betrouwbare signalen door consensus

### 1.3 Kernvoordelen

| Voordeel | Beschrijving |
|----------|--------------|
| **🎯 Betrouwbaarder** | Meerdere councils moeten het eens zijn |
| **📊 Uitlegbaar** | Je ziet WAAROM een beslissing is genomen |
| **🧠 Lerend** | Systeem leert van eerdere trades |
| **⚖️ Getest** | A/B testing toont statistisch bewijs |

---

## 2. Snelstart

### 2.1 Eerste Keer Opstarten

**Stap 1: Login**
1. Open de web interface: `http://localhost:5173`
2. Log in met je credentials
3. Je ziet het hoofddashboard

**Stap 2: Verbinding Testen**
1. Klik op "System Status" (rechtsboven)
2. Controleer of alle councils groen zijn:
   - ✅ Guna Council
   - ✅ Mind Council
   - ✅ Body Council
   - ✅ Buddhi Mind
   - ✅ Redis Event Bus

**Stap 3: Start Paper Trading**
1. Ga naar "Settings" → "Trading Mode"
2. Selecteer **"Paper Trading"** (oefenmodus)
3. Klik "Save"

### 2.2 Je Eerste Trade

**Methode 1: Automatisch (Aanbevolen)**
```
1. Ga naar "Auto Trading"
2. Selecteer asset: "BTC-USD"
3. Stel bedrag in: "1000 USD"
4. Klik "Start"

Het systeem analyseert nu automatisch en opent posities
wanneer alle councils het eens zijn.
```

**Methode 2: Handmatig**
```
1. Ga naar "Market Analysis"
2. Selecteer een asset
3. Klik "Analyze Now"
4. Bekijk de council outputs
5. Klik "Execute Trade" als je akkoord bent
```

### 2.3 Dashboard Overzicht

```
┌────────────────────────────────────────────────────────────┐
│  FEDERATED TRIAD                              [⚙️] [👤]   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📊 MARKT OVERZICHT                                       │
│  ┌──────────────┬──────────────┬──────────────┐           │
│  │   BTC-USD    │   ETH-USD    │   SOL-USD    │           │
│  │   $45,230    │   $3,450     │   $98.50     │           │
│  │   +2.3% 📈   │   +1.8% 📈   │   -0.5% 📉   │           │
│  └──────────────┴──────────────┴──────────────┘           │
│                                                            │
│  🎯 LAATSTE BESLISSING                                    │
│  ┌──────────────────────────────────────────────┐         │
│  │ Action:     BULLISH  🟢                      │         │
│  │ Confidence: 76%                              │         │
│  │ Coherence:  75%                              │         │
│  │ Risk:       Medium                           │         │
│  │ Time:       14:32:05                         │         │
│  └──────────────────────────────────────────────┘         │
│                                                            │
│  🧘 COUNCIL STATUS                                        │
│  ┌──────────┬──────────┬──────────┬──────────┐           │
│  │   GUNA   │   MIND   │   BODY   │  BUDDHI  │           │
│  │   72%    │   68%    │   85%    │   76%    │           │
│  │ Sattva   │  Greed   │  Good    │ Bullish  │           │
│  └──────────┴──────────┴──────────┴──────────┘           │
│                                                            │
│  📈 PRESTATIES (Vandaag)                                  │
│  Trades: 5 │ Wins: 3 │ PnL: +$234 │ Win Rate: 60%        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 3. De Vier Councils

### 3.1 Guna Council - Markttoestand

**Wat doet het?**
Analyseert de algemene "toestand" van de markt.

**De Drie Toestanden:**

| Toestand | Emoji | Betekenis | Trading Implicatie |
|----------|-------|-----------|-------------------|
| **Sattva** | 🧘 | Harmonie, balans | ✅ Goed voor trades |
| **Rajas** | 🔥 | Activiteit, momentum | ⚠️ Voorzichtig |
| **Tamas** | 🌑 | Inertie, verwarring | ❌ Vermijden |

**Voorbeeld Output:**
```
GUNA COUNCIL
────────────
Toestand: Sattva (Harmonie)
Verdeling:
  🧘 Sattva: 45% ████████████
  🔥 Rajas:  35% █████████
  🌑 Tamas:  20% █████

Advies: Gebalanceerde markt, matig bullish
```

**Hoe te gebruiken:**
- Sattva dominant = Ideaal voor trades
- Rajas dominant = Hoge volatiliteit, gebruik kleinere posities
- Tamas dominant = Markt is onduidelijk, wacht af

### 3.2 Mind Council - Sentiment

**Wat doet het?**
Meet de emotie (fear/greed) in de markt.

**Fear & Greed Indices:**

```
MIND COUNCIL
────────────
😱 Fear Index:  35/100  ███████
🤑 Greed Index: 55/100  ███████████
📊 Bias:        +20      (Netto Greed)

Interpretatie:
  • Markt toont meer greed dan fear
  • Mean reversion mogelijk
  • Wees voorzichtig met longs
```

**Sentiment Levels:**

| Fear | Greed | Interpretatie | Actie |
|------|-------|---------------|-------|
| 0-25 | 75-100 | Extreme Euphorie | ⚠️ Contrarian (verkoop) |
| 25-40 | 60-75 | Greed Dominant | ⚠️ Voorzichtig |
| 40-60 | 40-60 | Balanced | ✅ Normale trading |
| 60-75 | 25-40 | Fear Dominant | ⚠️ Contrarian (koop) |
| 75-100 | 0-25 | Extreme Panic | 🛒 Koop kansen |

**Hoe te gebruiken:**
- Extreme waarden (>75 of <25) = Contrarian signaal
- Balanced (40-60) = Trend following werkt beter

### 3.3 Body Council - Executie Kwaliteit

**Wat doet het?**
Meet hoe goed trades daadwerkelijk uitgevoerd worden (slippage, latency).

```
BODY COUNCIL
────────────
⚡ Executie Kwaliteit: 85%
💰 Slippage: 2.5 bps (0.025%)
⏱️  Latency: 45ms
📈 Fill Rate: 98%

Advies: ✅ Goede condities voor trading
```

**Metrics Uitleg:**

| Metric | Goed | Matig | Slecht |
|--------|------|-------|--------|
| **Executie Kwaliteit** | >80% | 60-80% | <60% |
| **Slippage** | <5 bps | 5-10 bps | >10 bps |
| **Latency** | <50ms | 50-100ms | >100ms |
| **Fill Rate** | >95% | 85-95% | <85% |

**Hoe te gebruiken:**
- Lage executie kwaliteit = Wacht op betere condities
- Hoge slippage = Gebruik limit orders ipv market orders

### 3.4 Buddhi Mind - De Beslisser

**Wat doet het?**
Combineert alle council views tot één finale beslissing.

```
BUDDHI DECISION
───────────────
🎯 Action:     BULLISH
💪 Confidence: 76%
🤝 Coherence:  75%
⚠️  Risk Level: Medium
📝 Rationale:
   • Guna toont Sattva dominantie (45%)
   • Mind toont matige greed (+20)
   • Body toont goede executie (85%)
   • Councils zijn 75% eens

✅ UITVOERBAAR
```

**Belangrijke Waarden:**

| Waarde | Drempel | Betekenis |
|--------|---------|-----------|
| **Confidence** | >50% | Vertrouwen in beslissing |
| **Coherence** | >30% | Overeenstemming councils |
| **Risk Level** | Low/Med | Acceptabel voor trading |

**Uitvoerbaar?**
- ✅ **JA** als: confidence > 50% + coherence > 30% + action ≠ hold
- ❌ **NEE** als: councils zijn het oneens OF te weinig vertrouwen

---

## 4. Het Dashboard

### 4.1 Hoofdscherm

```
┌─────────────────────────────────────────────────────────────┐
│                     FEDERATED TRIAD                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [🏠 Home] [📊 Analysis] [💰 Trades] [📈 Performance] [⚙️]  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔔 LIVE MARKET DATA                   Status: 🟢 Online    │
│                                                             │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │  BTC-USD    │  ETH-USD    │  SOL-USD    │  AAPL       │ │
│  │  $45,230    │  $3,450     │  $98.50     │  $178.50    │ │
│  │  +2.3% 🟢   │  +1.8% 🟢   │  -0.5% 🔴   │  +0.8% 🟢   │ │
│  │             │             │             │             │ │
│  │ [Analyze]   │ [Analyze]   │ [Analyze]   │ [Analyze]   │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
│                                                             │
│  🎯 LAATSTE BESLISSING                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Asset:      BTC-USD                                │   │
│  │  Action:     🟢 BULLISH                             │   │
│  │  Confidence: ████████████████████░░░░ 76%           │   │
│  │  Coherence:  ███████████████████░░░░░ 75%           │   │
│  │  Risk:       🟡 Medium                              │   │
│  │  Time:       2 minuten geleden                      │   │
│  │                                                     │   │
│  │  [Details]  [Execute Trade]  [Dismiss]              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📊 COUNCIL BREAKDOWN                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🧘 Guna (35%):  ████████████████░░ Sattva 45%      │   │
│  │  🧠 Mind (25%):  ██████████████░░░░ Greed +20       │   │
│  │  💪 Body (25%):  █████████████████ Quality 85%      │   │
│  │  🔮 Graha (15%): ░░░░░░░░░░░░░░░░░░ Neutral         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📈 DAGELIJKE PRESTATIES                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Trades:    12      │      PnL:      +$456         │   │
│  │  Wins:      7       │      Win Rate: 58%           │   │
│  │  Losses:    5       │      Avg Win:  $89           │   │
│  │                     │      Avg Loss: $42           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Analysis Scherm

Dit scherm toont gedetailleerde analyse van één asset:

```
┌─────────────────────────────────────────────────────────────┐
│  📊 ANALYSIS: BTC-USD                        [$45,230]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Overview] [Councils] [Chart] [History]                    │
│                                                             │
│  🧘 GUNA COUNCIL                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Market State: Sattva (Balanced Trending)           │   │
│  │                                                     │   │
│  │  🧘 Sattva  45% ████████████  Balanced             │   │
│  │  🔥 Rajas   35% █████████     Active               │   │
│  │  🌑 Tamas   20% █████         Quiet                │   │
│  │                                                     │   │
│  │  Volatility:  2.8% (Normal)                         │   │
│  │  RSI:         58 (Neutral)                          │   │
│  │  Trend:       Up +2.3% (7d)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🧠 MIND COUNCIL                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  😱 Fear:   35% ███████                           │   │
│  │  🤑 Greed:  55% ███████████                       │   │
│  │                                                     │   │
│  │  Interpretatie: Greed dominant (+20)                │   │
│  │  Mean Reversion: Mogelijk                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  💪 BODY COUNCIL                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Executie Kwaliteit: 85%  🟢                        │   │
│  │  Slippage: 2.5 bps                                  │   │
│  │  Latency: 45ms                                      │   │
│  │  Fill Rate: 98%                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🎯 BUDDHI DECISION                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Action:     🟢 BULLISH                             │   │
│  │  Confidence: 76%                                    │   │
│  │  Coherence:  75%  ✅ Goede overeenstemming          │   │
│  │  Risk:       🟡 Medium                              │   │
│  │                                                     │   │
│  │  Rationale:                                         │   │
│  │  "Guna toont sattva dominantie, markt is gebalanceerd│   │
│  │   met matige activiteit. Mind toont gematigde greed │   │
│  │   wat niet extreem is. Body bevestigt goede         │   │
│  │   executie mogelijkheden."                          │   │
│  │                                                     │   │
│  │              [🚀 EXECUTE TRADE]                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Performance Scherm

```
┌─────────────────────────────────────────────────────────────┐
│  📈 PERFORMANCE OVERVIEW                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Day] [Week] [Month] [Year] [All Time]                     │
│                                                             │
│  📊 SAMENVATTING                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Totale PnL:        +$4,567  🟢                    │   │
│  │  Win Rate:          58%                            │   │
│  │  Aantal Trades:     124                            │   │
│  │  Sharpe Ratio:      1.34                           │   │
│  │  Max Drawdown:      -12%                           │   │
│  │  Profit Factor:     1.45                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📈 PnL CURVE                                               │
│  │                                                          │
│  $5K ┤                                    ╭────╮           │
│      │                              ╭────╯    │           │
│  $3K ┤                        ╭────╯         │           │
│      │                  ╭────╯               │           │
│  $1K ┤            ╭────╯                     │           │
│      │      ╭────╯                           │           │
│   $0 ┼──────┴────────────────────────────────┴────       │
│      │                                                    │
│                                                             │
│  🎯 COUNCIL CONTRIBUTION                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🧘 Guna:   ████████████████████  35%              │   │
│  │  🧠 Mind:   ██████████████        25%              │   │
│  │  💪 Body:   ██████████████        25%              │   │
│  │  🔮 Graha:  ████████              15%              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📋 RECENTE TRADES                                          │
│  ┌──────────┬────────┬─────────┬─────────┬──────────┐     │
│  │ Time     │ Asset  │ Action  │ PnL     │ Outcome  │     │
│  ├──────────┼────────┼─────────┼─────────┼──────────┤     │
│  │ 14:32    │ BTC    │ Long    │ +$89    │ 🟢 Win   │     │
│  │ 13:15    │ ETH    │ Short   │ -$34    │ 🔴 Loss  │     │
│  │ 11:45    │ SOL    │ Long    │ +$156   │ 🟢 Win   │     │
│  │ 10:20    │ BTC    │ Long    │ +$67    │ 🟢 Win   │     │
│  └──────────┴────────┴─────────┴─────────┴──────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Trading Werkwijze

### 5.1 Automatisch Trading

**Stap-voor-stap:**

1. **Ga naar "Auto Trading"**
   ```
   Menu → Auto Trading
   ```

2. **Configureer Parameters**
   ```
   Asset:           BTC-USD (of multi-select)
   Capital:         $10,000
   Risk per Trade:  2%
   Max Positions:   3
   Mode:            Paper (oefen) / Live (echt)
   ```

3. **Start Bot**
   ```
   [▶️ START TRADING BOT]
   ```

4. **Monitor**
   - Het systeem analyseert elke 30 seconden
   - Toont "🟡 Scanning..." of "🟢 Trade Found!"
   - Voert automatisch uit als criteria voldaan zijn

### 5.2 Handmatig Trading

**Stap-voor-stap:**

1. **Analyseer Asset**
   ```
   Dashboard → [Analyze] bij gewenste asset
   ```

2. **Review Council Outputs**
   - Check Guna: Is de markt stabiel?
   - Check Mind: Is sentiment niet extreem?
   - Check Body: Is executie goed?

3. **Check Buddhi Decision**
   ```
   Confidence > 50%?  ✅
   Coherence > 30%?   ✅
   Risk acceptable?   ✅
   ```

4. **Execute Trade**
   ```
   [🚀 EXECUTE TRADE]

   Bevestig:
   - Asset: BTC-USD
   - Side: Buy (Bullish)
   - Size: 0.1 BTC
   - Entry: $45,230

   [✅ Confirm]
   ```

### 5.3 Risk Management

**Ingebouwde Bescherming:**

| Regel | Default | Betekenis |
|-------|---------|-----------|
| Max Risk/Trade | 2% | Max 2% van capital per trade |
| Stop Loss | 5% | Automatische exit bij -5% |
| Take Profit | 10% | Automatische exit bij +10% |
| Max Positions | 3 | Max 3 open posities |
| Coherence Min | 30% | Alleen trades als councils eens zijn |

**Aanpassen:**
```
Settings → Risk Management
```

---

## 6. A/B Testing

### 6.1 Wat is A/B Testing?

Vergelijk de Federated Triad strategie met een baseline (bv. V17) om te bewijzen dat het beter werkt.

```
┌─────────────────────────────────────────────┐
│              A/B TESTING                    │
│                                             │
│   🧪 VARIANT A       vs      🧪 VARIANT B   │
│   (Federated Triad)         (V17 Baseline)  │
│                                             │
│   Trade 1: +$125            Trade 1: +$89   │
│   Trade 2: -$45             Trade 2: -$67   │
│   Trade 3: +$230            Trade 3: +$156  │
│                                             │
│   Total:   +$310            Total:   +$178  │
│   Win Rate: 67%             Win Rate: 55%   │
│                                             │
│   Winner: 🏆 FEDERATED TRIAD                │
│   Significant: YES (p < 0.05)               │
└─────────────────────────────────────────────┘
```

### 6.2 Experiment Starten

```
1. Ga naar "A/B Testing"
2. Klik "New Experiment"
3. Configuratie:

   Name:         Test_vs_V17
   Baseline:     V17 Strategy
   Duration:     30 days
   Capital:      $10,000 per variant

4. [▶️ Start Experiment]
```

### 6.3 Resultaten Interpreteren

```
┌─────────────────────────────────────────────────────────────┐
│  EXPERIMENT: Test_vs_V17                                    │
│  Status: ✅ COMPLETED (30 days)                             │
│  End Date: 2024-02-27                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🧪 FEDERATED TRIAD (Variant A)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Trades:        47                                   │   │
│  │  Win Rate:      62%  ████████████████████           │   │
│  │  Total PnL:     +$1,234                             │   │
│  │  Avg Trade:     +$26.3                              │   │
│  │  Sharpe Ratio:  1.45                                │   │
│  │  Max Drawdown:  -8%                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🧪 V17 BASELINE (Variant B)                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Trades:        52                                   │   │
│  │  Win Rate:      54%  █████████████████              │   │
│  │  Total PnL:     +$678                               │   │
│  │  Avg Trade:     +$13.0                              │   │
│  │  Sharpe Ratio:  1.12                                │   │
│  │  Max Drawdown:  -12%                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📊 STATISTICAL COMPARISON                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  PnL Difference:     +$556 (Triad wins)            │   │
│  │  Relative Return:    +82% better                   │   │
│  │                                                     │   │
│  │  P-value:            0.032  ✅ < 0.05              │   │
│  │  Significant:        YES                           │   │
│  │                                                     │   │
│  │  Effect Size:        0.45  (Medium)                │   │
│  │  Confidence:         95%                           │   │
│  │                                                     │   │
│  │  🏆 WINNER: Federated Triad                        │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📝 CONCLUSION                                              │
│  Federated Triad presteert significant beter dan V17        │
│  met 82% meer rendement en betere risk-adjusted returns.    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Belangrijke Metrics:**

| Metric | Wat betekent het? | Goed resultaat |
|--------|-------------------|----------------|
| **P-value** | Kans op toeval | < 0.05 = betrouwbaar |
| **Effect Size** | Grootte van verschil | > 0.2 = merkbaar |
| **Win Rate** | % winnende trades | > 50% |
| **Sharpe** | Rendement per risico | > 1.0 |

---

## 7. Prestaties Monitoren

### 7.1 Belangrijke Metrics

| Metric | Goed | Uitstekend | Waar te vinden |
|--------|------|------------|----------------|
| **Win Rate** | > 50% | > 60% | Performance → Summary |
| **Sharpe Ratio** | > 1.0 | > 1.5 | Performance → Risk |
| **Max Drawdown** | < 15% | < 10% | Performance → Risk |
| **Coherence** | > 70% | > 80% | Dashboard |
| **Karma Score** | > 0.5 | > 0.7 | Memory → Stats |

### 7.2 Waarschuwingen

Het systeem toont waarschuwingen bij:

```
🟡 Low Coherence Alert
   Councils zijn het niet eens (< 30%)
   → Wacht op duidelijkere signalen

🟡 Low Confidence Alert
   Buddhi confidence < 50%
   → Markt is onzeker, vermijd trading

🔴 High Drawdown Alert
   Drawdown > 15%
   → Overweeg risico te verminderen

🔴 Tamas Dominant Alert
   Markt toont Tamas (inertie)
   → Geen duidelijke richting, wacht af
```

### 7.3 Weekly Review

**Checklist:**

```
□ Review win rate (> 50%?)
□ Check max drawdown (< 15%?)
□ Analyseer verliezende trades
□ Check coherence trends
□ Update risk parameters indien nodig
□ Export performance report
```

---

## 8. Troubleshooting

### 8.1 Veelvoorkomende Problemen

**Probleem: Geen trades worden uitgevoerd**

| Mogelijke oorzaak | Oplossing |
|-------------------|-----------|
| Trading mode = "Disabled" | Settings → Trading Mode → Paper/Live |
| Confidence < 50% | Normaal bij onzekere markten, wacht af |
| Coherence < 30% | Councils zijn het oneens, geen actie |
| Tamas dominant | Markt is onduidelijk, geen trades |

**Probleem: Slechte performance**

| Symptoom | Mogelijke oorzaak | Oplossing |
|----------|-------------------|-----------|
| Win rate < 40% | Marktregime veranderd | Check regime detection |
| Hoge drawdown | Te grote posities | Verlaat risk per trade |
| Veel slippage | Slechte executie | Check Body Council metrics |
| Laatste trades verliezen | Mean reversion | Check Mind Council fear/greed |

**Probleem: Systeem errors**

```
Error: "Redis Connection Failed"
→ Check of Docker Redis draait
→ docker-compose up -d redis

Error: "ML Trainer Not Ready"
→ Minimaal 10 trades nodig met outcomes
→ Voer meer paper trades uit

Error: "Low Coherence Warning"
→ Normaal bij onzekere markten
→ Verhoog coherence threshold of wacht
```

### 8.2 Systeem Status Check

```
Settings → System Status

🟢 Guna Council        Online    Last update: 2s ago
🟢 Mind Council        Online    Last update: 2s ago
🟢 Body Council        Online    Last update: 2s ago
🟢 Buddhi Mind         Online    Last update: 2s ago
🟢 Redis Event Bus     Online    Latency: 45ms
🟢 Episodic Memory     Online    Episodes: 24
🟡 ML Trainer          Waiting   (8/10 episodes)
🟢 A/B Framework       Online    Active: 0
```

### 8.3 Contact & Support

Bij aanhoudende problemen:
1. Check logs: `logs/triad_service.log`
2. Export diagnostiek: Settings → Export Logs
3. Contact support met log bestanden

---

## 9. Veelgestelde Vragen

### Q: Hoeveel geld kan ik verdienen?
**A:** Resultaten variëren afhankelijk van marktcondities. Backtests tonen:
- Gemiddelde maandrendement: 3-8%
- Win rate: 58-62%
- Max drawdown: < 15%

*Historische resultaten garanderen geen toekomstige resultaten.*

### Q: Is het veerkrachtig genoeg voor live trading?
**A:** Ja, het systeem heeft meerdere beveiligingen:
- Paper trading om te oefenen
- Risk management met stop losses
- Coherence checks (alleen traden als councils eens zijn)
- A/B testing om strategie te valideren

### Q: Wat als de councils het niet eens zijn?
**A:** Dan wordt er geen trade uitgevoerd. Dit is een feature, niet een bug:
- Coherence < 30% → Geen actie
- Dit voorkomt trades in onzekere markten
- Wacht tot de markt duidelijkheid geeft

### Q: Kan ik de strategie aanpassen?
**A:** Ja, via Settings:
- Council weights aanpassen
- Drempels wijzigen (confidence, coherence)
- Risk parameters aanpassen
- Assets selecteren

### Q: Wat is Karma Score?
**A:** Een gewogen performance score gebaseerd op je trading geschiedenis:
- 0.0 = Slechte performance
- 0.5 = Break-even
- 1.0 = Uitstekende performance

Het systeem gebruikt dit om vergelijkbare situaties te vinden.

### Q: Hoe vaak worden beslissingen genomen?
**A:** Standaard elke 30 seconden, maar aanpasbaar:
- Scalping: 5-10 seconden
- Day trading: 30-60 seconden
- Swing trading: 1-4 uur

### Q: Werkt het met alle assets?
**A:** Ja, maar optimaal voor:
- Crypto: BTC, ETH, SOL, etc.
- Forex: Majors (EUR/USD, GBP/USD)
- Stocks: Hoog volume equities
- Commodities: Goud, olie

### Q: Wat is het verschil met andere trading bots?
**A:** Federated Triad is uniek omdat het:
- Meerdere AI agents combineert (councils)
- Uitlegbaar is (je ziet WAAROM)
- Leert van ervaring (episodic memory)
- Statistisch valideert (A/B testing)

### Q: Kan ik het combineren met mijn eigen strategie?
**A:** Ja, via de API:
```python
from backend.services.triad_service import get_triad_service

service = get_triad_service()
decision = service.process_market_data(my_data)

# Combineer met je eigen analyse
if decision.confidence > 0.7 and my_signal == "buy":
    execute_trade()
```

### Q: Wat gebeurt er bij een crash?
**A:** Het systeem heeft meerdere fail-safes:
- Automatische stop losses
- Max drawdown limieten
- Paper trading fallback
- Error logging en alerts

---

## Snelle Referentie Kaart

```
┌─────────────────────────────────────────────────────────────┐
│                 QUICK REFERENCE                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🟢 GOEDE VOORWAARDEN VOOR TRADING                         │
│  • Sattva > 40% (Guna)                                     │
│  • Fear/Greed 40-60 (Mind)                                 │
│  • Executie > 80% (Body)                                   │
│  • Confidence > 70% (Buddhi)                               │
│  • Coherence > 70% (Alle councils)                         │
│                                                             │
│  🔴 VERMIJDEN                                               │
│  • Tamas dominant                                          │
│  • Extreme Fear (>75) of Greed (>75)                       │
│  • Executie < 60%                                          │
│  • Coherence < 30%                                         │
│                                                             │
│  ⚡ SNELLE ACTIES                                           │
│  • F5: Refresh data                                        │
│  • Ctrl+T: Nieuwe trade                                    │
│  • Ctrl+D: Dashboard                                       │
│  • Ctrl+P: Performance                                     │
│                                                             │
│  📞 SUPPORT                                                 │
│  • Docs: /docs                                             │
│  • Logs: logs/triad_service.log                            │
│  • Status: Settings → System Status                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Einde Gebruikershandleiding**

*Voor technische documentatie, zie FEDERATED_TRIAD_IMPLEMENTATIE_DOCUMENTATIE.md*
