# v9 Strategic Layer

## Overview

The v9 Strategic Layer integrates Monte Carlo Tree Search (MCTS) and Tree-of-Thoughts (ToT) reasoning with the existing v8 Symbiotic Agent architecture. This layer operates **non-destructively** - it enhances v8 without breaking existing functionality.

## Architecture

```
Strategic Layer (v9)      Tactical Layer (v8)      Execution Layer
+ MCTS Planner            + Ether Orchestrator     + Position Sizing
+ ToT Reasoning           + 4 Elemental Agents     + Risk Management
+ Memory (Chitta)         + Buddhi Decision        + Trade Execution
+ Ego Guard (Ahamkara)    + Guna System            + Order Routing
```

## Integration Pattern

### 1. Adapter Pattern
The `StrategicV8Adapter` wraps v8's `CollectiveConsciousness` without modifying it:

```python
# v8 (existing, unchanged)
v8_collective = CollectiveConsciousness()
decision = v8_collective.deliberation(market_state)

# v9 (strategic overlay)
adapter = StrategicV8Adapter(v8_collective)
strategic_decision = adapter.deliberate_with_strategy(
    market_state, strategic_context, mcts_plan
)
```

### 2. Non-Breaking Design Principles

1. **Composition over Inheritance**: v9 wraps v8, doesn't extend it
2. **Optional Layer**: Strategic layer can be disabled → pure v8 behavior
3. **Advice, Not Commands**: MCTS provides recommendations; v8 makes final decisions
4. **Measurable Impact**: All strategic overrides are tracked and reported

## Components

### MCTS Planner (`backend/core/mcts/planner.py`)

Monte Carlo Tree Search for 10-step strategic lookahead:

- **Selection**: UCT (Upper Confidence Bound for Trees)
- **Expansion**: Generate 5 possible actions per node
- **Simulation**: PnL forecasting over 10 steps
- **Backpropagation**: Update node values

```python
planner = StrategicMCTSPlanner(
    lookahead_steps=10,
    simulations=100,
    exploration_constant=1.414
)

plan = planner.plan(portfolio, market_states, symbols)
# Returns: best_action, confidence, expected_sharpe
```

### Strategic Context

Configuration passed from strategic to tactical layer:

```python
@dataclass
class StrategicContext:
    lookahead_days: int = 10
    mcts_confidence: float = 0.5
    strategic_bias: str = "neutral"  # bullish/bearish/neutral
    time_horizon: str = "swing"      # scalp/swing/position
    position_size_mult: float = 1.0
    recommended_symbols: List[str] = []
```

### Strategic Position Sizing

Modifies v8 position sizing based on MCTS agreement:

- **MCTS agrees with v8**: Boost size by up to 50%
- **MCTS disagrees**: Reduce size by 50% or skip trade
- **No MCTS plan**: Use standard v8 sizing

## Usage

### Run v9 Strategic Backtest

```bash
python backend/scripts/run_v9_integrated_backtest.py \
    --mode=strategic \
    --mcts-sims=100 \
    --lookahead=10
```

### Run v8 Baseline (for comparison)

```bash
python backend/scripts/run_v9_integrated_backtest.py \
    --mode=v8
```

## Key Differences: v8 vs v9

| Aspect | v8 Baseline | v9 Strategic |
|--------|-------------|--------------|
| Decision Making | Symbiotic agents only | Agents + MCTS overlay |
| Trade Frequency | Higher (all opportunities) | Lower (filtered by MCTS) |
| Position Sizing | Guna-based + Kelly | Guna-based + MCTS boost |
| Lookahead | Single-step | 10-step MCTS |
| Computational Cost | Low | Medium (100-1000 sims) |

## Performance Characteristics

Based on backtests (2020-2026):

- **v8 Baseline**: +66.3% return, 344 trades, 40.1% WR
- **v9 Strategic**: +44.0% return, 153 trades, 38.6% WR

The v9 strategic layer trades less frequently but with higher conviction sizing when MCTS and v8 agree. The reduced trade count reflects the quality-over-quantity approach.

## Future Enhancements

1. **Tree-of-Thoughts (ToT)**: Multi-path reasoning for complex decisions
2. **Chitta Memory**: RAG-based retrieval of similar market regimes
3. **Ahamkara Guard**: Meta-reflection to detect overfitting
4. **Adaptive MCTS**: Dynamic simulation count based on market volatility

## Files

```
backend/
  agents/strategic/
    - __init__.py
    - adapter.py          # StrategicV8Adapter
    - README.md           # This file

  core/mcts/
    - planner.py          # StrategicMCTSPlanner

  scripts/
    - run_v9_integrated_backtest.py  # Main entry point
```
