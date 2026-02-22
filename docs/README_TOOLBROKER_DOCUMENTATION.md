# ToolBroker V18 Documentatie Index

> **Agentic Trader Platform V18**
> **MCP SDK Implementatie**
> **Laatste Update**: 22 Februari 2026

---

## ⚠️ BELANGRIJK: Lees Eerst

**[ARCHITECTURE_CORRECTION_NOTICE.md](./ARCHITECTURE_CORRECTION_NOTICE.md)**
→ Essentiële correctie op oorspronkelijk advies. MOET gelezen worden voor implementatie.

---

## 📚 Documentatie Structuur

### Start Hier
| Document | Doel | Prioriteit |
|----------|------|------------|
| [ARCHITECTURE_CORRECTION_NOTICE.md](./ARCHITECTURE_CORRECTION_NOTICE.md) | Correctie op oorspronkelijk advies | **CRITICAL** |
| [TOOLBROKER_MCP_SDK_IMPLEMENTATION.md](./TOOLBROKER_MCP_SDK_IMPLEMENTATION.md) | Complete implementatie guide | **START HIER** |

### Conceptuele Documentatie
| Document | Doel | Status |
|----------|------|--------|
| [TOOLBROKER_ARCHITECTURE_AUDIT.md](./TOOLBROKER_ARCHITECTURE_AUDIT.md) | Architecturale analyse (conceptueel correct) | Reference |
| [PRD_TOOLBROKER_V18.md](./PRD_TOOLBROKER_V18.md) | Requirements (FR/NFR) | Reference |
| [TOOLBROKER_AUDIT_SUMMARY.md](./TOOLBROKER_AUDIT_SUMMARY.md) | Samenvatting audit | Reference |

---

## 🚀 Quick Start

### Stap 1: Lees De Correctie
```bash
# Lees eerst de architectuur correctie
cat docs/ARCHITECTURE_CORRECTION_NOTICE.md
```

### Stap 2: Volg De Implementatie Guide
```bash
# Gebruik de MCP SDK implementatie guide
cat docs/TOOLBROKER_MCP_SDK_IMPLEMENTATION.md
```

### Stap 3: Start Implementatie
```bash
# 1. Installeer dependencies
pip install mcp[cli] pydantic anyio

# 2. Creëer structuur
mkdir -p backend/mcp_broker/{resilience,tools}

# 3. Implementeer (zie guide)
# - resilience/circuit_breaker.py
# - resilience/retry.py
# - tools/elemental_tools.py
# - server.py
```

---

## 📋 Documentatie Status

### ✅ Actief & Geldig
- `ARCHITECTURE_CORRECTION_NOTICE.md` - Correctie op advies
- `TOOLBROKER_MCP_SDK_IMPLEMENTATION.md` - Complete implementatie guide (~47K woorden)

### 📖 Reference Material
- `TOOLBROKER_ARCHITECTURE_AUDIT.md` - Conceptuele architectuur (~20K woorden)
- `PRD_TOOLBROKER_V18.md` - Requirements (~23K woorden)
- `TOOLBROKER_AUDIT_SUMMARY.md` - Samenvatting (~10K woorden)

### ❌ Vervangen
- `TOOLBROKER_IMPLEMENTATION_GUIDE.md` (custom broker versie) → Vervangen door MCP SDK versie

---

## 🎯 Wat Is Waar?

### Als Je Wil Begrijpen
1. Lees: `ARCHITECTURE_CORRECTION_NOTICE.md`
2. Lees: `TOOLBROKER_ARCHITECTURE_AUDIT.md` (concepten)
3. Lees: `PRD_TOOLBROKER_V18.md` (requirements)

### Als Je Wil Implementeren
1. Lees: `ARCHITECTURE_CORRECTION_NOTICE.md` (essentiële context)
2. Volg: `TOOLBROKER_MCP_SDK_IMPLEMENTATION.md` (step-by-step)
3. Test: Gebruik de test scripts in de guide

### Als Je Wil Reviewen
1. Lees: `TOOLBROKER_AUDIT_SUMMARY.md`
2. Check: `TOOLBROKER_MCP_SDK_IMPLEMENTATION.md` code kwaliteit
3. Valideer: Constraints behouden (€2k cap, 60-day failsafe)

---

## 🔑 Key Takeaways

### 1. Gebruik Altijd De MCP SDK
```python
# ✅ DOEN
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("AgenticTraderBroker")

@mcp.tool()
async def my_tool(params: dict) -> dict:
    ...

# ❌ NIET DOEN (oude aanpak)
class ToolBroker:
    def register_tool(self, name, handler): ...
```

### 2. Behoud Resilience Decorators
```python
# ✅ DOEN
@circuit_breaker(failure_threshold=5)
@retry(max_attempts=3)
@mcp.tool()
async def vedastro_generate_signal(...):
    ...
```

### 3. V17 Constraints Behouden
```python
# ✅ DOEN - €2k cap afdwingen
MAX_POSITION_EUR = 2000.0
position_size = min(raw_size, MAX_POSITION_EUR)
```

---

## 📊 Documentatie Statistieken

| Document | Woorden | Status |
|----------|---------|--------|
| ARCHITECTURE_CORRECTION_NOTICE.md | ~6,000 | ✅ Actief |
| TOOLBROKER_MCP_SDK_IMPLEMENTATION.md | ~47,000 | ✅ Actief |
| TOOLBROKER_ARCHITECTURE_AUDIT.md | ~20,000 | 📖 Reference |
| PRD_TOOLBROKER_V18.md | ~23,000 | 📖 Reference |
| TOOLBROKER_AUDIT_SUMMARY.md | ~10,000 | 📖 Reference |
| **Totaal** | **~106,000** | - |

---

## 🏗️ Implementatie Structuur

### Nieuwe Structuur (MCP SDK)
```
backend/mcp_broker/
├── __init__.py
├── server.py                    # FastMCP server
├── resilience/
│   ├── __init__.py
│   ├── circuit_breaker.py       # Decorator
│   └── retry.py                 # Decorator
└── tools/
    ├── __init__.py
    ├── vedastro_tools.py        # MCP tools
    ├── elemental_tools.py       # MCP tools
    ├── data_tools.py            # MCP tools
    └── execution_tools.py       # MCP tools
```

### Oude Structuur (Deprecated)
```
backend/core/tool_broker/        # NIET GEBRUIKEN
├── broker.py                    # Custom broker (❌)
├── registry.py                  # Custom registry (❌)
├── router.py                    # Custom router (❌)
├── schemas.py                   # Handmatige schemas (❌)
├── circuit_breaker.py           # Wel behouden als decorator
└── retry.py                     # Wel behouden als decorator
```

---

## ✅ Pre-Implementatie Checklist

- [ ] `ARCHITECTURE_CORRECTION_NOTICE.md` gelezen
- [ ] `pip install mcp[cli]` uitgevoerd
- [ ] Begrip van FastMCP decorator pattern
- [ ] V17 constraints gedocumenteerd
- [ ] Test strategie bepaald

---

## 🆘 Support

### Bij Twijfel
1. Lees `ARCHITECTURE_CORRECTION_NOTICE.md`
2. Check `TOOLBROKER_MCP_SDK_IMPLEMENTATION.md` voor code voorbeelden
3. Raadpleeg officiële MCP docs: https://modelcontextprotocol.io/

### Veelvoorkomende Vragen

**Q: Moet ik de oude documentatie nog lezen?**
A: Ja, voor conceptueel begrip. De requirements (FR/NFR) zijn nog steeds geldig.

**Q: Wat moet ik implementeren?**
A: Alleen de documenten gemarkeerd met "Actief". Reference material is voor context.

**Q: Is de oude code waardeloos?**
A: Nee, de concepten (circuit breaker, retry logica) zijn correct. Alleen de technische executie is veranderd.

---

## 📅 Roadmap

### Week 1: Fundament
- [ ] Resilience decorators implementeren
- [ ] Elemental tools refactoren naar MCP
- [ ] Basis FastMCP server draaiend

### Week 2: Integratie
- [ ] VedAstro tools toevoegen
- [ ] Data & Execution tools
- [ ] Testing & debugging

### Week 3: Productie
- [ ] BacktestEngine integratie
- [ ] Monitoring & logging
- [ ] Documentatie afronden

---

*Document Index Version: 1.0*
*Status: READY FOR IMPLEMENTATION*
*Last Updated: 2026-02-22*
