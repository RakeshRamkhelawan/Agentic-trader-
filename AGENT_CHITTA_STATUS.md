# Chitta Memory Status per Agent

## Agents die WEL Chitta hebben gekregen (erven van ElementalBase):

| Agent | Status | Opmerking |
|-------|--------|-----------|
| **ElementalOrchestrator** | ✅ HEEFT CHITTA | Erf van ElementalBase |
| **Air Agent** (indien bestaat) | ✅ HEEFT CHITTA | Erf van ElementalBase |
| **Fire Agent** (indien bestaat) | ✅ HEEFT CHITTA | Erf van ElementalBase |
| **Water Agent** (indien bestaat) | ✅ HEEFT CHITTA | Erf van ElementalBase |
| **Earth Agent** (indien bestaat) | ✅ HEEFT CHITTA | Erf van ElementalBase |

## Agents die NOG GEEN Chitta hebben (ander base class):

| Agent | Huidige Base Class | Actie nodig |
|-------|-------------------|-------------|
| **SentimentAgentV2** | Geen (standaard class) | ⚠️ Moet worden aangepast |
| **VedAstroSignalAgent** | AgentWithTools | ⚠️ Moet worden aangepast |
| **MarketDataCollectorAgent** | ❌ Niet gevonden als class | 🔍 Zoek/maak aan |
| **DynamicGunaCouncil** | Geen (standaard class) | ⚠️ Is een council, geen agent |
| **RegimeDetector** | Geen (ML component) | ⚠️ Is ML component, geen agent |
| **BuddhiMind** | Geen (standaard class) | ⚠️ Is council, geen agent |

## Probleem

De agents die je noemt zijn **GEEN elemental agents**. Ze zijn:
1. **Councils** (BuddhiMind, DynamicGunaCouncil) - Zitten in `backend/councils/`
2. **ML Components** (RegimeDetector) - Zitten in `backend/core/ml/`
3. **Agents met andere base** (SentimentAgentV2, VedAstroSignalAgent) - Erfen NIET van ElementalBase

## Oplossingen

### Optie 1: Chitta toevoegen aan BaseAgent (voor ALLE agents)
Als je wilt dat ALLE agents Chitta hebben, moet ik `BaseAgent` aanpassen (de parent van ALLE agents).

### Optie 2: Specifieke agents aanpassen
Alleen de genoemde agents voorzien van Chitta.

### Optie 3: Chitta als mixin
Een ChittaMixin maken die aan elke class kan worden toegevoegd.

Wat wil je dat ik doe?
