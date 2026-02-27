---
name: strategy-versioning
description: Manage trading strategy versions (V13-V18+) with automated migration, result comparison, and new version scaffolding. Use when creating V18 from V17 results, comparing strategy versions, migrating between versions, or analyzing backtest performance across versions. Triggers include "V18", "V17", "strategy version", "migrate strategy", "compare versions", "version bump", "new strategy version", "backtest comparison", "V13 V14 V15 V16".
---

# Strategy Versioning Skill

Manage trading strategy versions with automated migration and result analysis.

## Overview

The Agentic Trader Platform uses versioned strategies (V13 → V18+). Each version represents a significant evolution in the trading algorithm.

## Version History

| Version | Key Feature | Return | Sharpe | Trades |
|---------|-------------|--------|--------|--------|
| V13 | Baseline | - | - | - |
| V14 | Elemental System | +223%* | 5.99 | 135 |
| V15 | Risk Management | +77%* | 0.77 | 386 |
| V16 | Multi-asset | +2.11% | 0.97 | 350 |
| **V17** | **VedAstro Integration** | **+6.96%** | **0.70** | **331** |
| V18 | TBD | - | - | - |

*Inflated by anomalies

## Quick Start

### Create V18 from V17

```bash
# Scaffold V18 based on V17 results
python .continue/skills/strategy-versioning/scripts/version_manager.py --create v18 --from v17

# This creates:
# - backend/agents/elemental_agent_manager_v18.py
# - scripts/backtest_elemental_v18.py
# - V18_RESULTS_SUMMARY.md
```

### Compare Versions

```bash
# Compare V16 vs V17
python .continue/skills/strategy-versioning/scripts/version_manager.py --compare v16,v17

# Show all version metrics
python .continue/skills/strategy-versioning/scripts/version_manager.py --list
```

### Analyze Improvements

```bash
# Analyze what changed between versions
python .continue/skills/strategy-versioning/scripts/version_manager.py --analyze v17 --suggest
```

## Version Manager CLI

```bash
# Create new version
python scripts/version_manager.py --create v18 --from v17 --name "Execute Rate Fix"

# Compare specific versions
python scripts/version_manager.py --compare v15,v16,v17 --metrics return,sharpe,trades

# Generate recommendations
python scripts/version_manager.py --analyze v17 --suggest --output v18_plan.md

# List all versions
python scripts/version_manager.py --list --format table
```

## Version File Structure

Each version has:

```
backend/agents/elemental_agent_manager_v{VERSION}.py    # Agent logic
scripts/backtest_elemental_v{VERSION}.py               # Backtest runner
scripts/backtest_elemental_v{VERSION}_full.py          # Full backtest
V{VERSION}_RESULTS_SUMMARY.md                          # Results doc
backtest_v{VERSION}_full_*.json                        # Result data
```

## Creating a New Version

### 1. Analyze Current Version

```bash
python scripts/version_manager.py --analyze v17 --suggest
```

### 2. Scaffold New Version

```bash
python scripts/version_manager.py --create v18 --from v17
```

### 3. Implement Changes

Edit `backend/agents/elemental_agent_manager_v18.py`:

```python
class ElementalAgentManagerV18(ElementalAgentManagerV17):
    """V18: Improved execute rate"""

    def __init__(self):
        super().__init__()
        # Relax VedAstro filters for V18
        self.vedastro_min_confidence = 0.40  # Was 0.50
        self.vedastro_min_score = 40         # Was 45
```

### 4. Run Backtest

```bash
# Smoke test
python scripts/backtest_elemental_v18.py

# Full backtest
python scripts/backtest_elemental_v18_full.py
```

### 5. Generate Summary

```bash
python scripts/version_manager.py --summarize v18
```

## Key Metrics to Track

| Metric | Target | V17 Value |
|--------|--------|-----------|
| Total Return | > 10% | +6.96% |
| Sharpe Ratio | > 1.0 | 0.70 |
| Max Drawdown | < 5% | -2.67% |
| Total Trades | 800-1500 | 331 |
| Win Rate | > 45% | 43.8% |
| Execute Rate | 15-25% | 6.34% |

## Common Improvements

### Execute Rate Issues

**Problem**: Low execute rate (6.34% vs target 15-25%)

**Solutions**:
1. Relax VedAstro filters (confidence 50% → 40%)
2. Lower min score (45 → 40)
3. Add momentum entries alongside VedAstro
4. Reduce elemental blocking

### Trade Count Issues

**Problem**: Too few trades (331 vs target 800-1500)

**Solutions**:
1. Allow "hold" signals to become entries
2. Parallel entry opportunities
3. Reduce Dasha period requirements

### Return Quality

**Problem**: Returns below target

**Solutions**:
1. Improve exit timing
2. Better position sizing
3. Add hedge logic

## References

- `references/version_history.md` - Complete version comparison
- `references/v17_analysis.md` - V17 deep dive
- `references/v18_recommendations.md` - Suggested V18 changes

## Integration

### In CI/CD

```yaml
# .github/workflows/strategy.yml
- name: Compare Versions
  run: |
    python scripts/version_manager.py --compare v16,v17
    python scripts/version_manager.py --validate v17
```

### In Reports

```python
from scripts.version_manager import generate_comparison_chart

generate_comparison_chart(
    versions=['v13', 'v14', 'v15', 'v16', 'v17'],
    metrics=['return', 'sharpe', 'trades'],
    output='version_comparison.png'
)
```
