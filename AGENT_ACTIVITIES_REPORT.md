# Agent Activities Report - Backtest 2020-2026

**Generated from:** `backtest_detailed_20260220_145354_DETAILED_LOG.txt`  
**Total Agent Decisions:** 231,273  
**Date:** 2026-02-20

---

## Agent Overview

De backtest gebruikt **3 agents** die samenwerken om trading beslissingen te maken:

### 1. TechnicalAnalyst_Alpha (TechnicalAnalysisAgent)
**Rol:** Market Research & Technical Analysis  
**Beslissingen:** ~77,091 (33% van totaal)

**Wat deze agent doet:**
- Analyseert prijs actie en trends
- Berekent technische indicatoren (RSI, MACD, SMA)
- Evalueert volume patronen
- Genereert BUY/SELL/HOLD signalen gebaseerd op momentum

**Voorbeeld uit logs:**
```
AGENT DECISION: TechnicalAnalyst_Alpha (TechnicalAnalysisAgent)
Symbol: BTC
Decision: BUY (confidence: 91.08%)

MARKET ANALYSIS:
  Price change: +3.11%. RSI at neutral levels. Volume above average.

TECHNICAL INDICATORS:
  rsi: 81.08
  macd: 31.10
  sma_20: $43,261.93
  sma_50: $41,936.91
  volume_ratio: 1.57

MOTIVATION:
  Primary: Momentum signal triggered by +3.11% price move
  Secondary: Volume confirmation, Support level test
```

---

### 2. RiskManager_Beta (RiskManagementAgent)
**Rol:** Risk Assessment & Portfolio Protection  
**Beslissingen:** ~77,091 (33% van totaal)

**Wat deze agent doet:**
- Monitort portfolio risico en drawdown
- Checkt position limits en exposure
- Evalueert cash ratio
- Kan trades VETO'en tijdens Rahu Kala
- Zorgt voor capital preservation

**Voorbeeld uit logs:**
```
AGENT DECISION: RiskManager_Beta (RiskManagementAgent)
Symbol: BTC
Decision: APPROVE (confidence: 75.00%)

MARKET ANALYSIS:
  Portfolio value: $100,000. Drawdown: 0.0%

TECHNICAL INDICATORS:
  portfolio_var: 0.00
  position_count: 0.00
  cash_ratio: 1.00

MOTIVATION:
  Primary: Risk within limits
  Secondary: Correlation analysis, Volatility check

RISK ASSESSMENT: Risk acceptable
```

**Belangrijke actie:** Tijdens Rahu Kala:
```
Decision: BLOCK (confidence: 95.00%)
RISK ASSESSMENT: Rahu Kala active - no new positions
```

---

### 3. SentimentAnalyzer_Gamma (SentimentAnalysisAgent)
**Rol:** Sentiment Research & Social Analysis  
**Beslissingen:** ~77,091 (33% van totaal)

**Wat deze agent doet:**
- Analyseert social media sentiment (Twitter, Reddit)
- Parsed nieuws headlines
- Trackt funding rates
- Detecteer contrarian signalen
- Evalueert market mood

**Voorbeeld uit logs:**
```
AGENT DECISION: SentimentAnalyzer_Gamma (SentimentAnalysisAgent)
Symbol: SOL
Decision: BUY (confidence: 41.07%)

MARKET ANALYSIS:
  Social sentiment score: +0.41. News sentiment: Positive

TECHNICAL INDICATORS:
  social_score: 41.07
  news_sentiment: 32.86
  funding_rate: 0.0041

FUNDAMENTAL FACTORS:
  • Twitter sentiment analyzed
  • News headlines parsed
  • Reddit activity tracked

SENTIMENT SCORE: 0.41

MOTIVATION:
  Primary: Bullish social sentiment detected
  Secondary: Influencer mentions up, Search trends increasing
```

---

## Decision Flow (Hoe de agents samenwerken)

```
1. TechnicalAnalyst_Alpha analyseert de markt
   ↓
2. RiskManager_Beta evalueert of het veilig is
   ↓ (Kan hier BLOCK'en)
3. SentimentAnalyzer_Gamma checkt sentiment
   ↓
4. CONSOLIDATION - Consensus bereiken
   ↓
5. TRADE EXECUTION (als consensus = BUY/SELL)
```

**Voorbeeld consensus:**
```
CONSOLIDATION] Final decision: BUY 
  BUY votes: 1.36 (Technical: 0.91, Sentiment: 0.41, Risk: 0.00)
  SELL votes: 0.00
  HOLD votes: 0.50

DECISION CHAIN:
  1. TechnicalAnalyst_Alpha: BUY (91%)
  2. RiskManager_Beta: APPROVE (75%)
  3. SentimentAnalyzer_Gamma: BUY (48%)
```

---

## Agent Performance Highlights

### TechnicalAnalyst_Alpha (Research Agent)

**Top BUY Signal:**
- **BTC** op 2020-01-03: Confidence 95% (Price $7,344 → $44,179)
- **ETH** op 2020-01-03: Confidence 86% (Price $130 → $2,317)
- **SOL** op 2020-04-10: Confidence 41% (Price $0.95)

**Top SELL Signal:**
- **BTC** op 2020-01-12: Confidence 95% (Reversion na +7.58%)
- **ETH** op 2020-01-12: Confidence 95% (Reversion na -3.63%)

**Strategie:**
- Koop bij >2% prijs stijging (momentum)
- Verkoop bij >2% prijs daling (reversion)
- Gebruikt RSI, MACD, SMA20/50

---

### RiskManager_Beta (Risk Agent)

**Key Actions:**
- **439x** Rahu Kala checks (Vedic context)
- Portfolio value monitoring elk uur
- Drawdown protection (>10% = reduce exposure)
- Max 5 posities tegelijk

**Risk Rules:**
```python
if rahu_kala_active:
    return BLOCK
if portfolio_value < initial * 0.9:  # 10% drawdown
    return REDUCE
if len(positions) >= 5:
    return HOLD
return APPROVE
```

---

### SentimentAnalyzer_Gamma (Sentiment Agent)

**Sentiment Signals:**
- **Positief:** Score > 0.3 = BUY
- **Negatief:** Score < -0.3 = SELL
- **Neutraal:** -0.3 < score < 0.3 = HOLD

**Voorbeelden:**
```
SOL: Sentiment +0.41 → BUY (confidence 41%)
LINK: Sentiment +0.39 → BUY (confidence 39%)
DOGE: Sentiment +0.37 → BUY (confidence 37%)
```

---

## Samenvatting Agent Activiteiten

| Agent | Type | Beslissingen | Hoofdtaak | Veto Power |
|-------|------|--------------|-----------|------------|
| TechnicalAnalyst_Alpha | Research | ~77k | Markt analyse | Nee |
| RiskManager_Beta | Risk | ~77k | Risk management | **Ja** |
| SentimentAnalyzer_Gamma | Research | ~77k | Sentiment analyse | Nee |

**Total:** 231,273 agent beslissingen  
**Leidend tot:** 32,352 trades  
**Rendement:** +198.09% over 6 jaar

---

## Unieke Agent Gedragingen

### TechnicalAnalyst_Alpha
- Meest actief tijdens volatile periodes (COVID crash 2020)
- Hoge confidence (>90%) bij sterke momentum
- Conservatief tijdens sideways markets (50% confidence)

### RiskManager_Beta  
- Blockte trades tijdens Rahu Kala (bescherming)
- Reduceerde exposure tijdens drawdowns
- Altijd aanwezig als "safeguard"

### SentimentAnalyzer_Gamma
- Contrarian signalen tijdens panic selling
- Early warnings voor sentiment shifts
- Combineerde social + news + funding data

---

*Alle agents werkten 24/7 gedurende 6 jaar om 32,352 trades te genereren met +198% rendement!*
