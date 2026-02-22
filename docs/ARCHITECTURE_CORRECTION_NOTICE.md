# ⚠️ Architectuur Correctie Notice

> **Datum**: 22 Februari 2026  
> **Status**: CRITICAL UPDATE

---

## Wat Is Er Veranderd?

### Oorspronkelijk Advies (VEROUDERD) ❌
In de eerste versie van de documentatie adviseerden we om:
- Custom ToolBroker from scratch te bouwen
- Eigen JSON-RPC protocol te implementeren
- Handmatige schema generatie
- Custom registry/router

**Dit was een inschattingsfout.**

### Gecorrigeerd Advies (HUIDIG) ✅
We gebruiken nu:
- **Anthropic Official MCP SDK** (`pip install mcp[cli]`)
- **FastMCP** als router en registry
- **@mcp.tool()** decorator voor tool registratie
- **STDIO/SSE** transport via officiële SDK

---

## Waarom Deze Correctie?

| Probleem met Oude Advies | Oplossing met MCP SDK |
|-------------------------|----------------------|
| Custom protocol = compatibiliteit issues | Officiële SDK = 100% compatibel met Claude Desktop, Cursor, LangChain |
| Duizenden regels boilerplate code | FastMCP handelt alles af in <100 regels |
| Handmatige schema generatie | Pydantic integratie werkt out-of-the-box |
| Eigen registry onderhoud | SDK handelt discovery en routing af |

---

## Documentatie Status

### Vervangen Documenten
De volgende documenten zijn **vervangen** door de MCP SDK versie:

| Oud Document | Nieuw Document | Status |
|--------------|----------------|--------|
| `TOOLBROKER_IMPLEMENTATION_GUIDE.md` | `TOOLBROKER_MCP_SDK_IMPLEMENTATION.md` | ✅ Gebruik nieuwe versie |
| `PRD_TOOLBROKER_V18.md` | Nog steeds geldig, technische executie aangepast | ✅ Bijwerken naar MCP SDK |
| `TOOLBROKER_ARCHITECTURE_AUDIT.md` | Nog steeds geldig, conceptueel correct | ✅ Context bijwerken |

### Actieve Documenten
- ✅ `TOOLBROKER_MCP_SDK_IMPLEMENTATION.md` - **GEBRUIK DIT**
- ✅ `TOOLBROKER_AUDIT_SUMMARY.md` - Conceptueel correct
- ✅ `ARCHITECTURE_CORRECTION_NOTICE.md` - Deze file

---

## Wat Blijft Hetzelfde?

### 1. Functionele Requirements (100% behouden)
Alle FR-001 t/m FR-040 uit de PRD blijven geldig:
- VedAstro tools
- Elemental tools (Fire, Earth, Water, Ether)
- Data tools
- Execution tools

### 2. Resilience Patterns (100% behouden)
- Circuit Breaker state machine
- Retry met exponential backoff
- Failure isolatie

**Verandering**: We implementeren ze nu als **decorators** op MCP tools, niet als onderdeel van een custom broker.

### 3. V17 Financiële Constraints (100% behouden)
```python
MAX_POSITION_EUR = 2000.0          # €2k cap
MAX_HOLD_DAYS = 60                  # 60-day failsafe
TRAILING_STOP_THRESHOLD = 0.40      # +40%
TRAILING_STOP_DISTANCE = 0.15       # -15%
```

### 4. Project Scheiding (100% behouden)
- Geen code overname uit SanskritiSetu
- Volledig eigen implementatie
- Alleen concept inspiratie

---

## Wat Is Er Anders?

### Technische Implementatie

#### Oud (Custom Broker)
```python
# Custom broker
broker = ToolBroker()
broker.register_tool("name", handler)
result = await broker.execute_tool("name", params)
```

#### Nieuw (FastMCP)
```python
# FastMCP
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AgenticTraderBroker")

@mcp.tool()
async def my_tool(params: dict) -> dict:
    ...

mcp.run(transport='stdio')
```

### Voordelen Nieuwe Aanpak

1. **Mindere Code**: ~500 regels vs ~3000+ regels
2. **Betrouwbaarder**: Officiële SDK getest door Anthropic
3. **Compatibeler**: Werkt direct met Claude Desktop, Cursor, etc.
4. **Minder Bugs**: Geen custom protocol implementatie
5. **Eenvoudiger**: Decorator pattern vs complexe registry

---

## Migratie Pad

### Als Je Bent Begonnen Met Oude Aanpak

1. **Stop** met custom broker implementatie
2. **Installeer** `pip install mcp[cli]`
3. **Gebruik** `TOOLBROKER_MCP_SDK_IMPLEMENTATION.md`
4. **Behoud** resilience decorators (circuit_breaker, retry)
5. **Refactor** tools naar `@mcp.tool()` pattern

### Stap-voor-Stap Conversie

| Oud Component | Nieuw Component |
|--------------|-----------------|
| `backend/core/tool_broker/broker.py` | `backend/mcp_broker/server.py` (FastMCP) |
| `backend/core/tool_broker/registry.py` | Verwijderd (FastMCP handelt af) |
| `backend/core/tool_broker/router.py` | Verwijderd (FastMCP handelt af) |
| `backend/core/tool_broker/schemas.py` | Optioneel (Pydantic via FastMCP) |
| `backend/core/tool_broker/circuit_breaker.py` | `backend/mcp_broker/resilience/circuit_breaker.py` |
| `backend/core/tool_broker/retry.py` | `backend/mcp_broker/resilience/retry.py` |

---

## Implementatie Prioriteit

### Direct Implementeren (Week 1)
1. ✅ `backend/mcp_broker/resilience/circuit_breaker.py`
2. ✅ `backend/mcp_broker/resilience/retry.py`
3. ✅ `backend/mcp_broker/tools/elemental_tools.py`
4. ✅ `backend/mcp_broker/server.py`

### Later Toevoegen (Week 2-3)
- VedAstro tools (vereist VedAstro integratie)
- Data tools (vereist database connectie)
- Execution tools (vereist paper trading engine)

---

## Vragen?

### Waarom Niet Gewoon De Oude Aanpak Afmaken?
De oude aanpak zou werken, maar:
- Meer bugs door custom protocol
- Geen compatibiliteit met bestaande MCP clients
- Meer onderhoud
- Geen toegang tot SDK updates

### Is De Oude Documentatie Waardeloos?
**Nee!** De concepten zijn correct:
- Circuit breaker logica ✓
- Retry strategie ✓
- Tool scheiding ✓
- V17 constraints ✓

Alleen de **technische executie** is veranderd van custom naar SDK.

---

## Conclusie

De **functionele requirements** en **architecturale principes** blijven identiek. Alleen de **technische implementatie** is geoptimaliseerd door gebruik te maken van de officiële Anthropic MCP SDK.

**Belangrijkste les**: Bij twijfel, gebruik de officiële SDK in plaats van custom implementaties.

---

*Correctie uitgevoerd*: 2026-02-22  
*Door*: Code Architect  
*Status*: APPROVED
