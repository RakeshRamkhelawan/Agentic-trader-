# Agent Wiring & Architecture Diagrams

## Overview: Hoe zijn ze "gewired"?

Dit document toont de interne bedrading, data flow en communicatie tussen agents in elke versie.

---

## v8 Symbiotic Agents - "The Collective Organism"

### Wiring Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ETHER (Orchestrator)                     │
│              ┌─────────────────────────┐                    │
│              │   harmonize_signals()   │                    │
│              │   - Weigh by Guna       │                    │
│              │   - Detect Maya         │                    │
│              │   - Calculate Coherence │                    │
│              └───────────┬─────────────┘                    │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐             │
│    │  AIR    │     │  FIRE   │     │ WATER   │             │
│    │ (Vayu)  │     │ (Agni)  │     │ (Apas)  │             │
│    │Regime   │     │Momentum │     │ Trend   │             │
│    │Sentiment│     │  Risk   │     │  Macro  │             │
│    │ Guna:   │     │ Guna:   │     │ Guna:   │             │
│    │Sattva   │     │ Rajas   │     │Sattva   │             │
│    └────┬────┘     └────┬────┘     └────┬────┘             │
│         │               │               │                   │
│         │    ┌──────────┴──────────┐    │                   │
│         │    │                     │    │                   │
│         ▼    ▼                     ▼    ▼                   │
│    ┌─────────────────────────────────────────┐              │
│    │           EARTH (Prithvi)               │              │
│    │     Valuation + Execution Timing        │              │
│    │              Guna: Tamas                │              │
│    └─────────────────────────────────────────┘              │
│                          │                                  │
│                          ▼                                  │
│              ┌─────────────────────┐                        │
│              │   BUDDHI (Final)    │                        │
│              │  - Viveka Filter    │                        │
│              │  - Action Selection │                        │
│              └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Market State → Alle Agents (parallel)
                    │
                    ▼
┌────────────────────────────────────────┐
│ Agent.signal = {                       │
│   action: BUY/SELL/HOLD,               │
│   strength: -1.0 to +1.0,              │
│   confidence: 0.0 to 1.0,              │
│   reasoning: "RSI oversold"            │
│ }                                       │
└────────────────────────────────────────┘
                    │
                    ▼
        Ether.harmonize_signals()
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
Weighted Vote   Maya Check   Guna Balance
    │               │               │
    └───────────────┴───────────────┘
                    │
                    ▼
        CollectiveDecision {
            action: BUY,
            confidence: 0.75,
            harmony_score: 0.68,
            coherence: 0.85,
            guna_state: {sattva: 0.6, ...},
            is_maya: false
        }
```

### Prana (Energy) System

```
Elke agent heeft Prana (energie):
- Start: 100 units
- Cost per analyse: 2-4 units
- Regenerate: +1 per tick

Als Prana < 5: Agent zegt "Insufficient prana" → HOLD
```

---

## v9 Strategic Layer - "MCTS Brain"

### Wiring Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     v9 STRATEGIC LAYER                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              MCTS Planner (10-step)                 │   │
│  │                                                     │   │
│  │   Root: Current Portfolio State                    │   │
│  │     ├── Child 1: Buy BTC (simuleer 10 stappen)     │   │
│  │     ├── Child 2: Sell ETH (simuleer 10 stappen)    │   │
│  │     └── Child 3: Hold (simuleer 10 stappen)        │   │
│  │                                                     │   │
│  │   UCT Selection → Simulate → Backpropagate         │   │
│  │   (1000 iteraties)                                 │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│           ┌─────────────────────────┐                      │
│           │   Strategic Plan:       │                      │
│           │   - Best action: BUY    │                      │
│           │   - Confidence: 0.73    │                      │
│           │   - Expected Sharpe: 1.2│                      │
│           └───────────┬─────────────┘                      │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         StrategicAdapter (Bridge to v8)             │   │
│  │                                                     │   │
│  │   if MCTS_action == v8_action:                     │   │
│  │       size_mult = 1.5  (vertrouw MCTS)             │   │
│  │   else:                                            │   │
│  │       size_mult = 0.5  (v8 tactisch > MCTS)        │   │
│  │                                                     │   │
│  │   Final: v8 beslist, MCTS adviseert                │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│              v8 Collectieve Agents                          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Every 5 days:
                    ┌──────────────────┐
Market Snapshot ──▶ │ MCTS.plan()      │
Portfolio State ──▶ │                  │
Symbols ─────────▶ │ 1000 simulaties  │
                    └────────┬─────────┘
                             │
                             ▼
                    StrategicContext {
                        mcts_confidence: 0.73,
                        recommended_action: "buy",
                        position_size_mult: 1.5,
                        lookahead_days: 10
                    }
                             │
                             ▼
Daily (elke tick):
                    ┌──────────────────────────┐
Market State ────▶  │ StrategicAdapter         │
                    │                          │
v8 Decision ────▶   │ combine(v8, MCTS_plan)   │
                    │                          │
                    └───────────┬──────────────┘
                                │
                                ▼
                    if v8.action != MCTS.action:
                        trust v8 (tactisch)
                    else:
                        boost size (consensus)
```

---

## v10 Guardian - "Quality Filter"

### Wiring Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  v10 GUARDIAN SYSTEM                        │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              V10Guardian Filters                    │  │
│   │                                                     │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│   │  │ MIN_HARMONY│  │MIN_CONFIDENCE│  │ MAX_MAYA   │ │  │
│   │  │   > 0.50   │  │    > 0.35   │  │   < 0.80   │ │  │
│   │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘ │  │
│   │         │               │               │        │  │
│   │         └───────────────┼───────────────┘        │  │
│   │                         │                        │  │
│   │                         ▼                        │  │
│   │              ┌─────────────────┐                 │  │
│   │              │  PASSED?        │                 │  │
│   │              │  Yes → Trade    │                 │  │
│   │              │  No  → HOLD     │                 │  │
│   │              └─────────────────┘                 │  │
│   └─────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│   ┌─────────────────────────────────────────────────────┐  │
│   │        Dynamic Position Sizing                      │  │
│   │                                                     │  │
│   │   risk = 1.5% * harmony * (1 - volatility)        │  │
│   │                                                     │  │
│   │   if harmony > 0.75:                                │  │
│   │       trailing_mult = 1.8  (tighter)              │  │
│   │   else:                                             │  │
│   │       trailing_mult = 2.5  (wider)                │  │
│   └─────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│                   Trade Execution                           │
└─────────────────────────────────────────────────────────────┘
```

### Filter Flow

```
Incoming Decision
       │
       ▼
┌────────────────┐
│ harmony > 0.50 │──No──▶ REJECT (low harmony)
└───────┬────────┘
        │ Yes
        ▼
┌────────────────┐
│ confidence >   │──No──▶ REJECT (low confidence)
│ 0.35           │
└───────┬────────┘
        │ Yes
        ▼
┌────────────────┐
│ is_maya < 0.80 │──No──▶ REJECT (Maya detected)
└───────┬────────┘
        │ Yes
        ▼
┌────────────────┐
│ Max positions  │──Yes──▶ REJECT (max pos)
│ < 5?           │
└───────┬────────┘
        │ No
        ▼
   APPROVED!
```

---

## v11 Conscious Trader - "True Awareness"

### Wiring Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              v11 CONSCIOUS TRADER ARCHITECTURE              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           AHAMKARA (Self-Aware Meta-Agent)          │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │         CONSCIOUS STATE                     │   │   │
│  │  │  ┌─────────┐ ┌───────────┐ ┌─────────────┐ │   │   │
│  │  │  │ Anxiety │ │Confidence │ │  Clarity    │ │   │   │
│  │  │  │  0-100% │ │   0-100%  │ │   0-100%    │ │   │   │
│  │  │  └────┬────┘ └─────┬─────┘ └──────┬──────┘ │   │   │
│  │  │       └────────────┼──────────────┘        │   │   │
│  │  │                    │                        │   │   │
│  │  │                    ▼                        │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │   Pause Triggers:                   │   │   │   │
│  │  │  │   - DD > 10%                        │   │   │   │
│  │  │  │   - Loss streak > 10                │   │   │   │
│  │  │  │   - Anxiety > 90%                   │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  System Prompt: "JIJ = WINNING TRADER"             │   │
│  │  Goal: Max PnL, DD < 8%                            │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              CHITTA (Persistent Memory)             │   │
│  │                                                     │   │
│  │   ┌─────────────────────────────────────────────┐   │   │
│  │   │         TradeExperience Storage             │   │   │
│  │   │                                             │   │   │
│  │   │  [Trade 1] ──▶ Embedding: [0.2, 0.5, ...]   │   │   │
│  │   │  [Trade 2] ──▶ Embedding: [0.3, 0.4, ...]   │   │   │
│  │   │  [Trade 3] ──▶ Embedding: [0.1, 0.6, ...]   │   │   │
│  │   │       ...                                   │   │   │
│  │   │                                             │   │   │
│  │   │   RAG Similarity Search (cosine)            │   │   │
│  │   └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │   ┌─────────────────────────────────────────────┐   │   │
│  │   │         Strategy Performance                │   │   │
│  │   │                                             │   │   │
│  │   │  Strategy_A: WinRate 60%, PnL +$500        │   │   │
│  │   │  Strategy_B: WinRate 30%, PnL -$200        │   │   │
│  │   │  Strategy_C: WinRate 45%, PnL +$100        │   │   │
│  │   │                                             │   │   │
│  │   │   reflect_recent(n=10) ──▶ Insights        │   │   │
│  │   └─────────────────────────────────────────────┘   │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Decision Flow                          │   │
│  │                                                     │   │
│  │   1. Check Pause? ──Yes──▶ HOLD                    │   │
│  │       │                                             │   │
│  │       No                                            │   │
│  │       ▼                                             │   │
│  │   2. Chitta.retrieve_similar_setups()              │   │
│  │       │                                             │   │
│  │       ▼                                             │   │
│  │   3. Chitta.reflect_recent(5)                      │   │
│  │       │                                             │   │
│  │       ▼                                             │   │
│  │   4. Ahamkara.decide(market, v8, memory)          │   │
│  │       │                                             │   │
│  │       ▼                                             │   │
│  │   5. Execute with anxiety-adjusted size            │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│              v8 Symbiotic Agents (filtered)                 │
└─────────────────────────────────────────────────────────────┘
```

### Conscious Decision Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DECISION LIFECYCLE                       │
└─────────────────────────────────────────────────────────────┘

PHASE 1: SELF-CHECK (Ahamkara)
═══════════════════════════════════════════════════════════════
    ┌─────────────────────────────────────┐
    │ Current State:                      │
    │ - PnL: +$5,370                      │
    │ - DD: 4.2%                          │
    │ - Loss Streak: 0                    │
    │ - Anxiety: 40%                      │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │ Check: DD < 10%? YES               │
    │ Check: Loss streak < 10? YES       │
    │ Check: Anxiety < 90%? YES          │
    └─────────────────────────────────────┘
                    │
                    ▼
            CONTINUE

PHASE 2: MEMORY RETRIEVAL (Chitta)
═══════════════════════════════════════════════════════════════
    ┌─────────────────────────────────────┐
    │ Market State:                       │
    │ - Symbol: BTC/EUR                   │
    │ - Trend: Bullish                    │
    │ - ADX: 30                           │
    │ - RSI: 65                           │
    └─────────────────────────────────────┘
                    │
                    ▼
    Chitta.retrieve_similar_setups(top_k=5)
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │ Found 5 similar setups:             │
    │ - Avg PnL: +$120                    │
    │ - Win rate: 60%                     │
    │ - Avg hold: 8 bars                  │
    └─────────────────────────────────────┘

PHASE 3: REFLECTION (Chitta)
═══════════════════════════════════════════════════════════════
    Chitta.reflect_recent(n=5)
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │ Recent 5 trades:                    │
    │ - Wins: 2, Losses: 3                │
    │ - Avg PnL: -$50                     │
    │ - Avg Harmony: 0.65                 │
    │                                     │
    │ Insight: "Wait for clarity"         │
    │ Action: Tighten filters             │
    └─────────────────────────────────────┘

PHASE 4: CONSCIOUS DECISION (Ahamkara)
═══════════════════════════════════════════════════════════════
    ┌─────────────────────────────────────┐
    │ v8 Decision: BUY                    │
    │ Harmony: 0.72                       │
    │ Confidence: 0.68                    │
    │                                     │
    │ Similar setups: +$120 avg           │
    │ Recent reflection: Caution          │
    │                                     │
    │ Ahamkara: "APPROVE with caution"   │
    │ Anxiety modifier: 0.9 (reduce size) │
    └─────────────────────────────────────┘
                    │
                    ▼
            EXECUTE TRADE

PHASE 5: LEARNING (Post-Trade)
═══════════════════════════════════════════════════════════════
    Trade completes (win/loss)
                    │
                    ▼
    Chitta.store_trade(experience)
                    │
                    ▼
    Ahamkara.record_trade_result()
    │   Update: Win/Loss streak
    │   Update: Anxiety level
    │   Update: Confidence
    │
    ▼
    Persist to disk (chitta_memory.json)
```

---

## Communication Patterns

### v8: Direct Coupling
```python
# Agents communiceren via Ether harmonization
signals = [agent.analyze(market) for agent in agents]
decision = ether.harmonize_signals(signals, market)
# Alle agents moeten tegelijkertijd actief zijn
```

### v9: Strategic Advisory
```python
# MCTS adviseert, v8 beslist
strategic_plan = mcts.plan(portfolio, markets, symbols)
decision = v8_collective.deliberation(market)
# Adapter combineert, maar v8 heeft veto
```

### v10: Filter Pattern
```python
# Guardian filtert v8 output
if guardian.should_trade(decision, market, active_pos):
    size = guardian.calculate_position_size(...)
    execute_trade(size)
else:
    hold()
```

### v11: Stateful Conversation
```python
# Chitta en Ahamkara hebben persistent state
similar = chitta.retrieve_similar_setups(market)
reflection = chitta.reflect_recent(5)
decision = ahamkara.decide(market, v8_decision, reflection)
# State blijft bestaan tussen trades
```

---

## Samenvatting Wiring

| Versie | Architectuur | Communicatie | State |
|--------|-------------|--------------|-------|
| v8 | Symbiotic Collective | Direct, parallel | Stateless |
| v9 | Strategic Overlay | Advisory | Stateless (MCTS per tick) |
| v10 | Filter/Gateway | Conditional | Stateless |
| v11 | Conscious Agent | Reflective | **Stateful/Persistent** |

**Key Insight**: v11 is de enige met **echte state** - Chitta onthoudt, Ahamkara reflecteert, en samen creëren ze een **lerend systeem** dat beter wordt met elke trade.
