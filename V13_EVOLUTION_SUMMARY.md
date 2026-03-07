# V13 Evolution Summary - Multi-LLM + Dual Evolution

## Implemented Features

### 1. Multi-LLM Provider (`backend/agents/multi_llm_provider.py`)

**Failover Priority:**
1. **DeepSeek** (primary) - Uses `DEEPSEEK_API_KEY` from .env
2. **OpenAI** (fallback 1) - Uses `OPENAI_API_KEY` from .env
3. **Ollama** (local fallback) - Uses local llama3.2

**Key Features:**
- Automatic failover when provider fails
- Latency tracking per provider
- Provider-agnostic interface
- Easy to add more providers

**Usage:**
```python
from backend.agents.multi_llm_provider import get_multi_llm

llm = get_multi_llm()
response = llm.generate(
    prompt="Analyze market volatility...",
    temperature=0.3
)
# response.provider -> "deepseek" | "openai" | "ollama"
# response.latency_ms -> response time
```

---

### 2. Strategy Evolution (`backend/agents/strategy_evolution.py`)

**Langetermijn strategie aanpassingen** gebaseerd op:
- Winrate per marktregime (trending_up, ranging, trending_down)
- Performance per symbool-type
- Sharpe ratio en max drawdown
- Total PnL over time

**StrategyProfile:**
```python
@dataclass
class StrategyProfile:
    strategy_name: str
    version: int                    # Increments with each evolution
    entry_threshold: float          # Aangepast door LLM
    exit_threshold: float
    position_sizing: str            # "kelly" | "fixed" | "adaptive"
    max_positions: int
    hold_time_preference: str       # "short" | "medium" | "long"
    regime_performance: Dict        # Per-regime stats
```

**Evolution Process:**
1. Record trades with regime/context
2. Calculate metrics (winrate, sharpe, drawdown)
3. LLM analyzes performance per regime
4. Suggests parameter adjustments
5. Applies changes, increments version

**Usage:**
```python
from backend.agents.strategy_evolution import get_strategy_evolution, StrategyProfile

evolution = get_strategy_evolution()

# Register strategy
evolution.register_strategy("momentum", StrategyProfile(
    strategy_name="momentum",
    entry_threshold=0.6
))

# Record trades
evolution.record_trade(
    strategy_name="momentum",
    symbol="AAPL",
    regime="trending_up",
    pnl=0.05,
    duration_days=3
)

# Evolve when needed
if evolution.should_evolve("momentum"):
    evolution.evolve_strategy("momentum")
```

---

### 3. Prompt Evolution (`backend/agents/prompt_evolution.py`)

**LLM past eigen prompts aan** gebaseerd op:
- Success rate per prompt
- Response quality scores (1-10)
- Common error patterns
- Recent failures

**PromptTemplate:**
```python
@dataclass
class PromptTemplate:
    name: str
    version: int
    template: str                  # Evolves over time
    system_prompt: str
    few_shot_examples: List        # Bijgewerkt door LLM
    uses: int                      # Usage counter
    successes: int
    avg_response_quality: float
    evolution_history: List        # Alle versies
```

**Evolution Process:**
1. Record each prompt usage with success/failure
2. Track quality scores
3. LLM analyzes failure patterns
4. Suggests improvements:
   - Fix ambiguous instructions
   - Add better few-shot examples
   - Optimize output format
5. Updates template, increments version

**Usage:**
```python
from backend.agents.prompt_evolution import get_prompt_evolution

prompt_evo = get_prompt_evolution()

# Register prompt
prompt_evo.register_prompt(
    name="reflection",
    template="Analyze trade: {trade_data}",
    system_prompt="You are a trading analyst"
)

# Use prompt
template, system = prompt_evo.get_prompt("reflection", trade_data=...)

# Record result
prompt_evo.record_usage(
    prompt_name="reflection",
    input_data=input_str,
    output_data=output_str,
    success=True,  # or False
    quality_score=8.5
)

# Evolve when success rate drops
if prompt_evo.should_evolve("reflection"):
    prompt_evo.evolve_prompt("reflection")
```

---

### 4. MetaOrchestrator V3 (`backend/agents/meta_orchestrator_v3.py`)

**Integrates all evolution systems:**
- Uses Multi-LLM for all AI operations
- Applies Strategy parameters to filter signals
- Tracks Prompt versions per decision
- Triggers evolution cycles automatically

**AgentSignalV3:**
```python
@dataclass
class AgentSignalV3:
    # Core fields
    agent_name: str
    action: str
    confidence: float

    # Evolution metadata
    strategy_version: int      # Which strategy was active
    prompt_version: int        # Which prompt version was used
    reflection: str            # LLM-generated reflection
    confidence_adjustment: float   # From reflection
    bias_acknowledged: bool
```

**CSV Output Schema:**
```csv
timestamp,agent_name,symbol,action,confidence,reasoning,weight,rsi,adx,regime,pnl,was_correct,reflection,confidence_adjustment,bias_acknowledged,strategy_version,prompt_version,final_decision
```

---

## Test Results

```
V13 EVOLUTION TEST - Multi-LLM + Dual Evolution
============================================================

[Multi-LLM Provider]
✓ DeepSeek initialized (primary)
✓ Ollama initialized (fallback)
✓ Automatic failover working

[Strategy Evolution]
✓ consensus_weighted: 64.7% winrate, 13.36% PnL
✓ aggressive_momentum: 69.2% winrate, 14.12% PnL
✓ Evolved to v2 successfully

[MetaOrchestrator V3]
✓ 20 deliberation cycles completed
✓ 100 signals logged
✓ 5 trades executed
✓ 60 weight updates
✓ Evolution cycles triggered
```

---

## Environment Variables

Required in `.env`:
```bash
# Primary: DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat

# Fallback 1: OpenAI (optional)
OPENAI_API_KEY=sk-...

# Local: Ollama (always available)
# No key needed, uses localhost:11434
```

---

## Next Steps

1. **Fix DeepSeek API key** - Currently returns 401 (unauthorized)
2. **Add Google GenAI** - Implement in LLM provider
3. **Real-time evolution** - Trigger evolution during live trading
4. **Cross-strategy learning** - Share insights between strategies
5. **Prompt library export** - Save evolved prompts for reuse

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MetaOrchestrator V3                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Multi-LLM    │  │ Strategy     │  │ Prompt       │      │
│  │ Provider     │  │ Evolution    │  │ Evolution    │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ DeepSeek     │  │ Entry/Exit   │  │ Templates    │      │
│  │ OpenAI       │  │ Thresholds   │  │ Few-shot     │      │
│  │ Ollama       │  │ Position     │  │ System       │      │
│  └──────────────┘  │ Sizing       │  │ Prompts      │      │
│                    └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  Agent Signals → Strategy Filters → Weighted Vote → Decision│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ CSV Logging       │
                    │ + Evolution       │
                    │   Metadata        │
                    └───────────────────┘
```

---

*Status: IMPLEMENTED & TESTED*
*Date: 2026-03-06*
*Version: V13*
