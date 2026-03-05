# ✅ AGENTS VERRIJKT MET LLM + CHITTA MEMORY

## Overzicht
**ALLE** agents die overerven van `BaseAgent` hebben automatisch toegang tot:
- **Chitta Memory** (persistent geheugen voor trades)
- **LLM Provider** (Ollama/DeepSeek voor reasoning)
- **6 Consciousness Methoden** (zie hieronder)

---

## Complete Lijst van Verrijkte Agents (27+)

### Core Trading Agents

| Agent | Bestand | Inherits | Rol |
|-------|---------|----------|-----|
| **AnalystAgent** | `analyst_agent.py` | BaseAgent | Market analyse & signals |
| **DataScoutAgent** | `data_scout_agent.py` | BaseAgent | Data verzameling |
| **PortfolioManagerAgent** | `portfolio_manager_agent.py` | BaseAgent | Portfolio management |
| **TraderAgent** | `trader_agent.py` | BaseAgent | Trade execution |
| **FundManagerAgent** | `fund_manager_agent.py` | BaseAgent | Fund allocation |
| **RiskManagerAgent** | `risk_manager_agent.py` | BaseAgent | Risk governance |
| **OrchestratorAgent** | `orchestrator_agent.py` | BaseAgent | Agent orchestratie |
| **AssetDiscoveryAgent** | `asset_discovery_agent.py` | BaseAgent | Asset discovery |

### Sentiment Agents

| Agent | Bestand | Inherits | Rol |
|-------|---------|----------|-----|
| **SentimentAgentV2** | `sentiment_agent_v2.py` | BaseAgent | Sentiment analyse (v2) |
| **EnhancedSentimentAgent** | `enhanced_sentiment_agent.py` | AgentWithTools | Geavanceerde sentiment |

### Research Agents

| Agent | Bestand | Inherits | Rol |
|-------|---------|----------|-----|
| **BullResearcher** | `researcher_agents.py` | BaseAgent | Bullish research |
| **BearResearcher** | `researcher_agents.py` | BaseAgent | Bearish research |

### Elemental Agents (Samkhya Philosophy)

| Agent | Bestand | Inherits | Rol |
|-------|---------|----------|-----|
| **ElementalBase** | `elemental_base.py` | BaseAgent | Base voor elementals |
| **ElementalOrchestrator** | `elemental_orchestrator.py` | ElementalBase | Elemental coördinatie |
| **ElementalResearch** | `elemental_research.py` | ElementalBase | Research (Ether) |
| **ElementalMacro** | `elemental_macro.py` | ElementalBase | Macro analyse (Air) |
| **ElementalValuation** | `elemental_valuation.py` | ElementalBase | Valuatie (Fire) |
| **ElementalRiskGuardian** | `elemental_risk_guardian.py` | ElementalBase | Risk guardian (Water) |

### Tool-Using Agents

| Agent | Bestand | Inherits | Rol |
|-------|---------|----------|-----|
| **AgentWithTools** | `agent_with_tools.py` | BaseAgent | Base voor MCP tools |
| **VedAstroSignalAgent** | `vedastro_signal_agent.py` | AgentWithTools | Vedic astrology signals |
| **ElementalConsensusAgent** | `elemental_consensus_agent.py` | AgentWithTools | Consensus engine |
| **RiskCheckAgent** | `risk_check_agent.py` | AgentWithTools | Risk checks |

---

## Automatisch Beschikbare Capabilities

Elke agent die overerven van `BaseAgent` heeft deze **6 consciousness methoden**:

### 1. `retrieve_similar_experiences(market_state, top_k=5)`
Haalt vergelijkbare trades op uit Chitta geheugen (RAG retrieval).

```python
similar = agent.retrieve_similar_experiences({
    'symbol': 'BTC',
    'regime': 'bullish',
    'volatility': 0.3
})
```

### 2. `reflect_recent_performance(n_trades=10)`
Analyseert recente trades en geeft aanbevelingen.

```python
reflection = agent.reflect_recent_performance(n_trades=20)
# Returns: {'insight': '...', 'action': 'continue'|'pause', ...}
```

### 3. `store_trade_experience(trade)`
Slaat een trade op in Chitta voor toekomstig leren.

```python
from backend.core.conscious.chitta_memory import TradeExperience

trade = TradeExperience(
    timestamp=datetime.now(UTC).isoformat(),
    symbol='BTC',
    action='buy',
    confidence=0.85,
    pnl=0.12,
    market_regime='bullish',
    reasoning='Breakout detected'
)
agent.store_trade_experience(trade)
```

### 4. `should_pause_trading(drawdown_limit=0.08)`
Checkt of agent moet pauzeren (loss streak, hoge drawdown).

```python
should_pause, reason = agent.should_pause_trading(drawdown_limit=0.05)
if should_pause:
    logger.warning(f"Trading paused: {reason}")
```

### 5. `generate_llm_analysis(prompt, temperature=0.3)`
Gebruikt LLM (Ollama/DeepSeek) voor analyse.

```python
result = agent.generate_llm_analysis(
    prompt="Analyze BTC trend based on recent data",
    temperature=0.3
)
# Returns: {'text': '...', 'confidence': 0.8, 'reasoning': '...'}
```

### 6. `get_conscious_stats()`
Geeft statistieken over agent consciousness.

```python
stats = agent.get_conscious_stats()
# Returns: {'trades': 150, 'strategies': 3, 'win_rate': 0.65, ...}
```

---

## Geheugen Locaties

Elke agent krijgt zijn eigen Chitta geheugen:

```
backend/data/conscious_memory/
├── analystagent_chitta/
│   └── chitta_memory.json
├── traderagent_chitta/
│   └── chitta_memory.json
├── sentimentagentv2_chitta/
│   └── chitta_memory.json
├── vedastrosignalagent_chitta/
│   └── chitta_memory.json
├── elementalorchestrator_chitta/
│   └── chitta_memory.json
└── ... (elke agent zijn eigen geheugen)
```

---

## LLM Provider Configuratie

Default configuratie per agent:

```python
self.llm_provider = create_llm_provider(
    backend="ollama",  # Of "deepseek"
    model="llama3.2"   # Of "tinyllama" voor snelle tests
)
```

Om te wisselen van LLM backend:

```python
from backend.core.llm.llm_provider import create_llm_provider, LLMBackend

# Ollama (lokaal)
agent.llm_provider = create_llm_provider(
    backend=LLMBackend.OLLAMA, 
    model="tinyllama"
)

# DeepSeek (cloud)
agent.llm_provider = create_llm_provider(
    backend=LLMBackend.DEEPSEEK, 
    model="deepseek-chat"
)
```

---

## Test Script

```python
import asyncio
from backend.agents.sentiment_agent_v2 import SentimentAgentV2

async def test_conscious_agent():
    # Initialize agent (automatisch met Chitta + LLM)
    agent = SentimentAgentV2()
    
    print(f"Agent: {agent.agent_name}")
    print(f"Has Chitta: {agent.chitta is not None}")
    print(f"Has LLM: {agent.llm_provider is not None}")
    print(f"Trades in memory: {len(agent.chitta.trades) if agent.chitta else 0}")
    
    # Test consciousness methods
    stats = agent.get_conscious_stats()
    print(f"Conscious stats: {stats}")
    
    # Test LLM
    result = agent.generate_llm_analysis("What is the meaning of trading?")
    print(f"LLM result: {result}")

asyncio.run(test_conscious_agent())
```

---

## Opmerkingen

- **Automatisch**: Alle BaseAgent subclasses krijgen Chitta zonder code wijzigingen
- **Isolated**: Elke agent heeft zijn eigen geheugen (geen conflicts)
- **Persistent**: Geheugen wordt opgeslagen naar JSON en hersteld na restart
- **Fallback**: Als LLM faalt, werkt agent gewoon verder (mock mode)

**Totaal agents verrijkt**: 27+ agents
