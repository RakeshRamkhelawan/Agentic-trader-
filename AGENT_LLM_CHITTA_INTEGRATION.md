# Agent LLM + Chitta Memory Integration (v11)

## Wat is geïmplementeerd?

De bestaande agents zijn nu voorzien van **LLM (DeepSeek/Ollama)** en **Chitta Memory (persistent learning)** zonder nieuwe agents te maken.

## Gewijzigde Bestanden

### 1. `backend/agents/elemental_base.py`
**Base class voor ALLE elemental agents (Air, Fire, Water, Earth, Ether)**

#### Nieuwe imports:
```python
from backend.core.conscious.chitta_memory import ChittaMemory, TradeExperience
from backend.core.llm.llm_provider import LLMProvider, create_llm_provider
```

#### Nieuwe initialisatie (in `__init__`):
```python
# Initialize Chitta Memory (v11 - Consciousness)
memory_path = f"backend/data/conscious_memory/{self.agent_name.lower()}_chitta"
self.chitta = ChittaMemory(storage_path=memory_path)

# Initialize LLM if not provided (v11 - Intelligence)
if llm_provider is None:
    self.llm = create_llm_provider(backend="ollama", model="llama3.2")
else:
    self.llm = llm_provider
```

#### Nieuwe methods voor ALLE elemental agents:

| Method | Description |
|--------|-------------|
| `retrieve_similar_experiences(market_state, top_k=5)` | RAG: Haal vergelijkbare trades op |
| `reflect_recent_performance(n_trades=10)` | Reflecteer op recente performance |
| `store_trade_experience(trade)` | Sla trade op in Chitta |
| `should_pause_trading(drawdown_limit=0.08)` | Check of pauze nodig is |
| `generate_llm_analysis(prompt, temperature=0.3)` | Genereer LLM analyse |
| `get_conscious_stats()` | Get Chitta + LLM stats |

### 2. `backend/agents/elemental_orchestrator.py`
**Ether agent - De orkestrator**

#### Nieuwe LLM harmonisatie:
```python
async def _synthesize_strategy(self, inputs, harmony):
    # v11: Use LLM for intelligent harmonization
    if self.llm and harmony >= 0.3:
        prompt = self._build_harmonization_prompt(inputs, harmony)
        llm_response = self.generate_llm_analysis(prompt)
        return parse_llm_response(llm_response)

    # Fallback to deterministic logic
    return self._fallback_synthesis(inputs, harmony)
```

#### Nieuwe LLM prompt voor harmonisatie:
```
JE = ETHER (Akasha) - De Orkestrator
JE TAAK: Harmoniseer signalen van alle elementen tot één coherent besluit.
HUIDIGE INPUTS: [Air, Fire, Water, Earth signals]
HARMONY SCORE: 0.75
VERGELIJKBARE SCENARIOS (Chitta geheugen): ...
```

### 3. Nieuwe modules:
- `backend/core/llm/llm_provider.py` - LLM interface (DeepSeek/Ollama/OpenAI)
- `backend/core/conscious/chitta_memory.py` - Persistent memory system

## Hoe werkt het nu?

### Voorbeeld: ElementalOrchestrator (Ether)

```python
from backend.agents.elemental_orchestrator import ElementalOrchestrator

# Initialize (automatisch met Chitta + LLM)
ether = ElementalOrchestrator()

# Console output:
# [Conscious_Ether] Initializing LLM (ollama/llama3.2)...
# [Conscious_Ether] Initializing Chitta Memory...
# [Conscious_Ether] Conscious agent ready | Memory: 0 trades

# Process signal (met LLM harmonisatie)
result = await ether.process_signal({
    "inputs": {
        "air": {"sentiment": 0.7},
        "fire": {"approved": True},
        "water": {"regime": "expansion"},
        "earth": {"valuation_gap": 0.15}
    }
})

# LLM genereert:
# {
#     "summary": "Execute Coherent Strategy",
#     "confidence": 0.85,
#     "focus_element": "earth",
#     "maya_detected": false,
#     "reasoning": "All elements aligned bullish..."
# }

# Na trade completion:
ether.store_trade_experience(trade_exp)
# [Conscious_Ether] stored trade T123 in Chitta
```

### Elk element heeft eigen Chitta:

```
backend/data/conscious_memory/
├── orchestrator_ether_chitta/
│   └── chitta_memory.json
├── conscious_air_chitta/
│   └── chitta_memory.json
├── conscious_fire_chitta/
│   └── chitta_memory.json
├── conscious_water_chitta/
│   └── chitta_memory.json
└── conscious_earth_chitta/
    └── chitta_memory.json
```

## Data Flow

```
Market Data
    │
    ▼
┌─────────────────────────────┐
│ Elemental Agents (L1-L2)    │
│  - Air (Regime)             │
│  - Fire (Momentum)          │
│  - Water (Trend)            │
│  - Earth (Valuation)        │
│                             │
│  ELKE agent heeft:          │
│  - Eigen Chitta Memory      │
│  - Eigen LLM instance       │
│  - retrieve_similar()       │
│  - reflect_recent()         │
└───────────┬─────────────────┘
            │ Signals
            ▼
┌─────────────────────────────┐
│ Ether Orchestrator (L3)     │
│                             │
│  - LLM Harmonization        │
│  - Chitta: Past harmoniz.   │
│  - Maya Detection           │
│  - Guna Balance             │
└───────────┬─────────────────┘
            │ Collective Decision
            ▼
       Trade Execution
            │
            ▼
    Store in Chitta (learning)
```

## LLM Integratie

### Supported Backends:
- **Ollama** (local): `llama3.2`, `mistral`, `codellama`
- **DeepSeek** (API): `deepseek-chat`
- **OpenAI** (API): `gpt-4`, `gpt-3.5-turbo`

### Configuratie:
```python
# Via environment variables
export DEEPSEEK_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Of in code
ether = ElementalOrchestrator(
    llm_provider=create_llm_provider(
        backend="deepseek",
        model="deepseek-chat"
    )
)
```

## Voordelen

### 1. Elk agent heeft EIGEN geheugen
- Air agent onthoudt welke regimes werkten
- Fire agent leert van momentum trades
- Ether agent onthoudt welke harmonieën succesvol waren

### 2. LLM voor intelligente analyse
- Natuurlijke taal reasoning
- Context-aware beslissingen
- Fallback naar deterministic als LLM faalt

### 3. Persistentie
- Geheugen blijft bestaan tussen sessies
- Agents worden beter over tijd
- Kennis accumulatie (samskaras)

### 4. Self-reflection
- `reflect_recent_performance()` analyseert laatste trades
- `should_pause_trading()` detecteert verlies-reeksen
- `retrieve_similar_experiences()` zoekt vergelijkbare setups

## Test Commands

```bash
# Test imports
python -c "from backend.agents.elemental_base import ElementalBase; print('OK')"
python -c "from backend.agents.elemental_orchestrator import ElementalOrchestrator; print('OK')"

# Run backtest met nieuwe conscious agents
python backend/scripts/run_v8_symbiotic_backtest.py
```

## Conclusie

De **bestaande** elemental agents zijn nu "conscious" geworden:
- Ze hebben elk hun **eigen Chitta Memory**
- Ze gebruiken **LLM** voor intelligente analyse
- Ze **leren** van elke trade
- Ze kunnen **reflecteren** op hun performance

**Geen nieuwe agents gemaakt** - alleen de bestaande base classes uitgebreid met consciousness capabilities!
