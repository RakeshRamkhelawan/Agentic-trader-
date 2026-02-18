# Unified Consciousness Integration - Complete Flow Diagram

## Architecture Overview

```mermaid
flowchart TB
    subgraph ENTRY["📥 ENTRY POINT"]
        MT[Market Tick<br/>symbol + price]
    end

    subgraph PHASE_B["🔮 PHASE B: Consciousness Gates"]
        direction TB
        NG[NavagrahaService<br/>get_current_state]
        TK[Trading Gate Check]
        TG_OPEN{Trading Gate<br/>Open?}
        RAHU{Rahu Kala<br/>Active?}
        TAMAS{Tamas > 60%?}
        GUNA[Guna Distribution<br/>Sattva/Rajas/Tamas]
        CONSC[Consciousness Level<br/>Pure Awareness → Material Density]
        
        NG --> GUNA
        GUNA --> TK
        TK --> RAHU
        RAHU -->|Yes| BLOCK1[BLOCKED_BY_CONSCIOUSNESS_GATE]
        RAHU -->|No| TAMAS
        TAMAS -->|Yes| BLOCK1
        TAMAS -->|No| TG_OPEN
        TG_OPEN -->|Yes| CONT1[Continue to Phase A]
    end

    subgraph PHASE_A["🧠 PHASE A: Orchestration"]
        direction TB
        COG_ORCH[CognitiveOrchestrator<br/>handle_market_tick]
        GUNA_BAL[Guna Balance<br/>current_guna_balance]
        
        CONT1 --> COG_ORCH
        COG_ORCH --> GUNA_BAL
    end

    subgraph OODA_LOOP["🔄 OODA LOOP (Primary Brain)"]
        direction TB
        
        subgraph OBSERVE["1️⃣ OBSERVE"]
            DS[DataScoutAgent<br/>observe]
            OBS[Observation<br/>price/volume/orderbook]
        end
        
        subgraph ORIENT["2️⃣ ORIENT"]
            direction TB
            CB[CognitiveBridge<br/>process_observation]
            AN[AnalystAgent<br/>orient]
            GUNA_MOD[Guna Modulation<br/>confidence -= tamas_penalty]
            BULL[BullResearcher<br/>generate_hypothesis]
            BEAR[BearResearcher<br/>generate_hypothesis]
            ORIENT_OBJ[Orientation<br/>regime/indicators/confidence]
            
            CB --> AN
            GUNA_BAL --> GUNA_MOD
            AN --> GUNA_MOD
            GUNA_MOD --> ORIENT_OBJ
            ORIENT_OBJ --> BULL
            ORIENT_OBJ --> BEAR
        end
        
        subgraph DECIDE["3️⃣ DECIDE"]
            direction TB
            TATTVA_CHECK[SystemIdentity<br/>Kanchuka Risk Gate]
            TRADER[TraderAgent<br/>propose_trade]
            STRAT_REG[UnifiedStrategyRegistry<br/>Dasha-based Strategy]
            PROP[TradeProposal<br/>side/size/entry/stop/take_profit]
            RISK_ORCH{RiskOrchestrator<br/>pre_trade_check}
            RISK_MGR[RiskManagerAgent<br/>assess_risk]
            RISK_RES{RiskAssessment<br/>APPROVE/REJECT/MODIFY}
            
            ORIENT_OBJ --> TATTVA_CHECK
            TATTVA_CHECK --> TRADER
            TRADER --> STRAT_REG
            STRAT_REG --> PROP
            PROP --> RISK_ORCH
            RISK_ORCH -->|Blocked| RISK_RES
            RISK_ORCH -->|Approved| RISK_MGR
            RISK_MGR --> RISK_RES
        end
        
        subgraph HARMONIZE["4️⃣ HARMONIZE"]
            ORCH[OrchestratorAgent<br/>harmonize]
            HARM{Harmony Check<br/>Pass?}
            
            RISK_RES -->|APPROVE| ORCH
            ORCH --> HARM
        end
        
        subgraph ACT["5️⃣ ACT"]
            FM[FundManager<br/>allocate_capital]
            ALLOC[CapitalAllocation<br/>approved/position_size]
            EXEC{Trading Mode<br/>AUTO?}
            OE[OrderExecutor<br/>execute_trade]
            EX_RES[ExecutionResult<br/>filled_qty/avg_price]
            
            HARM -->|Pass| FM
            FM --> ALLOC
            ALLOC --> EXEC
            EXEC -->|Yes| OE
            EXEC -->|No| NOTIFY[Notify Only]
            OE --> EX_RES
        end
    end

    subgraph PHASE_E["📚 PHASE E: Learning Loop"]
        direction TB
        KARMA[KarmaRegister<br/>register_feedback]
        SYS_ID[SystemIdentity<br/>update_outcome]
        RL[Reinforcement<br/>parameter tuning]
        
        EX_RES --> KARMA
        KARMA --> SYS_ID
        SYS_ID --> RL
    end

    subgraph EXIT["📤 EXIT POINTS"]
        direction TB
        SUCCESS[✅ Trade Executed<br/>P&L Recorded]
        BLOCKED[❌ Trade Blocked<br/>Reason Logged]
        NOTIFY_END[📧 Notification Sent<br/>Human Approval Required]
        
        EX_RES --> SUCCESS
        BLOCK1 --> BLOCKED
        RISK_RES -->|REJECT| BLOCKED
        HARM -->|Fail| BLOCKED
        NOTIFY --> NOTIFY_END
    end

    %% Main Flow Connections
    MT --> PHASE_B
    PHASE_B --> PHASE_A
    PHASE_A --> OBSERVE
    OBSERVE --> ORIENT
    ORIENT --> DECIDE
    DECIDE --> HARMONIZE
    HARMONIZE --> ACT
    ACT --> PHASE_E
    PHASE_E --> EXIT

    %% Styling
    style ENTRY fill:#e1f5fe
    style PHASE_B fill:#fff3e0
    style PHASE_A fill:#e8f5e9
    style OODA_LOOP fill:#fce4ec
    style PHASE_E fill:#f3e5f5
    style EXIT fill:#ffebee
    
    style BLOCK1 fill:#ff5252,color:#fff
    style BLOCKED fill:#ff5252,color:#fff
    style SUCCESS fill:#69f0ae
    style NOTIFY_END fill:#ffd740
```

## Component Interaction Diagram

```mermaid
flowchart LR
    subgraph UNIFIED["Unified Consciousness System"]
        direction TB
        
        subgraph COORDINATORS["Orchestrators"]
            OODA[OODALoopCoordinator<br/>Primary Brain]
            COG[CognitiveOrchestrator<br/>Message Bus]
        end
        
        subgraph CONSCIOUSNESS["Consciousness Layer"]
            NAV[NavagrahaService<br/>Cosmic Time]
            SID[SystemIdentity<br/>36-Tattva]
            GUNA[GunaQuantifier<br/>Sattva/Rajas/Tamas]
        end
        
        subgraph RISK["Risk Layer"]
            RORCH[RiskOrchestrator<br/>Kanchuka Layer]
            DD[DrawdownMonitor<br/>Kill Switch]
            KELLY[KellyCriterion<br/>Position Sizing]
            VAR[VaRCalculator<br/>Portfolio Risk]
        end
        
        subgraph STRATEGY["Strategy Layer"]
            SREG[UnifiedStrategyRegistry<br/>Dasha-based]
            TREND[TrendFollowingStrategy]
            MR[MeanReversionStrategy]
            DEF[DefensiveStrategy]
        end
        
        subgraph LEARNING["Learning Layer"]
            KRM[KarmaRegister<br/>Feedback Loop]
            RL[ReinforcementLearner<br/>Parameter Tuning]
            MEM[MemorySystem<br/>Episode Storage]
        end
    end
    
    %% Interactions
    OODA -->|market_tick| COG
    OODA -->|get_current_state| NAV
    OODA -->|_get_tattva_risk_gate_state| SID
    NAV -->|guna_distribution| GUNA
    GUNA -->|modulates| OODA
    
    OODA -->|pre_trade_check| RORCH
    RORCH -->|check| DD
    RORCH -->|size_with_kelly| KELLY
    RORCH -->|var_calculation| VAR
    
    OODA -->|get_strategy| SREG
    SREG -->|select| TREND
    SREG -->|select| MR
    SREG -->|select| DEF
    
    OODA -->|register_feedback| KRM
    KRM -->|tune| RL
    KRM -->|store| MEM
    SID -->|update_outcome| MEM
```

## Decision Tree Flow

```mermaid
flowchart TD
    START([Market Tick Received]) --> GATE1{Navagraha<br/>Trading Gate}
    
    GATE1 -->|Rahu Kala Active| END1[❌ Blocked<br/>Rahu Kala]
    GATE1 -->|High Tamas| END2[❌ Blocked<br/>Material Density]
    GATE1 -->|Gate Open| COG[CognitiveOrchestrator<br/>Process Tick]
    
    COG --> OBS[OBSERVE<br/>DataScout]
    OBS --> ORI[ORIENT<br/>Analyst + Guna Modulation]
    
    ORI --> TATTVA{Tattva Risk Gate<br/>Kanchuka 6-12}
    TATTVA -->|Blocked| END3[❌ Blocked<br/>Low Coherence]
    TATTVA -->|Open| DEC[DECIDE]
    
    DEC --> STRAT[Strategy Selection<br/>Dasha-based]
    STRAT --> RISK{RiskOrchestrator}
    
    RISK -->|Kill Switch| END4[❌ Blocked<br/>Max Drawdown]
    RISK -->|Max Positions| END5[❌ Blocked<br/>Limit Reached]
    RISK -->|Low Confidence| END6[❌ Blocked<br/>Confidence < 0.3]
    RISK -->|Approved| HARM[Harmonize<br/>Orchestrator]
    
    HARM -->|Fail| END7[❌ Blocked<br/>No Harmony]
    HARM -->|Pass| FUND[FundManager<br/>Capital Allocation]
    
    FUND --> MODE{Trading Mode}
    MODE -->|Notify Only| END8[📧 Notify<br/>Human Approval]
    MODE -->|AUTO| EXEC[Execute Trade]
    
    EXEC --> KARMA[Karma Feedback]
    KARMA --> LEARN[Update SystemIdentity]
    LEARN --> END9[✅ Trade Complete]
    
    style START fill:#e1f5fe
    style END1 fill:#ff5252,color:#fff
    style END2 fill:#ff5252,color:#fff
    style END3 fill:#ff5252,color:#fff
    style END4 fill:#ff5252,color:#fff
    style END5 fill:#ff5252,color:#fff
    style END6 fill:#ff5252,color:#fff
    style END7 fill:#ff5252,color:#fff
    style END8 fill:#ffd740
    style END9 fill:#69f0ae
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant MT as Market Tick
    participant NG as Navagraha
    participant CO as CognitiveOrchestrator
    participant OODA as OODALoop
    participant SI as SystemIdentity
    participant RO as RiskOrchestrator
    participant SR as StrategyRegistry
    participant KR as KarmaRegister

    MT->>NG: get_current_state()
    NG-->>MT: NavagrahaState<br/>trading_gate_open
    
    alt Gate Open
        MT->>CO: handle_market_tick()
        CO->>OODA: _execute_ooda_loop()
        
        OODA->>OODA: _observe()
        OODA->>OODA: _orient()
        Note over OODA: Guna modulation<br/>Tamas penalty
        
        OODA->>SI: _get_tattva_risk_gate_state()
        SI-->>OODA: risk_gate_blocked
        
        OODA->>SR: get_strategy_for_current_dasha()
        SR-->>OODA: strategy_id
        
        OODA->>RO: pre_trade_check()
        RO-->>OODA: RiskDecision
        
        alt Trade Approved
            OODA->>OODA: _act()
            OODA->>KR: register_feedback()
            KR->>SI: update_outcome()
            OODA-->>MT: ExecutionResult
        else Trade Blocked
            OODA-->>MT: BLOCKED
        end
    else Gate Closed
        NG-->>MT: BLOCKED_BY_CONSCIOUSNESS_GATE
    end
```

## Component State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle : System Start
    
    Idle --> Observing : Market Tick
    
    Observing --> ConsciousnessCheck : Raw Data
    
    ConsciousnessCheck --> GateBlocked : Rahu Kala / High Tamas
    ConsciousnessCheck --> Orienting : Gate Open
    
    Orienting --> RiskAssessment : Orientation Complete
    
    RiskAssessment --> Blocked : Kill Switch / Max DD
    RiskAssessment --> StrategySelect : Risk OK
    
    StrategySelect --> Decision : Strategy Selected
    
    Decision --> Blocked : Rejected
    Decision --> Harmonizing : Proposal Approved
    
    Harmonizing --> Blocked : No Harmony
    Harmonizing --> Executing : Harmony OK
    
    Executing --> Learning : Trade Executed
    Executing --> Notifying : Notify Mode
    
    Learning --> Idle : Feedback Recorded
    Notifying --> Idle : Awaiting Approval
    Blocked --> Idle : Log Reason
    GateBlocked --> Idle : Log Gate
    
    Idle --> [*] : System Shutdown
```

## Phase-by-Phase Breakdown

### Phase A: Unify Orchestration
```mermaid
graph LR
    A[Market Tick] --> B{CognitiveOrchestrator<br/>Enabled?}
    B -->|Yes| C[Delegate to CO]
    B -->|No| D[Direct OODA]
    C --> E[Process with<br/>Guna Balance]
    D --> E
    E --> F[Continue to<br/>OODA Loop]
```

### Phase B: Connect Consciousness
```mermaid
graph LR
    A[Market Tick] --> B[NavagrahaService]
    B --> C{Trading Gate}
    C -->|Open| D[SystemIdentity<br/>Kanchuka Check]
    C -->|Closed| E[BLOCKED]
    D -->|Pass| F[OODA Loop]
    D -->|Fail| G[Confidence Reduced]
    G --> F
```

### Phase C: Wire Risk Pipeline
```mermaid
graph LR
    A[Trade Proposal] --> B[RiskOrchestrator]
    B --> C[Drawdown Check]
    B --> D[VaR Check]
    B --> E[Position Sizing]
    C & D & E --> F{Risk Decision}
    F -->|Approved| G[Continue]
    F -->|Rejected| H[BLOCKED]
```

### Phase D: Strategy Integration
```mermaid
graph LR
    A[Current Dasha] --> B[DashaStrategyMap]
    B --> C[Planet Characteristics]
    C --> D[Risk Profile]
    C --> E[Time Horizon]
    C --> F[Asset Preference]
    D & E & F --> G[Select Strategy]
    G --> H[Trend/MeanRev/Defensive]
```

### Phase E: Learning Loop
```mermaid
graph LR
    A[Trade Execution] --> B[KarmaRegister]
    B --> C[Calculate Karma<br/>PnL/Drawdown/Speed]
    C --> D[Update Agent Karma]
    D --> E[SystemIdentity]
    E --> F[Update Outcome]
    F --> G[Adapt Parameters]
    G --> H[Store in Memory]
```

## Key Metrics & Monitoring Points

```mermaid
flowchart TB
    subgraph METRICS["📊 Key Metrics"]
        M1[Cycles Completed]
        M2[Trading Gate Status]
        M3[Guna Distribution]
        M4[Tattva Coherence]
        M5[Risk Score]
        M6[Harmony Score]
        M7[Karma Score]
        M8[Win Rate]
    end
    
    subgraph ALERTS["🚨 Alert Conditions"]
        A1[Rahu Kala Active]
        A2[Kill Switch Triggered]
        A3[Max Drawdown]
        A4[Low Sattva < 25%]
        A5[High Tamas > 60%]
        A6[Kanchuka Blocked]
    end
    
    M1 --> PROM[Prometheus Metrics]
    M2 --> PROM
    M3 --> PROM
    M4 --> PROM
    M5 --> PROM
    M6 --> PROM
    M7 --> PROM
    M8 --> PROM
    
    A1 --> ALERT[Alert Manager]
    A2 --> ALERT
    A3 --> ALERT
    A4 --> ALERT
    A5 --> ALERT
    A6 --> ALERT
```

---

*Last Updated: 2026-02-17*
*Unified Consciousness Flow v1.0*
